#!/usr/bin/env python3
"""Local server for lose-fat dashboard."""
import json
import os
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler

PORT = 8642
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _find_project_root():
    """Walk up from script dir to find the directory containing .lose-fat/."""
    d = SCRIPT_DIR
    for _ in range(10):
        if os.path.isdir(os.path.join(d, '.lose-fat')):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            break
        d = parent
    # Fallback: assume skill is at skills/<name>/ or .claude/skills/<name>/
    return os.path.dirname(os.path.dirname(SCRIPT_DIR))


PROJECT_ROOT = _find_project_root()
DEFAULT_PROFILES = os.path.join(PROJECT_ROOT, '.lose-fat', 'profiles')
DASHBOARD = os.path.join(SCRIPT_DIR, 'dashboard.html')


class Handler(SimpleHTTPRequestHandler):
    profiles_dir = DEFAULT_PROFILES

    def do_GET(self):
        route = self.path.split('?')[0]
        if route in ('/', '/index.html'):
            self._file(DASHBOARD, 'text/html')
        elif route == '/api/profiles':
            self._profiles()
        elif route.startswith('/api/profile/'):
            self._profile(route.split('/api/profile/', 1)[1])
        else:
            self.send_error(404)

    def _file(self, path, ctype):
        if not os.path.isfile(path):
            self.send_error(404)
            return
        self.send_response(200)
        self.send_header('Content-Type', f'{ctype}; charset=utf-8')
        self.end_headers()
        with open(path, 'rb') as f:
            self.wfile.write(f.read())

    def _json_resp(self, data, status=200):
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-cache, no-store')
        self.end_headers()
        self.wfile.write(json.dumps(data, ensure_ascii=False, indent=2).encode())

    def _profiles(self):
        result = []
        if not os.path.isdir(self.profiles_dir):
            self._json_resp(result)
            return
        for f in sorted(os.listdir(self.profiles_dir)):
            if not f.endswith('.json'):
                continue
            try:
                with open(os.path.join(self.profiles_dir, f), encoding='utf-8') as fp:
                    d = json.load(fp)
                result.append({
                    'filename': f,
                    'name': d.get('name', f),
                    'date': d.get('created_at', ''),
                    'bmi': d.get('bmi'),
                })
            except Exception:
                pass
        self._json_resp(result)

    def _profile(self, filename):
        path = os.path.join(self.profiles_dir, filename)
        if not filename.endswith('.json') or not os.path.isfile(path):
            self.send_error(404)
            return
        try:
            with open(path, encoding='utf-8') as f:
                self._json_resp(json.load(f))
        except Exception:
            self.send_error(500)

    def log_message(self, *args):
        pass


def main():
    import argparse
    parser = argparse.ArgumentParser(description='Lose-fat dashboard server')
    parser.add_argument('--port', type=int, default=PORT)
    parser.add_argument('--profiles', default=DEFAULT_PROFILES,
                        help='Path to profiles directory')
    args = parser.parse_args()
    Handler.profiles_dir = os.path.abspath(args.profiles)
    server = HTTPServer(('127.0.0.1', args.port), Handler)
    url = f'http://localhost:{args.port}'
    print(f'Dashboard running at {url}')
    print(f'Profiles dir: {Handler.profiles_dir}')
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\nServer stopped.')
        server.server_close()


if __name__ == '__main__':
    main()
