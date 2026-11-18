import json
import gi
gi.require_version('Gtk','4.0')
from gi.repository import Gtk, Gio, GLib
from .service import NAME, PATH

class LoginApp(Gtk.Application):
    def __init__(self):
        super().__init__(application_id='io.github.omniquota.Settings')
        self.connect('activate',self.activate)

    def activate(self,app):
        if self.get_active_window(): self.get_active_window().present(); return
        self.proxy = Gio.DBusProxy.new_for_bus_sync(Gio.BusType.SESSION,Gio.DBusProxyFlags.NONE,None,NAME,PATH,NAME,None)
        win = Gtk.ApplicationWindow(application=self,title='OmniRoute Cota — entrar')
        win.set_default_size(460,460)
        box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL,spacing=12,margin_top=20,margin_bottom=20,margin_start=20,margin_end=20)
        win.set_child(box)
        self.url = Gtk.Entry(placeholder_text='https://servidor:porta')
        self.connection = Gtk.Entry(placeholder_text='ID da conexão')
        self.password = Gtk.PasswordEntry(show_peek_icon=True)
        self.remember = Gtk.CheckButton(label='Lembrar senha no chaveiro para renovar o login')
        self.http = Gtk.CheckButton(label='Permitir HTTP (senha e sessão SEM criptografia)')
        self.message = Gtk.Label(wrap=True,xalign=0)
        for title, widget in [('Servidor',self.url),('ID da conexão',self.connection),('Senha do OmniRoute',self.password)]:
            box.append(Gtk.Label(label=title,xalign=0)); box.append(widget)
        box.append(self.remember); box.append(self.http)
        box.append(Gtk.Label(label='Sem refresh token: a renovação usa novo login.\nMFA/OIDC não são suportados nesta versão.',wrap=True,xalign=0))
        self.button = Gtk.Button(label='Salvar e entrar')
        self.button.connect('clicked',self.login)
        box.append(self.button); box.append(self.message)
        self.proxy.call('GetConfig',None,Gio.DBusCallFlags.NONE,5000,None,self.configured)
        win.present()

    def configured(self,proxy,result):
        try:
            data = json.loads(proxy.call_finish(result).unpack()[0])
            self.url.set_text(data['baseUrl']); self.connection.set_text(data['connectionId'])
            self.http.set_active(data.get('allowHttp',False))
        except Exception: self.message.set_text('Não foi possível ler a configuração.')

    def login(self,button):
        button.set_sensitive(False)
        config = {'baseUrl':self.url.get_text(),'connectionId':self.connection.get_text(),'allowHttp':self.http.get_active()}
        self.proxy.call('Configure',GLib.Variant('(s)',(json.dumps(config),)),Gio.DBusCallFlags.NONE,5000,None,self.saved)

    def saved(self,proxy,result):
        try: proxy.call_finish(result)
        except Exception:
            self.message.set_text('Confira a URL, o ID e a permissão de HTTP; aguarde se houver consulta em andamento.')
            self.button.set_sensitive(True); return
        password = self.password.get_text()
        self.password.set_text('')
        self.proxy.call('Login',GLib.Variant('(sb)',(password,self.remember.get_active())),Gio.DBusCallFlags.NONE,60000,None,self.logged_in)
        self.message.set_text('Entrando…')

    def logged_in(self,proxy,result):
        self.button.set_sensitive(True)
        try:
            proxy.call_finish(result)
            self.message.set_text('Sessão salva no chaveiro. Você pode fechar esta janela.')
        except Exception:
            self.proxy.call('GetState',None,Gio.DBusCallFlags.NONE,5000,None,self.show_error)

    def show_error(self,proxy,result):
        try: self.message.set_text(json.loads(proxy.call_finish(result).unpack()[0])['message'])
        except Exception: self.message.set_text('Serviço indisponível.')

if __name__ == '__main__': LoginApp().run(None)
