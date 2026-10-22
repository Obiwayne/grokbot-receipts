import functools
import threading
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

import pytest

FIXTURES = Path(__file__).parent / "fixtures"


class _Quiet(SimpleHTTPRequestHandler):
    def log_message(self, *args):
        pass


@pytest.fixture(scope="session")
def sites():
    """Four local web servers on different ports, so each counts as a different site."""
    servers, urls = [], {}
    for name in ("post", "gazette", "council", "blog"):
        handler = functools.partial(_Quiet, directory=str(FIXTURES))
        srv = ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=srv.serve_forever, daemon=True).start()
        servers.append(srv)
        urls[name] = f"http://127.0.0.1:{srv.server_address[1]}/{name}.html"
    yield urls
    for srv in servers:
        srv.shutdown()


CLAIM = "Riverside buses will be free for everyone from 1 January"
