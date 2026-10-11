"""Empty counterfactual reads and historical contradictions stay effect-free."""
from copy import deepcopy
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.replay import Replay, import_recording, _RecordedPort
from test_interaction_service import CATALOG, CountingLanguage
from test_replay_live_core import PROVENANCE
from test_session_contract import FixturePort, SLOT


class EmptyReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.catalog = deepcopy(CATALOG)
        appointment = {"appointmentId": "appt_9002", "patientId": "pat_1003",
            **{key: SLOT[key] for key in ("providerId", "specialty", "location", "startTime")},
            "status": "scheduled"}
        self.catalog["appointment-a"] = {"kind": "appointment", "value": appointment}
        self.port, self.language = FixturePort(), CountingLanguage()
        self.port.appointments = lambda patient: [deepcopy(appointment)]
        self.service = InteractionService(lambda: self.port, Path(self.temp.name) / "effects.json",
            fixture_catalog=self.catalog, provenance=PROVENANCE, language=self.language)
        self.token = self.service.create()["token"]
        self.service.capture(self.token, True)
        for action, data in (("discover", {"specialty": "primary_care", "location": "downtown"}),
                ("identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"}),
                ("availability", {}), ("select", {"index": 1}), ("confirm", None), ("appointments", {})):
            view = self.service.read(self.token)
            if data is None:
                data = {key: view["proposal"][key] for key in ("nonce",)}
                data["proposal_id"] = view["proposal"]["id"]
            self.service.command(self.token, action, data, view["revision"])
        report = self.service.capture(self.token, False)
        self.service.replay(self.token, "open", {"reference": report["reference"]})
        self.payload = self.service.replay(self.token, "export", {"reviewed": True})["payload"]

    def load(self, payload):
        return import_recording(payload, fixture_refs=self.catalog, expected_provenance=PROVENANCE)

    def test_empty_read_variants_clear_both_observations_and_recompute_without_effects(self):
        original = self.load(self.payload)
        before = original.to_dict()
        journal = self.service.journal_path.read_bytes()
        calls = deepcopy((self.port.reads, self.port.writes))
        with patch("socket.socket", side_effect=AssertionError("no network")), \
             patch("ochsner_bob.session.EffectJournal", side_effect=AssertionError("no disk claims")):
            replay = Replay(original, fixture_catalog=self.catalog)
            self.assertTrue(replay.fidelity["core_semantic_parity"])
            for action, count in (("discover", "provider_count"), ("availability", "slot_count"),
                                  ("appointments", "appointment_count")):
                with self.subTest(action=action):
                    index = next(i for i, event in enumerate(before["events"]) if event["input"]["action"] == action)
                    child = replay.fork(index, {"api_status": "empty"})
                    event = child.recording.to_dict()["events"][index]
                    self.assertEqual(event["outcomes"]["api"]["fixture_refs"], [])
                    self.assertEqual(event["core"]["api"]["fixture_refs"], [])
                    self.assertEqual(child.jump(index)["core"][count], 0)
                    imported = Replay(self.load(child.recording.export_json(reviewed=True)), fixture_catalog=self.catalog)
                    self.assertEqual(imported.jump(index)["core"][count], 0)
                    if action == "availability":
                        end = child.jump(len(before["events"]) - 1)["core"]
                        self.assertFalse(end["proposal"])
                        self.assertNotEqual(end["certainty"], "completed")
            self.assertEqual(original.to_dict(), before)
        self.assertEqual((self.port.reads, self.port.writes), calls)
        self.assertEqual(self.language.calls, 0)
        self.assertEqual(self.service.journal_path.read_bytes(), journal)

    def test_historical_empty_with_results_imports_unchanged_but_is_incomplete(self):
        document = json.loads(self.payload)
        index = next(i for i, event in enumerate(document["events"]) if event["input"]["action"] == "availability")
        event = document["events"][index]
        event["outcomes"]["api"]["status"] = event["core"]["api"]["status"] = "empty"
        document["digest"] = sha256(json.dumps({k: v for k, v in document.items() if k != "digest"},
            sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        payload = json.dumps(document)
        with patch("socket.socket", side_effect=AssertionError("no network")), \
             patch("ochsner_bob.session.EffectJournal", side_effect=AssertionError("no disk claims")):
            historical = self.load(payload)
            gap = f"step {index + 1}: contradictory empty API observation"
            self.assertIn(gap, historical.missing)
            self.assertEqual(historical.availability(), "incomplete_capture")
            self.assertEqual(historical.to_dict(), document)
            replay = Replay(historical, fixture_catalog=self.catalog)
            self.assertFalse(replay.fidelity["core_semantic_parity"])
            self.assertEqual(replay.jump(index)["core"]["slot_count"], 0)
            self.assertNotEqual(replay.jump(len(document["events"]) - 1)["core"]["certainty"], "completed")

    def test_recorded_port_does_not_return_historical_fixtures_for_empty_status(self):
        event = next(event for event in json.loads(self.payload)["events"] if event["input"]["action"] == "availability")
        observation = deepcopy(event["core"]["api"])
        observation["status"] = "empty"
        port = _RecordedPort(self.catalog)
        port.arm(observation)
        self.assertEqual(port.availability("pat_1003", "primary_care"), [])
        self.assertTrue(port.gap)
