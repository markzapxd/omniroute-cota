import json
import os
import tempfile
from pathlib import Path
from urllib.parse import urlsplit

CONFIG_PATH = Path(os.environ.get('XDG_CONFIG_HOME', Path.home()/'.config'))/'omniquota/config.json'
DEFAULT = {'baseUrl':'https://localhost', 'connectionId':'a3cc1389-7c54-4447-862d-e110beef21d0', 'allowHttp':False, 'pollSeconds':60}


def validate_config(data):
    url = str(data.get('baseUrl','')).rstrip('/')
    parsed = urlsplit(url)
    _ = parsed.port  # validate malformed ports
    if (parsed.scheme not in ('https','http') or not parsed.hostname or parsed.username
            or parsed.password or parsed.path or parsed.query or parsed.fragment
            or any(ch.isspace() for ch in url)):
        raise ValueError('Informe apenas a origem: https://servidor:porta')
    allow = data.get('allowHttp') is True
    if parsed.scheme == 'http' and not allow:
        raise ValueError('HTTP transmite senha e sessão sem criptografia. Confirme o risco.')
    connection = str(data.get('connectionId','')).strip()
    if not connection or len(connection) > 200:
        raise ValueError('Informe o ID da conexão.')
    return {'baseUrl':url,'connectionId':connection,'allowHttp':allow,'pollSeconds':60}


def save_config(path, data):
    clean = validate_config(data)
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=path.parent)
    try:
        with os.fdopen(fd,'w') as stream:
            json.dump(clean,stream)
        os.replace(tmp,path)
    finally:
        if os.path.exists(tmp): os.unlink(tmp)
    return clean


def load_config():
    try:
        return validate_config(json.loads(CONFIG_PATH.read_text()))
    except (OSError, ValueError, TypeError):
        return dict(DEFAULT)
