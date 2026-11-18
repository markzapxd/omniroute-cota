"""One bounded HTTP transaction; private stdin/stdout pipe to the service."""
import base64
import json
import sys
from .client import Transport

def main():
    try:
        args = json.load(sys.stdin)
        body = base64.b64decode(args['body']) if args['body'] is not None else None
        response = Transport()._request_blocking(args['method'],args['url'],args['headers'],body)
        print(json.dumps({'status':response.status,'headers':response.headers,
                          'body':base64.b64encode(response.body).decode()}))
    except Exception:
        print(json.dumps({'error':True}))

if __name__ == '__main__': main()
