"""Session-bus service. Network/keyring work is serialized off the GTK main loop."""
import json
import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import gi
gi.require_version('Gio','2.0')
from gi.repository import Gio, GLib
from .client import Client, ApiError
from .config import CONFIG_PATH, load_config, save_config, validate_config
from .engine import Engine
from .secrets import SecretStore

NAME = 'io.github.omniquota.Service'
PATH = '/io/github/omniquota/Service'
ROOT = Path(__file__).resolve().parents[2]

class Service:
    def __init__(self):
        self.engine = Engine()
        self.config = load_config()
        self.pool = ThreadPoolExecutor(max_workers=1)
        self.client = None
        self.connection = None
        self.timer = 0
        self.owner = Gio.bus_own_name(Gio.BusType.SESSION, NAME, Gio.BusNameOwnerFlags.NONE,
                                      None, self.acquired, self.lost)

    def lost(self, connection, name):
        # Exit rather than poll anonymously when another instance owns the name.
        if self.timer: GLib.source_remove(self.timer); self.timer = 0
        self.pool.shutdown(wait=False,cancel_futures=True)
        if hasattr(self,'loop'): self.loop.quit()

    def acquired(self, connection, name):
        self.connection = connection
        xml = (ROOT/'interfaces/io.github.omniquota.Service.xml').read_text()
        info = Gio.DBusNodeInfo.new_for_xml(xml)
        self.registration = connection.register_object(PATH,info.interfaces[0],self.call,None,None)
        if self.config['connectionId']: self.refresh()

    def emit(self):
        self.connection.emit_signal(None,PATH,NAME,'StateChanged',GLib.Variant('(s)',(json.dumps(self.engine.state),)))

    def schedule(self):
        if self.timer: GLib.source_remove(self.timer)
        self.timer = GLib.timeout_add_seconds(self.engine.delay,self.tick)

    def tick(self):
        self.timer = 0
        self.refresh()
        return GLib.SOURCE_REMOVE

    def submit(self, work, reply=None):
        ticket = self.engine.begin()
        if ticket is None:
            if reply: reply.return_dbus_error(NAME+'.Busy','Uma operação já está em andamento.')
            return
        future = self.pool.submit(work)
        future.add_done_callback(lambda f: GLib.idle_add(self.done,ticket,f,reply))

    def done(self,ticket,future,reply):
        try:
            payload = future.result()
            self.engine.success(ticket,payload)
            if reply: reply.return_value(None)
        except Exception as error:
            self.engine.failure(ticket,error)
            if reply: reply.return_dbus_error(NAME+'.Failed',self.engine.state['message'])
        self.emit()
        if self.engine.state['status'] != 'signed-out': self.schedule()
        return GLib.SOURCE_REMOVE

    def ensure_client(self):
        if self.client is None:
            self.client = Client(self.config['baseUrl'],SecretStore())
        return self.client

    def refresh(self):
        if not self.config['connectionId']: return
        def work():
            return self.ensure_client().fetch_usage(self.config['connectionId'])
        self.submit(work)

    def call(self,connection,sender,path,interface,method,params,reply):
        try:
            args = params.unpack()
            if method == 'GetState':
                reply.return_value(GLib.Variant('(s)',(json.dumps(self.engine.state),)))
            elif method == 'GetConfig':
                reply.return_value(GLib.Variant('(s)',(json.dumps(self.config),)))
            elif method == 'OpenSettings':
                subprocess.Popen([sys.executable,'-m','omniquota.login'])
                reply.return_value(None)
            elif method == 'Refresh':
                self.refresh(); reply.return_value(None)
            elif method == 'Configure':
                if self.engine.busy: raise ValueError('Aguarde a operação atual terminar.')
                config = validate_config(json.loads(args[0]))
                # Configuration changes never race keyring writes from a worker.
                self.config = save_config(CONFIG_PATH,config)
                self.client = None
                self.engine.reset()
                if self.timer: GLib.source_remove(self.timer); self.timer = 0
                self.emit(); reply.return_value(None)
            elif method == 'Login':
                password,remember = args
                if not self.config['connectionId']: raise ValueError('Configure a conexão primeiro.')
                def work():
                    client = self.ensure_client()
                    client.login(password,remember)
                    return client.fetch_usage(self.config['connectionId'])
                self.submit(work,reply)
            elif method == 'Logout':
                if self.engine.busy: raise ValueError('Aguarde a operação atual terminar antes de sair.')
                if self.timer: GLib.source_remove(self.timer); self.timer = 0
                def work():
                    self.ensure_client().logout()
                    return {}
                ticket = self.engine.begin()
                future = self.pool.submit(work)
                def finish(f):
                    def on_main():
                        try:
                            f.result(); self.engine.reset(); self.emit(); reply.return_value(None)
                        except Exception:
                            self.engine.failure(ticket,RuntimeError()); self.emit()
                            reply.return_dbus_error(NAME+'.Failed','Falha ao limpar o chaveiro; tente novamente.')
                        return False
                    GLib.idle_add(on_main)
                future.add_done_callback(finish)
            else: reply.return_dbus_error(NAME+'.Unknown','Método desconhecido.')
        except Exception:
            reply.return_dbus_error(NAME+'.Invalid','Configuração inválida ou operação em andamento; aguarde e confira os campos.')

    def close(self):
        if self.timer: GLib.source_remove(self.timer)
        self.pool.shutdown(wait=True,cancel_futures=True)
        Gio.bus_unown_name(self.owner)


def main():
    service = Service()
    loop = GLib.MainLoop()
    service.loop = loop
    try: loop.run()
    except KeyboardInterrupt: pass
    finally: service.close()

if __name__ == '__main__': main()
