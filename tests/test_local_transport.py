import json
from http.client import HTTPConnection
from pathlib import Path
from threading import Thread
import tempfile
import unittest

from test_session_contract import FixturePort


class LocalTransportTests(unittest.TestCase):
    def setUp(self):
        from ochsner_bob.interaction_service import InteractionService
        from ochsner_bob.local_transport import make_server
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.service = InteractionService(FixturePort, Path(self.temp.name) / "effects.json")
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

    def test_text_diagnostics_and_replay_routes_are_closed_and_effect_free(self):
        # Real service methods are tested separately. This boundary catches a
        # missing/wrong route or accidental command dispatch during inspection.
        self.service.text = lambda token,text,revision: {"message":text,"revision":revision}
        self.service.diagnostics = lambda token: {"recording":"off"}
        self.service.capture = lambda token,enabled,synthetic: {"recording":"off"}
        self.service.replay = lambda token,operation,data: {"simulation_only":True}
        token = self.call("POST", "/create", {})[1]["token"]
        self.assertEqual(self.call("POST","/text",{"text":"help","revision":0},token)[0],200)
        self.assertEqual(self.call("GET","/diagnostics",token=token)[1],{"recording":"off"})
        self.assertEqual(self.call("POST","/capture",{"enabled":True,"synthetic":True},token)[0],200)
        self.assertEqual(self.call("POST","/replay",{"operation":"step","data":{}},token)[1],{"simulation_only":True})
        self.assertEqual(self.call("POST","/replay",{"operation":"step","data":{},"nonce":"forged"},token)[0],400)
        self.assertEqual(self.service.read(token)["revision"],0)

    def test_real_capture_open_step_roundtrip_through_json_boundary(self):
        token=self.call("POST","/create",{})[1]["token"]
        self.assertEqual(self.call("POST","/capture",{"enabled":True,"synthetic":True},token)[0],200)
        self.assertEqual(self.call("POST","/command",{"action":"help","data":{},"revision":0},token)[0],200)
        status,report=self.call("POST","/capture",{"enabled":False,"synthetic":True},token)
        self.assertEqual(status,200)
        status,opened=self.call("POST","/replay",{"operation":"open","data":{"reference":report["reference"]}},token)
        self.assertEqual(status,200,opened)
        status,stepped=self.call("POST","/replay",{"operation":"step","data":{}},token)
        self.assertEqual(status,200,stepped)
        self.assertEqual(stepped["index"],0)
        self.assertTrue(stepped["simulation_only"])
        self.assertEqual(self.service.read(token)["revision"],1)

    def test_bounded_recording_import_above_normal_command_size(self):
        from ochsner_bob.replay import Recording
        token=self.call("POST","/create",{})[1]["token"]
        record=Recording(self.service.provenance,fixture_refs=self.service._catalog,synthetic=True)
        for _ in range(200):
            record.append({"action":"help","data":{}})
        record.seal()
        payload=record.export_json(reviewed=True)
        self.assertGreater(len(payload),16384)
        status,imported=self.call("POST","/replay",{"operation":"import","data":{"payload":payload}},token)
        self.assertEqual(status,200,imported)
        self.assertTrue(imported["simulation_only"])
        self.assertEqual(self.service.read(token)["revision"],0)

    def test_reference_denials_are_indistinguishable_and_preserve_valid_session(self):
        token = self.call("POST", "/create", {})[1]["token"]
        other = self.call("POST", "/create", {})[1]["token"]
        own = self.service.diagnostics(token)["reference"]
        foreign = self.service.diagnostics(other)["reference"]
        before = self.service.read(token)
        denials = []
        for reference in (foreign, "BOB-" + "0" * 32 + "/step/0/branch/original",
                          own.replace("/step/0/", "/step/7/")):
            denials.append(self.call("POST", "/replay", {"operation": "open", "data": {"reference": reference}}, token))
        self.assertEqual(denials, [(403, {"error": "reference_unavailable"})] * 3)
        self.assertEqual(self.service.read(token), before)
        self.assertEqual(self.call("GET", "/state", token=token), (200, before))
        status, result = self.call("POST", "/replay", {"operation": "open", "data": {"reference": own}}, token)
        self.assertEqual((status, result["recording"]), (200, "off"))
        invalid = self.call("POST", "/replay", {"operation": "open", "data": {"reference": foreign}}, "invalid-capability")
        self.assertEqual(invalid, (403, {"error": "capability_or_current_lease_required"}))

    def test_reference_recovery_notice_is_accepted_mirrored_and_recorded_as_category_only(self):
        token = self.call("POST", "/create", {})[1]["token"]
        support = self.service.join(self.service.pair(token))
        self.service.capture(token, True)
        view = self.service.command(token, "help", {}, 0)
        receipt = {"revision": view["revision"], "renderer": "bob-v1", "visible": [],
            "draft": {}, "focus": None, "scroll": 0, "expanded": [],
            "presentation": {"notice": "reference", "pending": False, "dirty": False, "can_confirm": False}}
        self.assertEqual(self.call("POST", "/ack", {"receipt": receipt}, token)[0], 200)
        self.assertEqual(self.service.read(support)["last_observed"]["presentation"], receipt["presentation"])
        report = self.service.capture(token, False)
        opened = self.service.replay(token, "open", {"reference": report["reference"]})
        observed = self.service.replay(token, "jump", {"index": opened["event_count"] - 1})["state"]["observed_views"]
        self.assertEqual(observed[-1]["receipt"]["presentation"], receipt["presentation"])
