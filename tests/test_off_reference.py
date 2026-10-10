"""OFF references inspect bounded public diagnostics, never exact recordings."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.replay import Limits
from test_interaction_service import CATALOG, CountingLanguage
from test_replay_live_core import PROVENANCE
from test_session_contract import FixturePort


class OffReferenceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port = FixturePort()
        self.language = CountingLanguage()
        self.now = 1000
        self.service = InteractionService(lambda: self.port, Path(self.temp.name) / "effects.json",
            fixture_catalog=CATALOG, provenance=PROVENANCE, language=self.language,
            limits=Limits(max_events=2, ttl_seconds=10), wall_clock=lambda: self.now)
        self.token = self.service.create()["token"]

    def test_owned_off_reference_opens_with_and_without_events_without_effects_or_store(self):
        for action in (None, "help"):
            if action:
                self.service.command(self.token, action, {}, 0)
            diagnostic = self.service.diagnostics(self.token)
            before = self.service.read(self.token)
            reads, writes = deepcopy(self.port.reads), deepcopy(self.port.writes)
            with patch.object(self.service, "_store", side_effect=AssertionError("inspection must not touch RecordingStore")):
                opened = self.service.replay(self.token, "open", {"reference": diagnostic["reference"]})
            self.assertEqual(opened["recording"], "off")
            self.assertEqual(opened["browser_mode"], "inspection")
            self.assertEqual(opened["inspection"]["kind"], "sanitized_current_diagnostics")
            self.assertFalse(opened["inspection"]["historical_state_available"])
            self.assertEqual(opened["inspection"]["events"], diagnostic["events"])
            self.assertEqual(self.service.read(self.token), before)
            self.assertEqual((self.port.reads, self.port.writes), (reads, writes))
            self.assertEqual(self.language.calls, 0)
            self.assertFalse(self.service.recording_directory.exists())
            self.assertFalse(opened["fidelity"]["core_semantic_parity"])
            self.assertFalse(opened["fidelity"]["core_renderer_parity"])

    def test_unknown_foreign_invalid_and_expired_off_references_never_gain_access(self):
        reference = self.service.diagnostics(self.token)["reference"]
        other = self.service.create()["token"]
        for token, candidate, error in ((other, reference, PermissionError),
                (self.token, reference.replace("/step/0/", "/step/7/"), PermissionError),
                (self.token, "not-a-reference", ValueError),
                ("invalid-capability", reference, PermissionError)):
            with self.subTest(candidate=candidate), self.assertRaises(error):
                self.service.replay(token, "open", {"reference": candidate})
        self.now += 10
        result = self.service.replay(self.token, "open", {"reference": reference})
        self.assertEqual(result["recording"], "unavailable")
        self.assertEqual(result["inspection_status"], "expired")
        self.assertNotIn("inspection", result)

    def test_inspection_is_paired_session_scoped_private_and_not_exact_replay(self):
        reference = self.service.diagnostics(self.token)["reference"]
        support = self.service.join(self.service.pair(self.token))
        self.service.command(self.token, "identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"}, 0)
        result = self.service.replay(support, "open", {"reference": reference})
        self.assertEqual(result["inspection"]["requested_revision"], 0)
        self.assertEqual(result["inspection"]["current_revision"], 1)
        serialized = json.dumps(result)
        for private in ("555-0130", "1978-09-22", "70115", "pat_1003", '"nonce"', '"identity_input"'):
            self.assertNotIn(private, serialized)
        for operation, data in (("step", {}), ("fork", {"index": 0, "changes": {}}),
                ("export", {"reviewed": True}), ("purge", {"reference": reference})):
            with self.subTest(operation=operation), self.assertRaises((ValueError, PermissionError)):
                self.service.replay(support, operation, data)
        self.assertFalse(self.service.recording_directory.exists())

    def test_off_reference_registry_is_bounded_and_does_not_renew_expiry_on_poll(self):
        initial = self.service.diagnostics(self.token)["reference"]
        self.now += 5
        self.service.diagnostics(self.token)
        self.now += 5
        self.assertEqual(self.service.replay(self.token, "open", {"reference": initial})["recording"], "unavailable")
        self.service.command(self.token, "help", {}, 0)
        self.service.command(self.token, "medical", {}, 1)
        with self.assertRaises(PermissionError):
            self.service.replay(self.token, "open", {"reference": initial})

    def test_opening_off_inspection_clears_previous_exact_replay_authority(self):
        reference = self.service.diagnostics(self.token)["reference"]
        self.service.capture(self.token, True)
        self.service.command(self.token, "help", {}, 0)
        recorded = self.service.capture(self.token, False)["reference"]
        self.service.replay(self.token, "open", {"reference": recorded})
        self.service.replay(self.token, "open", {"reference": reference})
        with self.assertRaises(ValueError):
            self.service.replay(self.token, "export", {"reviewed": True})

    def test_inspection_reports_trace_truncation_without_inventing_history(self):
        for revision, action in enumerate(("help", "medical", "unsupported")):
            self.service.command(self.token, action, {}, revision)
        reference = self.service.diagnostics(self.token)["reference"]
        result = self.service.replay(self.token, "open", {"reference": reference})["inspection"]
        self.assertEqual([event["seq"] for event in result["events"]], [2, 3])
        self.assertEqual(result["trace_dropped"], 1)
