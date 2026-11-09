"""A tiny stand-in for the GitHub releases API, for testing the updater.

    python3 fake_github.py ROOT PORT

ROOT/latest holds the tag of the "latest release"; ROOT/releases/<tag>/ holds its asset files. Serves
GET /repos/<owner>/<repo>/releases/latest and GET /repos/<owner>/<repo>/releases/assets/<id>.
"""
import json
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(sys.argv[1])
PORT = int(sys.argv[2])


def assets_for(tag):
    folder = ROOT / 'releases' / tag
    files = sorted(p for p in folder.iterdir() if p.is_file()) if folder.is_dir() else []
    return [(1000 + i, p) for i, p in enumerate(files)]


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *args):
        pass

    def send(self, code, body, ctype='application/json'):
        self.send_response(code)
        self.send_header('Content-Type', ctype)
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        tag = (ROOT / 'latest').read_text().strip() if (ROOT / 'latest').exists() else ''
        if self.path.endswith('/releases/latest'):
            if not tag:
                return self.send(404, b'{"message": "Not Found"}')
            data = {'tag_name': tag, 'assets': [{'id': i, 'name': p.name, 'url': f'/assets/{i}'} for i, p in assets_for(tag)]}
            return self.send(200, json.dumps(data).encode())
        if '/releases/assets/' in self.path:
            wanted = int(self.path.rsplit('/', 1)[1])
            if 'octet-stream' not in self.headers.get('Accept', ''):
                return self.send(415, b'{"message": "use Accept: application/octet-stream"}')
            for folder in (ROOT / 'releases').iterdir():
                for i, p in assets_for(folder.name):
                    if i == wanted and folder.name == tag:
                        return self.send(200, p.read_bytes(), 'application/octet-stream')
            return self.send(404, b'{"message": "Not Found"}')
        self.send(404, b'{}')


ThreadingHTTPServer(('127.0.0.1', PORT), Handler).serve_forever()
