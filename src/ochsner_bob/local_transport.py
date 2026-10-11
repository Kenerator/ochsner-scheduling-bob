"""Bounded loopback JSON transport. Never logs capabilities, bodies or identity."""
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
import json
import re

from .replay import ReferenceUnavailable


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def _reject(_value):
    raise ValueError("nonfinite value")


def _bounded(value, depth=0, *, import_payload=False, path=()):
    if depth > 8:
        raise ValueError("nested input")
    if isinstance(value, dict):
        for key, item in value.items():
            if len(key) > 128:
                raise ValueError("long key")
            _bounded(item, depth + 1, import_payload=import_payload, path=path+(key,))
    elif isinstance(value, list):
        if len(value) > 40:
            raise ValueError("long array")
        for item in value:
            _bounded(item, depth + 1, import_payload=import_payload, path=path+("item",))
    elif isinstance(value, str) and (len(value.encode("utf-8")) > (1048576 if import_payload and path==("data","payload") else 4096) or any(0xD800 <= ord(c) <= 0xDFFF for c in value)):
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
                elif self.path == "/diagnostics":
                    result = service.diagnostics(self.token())
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
                # JSON quoting overhead may double a 1 MiB recording payload;
                # only its strict import route receives that larger wire bound.
                wire_limit=2*1048576+16384 if self.path=="/replay" else 16384
                if (len(lengths) != 1 or not re.fullmatch(r"[0-9]{1,7}", lengths[0])
                        or int(lengths[0]) > wire_limit or self.headers.get("Transfer-Encoding")
                        or self.headers.get("Content-Type") != "application/json"):
                    raise ValueError("invalid body")
                raw = self.rfile.read(int(lengths[0]))
                if len(raw) != int(lengths[0]):
                    raise ValueError("incomplete body")
                data = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_reject)
                importing=(self.path=="/replay" and type(data) is dict and data.get("operation")=="import"
                           and type(data.get("data")) is dict and set(data["data"])=={"payload"})
                if not importing and len(raw)>16384:
                    raise ValueError("normal request size exceeded")
                _bounded(data,import_payload=importing)
                schema = {"/create":set(), "/join":{"grant"}, "/pair":set(),
                          "/command":{"action","data","revision"}, "/ack":{"receipt"},
                          "/suggest":{"preferences","revision"}, "/accept":{"id","revision"},
                          "/text":{"text","revision"}, "/capture":{"enabled","synthetic"},
                          "/replay":{"operation","data"}}
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
                elif self.path == "/accept":
                    result = service.accept(token, data["id"], data["revision"])
                elif self.path == "/text":
                    if type(data["text"]) is not str or type(data["revision"]) is not int:
                        raise ValueError("invalid public turn")
                    result = service.text(token, data["text"], data["revision"])
                elif self.path == "/capture":
                    if type(data["enabled"]) is not bool or type(data["synthetic"]) is not bool:
                        raise ValueError("explicit capture opt-in required")
                    result = service.capture(token, data["enabled"], synthetic=data["synthetic"])
                else:
                    if type(data["operation"]) is not str or type(data["data"]) is not dict:
                        raise ValueError("invalid replay operation")
                    result = service.replay(token, data["operation"], data["data"])
                self.reply(201 if self.path == "/create" else 200, result)
            except ReferenceUnavailable:
                self.reply(403, {"error":"reference_unavailable"})
            except PermissionError:
                self.reply(403, {"error":"capability_or_current_lease_required"})
            except (ValueError, UnicodeError, RecursionError, TypeError):
                self.reply(400, {"error":"invalid_request"})
            except Exception:
                self.reply(503, {"error":"local_state_unavailable"})

    return ThreadingHTTPServer(("127.0.0.1", port), Handler)
