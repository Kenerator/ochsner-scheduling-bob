"""Same-core simulation contracts; fixtures and temporary files only."""
from pathlib import Path
from copy import deepcopy
from hashlib import sha256
import json
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.session import SchedulingSession
from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.http_mock import ApiError, UnknownOutcome, HttpMockAdapter
from ochsner_bob.replay import Recording, Replay, make_provenance, import_recording
from test_session_contract import FixturePort
from test_interaction_service import CATALOG
from test_interaction_service import CountingLanguage
from http_support import supplied_server


PROVENANCE = make_provenance("a" * 40, dependencies=b"deps", policy=b"policy",
                             prompt=b"prompt", schema=b"schema", fixtures=b"fixtures")


class LiveCoreReplayTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port = FixturePort()
        self.service = InteractionService(lambda: self.port, Path(self.temp.name) / "effects.json",
                                          fixture_catalog=CATALOG, provenance=PROVENANCE)
        self.token = self.service.create()["token"]
        self.service.capture(self.token, True)

    def act(self, action, data=None):
        view = self.service.read(self.token)
        if action == "confirm" and data is None:
            proposal = view["proposal"]
            data = {"proposal_id": proposal["id"], "nonce": proposal["nonce"]}
        return self.service.command(self.token, action, data or {}, view["revision"])

    def prepared(self):
        self.act("identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"})
        self.act("preferences", {"specialty": "primary_care", "location": "downtown"})
        self.act("availability")
        self.act("select", {"index": 1})

    def opened(self):
        report = self.service.capture(self.token, False)
        self.assertEqual(report["recording"], "incomplete_capture", report)
        return self.service.replay(self.token, "open", {"reference": report["reference"]})

    def test_success_uses_actual_core_without_disk_journal_or_live_port(self):
        self.prepared()
        live = self.act("confirm")
        opened = self.opened()
        journal = (Path(self.temp.name) / "effects.json").read_bytes()
        writes = deepcopy(self.port.writes)
        with patch("ochsner_bob.session.EffectJournal", side_effect=AssertionError("disk journal forbidden")), \
             patch("socket.socket", side_effect=AssertionError("network forbidden")):
            replayed = self.service.replay(self.token, "jump", {"index": 4})
            self.assertEqual(replayed["state"].get("core", {}).get("state"), "completed")
            self.assertEqual(replayed["state"]["core"]["revision"], live["revision"])
            self.assertEqual(replayed["state"]["core"]["identity_status"], "verified")
            self.assertEqual(replayed["state"]["core"]["slot_count"], 0)
            self.assertEqual(replayed["state"]["core"]["certainty"], "completed")
            self.assertTrue(replayed["fidelity"]["core_semantic_parity"])
            self.assertFalse(replayed["fidelity"]["core_renderer_parity"])
            self.assertTrue(replayed["missing"])
            self.assertTrue(all("browser acknowledgement" in gap for gap in replayed["missing"]))
            second = self.service.replay(self.token, "open", {"reference": opened["reference"]})
            self.assertNotEqual(second["state"]["namespace"], opened["state"]["namespace"])
        self.assertEqual(self.port.writes, writes)
        self.assertEqual((Path(self.temp.name) / "effects.json").read_bytes(), journal)
        serialized = json.dumps(replayed)
        for private in ("555-0130", "1978-09-22", "70115", "pat_1003", "slot_4001", '"nonce"', '"proposal_id"'):
            self.assertNotIn(private, serialized)

    def test_rejected_failed_unknown_and_reset_reproduce_core_certainty(self):
        self.prepared()
        self.port.outcome = UnknownOutcome("private lost receipt")
        self.act("confirm")
        self.act("reset")
        self.opened()
        state = self.service.replay(self.token, "jump", {"index": 5})["state"]["core"]
        self.assertEqual((state["state"], state["identity_status"], state["certainty"]),
                         ("start", "missing", "unknown"))
        self.assertTrue(state["booking_blocked"])
        self.assertEqual(state["history"], [{"kind": "booking", "status": "unknown"}])

    def test_invalid_date_correction_preserves_preferences_and_invalidates_proposal(self):
        self.prepared()
        live = self.act("preferences", {"start_date": "2026-10-20", "end_date": "2026-10-10"})
        self.assertIsNone(live["proposal"])
        self.opened()
        replayed = self.service.replay(self.token, "jump", {"index": 4})
        self.assertEqual(replayed["state"]["core"]["preferences"],
                         {"specialty": "primary_care", "location": "downtown"})
        self.assertFalse(replayed["state"]["core"]["proposal"])
        self.assertEqual(replayed["state"]["core"]["state"], live["state"])

    def test_variant_recomputes_actual_guards_instead_of_success_observation(self):
        self.prepared()
        self.act("confirm")
        self.opened()
        self.service.replay(self.token, "fork", {"index": 1, "changes": {"preferences": {"specialty": None}}})
        result = self.service.replay(self.token, "jump", {"index": 4})
        self.assertNotEqual(result["state"]["core"]["certainty"], "completed")
        self.assertEqual(result["state"]["core"]["history"], [])
        self.assertEqual(len(self.port.writes), 1)

    def test_legacy_without_core_evidence_is_explicitly_incomplete(self):
        record = Recording(PROVENANCE, synthetic=True)
        record.append({"action": "help", "data": {}})
        record.seal()
        result = self.service.replay(self.token, "import", {"payload": record.export_json(reviewed=True)})
        self.assertEqual(result["recording"], "incomplete_capture")
        self.assertIn("step 1: core evidence", result["missing"])
        self.assertFalse(result["fidelity"]["core_semantic_parity"])

    def exported(self):
        self.opened()
        return json.loads(self.service.replay(self.token, "export", {"reviewed": True})["payload"])

    def import_document(self, document):
        document = deepcopy(document)
        document["digest"] = sha256(json.dumps({k: v for k, v in document.items() if k != "digest"},
            sort_keys=True, separators=(",", ":"), allow_nan=False).encode()).hexdigest()
        return self.service.replay(self.token, "import", {"payload": json.dumps(document)})

    def test_core_protocol_rejects_extra_authority_refs_versions_and_projection_bypass(self):
        self.act("help")
        document = self.exported()
        for index, mutation in enumerate(("authority", "version", "callback", "path", "null", "action", "boolean", "branch"), 1):
            changed = deepcopy(document)
            changed["id"] = f"{index:032x}"
            core = changed["events"][0]["core"]
            if mutation == "authority":
                core["view"]["identity"] = {"patientId": "private-id"}
            elif mutation == "version":
                core["version"] = 2
            elif mutation == "callback":
                core["callback"] = "execute"
            elif mutation == "path":
                core["data"]["path"] = "/tmp/private"
            elif mutation == "null":
                changed["events"][0]["core"] = None
            elif mutation == "action":
                core["action"] = "reset"
            elif mutation == "branch":
                changed["branch"] = "not-a-branch-object"
            else:
                core["view"]["proposal"] = 1
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.import_document(changed)

    def test_original_projection_mismatch_and_unbound_fixture_are_incomplete(self):
        self.act("help")
        document = self.exported()
        document["events"][0]["core"]["view"]["state"] = "completed"
        # New opaque recording ID avoids colliding with the retained original.
        document["id"] = "b" * 32
        result = self.import_document(document)
        self.assertEqual(result["recording"], "incomplete_capture")
        self.assertIn("step 1: semantic core mismatch", result["missing"])
        self.assertFalse(result["fidelity"]["core_semantic_parity"])

    def test_malformed_compound_branch_is_rejected_with_a_categorical_error(self):
        self.act("discover", {"specialty": "primary_care"})
        document = self.exported()
        document["branch"] = "not-a-branch-object"
        with self.assertRaises(ValueError) as caught:
            self.import_document(document)
        self.assertNotIn("not-a-branch-object", str(caught.exception))

    def test_definite_write_failures_preserve_exact_status_semantics(self):
        for status, certainty in ((400, "rejected"), (409, "rejected"), (404, "failed"), (503, "failed")):
            with self.subTest(status=status):
                self.port.outcome = ApiError(status)
                self.prepared()
                actual = self.act("confirm")
                self.opened()
                state = self.service.replay(self.token, "jump", {"index": 4})["state"]["core"]
                self.assertEqual(state["state"], certainty)
                self.assertEqual(state["certainty"], actual["current_result"]["status"])
                self.assertFalse(state["booking_blocked"])
                self.token = self.service.create()["token"]
                self.service.capture(self.token, True)

    def test_expired_proposal_confirmation_never_consumes_recorded_write(self):
        self.prepared()
        old = self.service.read(self.token)["proposal"]
        self.act("help")
        actual = self.act("confirm", {"proposal_id": old["id"], "nonce": old["nonce"]})
        self.assertIsNone(actual["current_result"])
        self.opened()
        result = self.service.replay(self.token, "jump", {"index": 5})
        self.assertEqual(result["state"]["core"]["state"], "help")
        self.assertEqual(result["state"]["core"]["history"], [])
        self.assertFalse(result["state"]["core"]["proposal"])
        self.assertEqual(self.port.writes, [])

    def test_blocked_lookup_and_support_takeover_recompute_policy_without_api(self):
        self.act("appointments")
        support = self.service.join(self.service.pair(self.token))
        revision = self.service.read(self.token)["revision"]
        self.service.ack(self.token, {"revision": revision, "renderer": "bob-v1", "visible": ["message"],
                                     "draft": {}, "focus": None, "scroll": 0, "expanded": []})
        self.service.command(support, "takeover", {}, revision)
        self.act("preferences", {"location": "uptown"})
        self.opened()
        result = self.service.replay(self.token, "jump", {"index": 2})
        self.assertEqual(result["state"]["core"]["preferences"], {})
        self.assertTrue(result["state"]["core"]["takeover"])
        self.assertEqual(result["state"]["core"]["history"], [])
        first = self.service.replay(self.token, "inspect", {"index": 0})["event"]
        self.assertEqual(first["after"]["core"]["policy"]["decision"], "deny")

    def test_typed_api_variant_changes_actual_core_receipt_and_before_after(self):
        self.prepared()
        self.act("confirm")
        self.opened()
        self.service.replay(self.token, "fork", {"index": 4, "changes": {"api_status": "unknown"}})
        result = self.service.replay(self.token, "beforeafter", {"index": 4})["inspection"]
        self.assertTrue(result["before"]["core"]["proposal"])
        self.assertEqual(result["after"]["core"]["certainty"], "unknown")
        self.assertTrue(result["after"]["core"]["booking_blocked"])
        proposal = self.service.replay(self.token, "promote-reviewed", {"reviewed": True})["proposal"]
        self.assertTrue(proposal["simulation_only"])
        self.assertEqual(len(self.port.writes), 1)

    def test_model_category_variant_does_not_apply_old_model_generated_commands(self):
        language = CountingLanguage()
        service = InteractionService(lambda: self.port, Path(self.temp.name) / "model-effects.json",
                                     fixture_catalog=CATALOG, provenance=PROVENANCE, language=language)
        token = service.create()["token"]
        service.capture(token, True)
        actual = service.text(token, "Find primary care providers", 0)
        self.assertEqual(actual["state"], "providers")
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture", report)
        service.replay(token, "open", {"reference": report["reference"]})
        service.replay(token, "fork", {"index": 0, "changes": {"model_category": "invalid"}})
        result = service.replay(token, "jump", {"index": 2})
        self.assertEqual(result["state"]["core"]["preferences"], {})
        self.assertEqual(result["state"]["core"]["provider_count"], 0)
        self.assertEqual(result["state"]["core"]["revision"], 1)
        self.assertEqual(language.calls, 1)

    def test_ambiguous_and_empty_recorded_identity_search_reproduce_actual_core(self):
        catalog = deepcopy(CATALOG)
        catalog["person-b"] = {"kind": "patient", "value": {**catalog["person-a"]["value"],
            "patientId": "pat_1004", "zipCode": "70005"}}
        service = InteractionService(lambda: self.port, Path(self.temp.name) / "ambiguous-effects.json",
                                     fixture_catalog=catalog, provenance=PROVENANCE)
        token = service.create()["token"]
        service.capture(token, True)
        first = service.command(token, "identity", {"phone": "555-0130", "dob": "1978-09-22"}, 0)
        self.assertEqual(first["identity_status"], "ambiguous")
        second = service.command(token, "identity", {"zip": "70115"}, 1)
        self.assertEqual(second["identity_status"], "verified")
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture", report)
        service.replay(token, "open", {"reference": report["reference"]})
        self.assertEqual(service.replay(token, "jump", {"index": 0})["state"]["core"]["state"], "ambiguous")
        self.assertEqual(service.replay(token, "step", {})["state"]["core"]["state"], "ready")

    def test_read_failure_clears_options_and_fails_closed_with_no_write(self):
        self.prepared()
        self.port.availability = lambda *args: (_ for _ in ()).throw(ApiError(503))
        actual = self.act("availability")
        self.assertEqual(actual["slots"], [])
        self.opened()
        result = self.service.replay(self.token, "jump", {"index": 4})
        self.assertEqual(result["state"]["core"]["state"], "outage")
        self.assertEqual(result["state"]["core"]["slot_count"], 0)
        self.assertFalse(result["state"]["core"]["proposal"])
        self.assertEqual(self.port.writes, [])

    def test_supplied_http_capture_replays_after_all_live_boundaries_are_disabled(self):
        with supplied_server() as server:
            service = InteractionService(lambda: HttpMockAdapter(server.base_url),
                                         Path(self.temp.name) / "supplied-effects.json")
            token = service.create()["token"]
            service.capture(token, True)
            revision = 0
            actual = None
            for action, data in (("discover", {"specialty": "primary_care", "location": "downtown"}),
                                 ("identity", {"phone": "555-0101", "dob": "1985-04-12", "zip": "70112"}),
                                 ("availability", {}), ("select", {"index": 1}), ("confirm", {})):
                if action == "confirm":
                    data = {"proposal_id": actual["proposal"]["id"], "nonce": actual["proposal"]["nonce"]}
                actual = service.command(token, action, data, revision)
                revision = actual["revision"]
            self.assertEqual(actual["current_result"]["status"], "completed")
            report = service.capture(token, False)
            self.assertEqual(report["recording"], "incomplete_capture", report)
            audits = server.wait_for_audits(4)
            journal = service.journal_path.read_bytes()
            registry = service.registry.read_bytes()
            with patch("socket.socket", side_effect=AssertionError("replay network forbidden")), \
                 patch("ochsner_bob.session.EffectJournal", side_effect=AssertionError("replay disk claims forbidden")), \
                 patch("ochsner_bob.replay._transition", side_effect=AssertionError("separate interpreter forbidden")):
                opened = service.replay(token, "open", {"reference": report["reference"]})
                result = service.replay(token, "jump", {"index": opened["event_count"] - 1})
                self.assertEqual(result["state"]["core"]["state"], actual["state"])
                self.assertEqual(result["state"]["core"]["revision"], revision)
                self.assertEqual(result["state"]["core"]["slot_count"], 0)
                self.assertTrue(result["fidelity"]["core_semantic_parity"])
            self.assertEqual(server.audits, audits)
            self.assertEqual(service.journal_path.read_bytes(), journal)
            self.assertEqual(service.registry.read_bytes(), registry)


class PresentationReceiptTests(unittest.TestCase):
    def test_optional_can_confirm_is_boolean_observation_only(self):
        with tempfile.TemporaryDirectory() as root:
            session = SchedulingSession(FixturePort(), journal_path=Path(root) / "effects.json")
            receipt = {"revision": 0, "renderer": "bob-v1", "visible": [],
                       "presentation": {"notice": "none", "pending": False, "dirty": False}}
            session.acknowledge(receipt)
            for value in (True, False):
                receipt["presentation"]["can_confirm"] = value
                session.acknowledge(receipt)
                self.assertEqual(session.last_ack, receipt)
                self.assertIsNone(session.proposal)
                self.assertEqual(session.api.writes, [])
            for value in (1, None, "true"):
                receipt["presentation"]["can_confirm"] = value
                with self.assertRaises(ValueError):
                    session.acknowledge(receipt)
