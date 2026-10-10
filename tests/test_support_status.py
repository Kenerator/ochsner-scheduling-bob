"""Pairing describes the caller; takeover describes only temporary control."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.browser_service import BrowserService
from test_session_contract import FixturePort


class SupportStatusTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bob-support-status-")
        self.addCleanup(temporary.cleanup)
        self.tick = 0.0
        self.service = BrowserService(
            FixturePort, Path(temporary.name) / "effects.json", clock=lambda: self.tick)
        self.patient = self.service.create()["token"]
        self.support = self.service.join(self.service.pair(self.patient))
        self.session, _ = self.service._resolve(self.patient)

    def act(self, token, action, **data):
        view = self.service.read(token)
        revision = view["patient"]["revision"] if token == self.support else view["revision"]
        return self.service.command(token, action, data, revision)

    def acknowledge(self, **changes):
        view = self.service.read(self.patient)
        receipt = {"revision": view["revision"], "renderer": "bob-v1", "visible": [],
                   "draft": {}, "focus": None, "scroll": 0, "expanded": [], **changes}
        return self.service.ack(self.patient, receipt)

    def takeover(self):
        self.acknowledge()
        return self.act(self.support, "takeover")

    def test_paired_support_is_joined_before_taking_control(self):
        before = self.service.read(self.patient)
        for _ in range(2):
            mirror = self.service.read(self.support)
            self.assertEqual(mirror["demo_support"], "joined")
            self.assertEqual(mirror["control_status"], "inactive")
            self.assertFalse(mirror["patient"]["takeover"])
            self.assertEqual(mirror["lease_seconds"], 0)
        self.assertEqual(self.service.read(self.patient), before)
        self.assertEqual(self.session.api.writes, [])

    def test_takeover_reports_active_control_separately_from_pairing(self):
        mirror = self.takeover()
        self.assertEqual(mirror["demo_support"], "joined")
        self.assertEqual(mirror.get("control_status"), "active")
        self.assertTrue(mirror["patient"]["takeover"])
        self.assertEqual(mirror["lease_seconds"], 300)
        self.tick = 42
        self.assertEqual(self.service.read(self.support)["lease_seconds"], 258)
        self.assertEqual(self.session.api.writes, [])

    def test_return_keeps_pairing_and_zeroes_unelapsed_lease(self):
        self.takeover()
        self.tick = 42
        returned = self.act(self.support, "return")
        self.assertEqual(returned["lease_seconds"], 0)
        self.assertEqual(returned["demo_support"], "joined")
        self.assertEqual(returned["control_status"], "inactive")
        self.assertFalse(returned["patient"]["takeover"])
        revision = returned["patient"]["revision"]
        self.assertEqual(self.service.read(self.support)["patient"]["revision"], revision)
        with self.assertRaises(PermissionError):
            self.service.suggest(self.support, {"location": "uptown"}, revision)
        self.assertEqual(self.session.api.writes, [])

    def test_expiry_returns_control_once_but_support_remains_paired(self):
        self.takeover()
        self.tick = 299
        self.assertTrue(self.service.read(self.support)["patient"]["takeover"])
        self.tick = 300
        mirror = self.service.read(self.support)
        self.assertEqual(mirror["demo_support"], "joined")
        self.assertEqual(mirror["control_status"], "inactive")
        self.assertEqual(mirror["lease_seconds"], 0)
        self.assertFalse(mirror["patient"]["takeover"])
        self.assertEqual(mirror["patient"]["revision"], 2)
        self.tick = 301
        self.assertEqual(self.service.read(self.support)["patient"]["revision"], 2)
        with self.assertRaises(PermissionError):
            self.service.suggest(self.support, {"location": "uptown"}, 2)
        self.assertEqual(self.session.api.writes, [])

    def test_session_does_not_infer_membership_from_control(self):
        # Even with a paired caller, the core itself has no capability registry.
        for active in (False, True, False):
            if active:
                self.takeover()
            elif self.session.takeover:
                self.act(self.support, "return")
            core = self.session.support_view()
            self.assertEqual(core["demo_support"], "unknown")
            self.assertEqual(core["control_status"], "active" if active else "inactive")

    def test_status_and_acknowledgement_never_grant_patient_authority(self):
        self.act(self.patient, "identity", phone="555-0130", dob="1978-09-22", zip="70115")
        self.act(self.patient, "preferences", specialty="primary_care", location="downtown")
        self.act(self.patient, "availability")
        proposal = self.act(self.patient, "select", index=1)["proposal"]
        self.acknowledge(draft={"message": "public scheduling draft"})
        for draft in ({"phone": "555-0130"}, {"message": "DOB 1978-09-22"},
                      {"message": proposal["nonce"]}):
            with self.subTest(draft=draft), self.assertRaises(ValueError):
                self.acknowledge(draft=draft)
        for stage in ("paired", "takeover", "return"):
            if stage != "paired":
                self.act(self.support, stage)
            mirror = self.service.read(self.support)
            serialized = json.dumps(mirror)
            for private in ("555-0130", "1978-09-22", "70115", proposal["nonce"]):
                self.assertNotIn(private, serialized)
            self.assertEqual(mirror["last_observed"]["draft"],
                             {"message": "public scheduling draft"})
            for action in ("identity", "confirm", "handoff", "select"):
                with self.subTest(stage=stage, action=action), self.assertRaises(PermissionError):
                    self.service.command(self.support, action, {}, mirror["patient"]["revision"])
            with self.assertRaises(PermissionError):
                self.act(self.patient, "takeover")
        # Return invalidates the old confirmation; pairing/receipts never restore it.
        result = self.act(self.patient, "confirm", proposal_id=proposal["id"], nonce=proposal["nonce"])
        self.assertIsNone(result["proposal"])
        self.assertIsNone(result["current_result"])
        self.assertEqual(self.session.api.writes, [])

    def test_expired_capability_cannot_read_paired_status(self):
        from ochsner_bob import browser_service as module
        issued = self.service.tokens[self.service._digest(self.support)][2]
        with patch.object(module, "time", return_value=issued + 86400):
            with self.assertRaises(PermissionError):
                self.service.read(self.support)


if __name__ == "__main__":
    unittest.main()
