"""R02/R04/R05/R06/R07: real-session boundaries, not browser/model evidence.

Normal facts come from the unchanged supplied HTTP service. Explicit hostile
transport/boundary faults cover responses that its eight scenarios cannot emit.
"""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from uuid import uuid4

from ochsner_bob.http_mock import HttpMockAdapter, UnknownOutcome
from ochsner_bob.session import SchedulingSession
from ochsner_bob.suggestions import suggest
from http_support import HostileServer, supplied_server


class TransitionAcceptanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bob-transitions-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.server = self.enterContext(supplied_server())
        self.session = self.new_session(self.server)

    def new_session(self, server):
        return SchedulingSession(HttpMockAdapter(server.base_url),
                                 journal_path=self.directory / (uuid4().hex + ".json"))

    def command(self, action, **data):
        return self.session.command(action, data, expected_revision=self.session.revision)

    def identify(self, **changes):
        return self.command("identity", **{"phone": "555-0101", "dob": "1985-04-12", "zip": "70112", **changes})

    def ready(self, slot_id="slot_4001"):
        self.identify()
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability")
        return self.select(slot_id)

    def select(self, slot_id):
        slots = self.session.view()["slots"]
        index = next(i for i, row in enumerate(slots, 1) if row["slotId"] == slot_id)
        proposal = self.command("select", index=index)["proposal"]
        self.assertIsNotNone(proposal)
        return proposal

    def confirm(self, proposal):
        return self.session.command("confirm", {"proposal_id": proposal["id"], "nonce": proposal["nonce"]},
                                    expected_revision=proposal["revision"])

    def assert_private_cleared(self, view):
        self.assertEqual((view["appointments"], view["slots"], view["proposal"]), ([], [], None))
        self.assertIsNone(self.session.identity)

    def test_zero_match_prevents_private_progress_without_disclosing_candidates(self):
        view = self.identify(phone="555-9999", dob="1990-01-01", zip="")
        self.assertEqual((view["state"], view["identity_status"]), ("identity_required", "missing"))
        for action in ("availability", "appointments", "select", "confirm"):
            self.command(action, index=1)
        self.assertEqual(self.server.wait_for_audits(1), [{"method": "GET", "route": "/patients/search", "status": 200}])
        self.assert_private_cleared(self.session.view())

    def test_duplicate_zip_a_to_b_revokes_private_results_and_old_confirmation(self):
        self.identify(phone="555-0130", dob="1978-09-22", zip="")
        self.assertEqual(self.session.view()["identity_status"], "ambiguous")
        self.command("appointments")
        first = self.command("identity", zip="70115")
        self.assertEqual(first["identity_status"], "verified")
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability")
        booked = self.confirm(self.select("slot_4001"))
        self.assertEqual(booked["current_result"]["receipt"]["patientId"], "pat_1003")
        self.assertTrue(self.command("appointments")["appointments"])
        self.command("availability")
        old = self.select("slot_conflict_001")
        corrected = self.command("identity", zip="70005")
        self.assertEqual(corrected["identity_status"], "verified")
        self.assertEqual((corrected["appointments"], corrected["slots"], corrected["proposal"]), ([], [], None))
        self.confirm(old)
        self.assertEqual(self.command("appointments")["appointments"], [])
        self.assertEqual(self.session.view()["history"], booked["history"])
        self.assertEqual(len(self.server.store.appointments), 3)
        for token in ("pat_1003", "pat_1004", "555-0130", "1978-09-22", "70115", "70005"):
            self.assertNotIn(token, json.dumps(self.session.trace()))

    def test_invalid_zip_including_falsy_wrong_types_revokes_before_search(self):
        expected_audits = 0
        for invalid in (0, False, None, [], {}, "1234", "123456", "private-zip"):
            with self.subTest(zip_type=type(invalid).__name__):
                proposal = self.ready()
                self.assertTrue(self.command("appointments")["appointments"])
                expected_audits += 3  # identity, availability, appointment lookup
                audits = len(self.server.wait_for_audits(expected_audits))
                corrected = self.command("identity", zip=invalid)
                self.assertEqual(corrected["identity_status"], "missing")
                self.assert_private_cleared(corrected)
                self.confirm(proposal)
                self.command("appointments")
                self.assertEqual(len(self.server.audits), audits)
                self.assertEqual(self.session.view()["history"], [])

    def test_invalid_birth_date_is_never_echoed_in_view_or_trace(self):
        for invalid in ("private-birth-sentinel", "1985-02-30", "19850412", "\ud800"):
            self.identify()
            view = self.command("identity", dob=invalid)
            self.assert_private_cleared(view)
            self.assertNotIn(invalid, json.dumps(view, ensure_ascii=False))
            self.assertNotIn(invalid, json.dumps(self.session.trace(), ensure_ascii=False))

    def test_empty_appointments_are_distinct_from_failed_refresh(self):
        self.identify(phone="555-0130", dob="1978-09-22", zip="70115")
        view = self.command("appointments")
        self.assertEqual((view["state"], view["appointments"]), ("appointments", []))
        self.assertIn("No existing", view["message"])
        self.assertEqual([r["status"] for r in self.server.wait_for_audits(2)], [200, 200])

    def test_404_appointment_refresh_clears_old_private_rows(self):
        self.identify()
        self.assertTrue(self.command("appointments")["appointments"])
        # Fault boundary only: the unchanged service cannot remove a verified
        # patient dynamically. Exercise its documented 404 shape over real HTTP.
        with HostileServer(status=404, payload={"code": "patient_not_found", "message": "private-patient"}) as hostile:
            self.session.api = HttpMockAdapter(hostile.base_url)
            view = self.command("appointments")
            self.assertEqual(hostile.wait_for_requests(1)[0]["method"], "GET")
        self.assertEqual((view["state"], view["appointments"]), ("rejected", []))
        self.assertNotIn("private-patient", view["message"])
        self.assertNotIn("No existing", view["message"])

    def test_503_appointment_refresh_clears_old_private_rows(self):
        self.identify()
        self.assertTrue(self.command("appointments")["appointments"])
        self.session.api = HttpMockAdapter(self.server.base_url, scenario="api_failure")
        view = self.command("appointments")
        self.assertEqual((view["state"], view["appointments"]), ("outage", []))
        self.assertEqual([r["status"] for r in self.server.wait_for_audits(3)], [200, 200, 503])
        self.assertNotIn("No existing", view["message"])

    def test_transport_and_malformed_appointment_refresh_clear_old_private_rows(self):
        for fault in ({"action": "disconnect"}, {"status": 200, "payload": {"wrong": []}}):
            self.session.api = HttpMockAdapter(self.server.base_url)
            self.identify()
            self.assertTrue(self.command("appointments")["appointments"])
            with HostileServer(**fault) as hostile:
                self.session.api = HttpMockAdapter(hostile.base_url)
                view = self.command("appointments")
                hostile.wait_for_requests(1)
            self.assertEqual(view["appointments"], [])
            self.assertIn(view["state"], {"outage", "rejected"})

    def test_failed_availability_refresh_cannot_reselect_stale_slots(self):
        old = self.ready()
        self.session.api = HttpMockAdapter(self.server.base_url, scenario="api_failure")
        view = self.command("availability")
        self.assertEqual((view["state"], view["slots"], view["proposal"]), ("outage", [], None))
        self.assertIsNone(self.command("select", index=1)["proposal"])
        self.confirm(old)
        self.assertEqual(self.session.view()["history"], [])

    def test_success_then_conflict_preserves_prior_receipt_and_current_rejection(self):
        original = deepcopy(self.confirm(self.ready())["current_result"])
        self.command("availability")
        rejected = self.confirm(self.select("slot_conflict_001"))
        self.assertEqual(rejected["current_result"]["status"], "rejected")
        self.assertNotIn("receipt", rejected["current_result"])
        self.assertEqual(rejected["history"], [original, rejected["current_result"]])
        for action in ("decline", "help", "medical", "unsupported", "reset"):
            view = self.command(action)
            self.assertEqual(view["history"][0], original)
            self.assertEqual(view["current_result"]["status"], "rejected")
            self.assertNotIn("never submitted", view["message"])
        self.assertEqual(len(self.server.store.appointments), 3)

    def build_state(self, state, server):
        self.session = self.new_session(server)
        if state == "start":
            return
        if state == "partial_identity":
            self.command("identity", phone="555-0101")
            return
        if state in {"ambiguous", "identity_required"}:
            self.identify(**({"phone": "555-0130", "dob": "1978-09-22", "zip": ""}
                             if state == "ambiguous" else {"phone": "555-9999", "dob": "1990-01-01"}))
            return
        if state == "ready":
            self.identify()
            return
        if state == "preferences":
            self.command("preferences", specialty="primary_care")
            return
        if state == "providers":
            self.command("discover")
            return
        if state in {"help", "medical", "unsupported", "declined"}:
            self.command("decline" if state == "declined" else state)
            return
        if state == "outage":
            self.session.api = HttpMockAdapter(server.base_url, scenario="api_failure")
            self.command("discover")
            self.session.api = HttpMockAdapter(server.base_url)
            return
        if state == "error":
            # Explicit programming-boundary fault, not a supplied scenario.
            class BrokenRead:
                def providers(self, *_args):
                    raise RuntimeError("private boundary sentinel")
            self.session.api = BrokenRead()
            self.command("discover")
            self.session.api = HttpMockAdapter(server.base_url)
            return
        if state == "queued":
            self.command("handoff", reason="user_requested")
            return
        if state == "failed":
            self.session.api = HttpMockAdapter(server.base_url, scenario="api_failure")
            self.command("handoff", reason="api_failure")
            self.session.api = HttpMockAdapter(server.base_url)
            return
        if state == "appointments":
            self.identify()
            self.command("appointments")
            return
        proposal = self.ready("slot_conflict_001" if state == "rejected" else "slot_4001")
        if state == "options":
            self.command("availability")
        elif state == "proposal":
            pass
        elif state == "takeover":
            self.command("takeover")
        elif state == "unknown":
            with HostileServer(action="disconnect") as hostile:
                self.session.api = HttpMockAdapter(hostile.base_url)
                self.confirm(proposal)
                hostile.wait_for_requests(1)
            self.session.api = HttpMockAdapter(server.base_url)
        else:
            self.confirm(proposal)

    def test_all_reachable_state_safety_and_public_interruptions_are_effect_free(self):
        states = ("start", "partial_identity", "ambiguous", "identity_required", "ready", "preferences", "providers",
                  "options", "proposal", "appointments", "help", "medical", "unsupported", "declined",
                  "completed", "rejected", "unknown", "queued", "failed", "outage", "error", "takeover")
        for state in states:
            for action in ("help", "medical", "unsupported", "discover"):
                with self.subTest(initial=state, action=action), supplied_server() as server:
                    self.build_state(state, server)
                    before = self.session.view()
                    if state not in {"partial_identity", "takeover"}:
                        self.assertEqual(before["state"], state)
                    appointments, handoffs = len(server.store.appointments), len(server.store.handoffs)
                    after = self.command(action)
                    self.assertEqual(after["state"], "providers" if action == "discover" else action)
                    self.assertIsNone(after["proposal"])
                    self.assertEqual(after["history"], before["history"])
                    self.assertEqual(after["booking_blocked"], before["booking_blocked"])
                    self.assertEqual((len(server.store.appointments), len(server.store.handoffs)), (appointments, handoffs))
                    if action == "medical":
                        self.assertIn("cannot give medical advice or triage", after["message"])
                    if action == "discover":
                        self.assertTrue(after["providers"])
                        self.assertEqual(self.session.last_policy["rule"], "public_discovery")

    def test_typo_suggestions_require_explicit_canonical_selection(self):
        self.command("preferences", location="downtown")
        view = self.command("preferences", specialty="primry_care")
        self.assertEqual(view["preferences"], {"location": "downtown"})
        self.assertIn({"field": "specialty", "value": "primary_care"}, view["suggestions"])
        self.assertEqual(self.server.audits, [])
        chosen = self.command("preferences", specialty="primary_care")
        self.assertEqual(chosen["preferences"], {"specialty": "primary_care", "location": "downtown"})
        self.assertEqual(chosen["suggestions"], [])

    def test_provider_name_suggestion_never_selects_or_changes_active_filter(self):
        self.command("discover", specialty="primary_care", location="downtown")
        self.command("preferences", provider_id="prov_2002")
        before = self.session.view()["preferences"]
        typo = self.command("preferences", provider_id="Dr. Elna Brooks")
        self.assertEqual(typo["preferences"], before)
        self.assertIn({"field": "provider_id", "value": "prov_2001", "label": "Dr. Elena Brooks"}, typo["suggestions"])
        self.assertEqual(self.server.wait_for_audits(1), [{"method": "GET", "route": "/providers", "status": 200}])
        selected = self.command("preferences", provider_id="prov_2001")
        self.assertEqual(selected["preferences"]["provider_id"], "prov_2001")
        self.command("preferences", provider_id=None)
        self.assertEqual(self.session.view()["preferences"], {"specialty": "primary_care", "location": "downtown"})

    def test_reset_and_unrelated_errors_cannot_keep_stale_suggestions(self):
        for action, data in (("reset", {}), ("help", {}), ("preferences", {"start_date": "bad-date"})):
            self.command("preferences", location="downtwn")
            self.assertTrue(self.session.view()["suggestions"])
            self.assertEqual(self.command(action, **data)["suggestions"], [])


