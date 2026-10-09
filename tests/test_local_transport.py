import json
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
import tempfile
import unittest

from test_session_contract import FixturePort


class LocalTransportTests(unittest.TestCase):
    def setUp(self):
        from ochsner_bob.browser_service import BrowserService
        from ochsner_bob.local_transport import make_server
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = BrowserService(FixturePort, Path(self.temp.name) / "effects.json")
        self.server = make_server(self.service, port=0, allowed_origin="http://127.0.0.1:28450")
        self.thread = Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()
        self.addCleanup(self.cleanup_server)

    def cleanup_server(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join()

    def call(self, method, path, data=None, token=None, origin="http://127.0.0.1:28450"):
        connection = HTTPConnection("127.0.0.1", self.server.server_port, timeout=2)
        headers = {"Origin": origin, "Content-Type":"application/json"}
        if token:
            headers["Authorization"] = "Bearer " + token
        body = json.dumps(data) if isinstance(data, dict) else data
        connection.request(method, path, body=body, headers=headers)
        result = connection.getresponse()
        status, document = result.status, json.loads(result.read())
        connection.close()
        return status, document

    def test_create_read_and_bad_origin(self):
        status, created = self.call("POST", "/create", {})
        self.assertEqual(status, 201)
        status, view = self.call("GET", "/state", token=created["token"])
        self.assertEqual(status, 200)
        self.assertEqual(view["revision"], 0)
        self.assertEqual(self.call("GET", "/state")[0], 403)
        self.assertEqual(self.call("POST", "/create", {}, origin="https://evil.example")[0], 403)

    def test_closed_json_and_command_schema(self):
        token = self.call("POST", "/create", {})[1]["token"]
        for body in ('{"action":"handoff","action":"confirm"}', '{"revision":NaN}', '[' * 200):
            self.assertEqual(self.call("POST", "/command", body, token)[0], 400)
        self.assertEqual(self.call("POST", "/command", {"action":"help","data":{},"revision":0,"authority":True}, token)[0], 400)
        self.assertEqual(self.service.read(token)["revision"], 0)
        status, view = self.call("POST", "/command", {"action":"help","data":{},"revision":0}, token)
        self.assertEqual(status, 200)
        self.assertEqual(view["state"], "help")
