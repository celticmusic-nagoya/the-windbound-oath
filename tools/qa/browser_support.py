"""Owned loopback server for stand-alone browser tests; PORT delegates ownership to runner."""
import contextlib, functools, http.server, os, threading
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
class QuietHandler(http.server.SimpleHTTPRequestHandler):
    def log_message(self,*args): pass
@contextlib.contextmanager
def server(default_port=8790):
    port=int(os.environ.get('PORT',default_port)); owned=None
    if 'PORT' not in os.environ:
        owned=http.server.ThreadingHTTPServer(('127.0.0.1',port),functools.partial(QuietHandler,directory=str(ROOT)))
        threading.Thread(target=owned.serve_forever,daemon=True).start()
    try:yield f'http://127.0.0.1:{port}'
    finally:
        if owned:owned.shutdown();owned.server_close()
