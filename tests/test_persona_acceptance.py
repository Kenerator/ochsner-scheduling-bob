"""Pinned-persona journeys over real local components and synthetic HTTP.

These are acceptance additions for existing behavior, not retrospective TDD
proof. No browser, model, identity authority or API fact is supplied by a mock
Session. The one named disconnected-wire case deliberately loses a response.
"""

from collections import Counter
from copy import deepcopy
from datetime import date, timedelta
import json
from pathlib import Path
import tempfile
import unittest

from ochsner_bob.browser_service import BrowserService
from ochsner_bob.conversation import Conversation
from ochsner_bob.http_mock import HttpMockAdapter
from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.session import SchedulingSession
from http_support import HostileServer, supplied_server


class PersonaAcceptanceTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bob-persona-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.server = self.enterContext(supplied_server())
        self.session = SchedulingSession(
            HttpMockAdapter(self.server.base_url), journal_path=self.directory / "session.json")
        self.conversation = Conversation(self.session)  # Explicit offline mode.

    def say(self, text):
        return self.conversation.interpret(text, self.session.revision)

    def identify(self):
        return self.conversation.enter_identity(
            "555-0101", "1985-04-12", "70112", expected_revision=self.session.revision)

    def ready(self):
        self.say("providers primary_care downtown")
        self.identify()
        options = self.say("availability")["slots"]
        self.assertTrue(options, "the supplied service must return an option before selection")
        return options, self.say("1")["proposal"]

    def confirm(self, proposal):
        return self.conversation.confirm(
            proposal["id"], proposal["nonce"], expected_revision=proposal["revision"])

    def audits(self, expected):
        # Original HTTP dispatch audits after responding. Wait for every known
        # request instead of sleeps; never accept only the expected subset.
        rows = self.server.wait_for_audits(len(expected))
        self.assertEqual(Counter((r["method"], r["route"], r["status"]) for r in rows),
                         Counter(expected))

    def service(self, kind=InteractionService):
        return kind(lambda: HttpMockAdapter(self.server.base_url), self.directory / "browser.json")

    @staticmethod
    def act(service, token, action, data=None):
        view = service.read(token)
        return service.command(token, action, data or {}, view.get("patient", view)["revision"])

    @staticmethod
    def receipt(view):
        return {"revision": view["revision"], "renderer": "bob-v1", "visible": ["message"],
                "draft": {}, "focus": None, "scroll": 0, "expanded": []}

    def test_jules_reviews_exact_returned_option_before_one_explicit_booking(self):
        # Catches selection/rendering becoming consent, or receipts drifting
        # from the appointment actually presented to the busy patient.
        options, proposal = self.ready()
        self.assertEqual(proposal["slot"], options[0])
        self.assertIsNone(self.conversation.view()["current_result"])
        self.assertIn("separate step", self.conversation.view()["message"])
        reads = [("GET", "/providers", 200), ("GET", "/patients/search", 200),
                 ("GET", "/availability", 200)]
        self.audits(reads)
        self.conversation.view()
        completed = self.confirm(proposal)
        result = completed["current_result"]
        self.assertEqual((result["kind"], result["status"]), ("booking", "completed"))
        for key in ("providerId", "specialty", "location", "startTime"):
            self.assertEqual(result["receipt"][key], options[0][key])
        self.assertTrue(self.confirm(proposal)["stale"])
        self.assertEqual(len(self.session.view()["history"]), 1)
        self.audits(reads + [("POST", "/appointments", 201)])

    def test_billy_june_corrects_travel_and_date_window_without_reusing_proposal(self):
        # Catches ignored window/provider constraints, partial invalid range
        # updates, or clearing one filter erasing unrelated valid preferences.
        options, old = self.ready()
        day = options[0]["startTime"][:10]  # Only a real HTTP-returned time is used.
        self.say(f"dates {day} {day}")
        self.say("provider 1")
        filtered = self.say("availability")
        self.assertTrue(filtered["slots"])
        for slot in filtered["slots"]:
            self.assertEqual((slot["location"], slot["providerId"], slot["startTime"][:10]),
                             ("downtown", "prov_2001", day))
        proposal = self.say("1")["proposal"]
        before = deepcopy(self.session.view()["preferences"])
        next_day = (date.fromisoformat(day) + timedelta(days=1)).isoformat()
        invalid = self.say("start " + next_day)
        self.assertEqual(invalid["preferences"], before)
        self.assertIsNone(invalid["proposal"])
        self.assertIn("previous valid range is retained", invalid["message"])
        self.assertTrue(self.confirm(proposal)["stale"])
        corrected = self.say("location uptown")
        self.assertEqual(corrected["preferences"]["location"], "uptown")
        self.assertIsNone(corrected["proposal"])
        cleared = self.say("clear provider")
        self.assertEqual(cleared["preferences"], {"specialty": "primary_care", "location": "uptown",
                                                "start_date": day, "end_date": day})
        self.assertEqual(cleared["identity_status"], "verified")
        self.assertTrue(self.confirm(old)["stale"])
        self.audits([("GET", "/providers", 200), ("GET", "/patients/search", 200),
                     ("GET", "/availability", 200), ("GET", "/availability", 200)])

    def test_amy_lou_gets_no_email_assistance_without_smartphone_or_identity(self):
        # Catches mandatory contact entry, private text blocking Help, or mock
        # queue creation being described as basic-phone access/staff delivery.
        partial = self.conversation.enter_identity("", "", expected_revision=0)
        self.assertEqual(partial["identity_status"], "missing")
        help_view = self.say("I have no email or smartphone. My phone is 555-0101; help")
        self.assertEqual(help_view["state"], "help")
        self.assertIn("No email is required", help_view["message"])
        self.assertIn("does not provide basic-phone access or real staff contact", help_view["message"])
        queued = self.say("handoff")
        self.assertEqual((queued["current_result"]["kind"], queued["current_result"]["status"]),
                         ("handoff", "queued"))
        self.assertIn("does not mean a real employee received it or joined", queued["message"])
        summary = self.server.store.handoffs[0]["summary"]
        self.assertIn("missing=private_identity", summary)
        self.assertNotIn("555-0101", summary)
        self.audits([("POST", "/handoffs", 201)])

    def test_ellie_rae_recovers_numbered_choice_without_reentering_valid_context(self):
        # Catches invalid choice erasing identity/options or a short number
        # booking immediately. This is text selection, not a browser focus test.
        options, old = self.ready()
        invalid = self.say("99")
        self.assertEqual(invalid["identity_status"], "verified")
        self.assertEqual(invalid["preferences"], {"specialty": "primary_care", "location": "downtown"})
        self.assertEqual(invalid["slots"], options)
        self.assertIsNone(invalid["proposal"])
        self.assertIn("Choose a number", invalid["message"])
        selected = self.say("1")
        self.assertEqual(selected["proposal"]["slot"], options[0])
        self.assertNotEqual(selected["proposal"]["id"], old["id"])
        self.assertIsNone(selected["current_result"])
        self.audits([("GET", "/providers", 200), ("GET", "/patients/search", 200),
                     ("GET", "/availability", 200)])

    def test_nina_jean_gets_plain_choice_and_explicit_typo_correction_not_clinical_guess(self):
        # Catches automatic typo selection and obscure/no next-step wording
        # when an identified patient has not selected a scheduling specialty.
        self.identify()
        unclear = self.say("availability")
        self.assertIn("Choose Primary care or Dermatology", unclear["message"])
        typo = self.say("specialty primry_care")
        self.assertEqual(typo["preferences"], {})
        self.assertIn({"field": "specialty", "value": "primary_care"}, typo["suggestions"])
        corrected = self.say("specialty primary_care")
        self.assertEqual(corrected["preferences"], {"specialty": "primary_care"})
        self.say("location downtown")
        self.say("availability")
        proposal = self.say("1")["proposal"]
        visible = self.say("location uptown")
        self.assertEqual(visible["preferences"], {"specialty": "primary_care", "location": "uptown"})
        self.assertIsNone(visible["proposal"])
        self.assertTrue(self.confirm(proposal)["stale"])
        medical = self.say("Which medication should I take for these symptoms?")
        self.assertEqual(medical["state"], "medical")
        self.assertIn("cannot give medical advice or triage", medical["message"])
        self.audits([("GET", "/patients/search", 200), ("GET", "/availability", 200)])

    def test_morgan_rae_observes_acknowledged_screen_and_truthful_paired_handoff(self):
        # Catches unseen state masquerading as observed, leaked consent,
        # cross-session context, and demo participation conflated with delivery.
        service = self.service(BrowserService)
        patient = service.create()["token"]
        other = service.create()["token"]
        support = service.join(service.pair(patient))
        initial = service.read(patient)
        service.ack(patient, self.receipt(initial))
        public = self.act(service, patient, "discover", {"specialty": "primary_care", "location": "downtown"})
        unseen = service.read(support)
        self.assertEqual(unseen["observed_patient"], initial)
        self.assertFalse(unseen["fresh"])
        self.assertEqual(unseen["patient"]["revision"], public["revision"])
        self.assertEqual((unseen["known"], unseen["missing"]), ([], ["private identity"]))
        self.act(service, patient, "identity", {"phone": "555-0101", "dob": "1985-04-12", "zip": "70112"})
        self.act(service, patient, "availability")
        delivered = self.act(service, patient, "select", {"index": 1})
        service.ack(patient, self.receipt(delivered))
        mirror = service.read(support)
        expected = deepcopy(delivered)
        nonce = expected["proposal"].pop("nonce")
        self.assertEqual(mirror["observed_patient"], expected)
        self.assertEqual((mirror["known"], mirror["missing"]), (["synthetic identity verified"], []))
        self.assertTrue(mirror["fresh"])
        self.assertNotIn(nonce, json.dumps(mirror))
        with self.assertRaises(PermissionError):
            service.command(support, "confirm", {}, delivered["revision"])
        takeover = self.act(service, support, "takeover")
        self.assertEqual(takeover["demo_support"], "joined")
        self.assertIsNone(takeover["patient"]["proposal"])
        self.act(service, support, "return")
        self.act(service, patient, "help")
        queued = self.act(service, patient, "handoff", {"reason": "user_requested"})
        self.assertEqual(queued["current_result"]["status"], "queued")
        self.assertIn("does not mean a real employee", queued["message"])
        self.assertEqual(service.read(support)["demo_support"], "not_joined")
        self.assertEqual([r["kind"] for r in queued["history"]], ["handoff"])
        self.assertIn("current_booking=not_attempted", self.server.store.handoffs[0]["summary"])
        self.assertEqual((service.read(other)["history"], service.read(other)["identity_status"]), ([], "missing"))
        self.audits([("GET", "/providers", 200), ("GET", "/patients/search", 200),
                     ("GET", "/availability", 200), ("POST", "/handoffs", 201)])

    def test_sam_rae_reviews_and_forks_recording_without_live_authority_or_hidden_parity(self):
        # Catches replay reaching the live HTTP core, references authorizing
        # another session, or a simulation claiming live-renderer equivalence.
        service = self.service()
        patient = service.create()["token"]
        service.capture(patient, True, synthetic=True)
        service.text(patient, "help", 0)
        service.text(patient, "providers primary_care downtown", service.read(patient)["revision"])
        report = service.capture(patient, False, synthetic=True)
        self.assertEqual(report["recording"], "full_replay")
        before = service.read(patient)
        opened = service.replay(patient, "open", {"reference": report["reference"]})
        self.assertTrue(opened["simulation_only"])
        self.assertFalse(opened["fidelity"]["core_renderer_parity"])
        self.assertEqual(service.replay(patient, "step", {})["index"], 0)
        fork = service.replay(patient, "fork", {"index": 1, "changes": {"preferences": {"location": "uptown"}}})
        self.assertTrue(fork["simulation_only"])
        self.assertNotEqual(fork["reference"], report["reference"])
        comparison = service.replay(patient, "compare", {"reference": report["reference"]})
        self.assertTrue(comparison["comparison"]["differences"])
        with self.assertRaises(PermissionError):
            service.replay(patient, "promote", {"reviewed": False})
        promoted = service.replay(patient, "promote", {"reviewed": True})["proposal"]
        self.assertTrue(promoted["fixture"])
        self.assertTrue(promoted["requires_execution_review"])
        with self.assertRaises(PermissionError):
            service.replay(service.create()["token"], "open", {"reference": report["reference"]})
        service.replay(patient, "close", {})
        self.assertEqual(service.read(patient), before)
        self.audits([("GET", "/providers", 200)])

    def test_sam_rae_unknown_wire_result_survives_reset_and_fresh_identity_without_retry(self):
        # Catches reset/re-identification reviving a claim after a submitted
        # POST loses its response. Only the external wire is fault-injected.
        _, proposal = self.ready()
        with HostileServer(action="disconnect") as wire:
            self.session.api = HttpMockAdapter(wire.base_url)
            unknown = self.confirm(proposal)
            self.assertEqual(unknown["current_result"]["status"], "unknown")
            self.assertIn("may have succeeded", unknown["message"])
            self.assertTrue(unknown["booking_blocked"])
            self.say("reset")
            self.assertTrue(self.session.view()["booking_blocked"])
            self.session.api = HttpMockAdapter(self.server.base_url)
            _, fresh = self.ready()
            denied = self.confirm(fresh)
            self.assertEqual(denied["current_result"]["status"], "unknown")
            self.assertEqual([r["status"] for r in denied["history"]], ["unknown"])
            self.assertTrue(denied["booking_blocked"])
            self.assertEqual(len(wire.wait_for_requests(1)), 1)
            self.audits([("GET", "/providers", 200), ("GET", "/patients/search", 200),
                         ("GET", "/availability", 200)] * 2)


if __name__ == "__main__":
    unittest.main()
