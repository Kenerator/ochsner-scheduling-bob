"""Authority contracts independent of reactive browser kernels."""
import tempfile
import unittest
from pathlib import Path

from test_session_contract import FixturePort


class BrowserServiceTests(unittest.TestCase):
    def setUp(self):
        from ochsner_bob.browser_service import BrowserService
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ports = []
        def factory():
            port = FixturePort()
            self.ports.append(port)
            return port
        self.service = BrowserService(factory, Path(self.temp.name) / "effects.json")
        self.patient = self.service.create()

    def test_capability_is_not_session_or_trace_reference(self):
        view = self.service.read(self.patient["token"])
        for bad in (view["session_id"], view["reference"], "", "unknown"):
            with self.assertRaises(PermissionError):
                self.service.read(bad)

    def test_two_sessions_and_polling_do_not_share_or_execute(self):
        other = self.service.create()
        self.service.command(self.patient["token"], "identity", {"phone":"555-0101", "dob":"1985-04-12"}, 0)
        self.assertEqual(self.service.read(other["token"])["identity_status"], "missing")
        for _ in range(5):
            self.service.read(self.patient["token"])
        self.assertEqual(self.ports[0].writes, [])
        self.assertEqual(self.service.read(self.patient["token"])["revision"], 1)

    def test_pairing_requires_single_use_patient_grant(self):
        grant = self.service.pair(self.patient["token"])
        support = self.service.join(grant)
        with self.assertRaises(PermissionError):
            self.service.join(grant)
        with self.assertRaises(PermissionError):
            self.service.pair(support)
        self.assertEqual(self.service.read(support)["patient"]["revision"], 0)
        with self.assertRaises(PermissionError):
            self.service.command(support, "identity", {}, 0)

    def test_ack_mirror_and_stale_submission_are_effect_free(self):
        support = self.service.join(self.service.pair(self.patient["token"]))
        receipt = {"revision":0,"renderer":"bob-v1","visible":["start"],
                   "draft":{"message":"public draft"},"focus":"message","scroll":0,"expanded":[]}
        self.service.ack(self.patient["token"], receipt)
        mirror = self.service.read(support)
        self.assertTrue(mirror["fresh"])
        self.assertEqual(mirror["last_observed"]["draft"]["message"], "public draft")
        self.service.command(self.patient["token"], "help", {}, 0)
        stale = self.service.command(self.patient["token"], "handoff", {}, 0)
        self.assertTrue(stale["stale"])
        self.assertFalse(self.service.read(support)["fresh"])
        self.assertEqual(self.ports[0].writes, [])

    def test_support_lease_expiry_and_suggestion_require_patient_acceptance(self):
        support = self.service.join(self.service.pair(self.patient["token"]))
        with self.assertRaises(PermissionError):
            self.service.command(support, "takeover", {}, 0)
        self.service.ack(self.patient["token"], {"revision":0,"renderer":"bob-v1","visible":["start"],"draft":{},"focus":None,"scroll":0,"expanded":[]})
        self.service.command(support, "takeover", {}, 0)
        self.service.suggest(support, {"specialty":"dermatology"}, 1)
        view = self.service.read(self.patient["token"])
        self.assertEqual(view["preferences"], {})
        self.assertIsNone(view["proposal"])
        self.service.command(support, "return", {}, view["revision"])
        view = self.service.read(self.patient["token"])
        self.service.accept(self.patient["token"], view["support_suggestion"]["id"], view["revision"])
        self.assertEqual(self.service.read(self.patient["token"])["preferences"]["specialty"], "dermatology")
        self.assertEqual(self.ports[0].writes, [])

    def test_restart_recovers_effect_namespace_but_not_identity_or_consent(self):
        from ochsner_bob.browser_service import BrowserService
        token = self.patient["token"]
        session, _ = self.service._resolve(token)
        session.journal.claim(session._key("booking"))
        original_id = session.id
        restarted = BrowserService(FixturePort, Path(self.temp.name) / "effects.json")
        view = restarted.read(token)
        self.assertEqual(view["session_id"], original_id)
        self.assertTrue(view["booking_blocked"])
        self.assertEqual(view["identity_status"], "missing")
        self.assertIsNone(view["proposal"])

    def test_ack_schema_rejects_private_fields_and_nested_authority(self):
        for receipt in ({"revision":0,"renderer":"bob-v1","draft":{"phone":"555-0101"}},
                        {"revision":0,"renderer":"bob-v1","draft":{"message":{"confirm":True}}}):
            with self.assertRaises(ValueError):
                self.service.ack(self.patient["token"], receipt)


if __name__ == "__main__":
    unittest.main()
