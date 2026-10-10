"""Supplied scenario integration: actual session, ZEN, journal and original HTTP API.

These are deterministic command journeys with synthetic identity controls. They
do not qualify natural-language classification, browser behavior or live models.
No scheduling fixtures or SessionContractTests doubles supply application facts.
"""

from collections import Counter
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.http_mock import HttpMockAdapter
from ochsner_bob.journal import EffectJournal
from ochsner_bob.policy import Policy
from ochsner_bob.session import SchedulingSession
from http_support import supplied_server


SCENARIO_IDS = (
    "happy_path_booking", "provider_lookup", "no_patient_match",
    "multiple_patient_matches", "slot_conflict", "no_availability",
    "api_failure", "unsupported_request",
)
SEARCH = ("GET", "/patients/search", 200)
AVAILABILITY = ("GET", "/availability", 200)
APPOINTMENTS = ("GET", "/patients/{patientId}/appointments", 200)
BOOKED = ("POST", "/appointments", 201)
QUEUED = ("POST", "/handoffs", 201)
PRIVATE = ("555-0101", "1985-04-12", "70112", "pat_1001", "Maya", "Chen",
           "555-0102", "1992-06-03", "70118", "pat_1002", "Jordan", "Lee",
           "555-9999", "1990-01-01",
           "555-0130", "1978-09-22", "70115", "70005", "pat_1003", "pat_1004",
           "Avery", "Patel", "slot_4001", "slot_4002", "slot_4003", "slot_conflict_001")


class SuppliedHttpScenarioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # ID-only source binding survives clean export; raw intake is not a test
        # runtime dependency. The manifest includes the reviewed original hash.
        source = Path(__file__).resolve().parent / "fixtures/supplied_scenarios.json"
        ids = json.loads(source.read_text(encoding="utf-8"))["scenario_ids"]
        methods = {name for name in cls.__dict__ if name.startswith("test_")}
        if (type(ids) is not list or len(ids) != 8 or set(ids) != set(SCENARIO_IDS)
                or methods != {"test_" + i for i in ids}):
            raise AssertionError("Executable scenario IDs must match all eight supplied scenarios")

    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bob-supplied-http-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.server = self.enterContext(supplied_server())
        self.api_events = []
        self.session_events = []
        self.expected_audits = []
        self.new_session(self._testMethodName.removeprefix("test_"))

    def new_session(self, scenario, journal_name="effects.json"):
        self.journal_path = self.directory / journal_name
        self.session = SchedulingSession(
            HttpMockAdapter(self.server.base_url, scenario=scenario, event_sink=self.api_events.append),
            journal_path=self.journal_path, policy=Policy(), event_sink=self.session_events.append,
        )

    def assert_audits(self, expected):
        self.expected_audits.extend(expected)
        rows = self.server.wait_for_audits(len(self.expected_audits))
        # Dispatch emits audits after responding: wait for known requests instead
        # of sleeping. Independent handler audit order need not equal response order.
        actual = Counter((r["method"], r["route"], r["status"]) for r in rows)
        self.assertEqual(actual, Counter(self.expected_audits))

    def command(self, action, *, expect=(), **data):
        view = self.session.command(action, data, expected_revision=self.session.revision)
        self.assert_audits(expect)
        return view

    def confirm(self, proposal, *, expect):
        view = self.session.command("confirm", {"proposal_id": proposal["id"], "nonce": proposal["nonce"]},
                                    expected_revision=proposal["revision"])
        self.assert_audits(expect)
        return view

    def assert_private_absent(self, value):
        encoded = json.dumps(value)
        for token in PRIVATE:
            self.assertNotIn(token, encoded)

    def assert_policy(self, rule, allow=True):
        decision = self.session.last_policy
        self.assertIsNotNone(decision)
        self.assertEqual((decision["engine"], decision["rule"], decision["allow"]),
                         ("zen-engine", rule, allow))
        self.assertRegex(decision["policy_digest"], r"^[0-9a-f]{64}$")

    def assert_persisted(self, kind, status):
        # Read through a fresh real journal, not just the session's cached result.
        self.assertEqual(EffectJournal(self.journal_path).status(self.session.id + ":" + kind), status)

    def identify(self, *, phone="555-0101", dob="1985-04-12", zip_code="70112"):
        view = self.command("identity", phone=phone, dob=dob, zip=zip_code, expect=(SEARCH,))
        self.assertEqual(view["identity_status"], "verified")
        return view

    def select_returned(self, slot_id):
        options = self.session.view()["slots"]
        claim_before = self.session.journal.status(self.session.id + ":booking")
        indices = [i for i, slot in enumerate(options, 1) if slot["slotId"] == slot_id]
        self.assertEqual(len(indices), 1, "select only a uniquely returned API option")
        view = self.command("select", index=indices[0])
        self.assertIsNotNone(view["proposal"])
        self.assertEqual(view["proposal"]["slot"], options[indices[0] - 1])
        self.assertEqual(self.session.journal.status(self.session.id + ":booking"), claim_before)
        return view["proposal"]

    def ready(self, slot_id="slot_4001"):
        self.identify()
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability", expect=(AVAILABILITY,))
        self.assert_policy("verified_read")
        return self.select_returned(slot_id)

    def assert_diagnostics_private(self):
        self.assert_private_absent({"trace": self.session.trace(), "session_sink": self.session_events,
                                    "http_sink": self.api_events})

    def test_happy_path_booking(self):
        proposal = self.ready()
        self.assertIsNone(self.session.view()["current_result"])
        self.assertEqual(sum(r[0] == "POST" for r in self.expected_audits), 0)
        completed = self.confirm(proposal, expect=(BOOKED,))
        self.assert_policy("booking_ready")
        self.assertEqual(completed["current_result"]["status"], "completed")
        receipt = completed["current_result"]["receipt"]
        self.assertEqual((receipt["patientId"], receipt["providerId"], receipt["status"]),
                         ("pat_1001", "prov_2001", "scheduled"))
        for field in ("providerId", "specialty", "location", "startTime"):
            self.assertEqual(receipt[field], proposal["slot"][field])
        self.assert_persisted("booking", "completed")
        # Real appointment lookup proves that the supplied server accepted it.
        lookup = self.command("appointments", expect=(APPOINTMENTS,))
        self.assertIn(receipt, lookup["appointments"])
        self.assertTrue(all(a["patientId"] == "pat_1001" for a in lookup["appointments"]))
        self.command("confirm", proposal_id=proposal["id"], nonce=proposal["nonce"])
        self.assertEqual(len(self.session.view()["history"]), 1)
        self.assert_diagnostics_private()

    def test_provider_lookup(self):
        view = self.command("discover", specialty="primary_care", location="downtown",
                            expect=(("GET", "/providers", 200),))
        self.assertEqual(view["identity_status"], "missing")
        self.assertEqual([p["providerId"] for p in view["providers"]], ["prov_2001", "prov_2002"])
        self.assert_policy("public_discovery")
        self.assertEqual((view["slots"], view["appointments"], view["history"]), ([], [], []))
        self.command("appointments")
        self.assert_policy("identity_required", allow=False)
        self.assert_persisted("booking", None)
        self.assert_diagnostics_private()

    def test_no_patient_match(self):
        view = self.command("identity", phone="555-9999", dob="1990-01-01", expect=(SEARCH,))
        self.assertEqual(view["identity_status"], "missing")
        self.assertEqual(view["state"], "identity_required")
        self.assertEqual((view["slots"], view["appointments"], view["history"]), ([], [], []))
        self.assert_private_absent(view)
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability")
        self.assert_policy("identity_required", allow=False)
        self.command("appointments")
        self.command("select", index=1)
        self.command("confirm", proposal_id="invented", nonce="invented")
        handoff = self.command("handoff", reason="identity_unclear", expect=(QUEUED,))
        self.assertEqual(handoff["current_result"]["status"], "queued")
        self.assertEqual(handoff["current_result"]["receipt"]["status"], "queued")
        self.assert_persisted("handoff", "completed")
        self.assert_persisted("booking", None)
        self.assertEqual(self.server.store.handoffs[0]["reason"], "identity_unclear")
        self.assert_private_absent(self.server.store.handoffs[0]["summary"])
        self.assert_diagnostics_private()

    def test_multiple_patient_matches(self):
        ambiguous = self.command("identity", phone="555-0130", dob="1978-09-22", expect=(SEARCH,))
        self.assertEqual(ambiguous["identity_status"], "ambiguous")
        self.assert_private_absent(ambiguous)
        self.command("appointments")
        self.assert_policy("identity_required", allow=False)
        # ZIP is a private local filter. Both resolutions still use real HTTP search.
        first = self.command("identity", zip="70115", expect=(SEARCH,))
        self.assertEqual(first["identity_status"], "verified")
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability", expect=(AVAILABILITY,))
        old = self.select_returned("slot_4001")
        corrected = self.command("identity", zip="70005", expect=(SEARCH,))
        self.assertEqual(corrected["identity_status"], "verified")
        self.assertIsNone(corrected["proposal"])
        self.assertEqual((corrected["slots"], corrected["appointments"]), ([], []))
        self.command("confirm", proposal_id=old["id"], nonce=old["nonce"])
        self.assertEqual(self.command("appointments", expect=(APPOINTMENTS,))["appointments"], [])
        self.command("availability", expect=(AVAILABILITY,))
        fresh = self.select_returned("slot_4001")
        booked = self.confirm(fresh, expect=(BOOKED,))
        self.assertEqual(booked["current_result"]["receipt"]["patientId"], "pat_1004")
        self.assert_persisted("booking", "completed")
        invalid = self.command("identity", zip="invalid")
        self.assertEqual(invalid["identity_status"], "missing")
        self.assertIsNone(invalid["proposal"])
        self.command("appointments")
        self.assert_policy("identity_required", allow=False)
        self.assertEqual(len(invalid["history"]), 1)
        self.assert_diagnostics_private()

    def test_slot_conflict(self):
        proposal = self.ready("slot_conflict_001")
        rejected = self.confirm(proposal, expect=(("POST", "/appointments", 409),))
        self.assertEqual((rejected["current_result"]["status"], rejected["current_result"]["http_status"]),
                         ("rejected", 409))
        self.assertNotIn("receipt", rejected["current_result"])
        self.assertIsNone(rejected["proposal"])
        self.assert_persisted("booking", "rejected")
        # Conflict does not carry confirmation into another slot or a retry.
        self.command("confirm", proposal_id=proposal["id"], nonce=proposal["nonce"])
        self.assertIsNone(self.command("select", index=1)["proposal"])
        self.command("availability", expect=(AVAILABILITY,))
        fresh = self.select_returned("slot_4001")
        self.assertNotEqual(fresh["id"], proposal["id"])
        self.assertNotEqual(fresh["nonce"], proposal["nonce"])
        self.assertEqual(self.session.view()["current_result"]["status"], "rejected")
        completed = self.confirm(fresh, expect=(BOOKED,))
        self.assertEqual([r["status"] for r in completed["history"]], ["rejected", "completed"])
        self.assertEqual(completed["current_result"]["receipt"]["startTime"], fresh["slot"]["startTime"])
        self.assert_persisted("booking", "completed")
        self.assert_diagnostics_private()

    def test_no_availability(self):
        self.identify(phone="555-0102", dob="1992-06-03", zip_code="70118")
        self.command("preferences", specialty="dermatology", location="lakeside")
        empty = self.command("availability", expect=(AVAILABILITY,))
        self.assertEqual(empty["slots"], [])
        self.assertIsNone(empty["proposal"])
        self.assertIsNone(self.command("select", index=1)["proposal"])
        self.command("confirm", proposal_id="invented", nonce="invented")
        handoff = self.command("handoff", reason="no_availability", expect=(QUEUED,))
        self.assertEqual(handoff["current_result"]["status"], "queued")
        self.assertEqual(self.server.store.handoffs[0]["reason"], "no_availability")
        self.assert_persisted("booking", None)
        self.assert_persisted("handoff", "completed")
        self.assert_diagnostics_private()

    def test_api_failure(self):
        outage = self.command("identity", phone="555-0101", dob="1985-04-12",
                              expect=(("GET", "/patients/search", 503),))
        self.assertEqual((outage["state"], outage["identity_status"]), ("outage", "missing"))
        public = self.command("discover", specialty="primary_care", location="downtown",
                              expect=(("GET", "/providers", 503),))
        self.assertEqual(public["providers"], [])
        failed = self.command("handoff", reason="api_failure", expect=(("POST", "/handoffs", 503),))
        self.assertEqual((failed["current_result"]["status"], failed["current_result"]["http_status"]),
                         ("failed", 503))
        self.assertNotIn("receipt", failed["current_result"])
        self.assertEqual(self.server.store.handoffs, [])
        self.assert_persisted("handoff", "failed")
        self.assert_persisted("booking", None)
        self.assert_diagnostics_private()

        # Introduce the documented outage after a real fresh proposal using a
        # second actual adapter. Neither the supplied handler nor policy is patched.
        self.new_session(None, journal_name="booking-effects.json")
        proposal = self.ready()
        self.session.api = HttpMockAdapter(self.server.base_url, scenario="api_failure",
                                           event_sink=self.api_events.append)
        failed_booking = self.confirm(proposal, expect=(("POST", "/appointments", 503),))
        self.assertEqual((failed_booking["current_result"]["status"], failed_booking["current_result"]["http_status"]),
                         ("failed", 503))
        self.assertNotIn("receipt", failed_booking["current_result"])
        self.assert_persisted("booking", "failed")
        self.command("confirm", proposal_id=proposal["id"], nonce=proposal["nonce"])
        self.assertEqual(len(self.session.view()["history"]), 1)
        self.assert_diagnostics_private()

    def test_unsupported_request(self):
        # The supplied ID describes medical advice, not general unsupported intent.
        medical = self.command("medical")
        self.assertEqual((medical["state"], medical["identity_status"]), ("medical", "missing"))
        self.assertIn("cannot give medical advice", medical["message"])
        self.assertIsNone(medical["proposal"])
        queued = self.command("handoff", reason="medical_advice", expect=(QUEUED,))
        self.assert_policy("handoff_ready")
        self.assertEqual(queued["current_result"]["status"], "queued")
        self.assertEqual(self.server.store.handoffs[0]["reason"], "medical_advice")
        self.assertIsNone(self.server.store.handoffs[0]["patientId"])
        self.assert_persisted("handoff", "completed")
        self.assert_persisted("booking", None)
        # The same boundary must interrupt a current booking summary safely.
        proposal = self.ready()
        interrupted = self.command("medical")
        self.assertIsNone(interrupted["proposal"])
        self.assertIn("cannot give medical advice", interrupted["message"])
        self.command("confirm", proposal_id=proposal["id"], nonce=proposal["nonce"])
        self.assert_persisted("booking", None)
        self.assertEqual([r["kind"] for r in self.session.view()["history"]], ["handoff"])
        self.assert_private_absent(self.server.store.handoffs[0]["summary"])
        self.assert_diagnostics_private()


class CleanExportScenarioTests(unittest.TestCase):
    def test_all_eight_real_http_scenarios_run_without_private_source_files(self):
        # Simulate omitted raw intake at the filesystem-read boundary. Never move,
        # rename or delete user originals; every nonprivate read remains real.
        root = Path(__file__).resolve().parents[1]
        private = (root / "docs/product/intake", root / "docs/product/RFP/source")
        original_open = Path.open

        def exported_open(path, *args, **kwargs):
            if any(path.resolve().is_relative_to(directory) for directory in private):
                raise FileNotFoundError("Private source omitted from clean export")
            return original_open(path, *args, **kwargs)

        suite = unittest.defaultTestLoader.loadTestsFromTestCase(SuppliedHttpScenarioTests)
        self.assertEqual(suite.countTestCases(), 8)
        result = unittest.TestResult()
        with patch.object(Path, "open", exported_open):
            suite.run(result)
        self.assertTrue(result.wasSuccessful(), (result.failures, result.errors))
        self.assertEqual(result.testsRun, 8, "all eight actual HTTP journeys must execute, not skip setup")
        self.assertEqual(result.skipped, [])


if __name__ == "__main__":
    unittest.main()
