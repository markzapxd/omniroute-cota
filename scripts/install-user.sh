#!/usr/bin/env bash
set -euo pipefail
root=$(CDPATH= cd -- "$(dirname -- "$0")/.." && pwd)
data=${XDG_DATA_HOME:-$HOME/.local/share}
config=${XDG_CONFIG_HOME:-$HOME/.config}
bin=$HOME/.local/bin
service=0; gnome=0; kde=0
if (($# == 0)); then printf 'Uso: bash scripts/install-user.sh --service [--gnome] [--kde]\n'; exit 0; fi
for arg in "$@"; do
    case "$arg" in
        --service) service=1;; --gnome) gnome=1;; --kde) kde=1;;
        *) printf 'Opção desconhecida: %s\n' "$arg" >&2; exit 2;;
    esac
done
# Validate destinations before replacing app-owned files.
for path in "$data/omniquota" "$data/gnome-shell/extensions/omniquota@local" "$data/plasma/plasmoids/io.github.omniquota"; do
    if [[ -L "$path" ]]; then printf 'Destino é symlink; recuso sobrescrever: %s\n' "$path" >&2; exit 1; fi
done
if ((service)); then
    mkdir -p "$data/omniquota" "$data/dbus-1/services" "$data/applications" "$config/systemd/user" "$bin"
    cp -R "$root/service" "$root/interfaces" "$data/omniquota/"
    # %q protects shell paths in the launcher; unit paths are quoted separately below.
    python=${OMNIQUOTA_PYTHON:-$(command -v python3)}
    printf '#!/usr/bin/env bash\nexport PYTHONPATH=%q\nif [[ ${1:-} == --help ]]; then printf "OmniQuota service\\n"; exit 0; fi\nexec %q -m omniquota.service "$@"\n' "$data/omniquota/service" "$python" > "$bin/omniquota-service"
    printf '#!/usr/bin/env bash\nexport PYTHONPATH=%q\nexec %q -m omniquota.login "$@"\n' "$data/omniquota/service" "$python" > "$bin/omniquota-settings"
    # Preserve introspection/runtime paths needed outside the nix-shell.
    for launcher in "$bin/omniquota-service" "$bin/omniquota-settings"; do
        runtime=$(mktemp)
        { printf '#!/usr/bin/env bash\n';
          for variable in GI_TYPELIB_PATH LD_LIBRARY_PATH XDG_DATA_DIRS; do
              if [[ -n ${!variable:-} ]]; then printf 'export %s=%q\n' "$variable" "${!variable}"; fi
          done
          while IFS= read -r line; do [[ $line == '#!/usr/bin/env bash' ]] || printf '%s\n' "$line"; done < "$launcher"
        } > "$runtime"
        cp "$runtime" "$launcher"; rm "$runtime"
    done
    chmod 755 "$bin/omniquota-service" "$bin/omniquota-settings"
    printf '[D-BUS Service]\nName=io.github.omniquota.Service\nExec="%s/omniquota-service"\nSystemdService=omniquota.service\n' "$bin" > "$data/dbus-1/services/io.github.omniquota.Service.service"
    printf '[Unit]\nDescription=OmniQuota quota indicator service\n[Service]\nType=dbus\nBusName=io.github.omniquota.Service\nExecStart="%s/omniquota-service"\n' "$bin" > "$config/systemd/user/omniquota.service"
    printf '[Desktop Entry]\nType=Application\nName=OmniQuota Settings\nExec="%s/omniquota-settings"\nIcon=view-statistics\nCategories=Utility;\nTerminal=false\n' "$bin" > "$data/applications/io.github.omniquota.Settings.desktop"
    if [[ ${OMNIQUOTA_NO_ACTIVATE:-0} != 1 ]]; then systemctl --user daemon-reload; fi
fi
if ((gnome)); then
    mkdir -p "$data/gnome-shell/extensions/omniquota@local"
    cp "$root/gnome/omniquota@local/metadata.json" "$root/gnome/omniquota@local/extension.js" "$data/gnome-shell/extensions/omniquota@local/"
fi
if ((kde)); then
    build=${OMNIQUOTA_BUILD_DIR:-$root/build/kde-user}
    cmake -S "$root/kde/bridge" -B "$build" -DCMAKE_BUILD_TYPE=Release
    cmake --build "$build" --parallel 2
    mkdir -p "$data/plasma/plasmoids/io.github.omniquota"
    cp -R "$root/kde/package/." "$data/plasma/plasmoids/io.github.omniquota/"
    cmake --install "$build" --prefix "$data/plasma/plasmoids/io.github.omniquota/bridge"
fi
printf 'Arquivos instalados. GNOME: habilite omniquota@local após novo login. KDE: adicione o widget OmniQuota.\n'
