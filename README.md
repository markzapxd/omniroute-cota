# OmniRoute Cota

Monitor de cota do **OmniRoute** para a barra do **GNOME** e **KDE Plasma**.

## Como funciona

- O anel verde e o percentual mostram a **cota restante**, não o consumo.
- Ao clicar, aparecem os limites, a renovação e os **resets disponíveis**, quando informados pelo servidor.
- Consulta automaticamente a cada 60 segundos. Se houver vários limites, o painel mostra o menor saldo conhecido.
- Login com a senha do painel OmniRoute. Sessão no chaveiro do sistema; **Lembrar senha** permite refazer o login quando expirar.

Requer uma instância OmniRoute acessível e chaveiro Secret Service desbloqueado, como GNOME Keyring ou KWallet compatível. MFA/OIDC ainda não são suportados.

## Instalar no Ubuntu / Debian

Execute os comandos dentro da sua sessão gráfica, sem usar `sudo` no instalador do projeto.

### 1. Dependências e código

```bash
sudo apt update
sudo apt install git python3 python3-gi gir1.2-gtk-4.0 gir1.2-secret-1 gnome-keyring libglib2.0-bin

git clone https://github.com/markzapxd/omniroute-cota.git
cd omniroute-cota
```

Se já usa KWallet com Secret Service, pode usar esse chaveiro em vez do GNOME Keyring. Evite executar dois provedores concorrentes.

### 2. Escolha seu desktop

#### GNOME Shell 45–50

Confira a versão:

```bash
gnome-shell --version
```

Instale e ative:

```bash
bash scripts/install-user.sh --service --gnome
gnome-extensions enable omniquota@local
```

Se disser que a extensão não existe, **saia da sessão e entre novamente**, depois repita o comando de ativação. Também é possível habilitar **OmniRoute Cota** pelo aplicativo Extensões.

#### KDE Plasma 6

Requer **Qt 6.5+**, CMake 3.21+ e compilador C++17. Distribuições com Plasma 5 ou Qt mais antigo não são suportadas por esta interface.

```bash
sudo apt install cmake g++ qt6-base-dev qt6-declarative-dev
bash scripts/install-user.sh --service --kde
```

Clique com o botão direito no painel → **Adicionar widgets** → procure **OmniRoute Cota** e arraste para a barra. Se não aparecer, saia da sessão e entre novamente.

## Iniciar e entrar

O instalador inicia o serviço. Para iniciar manualmente e abrir o login:

```bash
systemctl --user start omniquota.service
~/.local/bin/omniquota-settings
```

Preencha:

- **Servidor:** URL da sua instância, como `https://omniroute.exemplo.com`, sem `/api/...`.
- **ID da conexão:** ID da conta cuja cota deseja acompanhar. É o trecho após `/api/usage/` na requisição do dashboard; substitua o ID pré-preenchido se necessário.
- **Senha:** a mesma usada para entrar no painel OmniRoute.
- **Lembrar senha:** opcional; salva no chaveiro para renovar o login automaticamente, sem refresh token.

Prefira **HTTPS**. HTTP exige confirmação e transmite senha e sessão sem criptografia.

## Atualizar e recarregar

Na pasta do projeto:

```bash
git pull

# GNOME:
bash scripts/install-user.sh --service --gnome --reload

# OU KDE:
bash scripts/install-user.sh --service --kde --reload
```

Para apenas recarregar a instalação atual:

```bash
bash scripts/reload-user.sh
```

No KDE, a barra desaparece por alguns segundos enquanto o Plasma Shell reinicia. No GNOME, o script desativa/ativa a extensão, mas mudanças de JavaScript podem exigir sair e entrar na sessão por causa do cache. Não é necessário reiniciar o computador. Sua configuração e login são preservados.

## Se não funcionar

```bash
# Estado do serviço
systemctl --user status omniquota.service

# Logs
journalctl --user -u omniquota.service -n 50 --no-pager

# Estado da extensão, dentro do GNOME
gnome-extensions info omniquota@local
```

Não compartilhe senhas ou cookies nos logs.

---

Projeto independente, não oficial. Layout KDE adaptado de [izll/plasma-claude-usage](https://github.com/izll/plasma-claude-usage). Licença **GPL-3.0-or-later**; consulte [LICENSE](LICENSE).
