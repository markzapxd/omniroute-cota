# OmniRoute Cota

**Analisador e monitor de cota para o OmniRoute**, direto na barra do Linux. Disponível como extensão do GNOME Shell e widget do KDE Plasma.

Um anel verde e a porcentagem mostram quanto você **ainda pode usar**. Clique para consultar os limites disponíveis e quando eles renovam, sem precisar abrir o dashboard.

> Projeto independente, não oficial. Requer uma instância OmniRoute acessível e uma conta com acesso ao seu painel.

## Recursos

- Anel verde fino + percentual restante no painel.
- Detalhes por janela de limite e horário de renovação; só aparecem limites informados pela API.
- Atualização automática a cada 60 segundos, sem consultas sobrepostas.
- Serviço compartilhado entre GNOME e KDE; login por uma janela local.
- Sessão no chaveiro do sistema. Senha salva apenas se você escolher **Lembrar senha**.
- Renovação por novo login quando a sessão expira e existe senha salva; não é um refresh token.
- Erros e dados desatualizados identificados; espera progressiva após falhas e respeito a `Retry-After`.

**Como ler:** 91% significa **91% restante**, não 91% consumido. Se houver várias janelas, o indicador usa o menor saldo conhecido, sem somar capacidades diferentes. Cota desconhecida aparece como `—`.

## Compatibilidade

| Componente | Requisitos |
| --- | --- |
| Serviço | Linux, Python 3.10+, PyGObject/Gio, GTK4, libsecret e D-Bus de sessão |
| Chaveiro | Secret Service desbloqueado, como GNOME Keyring ou KWallet com esse serviço habilitado |
| GNOME | Shell 45–50 declarado nos metadados; carregamento e indicador conferidos no GNOME 50 em sessão de teste aninhada |
| KDE | Plasma 6, Qt 6.5+; indicador conferido em painel real |
| Compilação KDE | CMake 3.21+, compilador C++17, desenvolvimento Qt6 Core/Qml/DBus |

Versões anteriores do GNOME e todos os fluxos de popup/login não foram validados individualmente. MFA e OIDC ainda não são suportados. A API da versão instalada do OmniRoute pode diferir da versão pública usada no desenvolvimento.

## 1. Obter o projeto

Baixe ou clone este repositório e abra um terminal na pasta que contém `scripts/install-user.sh`.

Não é necessário copiar tokens, senha ou arquivos do chaveiro de outro computador. Faça login novamente na nova máquina.

## 2. Instalar as dependências

### Debian / Ubuntu

Os nomes podem variar conforme a versão da distribuição. Para o serviço e GNOME:

```bash
sudo apt update
sudo apt install python3 python3-gi gir1.2-gtk-4.0 gir1.2-secret-1 gnome-keyring
```

Para KDE, acrescente as dependências de compilação:

```bash
sudo apt install cmake g++ qt6-base-dev qt6-declarative-dev
```

Use um provedor Secret Service apropriado para sua sessão. Não é necessário instalar dois chaveiros concorrentes.

### NixOS / Nix

Na pasta do projeto:

```bash
nix-shell
```

Execute os próximos comandos de instalação dentro desse shell. O instalador registra o Python e os caminhos de introspecção desse ambiente nos launchers.

**Limitação:** os caminhos do Nix store precisam continuar disponíveis; após garbage collection, pode ser necessário reinstalar. O `shell.nix` não habilita nem configura o chaveiro da sua sessão. Um pacote Nix persistente ainda não é fornecido.

### Outras distribuições

Instale os equivalentes de Python/PyGObject, Gio, GTK4, libsecret com introspecção e um Secret Service. Para KDE, instale também CMake, C++17 e Qt6 Core/Qml/DBus com arquivos de desenvolvimento.

## 3. Instalar a extensão/widget

Instalação por usuário, **sem sudo**. Não troca seu desktop nem altera o servidor OmniRoute.

### GNOME

```bash
bash scripts/install-user.sh --service --gnome
```

Encerre e entre novamente na sessão GNOME se a extensão ainda não for descoberta, depois habilite:

```bash
gnome-extensions enable omniquota@local
```

Também pode habilitá-la pelo aplicativo **Extensões**, procurando **OmniRoute Cota**.

### KDE Plasma

```bash
bash scripts/install-user.sh --service --kde
```

Esse comando compila a ponte Qt6. Clique com o botão direito no painel → **Adicionar widgets** → procure **OmniRoute Cota** e arraste para o painel.

Se a lista não atualizar, encerre e entre novamente na sessão. Não é necessário mudar a altura do painel.

### Ambos

```bash
bash scripts/install-user.sh --service --gnome --kde
```

## 4. Configurar o OmniRoute

Abra **Configurações / Entrar** pelo indicador ou execute:

```bash
~/.local/bin/omniquota-settings
```

Preencha:

| Campo | O que informar |
| --- | --- |
| Servidor | Origem da sua instância, por exemplo `https://omniroute.exemplo.com`, sem `/api/...` |
| ID da conexão | Identificador da conta/provedor cuja cota você quer acompanhar |
| Senha | Senha de gerenciamento usada para entrar no painel OmniRoute |
| Lembrar senha | Opcional: guarda a senha no chaveiro para refazer o login após expirar |

O ID é o trecho após `/api/usage/` na requisição usada pelo dashboard de cotas. Ele não é uma API key. O campo pode vir com um ID padrão desta instalação: **troque pelo ID da sua própria conexão**, caso necessário.

