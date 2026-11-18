"""Bounded HTTP client. No redirects, no TLS bypass, no secret logging."""
import json
import time
from dataclasses import dataclass
from email.utils import parsedate_to_datetime
from http.cookies import SimpleCookie
from urllib.error import HTTPError, URLError
from urllib.parse import quote
from urllib.request import HTTPRedirectHandler, Request, build_opener

class ApiError(Exception):
    def __init__(self, message, status=502, retry_after=60):
        super().__init__(message)
        self.status, self.retry_after = status, retry_after

@dataclass
class Response:
    status: int
    headers: dict
    body: bytes

class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

class Transport:
    total_timeout = 15

    def request(self, method, url, headers, body=None):
        # A separate process gives DNS, TLS, headers and body a hard total deadline.
        # Credentials travel over stdin, never arguments/environment or logs.
        import subprocess
        import sys
        import base64
        request = json.dumps({'method':method,'url':url,'headers':headers,
                              'body':base64.b64encode(body).decode() if body is not None else None})
        try:
            result = subprocess.run([sys.executable,'-m','omniquota.http_worker'],input=request,
                                    capture_output=True,text=True,timeout=self.total_timeout,check=True)
            data = json.loads(result.stdout)
            if 'error' in data: raise ApiError('Falha de rede, TLS ou resposta inválida.')
            return Response(data['status'],data['headers'],base64.b64decode(data['body']))
        except (subprocess.SubprocessError, ValueError, KeyError):
            raise ApiError('Consulta excedeu o prazo ou falhou; tente novamente.') from None

    def _request_blocking(self, method, url, headers, body=None):
        req = Request(url, data=body, headers=headers, method=method)
        try:
            result = build_opener(NoRedirect).open(req, timeout=15)
        except HTTPError as error:
            result = error
        except (URLError, OSError, TimeoutError):
            raise ApiError('Falha de rede ou TLS; verifique o servidor.') from None
        with result:
            data = result.read(1024 * 1024 + 1)
            if len(data) > 1024 * 1024:
                raise ApiError('Resposta excedeu 1 MiB.')
            headers = dict(result.headers)
            headers['Set-Cookie'] = result.headers.get_all('Set-Cookie', [])
            return Response(result.code, headers, data)


def header(headers, key):
    return next((v for k,v in headers.items() if k.lower() == key.lower()), '')

class Client:
    def __init__(self, origin, store, transport=None):
        self.origin, self.store = origin, store
        self.transport = transport or Transport()
        self.blocked_until = 0

    def key(self, kind):
        return self.origin + '|' + kind

    def _request(self, method, path, data=None):
        if time.monotonic() < self.blocked_until:
            raise ApiError('Aguarde antes de consultar novamente.',429,
                           max(1,int(self.blocked_until-time.monotonic())))
        headers = {'Accept':'application/json','Origin':self.origin}
        token = self.store.get(self.key('session'))
        if token: headers['Cookie'] = 'auth_token=' + token
        body = None
        if data is not None:
            headers['Content-Type'] = 'application/json'
            body = json.dumps(data).encode()
        response = self.transport.request(method,self.origin+path,headers,body)
        if response.status != 200:
            retry = 60
            if response.status == 429:
                raw = header(response.headers,'Retry-After')
                try: retry = max(1,int(raw))
                except (ValueError,TypeError):
                    try: retry = max(1,int(parsedate_to_datetime(raw).timestamp()-time.time()))
                    except (ValueError,TypeError,OverflowError): pass
                self.blocked_until = time.monotonic()+retry
            raise ApiError({401:'Entre novamente.',403:'Acesso negado.',429:'Limite de consultas; aguarde.'}.get(response.status, f'Servidor retornou HTTP {response.status}.'),response.status,retry)
        try:
            payload = json.loads(response.body)
        except (ValueError,UnicodeError):
            raise ApiError('Resposta não é JSON válido.') from None
        if not isinstance(payload,dict): raise ApiError('Formato de resposta não suportado.')
        return payload,response

    def login(self, password, remember=False):
        payload,response = self._request('POST','/api/auth/login',{'password':password})
        if payload.get('mfaRequired'):
            raise ApiError('MFA não suportado neste widget; use o dashboard.',501)
        cookies = SimpleCookie()
        raw_cookies = header(response.headers,'Set-Cookie')
        for raw in raw_cookies if isinstance(raw_cookies,list) else [raw_cookies]:
            cookies.load(raw)
        if payload.get('success') is not True or 'auth_token' not in cookies:
            raise ApiError('Login não retornou uma sessão válida.')
        self.store.set(self.key('session'),cookies['auth_token'].value)
        if remember: self.store.set(self.key('password'),password)
        else: self.store.delete(self.key('password'))

    def fetch_usage(self, connection_id):
        path = '/api/usage/'+quote(connection_id,safe='')
        try:
            return self._request('GET',path)[0]
        except ApiError as error:
            if error.status != 401: raise
            password = self.store.get(self.key('password'))
            if not password: raise
            self.login(password,True)
            return self._request('GET',path)[0]

    def logout(self):
        # Local removal always works even when the server is offline.
        try:
            self._request('POST','/api/auth/logout',{})
        except ApiError:
            pass
        finally:
            failed = False
            for kind in ('session','password'):
                try: self.store.delete(self.key(kind))
                except Exception: failed = True
            if failed: raise RuntimeError('Não foi possível limpar todos os segredos do chaveiro.')
