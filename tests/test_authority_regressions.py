"""Regressions that expose unsafe behavior in the initial BOB sketch."""
import json
import unittest

from ochsner_bob import BobSession, MockSchedulingApi


class InitialAuthorityRegressions(unittest.TestCase):
    def setUp(self):
        self.api = MockSchedulingApi()
        self.session = BobSession(self.api)

    def ready(self):
        self.session.resolve_identity("5045550100", "1980-01-01", "70112")
        self.session.discover("cardio", "new orleans")
        slots = self.session.find_slots("provider-1")
        proposal = self.session.propose(slots[0]["id"])
        self.session.confirm(proposal["id"])

    def test_returned_options_are_mandatory(self):
        with self.assertRaises(ValueError):
            self.session.propose("invented-slot")

    def test_confirmation_is_single_use(self):
        self.ready()
        self.session.book()
        with self.assertRaises((PermissionError, ValueError, RuntimeError)):
            self.session.book()
        self.assertEqual(len(self.api.bookings), 1)

    def test_diagnostic_trace_has_no_patient_identifier(self):
        self.session.resolve_identity("5045550100", "1980-01-01", "70112")
        trace = json.dumps(self.session.events)
        self.assertNotIn("patient-1", trace)
        self.assertNotIn("5045550100", trace)

    def test_direct_identity_resolution_also_revokes_proposal(self):
        self.ready()
        self.session.resolve_identity("unknown", "1980-01-01", "70112")
        self.assertIsNone(self.session.proposal)
        self.assertIsNone(self.session.confirmed)
