import json
import tempfile
import unittest
from pathlib import Path
from omniquota.client import Client, ApiError, Response, Transport
from omniquota.config import validate_config, save_config

class Store:
    def __init__(self): self.data = {}
    def get(self, key): return self.data.get(key)
    def set(self, key, value): self.data[key] = value
    def delete(self, key): self.data.pop(key, None)

class FakeTransport:
    def __init__(self, responses): self.responses, self.calls = list(responses), []
    def request(self, method, url, headers, body=None):
        self.calls.append((method, url, headers, body))
        return self.responses.pop(0)

def response(status=200, payload=None, headers=None):
    return Response(status, headers or {}, json.dumps(payload if payload is not None else {}).encode())

class ClientTests(unittest.TestCase):
    def client(self, responses):
        self.store = Store()
        self.transport = FakeTransport(responses)
        return Client('https://example.test', self.store, self.transport)
    def test_login_cookie(self):
        c = self.client([response(payload={'success':True}, headers={'Set-Cookie':'auth_token=abc; HttpOnly'}), response(payload={'quotas':{}})])
        c.login('secret', True)
        self.assertEqual(c.fetch_usage('id'), {'quotas':{}})
        self.assertEqual(self.transport.calls[1][2]['Cookie'], 'auth_token=abc')
        self.assertEqual(json.loads(self.transport.calls[0][3]), {'password':'secret'})
    def test_relogin_once(self):
        c = self.client([response(401), response(payload={'success':True}, headers={'Set-Cookie':'auth_token=new'}), response(401)])
        self.store.set(c.key('password'), 'secret')
        with self.assertRaises(ApiError): c.fetch_usage('id')
        self.assertEqual(len(self.transport.calls), 3)
    def test_no_saved_password(self):
        c = self.client([response(401)])
        with self.assertRaises(ApiError) as ctx: c.fetch_usage('id')
        self.assertEqual(ctx.exception.status, 401)
        self.assertEqual(len(self.transport.calls), 1)
    def test_errors(self):
        for r, status in [(response(403),403), (response(429, headers={'Retry-After':'120'}),429), (response(302),302), (Response(200,{},b'<html>'),502)]:
            c = self.client([r])
            with self.assertRaises(ApiError) as ctx: c.fetch_usage('id')
            self.assertEqual(ctx.exception.status,status)
            if status == 429: self.assertEqual(ctx.exception.retry_after,120)
    def test_mfa(self):
        c = self.client([response(payload={'mfaRequired':True})])
        with self.assertRaises(ApiError) as ctx: c.login('s')
        self.assertEqual(ctx.exception.status,501)
    def test_logout_clears(self):
        c = self.client([response()])
        self.store.set(c.key('session'),'a'); self.store.set(c.key('password'),'b')
        c.logout()
        self.assertEqual(self.store.data,{})
    def test_keyring_failure_propagates(self):
        c = self.client([response(payload={'success':True},headers={'Set-Cookie':'auth_token=abc'})])
        def fail(*args): raise RuntimeError('locked')
        self.store.set = fail
        with self.assertRaisesRegex(RuntimeError,'locked'): c.login('s')
    def test_multiple_cookies(self):
        c = self.client([response(payload={'success':True},headers={'Set-Cookie':['csrf=x; Path=/','auth_token=abc; HttpOnly']})])
        c.login('s')
        self.assertEqual(self.store.get(c.key('session')),'abc')
    def test_logout_attempts_both_deletions(self):
        c = self.client([response()])
        calls = []
        def delete(key):
            calls.append(key)
            if key.endswith('|session'): raise RuntimeError('locked')
        self.store.delete = delete
        with self.assertRaises(RuntimeError): c.logout()
        self.assertEqual(calls,[c.key('session'),c.key('password')])
    def test_forgetting_removes_password(self):
        c = self.client([response(payload={'success':True},headers={'Set-Cookie':'auth_token=abc'})])
        self.store.set(c.key('password'),'old')
        c.login('new',False)
        self.assertIsNone(self.store.get(c.key('password')))

class ConfigTests(unittest.TestCase):
    def test_http_consent(self):
        with self.assertRaises(ValueError): validate_config({'baseUrl':'http://host.test','connectionId':'id'})
        self.assertEqual(validate_config({'baseUrl':'http://host.test','connectionId':'id','allowHttp':True})['baseUrl'],'http://host.test')
    def test_invalid_urls(self):
        for url in ['file:///etc/passwd','https://u:p@host.test','https://host.test/path','https://host.test?x=1','https://host.test:bad']:
            with self.subTest(url=url), self.assertRaises(ValueError): validate_config({'baseUrl':url,'connectionId':'id'})
    def test_no_secrets_persisted(self):
        with tempfile.TemporaryDirectory() as d:
            p = Path(d)/'config.json'
            save_config(p,{'baseUrl':'https://host.test','connectionId':'id','password':'secret','token':'secret'})
            self.assertNotIn('secret',p.read_text())