Prefira **HTTPS com certificado válido**. HTTP exige consentimento explícito e transmite senha e sessão sem criptografia. Não há opção de ignorar validação TLS.

O serviço é iniciado por D-Bus quando necessário. Para iniciar manualmente:

```bash
systemctl --user start omniquota.service
```

## Segurança e sessão

- Não há senha, cookie de login nem token de provedor distribuídos com o código.
- Configuração não secreta: `${XDG_CONFIG_HOME:-~/.config}/omniquota/config.json`.
- Sessão e senha opcional ficam no Secret Service, sem fallback para arquivo em texto puro.
- O servidor público consultado usa cookie `auth_token`; não foi identificado endpoint de refresh do dashboard. Com senha lembrada, a aplicação refaz o login após 401. Sem ela, pede nova autenticação.
- A aplicação é por usuário: não isola segredos de processos maliciosos executados pelo mesmo usuário com acesso ao chaveiro/barramento.
- Logout tenta revogar a sessão remota e limpar os segredos locais. Sem acesso ao servidor, remoção local não garante revogação remota. Credenciais de outras origens não são apagadas automaticamente.
- A interface GNOME simplificada não expõe logout no menu. Para solicitá-lo sem colocar credenciais na linha de comando:

```bash
gdbus call --session --dest io.github.omniquota.Service \
  --object-path /io/github/omniquota/Service \
  --method io.github.omniquota.Service.Logout
```

## Atualizar

Atualize o código e reinstale com recarregamento explícito:

```bash
git pull
# No NixOS, entre em nix-shell primeiro.
bash scripts/install-user.sh --service --gnome --reload
# Ou, no KDE:
bash scripts/install-user.sh --service --kde --reload
```

Para somente recarregar o que já está instalado:

```bash
bash scripts/reload-user.sh
```

O script reinicia o serviço e identifica a sessão pelo `XDG_CURRENT_DESKTOP`. No GNOME, desativa/ativa a extensão; no KDE, reinicia apenas o Plasma Shell (a barra desaparece por alguns segundos, sem fechar aplicativos). Sem `--reload`, o instalador não reinicia a interface. Execute na sessão do desktop desejado, não em SSH nem na sessão KDE para recarregar um GNOME aninhado.

Configuração e chaveiro são preservados. **No GNOME, módulos JavaScript podem continuar em cache mesmo após reativar:** se a interface não mudar, saia e entre novamente na sessão. O script não força logout nem reinicia o computador.

## Diagnóstico

```bash
systemctl --user status omniquota.service
journalctl --user -u omniquota.service

gdbus call --session --dest io.github.omniquota.Service \
  --object-path /io/github/omniquota/Service \
  --method io.github.omniquota.Service.GetState
```

- **Janela não abre:** confira GTK4/PyGObject e o log do serviço; no Nix, reinstale dentro do `nix-shell`.
- **Erro de chaveiro:** habilite/desbloqueie um provedor Secret Service.
- **401:** autentique novamente; conferir se a senha salva ainda é válida.
- **429:** aguarde o prazo do servidor, sem insistir em atualizar.
- **Cota indisponível:** confira servidor/ID e se o provedor retorna o formato suportado.
- **Interface antiga:** novo login no desktop para limpar o cache.

Não publique senhas, cookies nem dumps do chaveiro em issues ou logs.

## Desenvolvimento e testes

```bash
PYTHONPATH=service python3 -m unittest discover -s tests -v
python3 -m compileall -q service
bash -n scripts/install-user.sh
cmake -S kde/bridge -B build/kde-dev
cmake --build build/kde-dev
```

Os testes usam dados sintéticos, incluindo um servidor HTTP local. Testes de contrato não substituem validação visual nos desktops. O formato suportado é `quotas: {nome: {remainingPercentage, remaining, total, resetAt, unlimited, fractionReported}}`.

## Desinstalar

1. Solicite logout para limpar os segredos da origem atual.
2. Desabilite `omniquota@local` no GNOME ou remova o widget do painel KDE.
3. Pare `omniquota.service`.
4. Remova apenas os arquivos deste aplicativo: diretório `omniquota`, extensão `gnome-shell/extensions/omniquota@local`, widget `plasma/plasmoids/io.github.omniquota`, ativação `dbus-1/services/io.github.omniquota.Service.service` e desktop entry `applications/io.github.omniquota.Settings.desktop`, sob seu diretório XDG de dados (normalmente `~/.local/share`). Remova os launchers `~/.local/bin/omniquota-service` e `~/.local/bin/omniquota-settings` e a unidade `~/.config/systemd/user/omniquota.service`.
5. Execute `systemctl --user daemon-reload`.

Configuração e credenciais de outras origens devem ser removidas separadamente se desejado. Os nomes técnicos `omniquota` são mantidos para compatibilidade, embora o nome exibido seja **OmniRoute Cota**.

## Créditos e licença

O layout compacto KDE foi adaptado de [izll/plasma-claude-usage](https://github.com/izll/plasma-claude-usage), sob **GPL-3.0-or-later**, com atribuição no arquivo `CompactView.qml`. A licença está em `kde/package/COPYING`; o código derivado deve manter esses termos. Este projeto não é afiliado ao OmniRoute nem ao projeto usado como referência visual.
