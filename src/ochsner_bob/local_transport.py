"""Bounded loopback JSON transport. Never logs capabilities, bodies or identity."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def _reject(_value):
    raise ValueError("nonfinite value")


def _bounded(value, depth=0):
    if depth > 8:
        raise ValueError("nested input")
    if isinstance(value, dict):
        for key, item in value.items():
            if len(key) > 128:
                raise ValueError("long key")
            _bounded(item, depth + 1)
    elif isinstance(value, list):
        if len(value) > 40:
            raise ValueError("long array")
        for item in value:
            _bounded(item, depth + 1)
    elif isinstance(value, str) and (len(value) > 4096 or any(0xD800 <= ord(c) <= 0xDFFF for c in value)):
        raise ValueError("invalid string")


def make_server(service, *, port=28451, allowed_origin="http://127.0.0.1:28450"):
    if type(port) is not int or not 0 <= port <= 65535 or not re.fullmatch(r"http://127\.0\.0\.1:[0-9]{1,5}", allowed_origin):
        raise ValueError("Use numeric loopback ports only.")

    class Handler(BaseHTTPRequestHandler):
        def log_message(self, *_args):
            pass

        def setup(self):
            super().setup()
            self.connection.settimeout(5)

        def reply(self, status, document):
            encoded = json.dumps(document, allow_nan=False).encode()
            self.send_response(status)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(encoded)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Access-Control-Allow-Origin", allowed_origin)
            self.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
            self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
            self.end_headers()
            self.wfile.write(encoded)

        def allowed(self):
            # Host check also prevents DNS-rebinding access to a local capability API.
            return (self.headers.get("Origin") in {None, allowed_origin}
                    and self.headers.get("Host") == f"127.0.0.1:{self.server.server_port}")

        def token(self):
            value = self.headers.get("Authorization", "")
            return value[7:] if value.startswith("Bearer ") else ""

        def do_OPTIONS(self):
            self.reply(200 if self.allowed() else 403, {})

        def do_GET(self):
            if not self.allowed():
                return self.reply(403, {"error":"origin_denied"})
            try:
                if self.path == "/state":
                    result = service.read(self.token())
                elif self.path == "/trace":
                    session, _ = service._resolve(self.token())
                    result = {"events":session.trace()}
                else:
                    return self.reply(404, {"error":"not_found"})
                self.reply(200, result)
            except PermissionError:
                self.reply(403, {"error":"capability_required"})
            except Exception:
                self.reply(503, {"error":"local_state_unavailable"})

        def do_POST(self):
            if not self.allowed():
                return self.reply(403, {"error":"origin_denied"})
            try:
                lengths = self.headers.get_all("Content-Length", [])
                if (len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,5}", lengths[0])
                        or int(lengths[0]) > 16384 or self.headers.get("Transfer-Encoding")
                        or self.headers.get("Content-Type") != "application/json"):
                    raise ValueError("invalid body")
                raw = self.rfile.read(int(lengths[0]))
                if len(raw) != int(lengths[0]):
                    raise ValueError("incomplete body")
                data = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject)
                _bounded(data)
                schema = {"/create":set(), "/join":{"grant"}, "/pair":set(),
                          "/command":{"action","data","revision"}, "/ack":{"receipt"},
                          "/suggest":{"preferences","revision"}, "/accept":{"id","revision"}}
                if self.path not in schema or type(data) is not dict or set(data) != schema[self.path]:
                    raise ValueError("invalid schema")
                token = self.token()
                if self.path == "/create":
                    result = service.create()
                elif self.path == "/join":
                    result = {"token":service.join(data["grant"])}
                elif self.path == "/pair":
                    result = {"grant":service.pair(token)}
                elif self.path == "/command":
                    if type(data["action"]) is not str or type(data["data"]) is not dict or type(data["revision"]) is not int:
                        raise ValueError("invalid command")
                    result = service.command(token, data["action"], data["data"], data["revision"])
                elif self.path == "/ack":
                    result = service.ack(token, data["receipt"])
                elif self.path == "/suggest":
                    result = service.suggest(token, data["preferences"], data["revision"])
                else:
                    result = service.accept(token, data["id"], data["revision"])
                self.reply(201 if self.path == "/create" else 200, result)
            except PermissionError:
                self.reply(403, {"error":"capability_or_current_lease_required"})
            except (ValueError, UnicodeError, RecursionError, TypeError):
                self.reply(400, {"error":"invalid_request"})
            except Exception:
                self.reply(503, {"error":"local_state_unavailable"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