class PublicSuggestionBoundaryTests(unittest.TestCase):
    def test_arbitrary_patient_vocabulary_is_rejected_before_fuzzy_matching(self):
        with self.assertRaises(ValueError):
            suggest("Avery", ["Avery Patel", "Maya Chen"])

    def test_private_records_cannot_masquerade_as_returned_providers(self):
        with self.assertRaises(ValueError):
            suggest("Avery", "provider", providers=[{"patientId": "pat_1003", "firstName": "Avery", "lastName": "Patel"}])

    def test_public_fuzzy_fields_are_bounded_and_return_only_canonical_choices(self):
        self.assertEqual(suggest("dermatolgy", "specialty"), [{"field": "specialty", "value": "dermatology"}])
        self.assertEqual(suggest("downtwn", "location"), [{"field": "location", "value": "downtown"}])
        for query in ("555-0130", "1978-09-22", "pat_1003", "x" * 129, None):
            with self.assertRaises(ValueError):
                suggest(query, "specialty")
        for limit in (0, 4, True, float("inf")):
            with self.assertRaises(ValueError):
                suggest("dermatolgy", "specialty", limit=limit)

    def test_package_exports_production_session_and_http_unknown_outcome(self):
        import ochsner_bob
        self.assertIs(getattr(ochsner_bob, "SchedulingSession", None), SchedulingSession)
        self.assertIs(ochsner_bob.UnknownOutcome, UnknownOutcome)
        self.assertIs(getattr(ochsner_bob, "HttpMockAdapter", None), HttpMockAdapter)
        self.assertFalse(hasattr(ochsner_bob, "BobSession"))
        self.assertFalse(hasattr(ochsner_bob, "MockSchedulingApi"))
