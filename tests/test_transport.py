"""Real loopback HTTP, synthetic credentials only."""
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from omniquota.client import Transport, ApiError

class TransportTests(unittest.TestCase):
    def setUp(self):
        self.hits = []
        hits = self.hits
        class Handler(BaseHTTPRequestHandler):
            def log_message(self,*args): pass
            def do_GET(self):
                hits.append(self.path)
                if self.path == '/redirect':
                    self.send_response(302); self.send_header('Location','/stolen'); self.end_headers()
                elif self.path == '/slow':
                    import time
                    time.sleep(0.5)
                    self.send_response(200); self.end_headers()
                elif self.path == '/large':
                    self.send_response(200); self.end_headers()
                    self.wfile.write(b'x'*(1024*1024+1))
                else:
                    self.send_response(200); self.end_headers(); self.wfile.write(b'{}')
        self.server = ThreadingHTTPServer(('127.0.0.1',0),Handler)
        self.thread = threading.Thread(target=self.server.serve_forever,daemon=True)
        self.thread.start()
        self.origin = 'http://127.0.0.1:'+str(self.server.server_port)
    def tearDown(self):
        self.server.shutdown(); self.server.server_close(); self.thread.join()
    def test_redirect_never_followed(self):
        response = Transport().request('GET',self.origin+'/redirect',{'Cookie':'auth_token=synthetic'})
        self.assertEqual(response.status,302)
        self.assertEqual(self.hits,['/redirect'])
    def test_total_deadline(self):
        import time
        class SlowTransport(Transport):
            total_timeout = 0.1
        started = time.monotonic()
        with self.assertRaises(ApiError): SlowTransport().request('GET',self.origin+'/slow',{})
        self.assertLess(time.monotonic()-started,0.4)
    def test_response_limit(self):
        with self.assertRaises(ApiError): Transport().request('GET',self.origin+'/large',{})
