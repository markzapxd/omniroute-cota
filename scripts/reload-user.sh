#!/usr/bin/env bash
set -euo pipefail
systemctl --user restart omniquota.service
case ":${XDG_CURRENT_DESKTOP:-}:" in
    *:GNOME:*|*:gnome:*)
        if ! command -v gnome-extensions >/dev/null; then
            printf 'Serviço atualizado; gnome-extensions não está disponível. Reative a extensão pelo app Extensões.\n'
            exit 0
        fi
        gnome-extensions disable omniquota@local || true
        if ! gnome-extensions enable omniquota@local; then
            printf 'Não foi possível ativar a extensão. Saia e entre na sessão GNOME.\n' >&2
            exit 1
        fi
        printf 'Extensão reativada. Se o JavaScript continuar antigo, é necessário sair e entrar na sessão (cache do GNOME).\n'
        ;;
    *:KDE:*|*:Plasma:*)
        printf 'Reiniciando apenas o Plasma Shell; a barra desaparecerá por alguns segundos.\n'
        systemctl --user restart plasma-plasmashell.service
        ;;
    *) printf 'Serviço atualizado. Desktop não reconhecido; interface não reiniciada.\n';;
esac
