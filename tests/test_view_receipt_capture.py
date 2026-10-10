"""Observed browser evidence must not be synthesized from the domain state."""
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import json
from pathlib import Path
import tempfile
import unittest

from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.replay import Limits
from test_interaction_service import CATALOG
from test_replay_live_core import PROVENANCE
from test_session_contract import FixturePort


def receipt(revision, *, notice="domain", pending=False):
    return {"revision": revision, "renderer": "bob-v1", "visible": ["message"],
            "draft": {}, "focus": None, "scroll": 0, "expanded": [],
            "presentation": {"notice": notice, "pending": pending,
                             "dirty": False, "can_confirm": False}}


class ViewReceiptCaptureTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port = FixturePort()
        self.service = InteractionService(lambda: self.port, Path(self.temp.name) / "effects.json",
                                          fixture_catalog=CATALOG, provenance=PROVENANCE)
        self.token = self.service.create()["token"]
        self.service.capture(self.token, True)

    def test_absent_browser_ack_is_incomplete_even_when_core_recomputes(self):
        self.service.command(self.token, "help", {}, 0)
        report = self.service.capture(self.token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        self.assertIn("step 1: browser acknowledgement", report["missing"])
        self.assertTrue(report["fidelity"]["core_semantic_parity"])
        self.assertFalse(report["fidelity"]["core_renderer_parity"])

    def test_ordered_observations_preserve_loading_validation_and_enabled_state(self):
        view = self.service.command(self.token, "help", {}, 0)
        first = receipt(view["revision"], notice="working", pending=True)
        second = receipt(view["revision"], notice="ready")
        self.service.ack(self.token, first)
        self.service.ack(self.token, second)
        view = self.service.command(self.token, "medical", {}, view["revision"])
        third = receipt(view["revision"])
        self.service.ack(self.token, third)
        report = self.service.capture(self.token, False)
        self.assertEqual(report["recording"], "full_replay", report)
        self.service.replay(self.token, "open", {"reference": report["reference"]})
        first_step = self.service.replay(self.token, "jump", {"index": 0})
        self.assertEqual([item["receipt"] for item in first_step["state"]["observed_views"]], [first, second])
        last = self.service.replay(self.token, "step", {})
        self.assertEqual([item["receipt"] for item in last["state"]["observed_views"]], [first, second, third])
        self.assertEqual(self.port.writes, [])

    def test_legacy_presentation_receipt_does_not_invent_enabled_controls(self):
        self.service.command(self.token, "help", {}, 0)
        legacy = receipt(1)
        del legacy["presentation"]["can_confirm"]
        self.service.ack(self.token, legacy)
        report = self.service.capture(self.token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        self.assertIn("step 1: browser presentation", report["missing"])

    def test_receipt_history_bound_reports_gap_without_affecting_commands(self):
        self.service.limits = Limits(max_events=2)
        # Fresh capture adopts the configured event and receipt bounds.
        self.service.capture(self.token, False)
        self.service.capture(self.token, True)
        self.service.command(self.token, "help", {}, 0)
        for notice in ("working", "ready", "domain"):
            self.service.ack(self.token, receipt(1, notice=notice))
        report = self.service.capture(self.token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        self.assertGreater(report["dropped"], 0)
        self.assertEqual(self.service.read(self.token)["state"], "help")
        self.assertEqual(self.port.writes, [])

    def test_import_cannot_forge_receipt_authority_or_cross_revision_binding(self):
        self.service.command(self.token, "help", {}, 0)
        self.service.ack(self.token, receipt(1))
        report = self.service.capture(self.token, False)
        self.service.replay(self.token, "open", {"reference": report["reference"]})
        document = json.loads(self.service.replay(self.token, "export", {"reviewed": True})["payload"])
        for mutation in ("nonce", "revision", "order"):
            changed = deepcopy(document)
            changed["id"] = "b" * 32
            observed = changed["view_receipts"]["observed"][0]
            if mutation == "nonce":
                observed["receipt"]["nonce"] = "cannot-authorize"
            elif mutation == "revision":
                observed["receipt"]["revision"] = 9
            else:
                observed["step"] = 9
            changed["digest"] = sha256(json.dumps({k: v for k, v in changed.items() if k != "digest"},
                sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.service.replay(self.token, "import", {"payload": json.dumps(changed)})
        self.assertEqual(self.port.writes, [])

    def test_import_receipt_reuses_live_privacy_gate(self):
        self.service.command(self.token, "help", {}, 0)
        self.service.ack(self.token, receipt(1))
        report = self.service.capture(self.token, False)
        self.service.replay(self.token, "open", {"reference": report["reference"]})
        document = json.loads(self.service.replay(self.token, "export", {"reviewed": True})["payload"])
        for index, value in enumerate(("sk-synthetic-sensitive-sentinel", "token synthetic-sensitive-sentinel", "a" * 32)):
            changed = deepcopy(document)
            changed["id"] = str(index + 1) * 32
            changed["view_receipts"]["observed"][0]["receipt"]["draft"] = {"message": value}
            changed["digest"] = sha256(json.dumps({k: v for k, v in changed.items() if k != "digest"},
                sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
            with self.subTest(value=value), self.assertRaises(ValueError):
                self.service.replay(self.token, "import", {"payload": json.dumps(changed)})

    def test_forward_clock_variant_keeps_core_but_does_not_predict_browser_observation(self):
        self.service.command(self.token, "help", {}, 0)
        self.service.ack(self.token, receipt(1))
        report = self.service.capture(self.token, False)
        self.service.replay(self.token, "open", {"reference": report["reference"]})
        document = json.loads(self.service.replay(self.token, "export", {"reviewed": True})["payload"])
        variant = self.service.replay(self.token, "fork", {"index": 0,
            "changes": {"clock": document["events"][0]["clock"] + 12}})
        self.assertEqual(variant["recording"], "incomplete_capture")
        self.assertEqual(variant["state"]["observed_views"], [])
        self.assertFalse(variant["fidelity"]["core_semantic_parity"], "counterfactuals do not prove original parity")
        stepped = self.service.replay(self.token, "jump", {"index": 0})
        self.assertEqual(stepped["state"]["core"]["state"], "help")
        self.assertEqual(self.port.writes, [])

    def test_required_marker_obeys_record_and_aggregate_byte_budgets(self):
        self.service.command(self.token, "help", {}, 0)
        session, _ = self.service._resolve(self.token)
        recording = self.service._attach(session)["active"]
        recording._data["view_receipts"]["required"].clear()
        size = len(json.dumps(recording.to_dict(), sort_keys=True, separators=(",", ":")).encode())
        for limit in (size, size + 1000):
            recording.limits = replace(recording.limits, max_record_bytes=limit)
            with self.subTest(record_limit=limit):
                self.assertFalse(recording.require_view(1, max_bytes=size))
                self.assertEqual(recording.to_dict()["view_receipts"]["required"], [])
                self.assertIn("browser acknowledgement capture unavailable", recording.missing)
        self.assertEqual(recording.to_dict()["dropped"], 2)
