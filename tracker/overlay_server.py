import json
import time
import threading
import sys
from pathlib import Path
from http.server import ThreadingHTTPServer, SimpleHTTPRequestHandler
from .paths import DATA
from .profiles import selected_profile
ROOT = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent)) / "overlay"

from .overlay_state import state

class Handler(SimpleHTTPRequestHandler):
    def __init__(self,*args,**kwargs):super().__init__(*args,directory=str(ROOT),**kwargs)
    def do_GET(self):
        route = self.path.split('?', 1)[0]
        if route not in ('/api/state', '/api/combat-catalogue', '/api/combat-history'):
            return super().do_GET()
        try:
            if route == '/api/state':
                data = state()
            elif route == '/api/combat-catalogue':
                from .combat_views import catalogue_view
                data = catalogue_view()
            else:
                from .combat_views import history_view
                data = history_view()
            body = json.dumps(data, ensure_ascii=False, allow_nan=False).encode('utf-8')
            self.send_response(200)
        except (OSError, ValueError, TypeError):
            body = json.dumps({'error': 'Combat data unavailable'}).encode('utf-8')
            self.send_response(503)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Cache-Control', 'no-store')
        self.send_header('Content-Length', str(len(body)))
        self.end_headers()
        self.wfile.write(body)
    def log_message(self,*args):pass

def start_server():
    server=ThreadingHTTPServer(("127.0.0.1",8765),Handler);server.daemon_threads=True;threading.Thread(target=server.serve_forever,daemon=True).start();return server

# COMBAT_CATALOGUE_HISTORY_V1
