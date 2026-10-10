"""Owned HTTP test lifecycles; the supplied scheduling service stays unchanged."""

import importlib.util
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import socket
import threading
import time


class _QuietServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = True

    def handle_error(self, request, client_address):
        # Hostile-response tests deliberately disconnect sockets; never dump bodies.
        pass


class _Lifecycle:
    def _start(self, handler):
        self.server = _QuietServer(("127.0.0.1", 0), handler)
        self.base_url = f"http://127.0.0.1:{self.server.server_port}"
        self.thread = threading.Thread(
            target=self.server.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True
        )
        self.thread.start()
        return self

    def __exit__(self, *_exc):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=2)
        if self.thread.is_alive():
            raise AssertionError("owned HTTP server did not stop")


class SuppliedServer(_Lifecycle):
    """Fresh original Store/Handler on an OS-selected port with bounded audit waits."""

    def __init__(self):
        self.audits = []
        self._condition = threading.Condition()

    def __enter__(self):
        path = Path(__file__).resolve().parents[1] / "vendor/reference/mock-api/server.py"
        spec = importlib.util.spec_from_file_location("bob_owned_supplied_http", path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        self.module = module
        self.store = module.Store()
        owner = self

        class OwnedHandler(module.Handler):
            store = owner.store
            log_fh = None

            def audit(self, method, path, status, ms):
                # Original dispatch calls audit AFTER responding. Synchronize that race.
                route = "/patients/{patientId}/appointments" if path.startswith("/patients/") and path.endswith("/appointments") else path
                with owner._condition:
                    owner.audits.append({"method": method, "route": route, "status": status})
                    owner._condition.notify_all()

        return self._start(OwnedHandler)

    def wait_for_audits(self, count, timeout=2):
        with self._condition:
            if not self._condition.wait_for(lambda: len(self.audits) >= count, timeout):
                raise AssertionError("supplied HTTP audit did not arrive within bound")
            return list(self.audits)


def supplied_server():
    return SuppliedServer()


class HostileServer(_Lifecycle):
    """Transport double only: one programmable wire response, no scheduling backend."""

    def __init__(self, status=200, payload=None, *, raw=None, headers=None, action=None):
        self.status = status
        self.raw = raw if raw is not None else json.dumps(payload).encode()
        self.headers = headers or {}
        self.action = action
        self.requests = []
        self._condition = threading.Condition()

    def __enter__(self):
        owner = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *_args):
                pass

            def do_GET(self):
                self.reply()

            def do_POST(self):
                self.reply()

            def reply(self):
                body = self.rfile.read(int(self.headers.get("Content-Length", "0")))
                with owner._condition:
                    owner.requests.append({"method": self.command, "path": self.path,
                                           "body": body, "scenario": self.headers.get("X-Mock-Scenario")})
                    owner._condition.notify_all()
                if owner.action == "disconnect":
                    self.connection.shutdown(socket.SHUT_RDWR)
                    self.connection.close()
                    return
                if owner.action == "delay":
                    time.sleep(0.25)
                self.send_response(owner.status)
                headers = {"Content-Type": "application/json", "Content-Length": str(len(owner.raw)), **owner.headers}
                for key, value in headers.items():
                    self.send_header(key, value)
                self.end_headers()
                if owner.action == "drip":
                    for byte in owner.raw:
                        self.wfile.write(bytes([byte]))
                        self.wfile.flush()
                        time.sleep(0.02)
                else:
                    self.wfile.write(owner.raw)
                self.close_connection = True

        return self._start(Handler)

    def wait_for_requests(self, count, timeout=2):
        with self._condition:
            if not self._condition.wait_for(lambda: len(self.requests) >= count, timeout):
                raise AssertionError("hostile transport request did not arrive within bound")
            return list(self.requests)
