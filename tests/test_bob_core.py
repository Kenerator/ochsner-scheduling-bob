import unittest

from ochsner_bob import BobSession, MockSchedulingApi, UnknownOutcome
from ochsner_bob.adapters import parse_language_output, policy_decision
from ochsner_bob.replay import fork, promote


class BobCoreTests(unittest.TestCase):
    def setUp(self):
        self.api = MockSchedulingApi()
        self.session = BobSession(self.api)

    def test_public_discovery_and_explicit_confirmation_are_separate(self):
        self.session.resolve_identity("5045550100", "1980-01-01", "70112")
        providers = self.session.discover("cardio", "new orleans")
        self.assertTrue(providers)
        slots = self.session.find_slots(providers[0]["id"])
        proposal = self.session.propose(slots[0]["id"])
        self.assertEqual(self.api.bookings, [])
        with self.assertRaises(PermissionError):
            self.session.book()
        self.session.confirm(proposal["id"])
        receipt = self.session.book()
        self.assertEqual(receipt.status, "completed")
        self.assertEqual(len(self.api.bookings), 1)

    def test_identity_correction_revokes_private_state_and_proposal(self):
        self.session.resolve_identity("5045550100", "1980-01-01", "70112")
        provider = self.session.discover("cardio", "new orleans")[0]
        self.session.propose(self.session.find_slots(provider["id"])[0]["id"])
        self.session.correct_identity("5045550100", "1980-01-01", "70113")
        self.assertEqual(self.session.identity["zip"], "70113")
        self.assertIsNone(self.session.proposal)
        self.assertEqual(self.session.appointments(), [])

    def test_unknown_booking_is_not_retried(self):
        self.session.resolve_identity("5045550100", "1980-01-01", "70112")
        provider = self.session.discover("cardio", "new orleans")[0]
        self.session.propose(self.session.find_slots(provider["id"])[0]["id"])
        self.session.confirm(self.session.proposal["id"])
        self.api.next_booking = UnknownOutcome("timeout")
        receipt = self.session.book()
        self.assertEqual(receipt.status, "unknown")
        with self.assertRaises(RuntimeError):
            self.session.book()
        self.assertEqual(len(self.api.bookings), 0)

    def test_help_is_available_after_success_and_handoff_is_truthful(self):
        self.assertEqual(self.session.help()["kind"], "human_help")
        self.session.api.next_handoff = UnknownOutcome("lost response")
        result = self.session.handoff("needs help")
        self.assertEqual(result.status, "unknown")
        self.assertNotEqual(result.status, "queued")

    def test_model_cannot_return_authority_and_replay_is_effect_free(self):
        with self.assertRaises(ValueError):
            parse_language_output({"patient_id": "patient-1"})
        self.session.discover("cardio", "new orleans")
        variant = fork(self.session.events, 0, {"fault": "timeout"})
        self.assertTrue(variant["simulation_only"])
        self.assertTrue(promote(variant, reviewed=True)["fixture"])
        self.assertFalse(policy_decision({"identity_verified": True, "proposal_current": True, "confirmation_current": True, "medical_request": True})["allow"])


if __name__ == "__main__":
    unittest.main()
