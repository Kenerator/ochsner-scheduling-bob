"""Independent domain expectations; hostile transport is tested separately."""
import copy
import importlib
import json
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path


SLOT = {"slotId": "slot_4001", "providerId": "prov_2001", "specialty": "primary_care", "location": "downtown", "startTime": "2026-10-16T09:00:00-05:00", "available": True}


class FixturePort:
    def __init__(self):
        self.writes = []
        self.reads = []
        self.outcome = None
    def providers(self, specialty=None, location=None):
        self.reads.append("public")
        return [{"providerId": "prov_2001", "name": "Dr. Elena Brooks", "specialty": "primary_care", "locations": ["downtown"], "modalities": ["in_person"]}]
    def search_patients(self, phone, dob):
        self.reads.append("identity")
        if phone == "555-9999":
            return []
        return [{"patientId": "pat_1003", "phone": phone, "dateOfBirth": dob, "zipCode": "70115"}, {"patientId": "pat_1004", "phone": phone, "dateOfBirth": dob, "zipCode": "70005"}]
    def availability(self, *args, **kwargs):
        self.reads.append("availability")
        return [copy.deepcopy(SLOT)]
    def appointments(self, patient_id):
        self.reads.append("appointments")
        return []
    def book(self, patient_id, slot):
        self.writes.append((patient_id, slot["slotId"]))
        if self.outcome:
            raise self.outcome
        return {"appointmentId": "appt_9002", "patientId": patient_id, **{k: slot[k] for k in ("providerId", "specialty", "location", "startTime")}, "status": "scheduled"}
    def handoff(self, reason, summary):
        self.writes.append((reason, summary))
        return {"handoffId": "handoff_9003", "status": "queued"}


class SessionContractTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        try:
            module = importlib.import_module("ochsner_bob.session")
        except ModuleNotFoundError:
            self.fail("the shared revisioned SchedulingSession contract is missing")
        self.Session = module.SchedulingSession
        self.api = FixturePort()
        self.session = self.Session(self.api, journal_path=Path(self.tmp.name) / "effects.json", session_id="unit-session")

    def command(self, action, **data):
        return self.session.command(action, data, expected_revision=self.session.revision)

    def ready(self):
        self.command("identity", phone="555-0130", dob="1978-09-22", zip="70115")
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability")
        return self.command("select", index=1)["proposal"]

    def confirm(self, proposal):
        return self.session.command("confirm", {"proposal_id": proposal["id"], "nonce": proposal["nonce"]}, expected_revision=proposal["revision"])

    def test_public_lookup_needs_no_identity(self):
        view = self.command("discover", specialty="primary_care", location="downtown")
        self.assertEqual(len(view["providers"]), 1)
        self.assertEqual(self.api.reads, ["public"])

    def test_private_lookup_requires_current_identity(self):
        self.command("appointments")
        self.assertEqual(self.api.reads, [])

    def test_unreturned_slot_is_never_fabricated(self):
        self.command("select", index=1)
        self.assertIsNone(self.session.view()["proposal"])
        self.assertEqual(self.api.writes, [])

    def test_choice_is_not_confirmation_and_nonce_is_single_use(self):
        p = self.ready()
        self.assertEqual(self.api.writes, [])
        self.assertEqual(self.confirm(p)["current_result"]["status"], "completed")
        self.confirm(p)
        self.assertEqual(len(self.api.writes), 1)

    def test_concurrent_confirmation_claims_one_effect(self):
        p = self.ready()
        with ThreadPoolExecutor(max_workers=2) as pool:
            list(pool.map(lambda _: self.confirm(p), range(2)))
        self.assertEqual(len(self.api.writes), 1)

    def test_zip_correction_and_invalid_zip_clear_private_authority(self):
        p = self.ready()
        view = self.command("identity", phone="555-0130", dob="1978-09-22", zip="invalid")
        self.assertEqual(view["identity_status"], "missing")
        self.assertIsNone(view["proposal"])
        self.assertEqual(view["appointments"], [])
        self.confirm(p)
        self.assertEqual(self.api.writes, [])

    def test_duplicate_candidates_never_appear_in_view_or_trace(self):
        view = self.command("identity", phone="555-0130", dob="1978-09-22")
        self.assertEqual(view["identity_status"], "ambiguous")
        text = json.dumps({"view": view, "trace": self.session.events})
        for value in ("pat_1003", "pat_1004", "555-0130", "1978-09-22", "70115", "70005"):
            self.assertNotIn(value, text)

    def test_intervening_invalid_turn_revokes_proposal(self):
        p = self.ready()
        self.command("not_a_command")
        self.confirm(p)
        self.assertEqual(self.api.writes, [])

    def test_invalid_merged_dates_do_not_call_availability(self):
        self.command("identity", phone="555-0130", dob="1978-09-22", zip="70115")
        self.command("preferences", specialty="primary_care", start_date="2026-10-10", end_date="2026-10-20")
        self.command("preferences", start_date="2026-10-21")
        self.assertEqual(self.session.view()["preferences"]["start_date"], "2026-10-10")
        self.assertNotIn("availability", self.api.reads)

    def test_help_and_medical_are_reachable_from_terminal_and_takeover(self):
        p = self.ready()
        self.confirm(p)
        self.command("takeover")
        self.assertEqual(self.command("medical")["state"], "medical")
        self.assertEqual(self.command("help")["state"], "help")
        self.assertEqual(len(self.api.writes), 1)

    def test_trace_is_sanitized_and_observer_cannot_mutate_it(self):
        self.ready()
        trace = self.session.trace()
        text = json.dumps(trace)
        for value in ("pat_1003", "slot_4001", "555-0130", "1978-09-22", "70115"):
            self.assertNotIn(value, text)
        trace.clear()
        self.assertTrue(self.session.trace())

    def test_unknown_survives_reset_and_reconstruction(self):
        from ochsner_bob.http_mock import UnknownOutcome
        p = self.ready()
        self.api.outcome = UnknownOutcome("lost response")
        self.assertEqual(self.confirm(p)["current_result"]["status"], "unknown")
        self.command("reset")
        self.session = self.Session(self.api, journal_path=Path(self.tmp.name) / "effects.json", session_id="unit-session")
        self.assertTrue(self.session.view()["booking_blocked"])
        self.assertEqual(len(self.api.writes), 1)

    def test_decline_preserves_historical_success(self):
        p = self.ready()
        self.confirm(p)
        view = self.command("decline")
        self.assertEqual(view["history"][0]["status"], "completed")
        self.assertNotIn("never submitted", view["message"])

    def test_transport_read_error_has_safe_recovery_without_status(self):
        from ochsner_bob.http_mock import ApiError
        def unavailable(*args):
            raise ApiError(code="transport_error")
        self.api.providers = unavailable
        view = self.command("discover", specialty="primary_care")
        self.assertEqual(view["state"], "outage")
        self.assertEqual(self.command("help")["state"], "help")
