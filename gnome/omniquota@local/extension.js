import Gio from 'gi://Gio';
import St from 'gi://St';
import Clutter from 'gi://Clutter';
import {Extension} from 'resource:///org/gnome/shell/extensions/extension.js';
import * as Main from 'resource:///org/gnome/shell/ui/main.js';
import * as PanelMenu from 'resource:///org/gnome/shell/ui/panelMenu.js';
import * as PopupMenu from 'resource:///org/gnome/shell/ui/popupMenu.js';

const xml = `<node><interface name="io.github.omniquota.Service">
<method name="GetState"><arg type="s" direction="out"/></method>
<method name="Refresh"/><method name="OpenSettings"/><method name="Logout"/>
<signal name="StateChanged"><arg type="s"/></signal>
</interface></node>`;
const Proxy = Gio.DBusProxy.makeProxyWrapper(xml);

export default class OmniRoute Cota extends Extension {
    enable() {
        this._active = true;
        this._button = new PanelMenu.Button(0.0, 'OmniRoute Cota');
        this._value = null;
        const row = new St.BoxLayout({style: 'spacing: 5px;'});
        this._ring = new St.DrawingArea({width: 18, height: 18, y_align: Clutter.ActorAlign.CENTER});
        this._ring.connect('repaint', area => {
            const [width, height] = area.get_surface_size();
            const cr = area.get_context();
            const radius = Math.max(0, Math.min(width, height) / 2 - 2);
            cr.setLineWidth(1.5);
            cr.setSourceRGBA(0.5, 0.5, 0.5, 0.6);
            cr.arc(width / 2, height / 2, radius, 0, Math.PI * 2);
            cr.stroke();
            if (typeof this._value === 'number') {
                cr.setSourceRGBA(0.18, 0.8, 0.44, 1);
                cr.arc(width / 2, height / 2, radius, -Math.PI / 2,
                    -Math.PI / 2 + Math.PI * 2 * Math.max(0, Math.min(100, this._value)) / 100);
                cr.stroke();
            }
            cr.$dispose();
        });
        this._label = new St.Label({text: '—', y_align: Clutter.ActorAlign.CENTER});
        row.add_child(this._ring);
        row.add_child(this._label);
        this._button.add_child(row);
        Main.panel.addToStatusArea(this.uuid, this._button);
        this._render({message: 'Conectando ao serviço…'});
        this._proxy = new Proxy(Gio.DBus.session, 'io.github.omniquota.Service',
            '/io/github/omniquota/Service', (proxy, error) => {
                if (!this._active) return;
                if (error) { this._render({message: 'Instale/inicie o serviço OmniRoute Cota.'}); return; }
                this._signal = proxy.connectSignal('StateChanged', (_p, _s, [state]) => this._parse(state));
                proxy.GetStateRemote((result, err) => {
                    if (!this._active) return;
                    if (err) this._render({message: 'Serviço indisponível.'});
                    else this._parse(result[0]);
                });
            });
    }

    _parse(raw) {
        if (!this._active) return;
        try { this._render(JSON.parse(raw)); }
        catch (_) { this._render({message: 'Estado inválido do serviço.'}); }
    }

    _call(method) {
        this._proxy?.[`${method}Remote`]((_result, error) => {
            if (error && this._active) this._render({message: 'Operação falhou; aguarde e tente novamente.'});
        });
    }

    _render(state) {
        const value = state.remainingPercent;
        this._value = value;
        this._ring.queue_repaint();
        this._label.text = `${typeof value === 'number' ? Math.round(value) + '%' : '—'}${state.stale ? ' *' : ''}`;
        this._button.menu.removeAll();
        const info = text => this._button.menu.addMenuItem(new PopupMenu.PopupMenuItem(text, {reactive: false}));
        info('OmniRoute Cota');
        for (const w of state.windows ?? []) {
            info(`${w.label} · ${typeof w.remainingPercent === 'number' ? Math.round(w.remainingPercent) + '% restante' : 'indisponível'}`);
            const item = new PopupMenu.PopupBaseMenuItem({reactive: false});
            const track = new St.Widget({style: 'background-color: rgba(128,128,128,0.35); border-radius: 3px;',
                width: 250, height: 6, y_align: Clutter.ActorAlign.CENTER});
            const fill = new St.Widget({style: 'background-color: #2ecc71; border-radius: 3px;',
                width: 250 * (typeof w.remainingPercent === 'number' ? Math.max(0, Math.min(100, w.remainingPercent)) / 100 : 0), height: 6});
            track.add_child(fill);
            item.add_child(track);
            this._button.menu.addMenuItem(item);
            if (w.resetAt) {
                const date = new Date(w.resetAt);
                if (!Number.isNaN(date.getTime())) {
                    const formatted = new Intl.DateTimeFormat('pt-BR', {
                        day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit',
                    }).format(date);
                    const minutes = Math.max(0, Math.ceil((date.getTime() - Date.now()) / 60000));
                    const duration = minutes >= 1440
                        ? `${Math.floor(minutes / 1440)}d ${Math.floor(minutes % 1440 / 60)}h`
                        : `${Math.floor(minutes / 60)}h ${minutes % 60}min`;
                    info(`Renova ${formatted} · ${minutes ? 'em ' + duration : 'aguardando atualização'}`);
                }
            }
        }
        if (typeof state.bankedResetCredits === 'number')
            info(`Resets disponíveis: ${state.bankedResetCredits}`);
        if (state.stale) info('Dados desatualizados');
        if (!(state.windows ?? []).length) info(state.message || 'Entre para consultar sua cota.');
        this._button.menu.addMenuItem(new PopupMenu.PopupSeparatorMenuItem());
        for (const [label, method] of [['Atualizar','Refresh'],['Configurações','OpenSettings']]) {
            const item = new PopupMenu.PopupMenuItem(label);
            item.connect('activate', () => this._call(method));
            this._button.menu.addMenuItem(item);
        }
    }

    disable() {
        this._active = false;
        if (this._signal) this._proxy.disconnectSignal(this._signal);
        this._signal = null;
        this._proxy = null;
        this._button?.destroy();
        this._button = null;
        this._label = null;
    }
}
