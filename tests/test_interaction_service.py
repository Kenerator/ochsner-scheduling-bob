"""Actual browser orchestration contract, not a test of notebook reactivity."""
import json
import importlib.util
from pathlib import Path
import tempfile
import unittest
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
from unittest.mock import patch
from concurrent.futures import ThreadPoolExecutor, TimeoutError as FutureTimeout
from threading import Event, Lock
from time import perf_counter

from test_session_contract import FixturePort, SLOT
from ochsner_bob.language import LanguageOutcome
from ochsner_bob.language import LanguageAdapter
from ochsner_bob.replay import Limits, Recording, import_recording, make_provenance
from test_language import ENV, response, proposal


PATIENT = {"patientId": "pat_1003", "phone": "555-0130", "dateOfBirth": "1978-09-22", "zipCode": "70115"}
PROVIDER = {"providerId": "prov_2001", "name": "Dr. Elena Brooks", "specialty": "primary_care",
            "locations": ["downtown"], "modalities": ["in_person"]}
CATALOG = {"person-a": {"kind": "patient", "value": PATIENT},
           "option-a": {"kind": "slot", "value": SLOT},
           "provider-a": {"kind": "provider", "value": PROVIDER}}


class CountingLanguage:
    mode = "fixture"

    def __init__(self):
        self.calls = 0

    def interpret(self, text, context):
        self.calls += 1
        return LanguageOutcome("ok", "fixture", "discover", {"specialty": "primary_care"}, "private model prose")


class BlockedLanguageTransport:
    """Real bounded adapter, event-controlled transport; no network or paid calls."""
    def __init__(self):
        self.entered, self.release = Event(), Event()
        self.lock = Lock()
        self.calls = []

    def __call__(self, payload, **kwargs):
        text = json.loads(json.loads(payload)["input"][0]["content"])["text"]
        with self.lock:
            self.calls.append(text)
        if text == "Find primary care providers":
            self.entered.set()
            if not self.release.wait(5):
                raise TimeoutError("synthetic blocked transport safety deadline")
            return response(proposal(specialty="primary_care"))
        return response(proposal(location="uptown" if "uptown" in text else "downtown"))


class InteractionServiceTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.interaction_service"),
                             "shared browser Conversation and capture orchestration missing")
        from ochsner_bob import interaction_service
        self.assertTrue(callable(getattr(interaction_service, "InteractionService", None)),
                        "shared browser Conversation and capture orchestration missing")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port = FixturePort()
        self.module = interaction_service
        self.service = interaction_service.InteractionService(
            lambda:self.port, Path(self.temp.name)/"effects.json")
        self.token = self.service.create()["token"]

    def test_text_routes_shared_offline_discovery_and_stale_has_no_effect(self):
        result = self.service.text(self.token,"providers primary_care downtown",0)
        self.assertEqual(result["state"],"providers")
        self.assertEqual(result["interpretation"]["mode"],"offline")
        stale = self.service.text(self.token,"handoff",0)
        self.assertTrue(stale["stale"])
        self.assertEqual(self.port.writes,[])
        grant=self.service.pair(self.token)
        support=self.service.join(grant)
        with self.assertRaises(PermissionError):
            self.service.text(support,"handoff",result["revision"])

    def test_capture_is_opt_in_reference_inspection_never_executes(self):
        self.assertEqual(self.service.diagnostics(self.token)["recording"],"off")
        with self.assertRaises(PermissionError):
            self.service.capture(self.token,True,synthetic=False)
        self.service.capture(self.token,True,synthetic=True)
        self.service.command(self.token,"help",{},0)
        report=self.service.capture(self.token,False,synthetic=True)
        self.assertEqual(report["recording"],"incomplete_capture")
        reference=report["reference"]
        before=self.service.read(self.token)["revision"]
        inspected=self.service.replay(self.token,"open",{"reference":reference})
        self.assertTrue(inspected["simulation_only"])
        stepped=self.service.replay(self.token,"step",{})
        self.assertEqual(stepped["index"],0)
        self.assertEqual(self.service.read(self.token)["revision"],before)
        self.assertEqual(self.port.writes,[])
        other=self.service.create()["token"]
        with self.assertRaises(PermissionError):
            self.service.replay(other,"open",{"reference":reference})

    def test_private_identity_not_in_diagnostics_or_recording(self):
        self.service.capture(self.token,True,synthetic=True)
        self.service.command(self.token,"identity",{"phone":"555-0101","dob":"1985-04-12"},0)
        report=self.service.capture(self.token,False,synthetic=True)
        inspected=self.service.replay(self.token,"open",{"reference":report["reference"]})
        serialized=json.dumps([self.service.diagnostics(self.token),inspected])
        self.assertNotIn("555-0101",serialized)
        self.assertNotIn("1985-04-12",serialized)
        self.assertNotIn('"nonce"',serialized)
        self.assertNotIn('"patientId"',serialized)

    def configured(self, **kwargs):
        root = Path(self.temp.name) / ("configured-" + str(len(list(Path(self.temp.name).iterdir()))))
        root.mkdir(mode=0o700)
        service = self.module.InteractionService(lambda: self.port, root / "effects.json",
                                                fixture_catalog=CATALOG, **kwargs)
        return service, service.create()["token"]

    @staticmethod
    def receipt(revision):
        return {"revision": revision, "renderer": "bob-v1", "visible": ["message"],
                "draft": {}, "focus": None, "scroll": 0, "expanded": []}

    def test_conversation_notices_survive_polling_and_are_the_acknowledged_screen(self):
        def unavailable(*args, **kwargs):
            raise RuntimeError("private-model-error-sentinel")

        cases = [("", "invalid_input", None),
                 ("phone 555-0130", "private_input", None),
                 ("Find primary care providers", "disabled", LanguageAdapter(environ={})),
                 ("Find primary care providers", "unavailable",
                  LanguageAdapter(transport=unavailable, environ=ENV))]
        for text, status, language in cases:
            with self.subTest(status=status):
                service, token = self.configured(language=language)
                support = service.join(service.pair(token))
                service.capture(token, True)
                response_view = service.text(token, text, 0)
                self.assertEqual(response_view["interpretation"]["status"], status)
                polled = service.read(token)
                self.assertEqual(polled["message"], response_view["message"])
                self.assertEqual(polled["interpretation"], response_view["interpretation"])
                service.ack(token, self.receipt(response_view["revision"]))
                observed = service.read(support)["observed_patient"]
                self.assertEqual(observed, response_view)
                for private in ("555-0130", "private-model-error-sentinel"):
                    self.assertNotIn(private, json.dumps(observed))
                help_view = service.command(token, "help", {}, response_view["revision"])
                mirror = service.read(support)
                self.assertEqual(mirror["observed_patient"], observed)
                self.assertEqual(mirror["patient"]["message"], help_view["message"])
                self.assertNotEqual(help_view["message"], response_view["message"])
                with self.assertRaises(ValueError):
                    service.ack(token, self.receipt(response_view["revision"]))
                self.assertEqual(service.read(support)["observed_patient"], observed)
                self.assertEqual(self.port.writes, [])

    def test_acknowledged_screen_includes_decorated_fields_and_never_a_proposal_nonce(self):
        service, token = self.configured()
        support = service.join(service.pair(token))
        service.capture(token, True)
        self.act(service, token, "identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"})
        self.act(service, token, "preferences", {"specialty": "primary_care", "location": "downtown"})
        self.act(service, token, "availability")
        delivered = self.act(service, token, "select", {"index": 1})
        nonce = delivered["proposal"]["nonce"]
        expected = deepcopy(delivered)
        expected["proposal"].pop("nonce")
        self.assertEqual(delivered["recording"], "capturing")
        service.ack(token, self.receipt(delivered["revision"]))
        mirror = service.read(support)
        self.assertEqual(mirror["observed_patient"], expected)
        self.assertNotIn(nonce, json.dumps(mirror))
        self.assertNotIn("555-0130", json.dumps(mirror))
        mirror["observed_patient"]["interpretation"]["status"] = "forged"
        self.assertEqual(service.read(support)["observed_patient"], expected)
        # A direct core revision never delivered to the patient remains unacknowledgeable.
        session = service.sessions[delivered["session_id"]]
        session.command("help", expected_revision=delivered["revision"])
        service.read(support)
        with self.assertRaises(ValueError):
            service.ack(token, self.receipt(session.revision))
        self.assertEqual(service.read(support)["observed_patient"], expected)
        self.assertEqual(self.port.writes, [])

    def test_stale_text_and_command_acknowledge_the_actual_response_not_an_unseen_view(self):
        service, token = self.configured(language=LanguageAdapter(environ={}))
        support = service.join(service.pair(token))
        notice = service.text(token, "Find primary care providers", 0)
        for stale_call in (lambda: service.text(token, "handoff", 0),
                           lambda: service.command(token, "handoff", {}, 0)):
            with self.subTest(call=stale_call):
                delivered = stale_call()
                self.assertTrue(delivered["stale"])
                self.assertNotEqual(delivered["message"], notice["message"])
                service.ack(token, self.receipt(delivered["revision"]))
                self.assertEqual(service.read(support)["observed_patient"], delivered)
                polled = service.read(token)
                self.assertEqual(polled["message"], notice["message"])
                self.assertEqual(polled["interpretation"], notice["interpretation"])
                self.assertNotIn("stale", polled)
                service.ack(token, self.receipt(polled["revision"]))
                self.assertEqual(service.read(support)["observed_patient"], polled)
        self.assertEqual(self.port.writes, [])

    def act(self, service, token, action, data=None):
        return service.command(token, action, data or {}, service.read(token)["revision"])

    def booking(self, service, token):
        self.act(service, token, "identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"})
        self.act(service, token, "preferences", {"specialty": "primary_care", "location": "downtown"})
        self.act(service, token, "availability")
        proposal = self.act(service, token, "select", {"index": 1})["proposal"]
        return self.act(service, token, "confirm", {"proposal_id": proposal["id"], "nonce": proposal["nonce"]})

    def test_capture_records_actual_shared_core_commands_and_api_fixture_outcomes(self):
        service, token = self.configured()
        service.capture(token, True)
        view = service.text(token, "providers primary_care downtown", 0)
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        opened = service.replay(token, "open", {"reference": report["reference"]})
        self.assertEqual(opened["event_count"], 2)
        preferences = service.replay(token, "inspect", {"index": 0})["event"]
        self.assertEqual(preferences["input"], {"action": "preferences", "data": {"specialty": "primary_care", "location": "downtown"}})
        event = service.replay(token, "inspect", {"index": 1})["event"]
        self.assertEqual(event["input"], {"action": "discover", "data": {}})
        self.assertEqual(event["outcomes"]["api"]["fixture_refs"], ["provider-a"])
        self.assertEqual(event["outcomes"]["api"]["status"], "ok")
        self.assertIsNone(event["view"], "Server projections are not browser observations")
        self.assertEqual(event["core"]["view"]["revision"], view["revision"])
        self.assertEqual(service.replay(token, "jump", {"index": 1})["state"]["providers"], ["provider-a"])

    def test_representative_booking_simulates_actual_certainty_without_reusing_ports_or_journal(self):
        service, token = self.configured()
        service.capture(token, True)
        actual = self.booking(service, token)
        self.assertEqual(actual["current_result"]["status"], "completed")
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        journal = service.journal_path.read_bytes()
        registry = service.registry.read_bytes()
        reads, writes = deepcopy(self.port.reads), deepcopy(self.port.writes)
        opened = service.replay(token, "open", {"reference": report["reference"]})
        result = service.replay(token, "jump", {"index": opened["event_count"] - 1})
        self.assertEqual(result["state"]["outcome"], actual["current_result"]["status"])
        self.assertEqual(result["state"]["history"][0]["kind"], "booking")
        self.assertEqual(result["state"]["preferences"], {"specialty": "primary_care", "location": "downtown"})
        # Real SchedulingSession clears options after booking. The historical
        # typed interpreter retained them; that is not same-core fidelity.
        self.assertEqual(result["state"]["options"], [])
        self.assertEqual(result["state"]["core"]["slot_count"], len(actual["slots"]))
        self.assertTrue(result["fidelity"]["core_semantic_parity"])
        self.assertFalse(result["state"]["executable_authority"])
        self.assertFalse(result["fidelity"]["core_renderer_parity"])
        self.assertEqual(service.journal_path.read_bytes(), journal)
        self.assertEqual(service.registry.read_bytes(), registry)
        self.assertEqual((self.port.reads, self.port.writes), (reads, writes))
        serialized = json.dumps([service.diagnostics(token), result])
        for private in ("555-0130", "1978-09-22", "70115", "pat_1003", "slot_4001", '"nonce"', '"patientId"'):
            self.assertNotIn(private, serialized)
        for path in service.recording_directory.glob("rec-*.json"):
            self.assertNotIn("555-0130", path.read_text())
            self.assertNotIn('"nonce"', path.read_text())

    def test_recorded_unknown_rejected_and_failed_are_not_upgraded_to_success(self):
        from ochsner_bob.http_mock import ApiError, UnknownOutcome
        for error, status in ((UnknownOutcome(), "unknown"), (ApiError(status=409), "rejected"),
                              (ApiError(status=500), "failed")):
            with self.subTest(status=status):
                self.port.outcome = error
                service, token = self.configured()
                service.capture(token, True)
                actual = self.booking(service, token)
                report = service.capture(token, False)
                opened = service.replay(token, "open", {"reference": report["reference"]})
                result = service.replay(token, "jump", {"index": opened["event_count"] - 1})
                self.assertEqual(actual["current_result"]["status"], status)
                self.assertEqual(result["state"]["outcome"], status)

    def test_gap_unbound_fixture_invalid_command_and_late_capture_are_honest(self):
        for scenario in ("fixture", "invalid", "late", "identity"):
            service, token = self.configured()
            if scenario == "late":
                self.act(service, token, "help")
            service.capture(token, True)
            if scenario == "fixture":
                original = self.port.providers
                self.port.providers = lambda *args: [{**PROVIDER, "name": "Unapproved replacement"}]
                try:
                    self.act(service, token, "discover")
                finally:
                    self.port.providers = original
            elif scenario == "invalid":
                self.act(service, token, "not-a-command")
            elif scenario == "identity":
                self.act(service, token, "identity", {"phone": "555-9999", "dob": "1985-04-12"})
            else:
                self.act(service, token, "help")
            report = service.capture(token, False)
            self.assertEqual(report["recording"], "incomplete_capture", scenario)
            self.assertTrue(report["missing"], scenario)
            opened = service.replay(token, "open", {"reference": report["reference"]})
            self.assertEqual(opened["recording"], "incomplete_capture")

    def test_all_replay_controls_are_pure_and_review_is_explicit(self):
        service, token = self.configured()
        service.capture(token, True)
        self.act(service, token, "preferences", {"location": "downtown"})
        self.act(service, token, "help")
        report = service.capture(token, False)
        revision = service.read(token)["revision"]
        service.replay(token, "open", {"reference": report["reference"]})
        service.replay(token, "play", {})
        self.assertEqual(service.replay(token, "tick", {})["index"], 0)
        service.replay(token, "pause", {})
        self.assertEqual(service.replay(token, "tick", {})["index"], 0)
        service.replay(token, "bookmark", {"name": "preference"})
        self.assertEqual(service.replay(token, "step", {})["index"], 1)
        self.assertEqual(service.replay(token, "go_bookmark", {"name": "preference"})["index"], 0)
        self.assertEqual(service.replay(token, "previous", {})["index"], -1)
        delta = service.replay(token, "beforeafter", {"index": 0})
        self.assertEqual(delta["inspection"]["after"]["preferences"], {"location": "downtown"})
        forked = service.replay(token, "fork", {"index": 0, "changes": {"preferences": {"location": "uptown"}}})
        self.assertNotEqual(forked["reference"], report["reference"])
        comparison = service.replay(token, "compare", {"reference": report["reference"]})
        self.assertTrue(comparison["comparison"]["differences"])
        with self.assertRaises(PermissionError):
            service.replay(token, "promote", {"reviewed": False})
        proposal = service.replay(token, "promote", {"reviewed": True})["proposal"]
        self.assertTrue(proposal["fixture"])
        self.assertTrue(proposal["requires_execution_review"])
        self.assertEqual(service.read(token)["revision"], revision)
        self.assertEqual(self.port.writes, [])

    def test_optional_language_observations_are_captured_but_never_called_by_replay(self):
        language = CountingLanguage()
        service, token = self.configured(language=language)
        service.capture(token, True)
        view = service.text(token, "Find primary care providers", 0)
        self.assertEqual(view["state"], "providers")
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        opened = service.replay(token, "open", {"reference": report["reference"]})
        event = service.replay(token, "inspect", {"index": 0})["event"]
        self.assertEqual(event["input"]["action"], "language")
        self.assertEqual(event["outcomes"]["model"]["category"], "accepted")
        self.assertNotIn("private model prose", json.dumps(event))
        service.replay(token, "jump", {"index": opened["event_count"] - 1})
        self.assertEqual(language.calls, 1)
        self.assertNotIn("Find primary care providers", json.dumps(service.diagnostics(token)))

    def test_stale_and_polling_do_not_append_capture_or_call_language(self):
        language = CountingLanguage()
        service, token = self.configured(language=language)
        service.capture(token, True)
        self.act(service, token, "help")
        self.assertTrue(service.text(token, "Find primary care", 0)["stale"])
        for _ in range(4):
            service.read(token)
            service.diagnostics(token)
        report = service.capture(token, False)
        self.assertEqual(service.replay(token, "open", {"reference": report["reference"]})["event_count"], 1)
        self.assertEqual(language.calls, 0)

    def test_support_and_other_sessions_cannot_capture_or_access_foreign_references(self):
        service, token = self.configured()
        support = service.join(service.pair(token))
        for method in (lambda: service.capture(support, True), lambda: service.text(support, "help", 0)):
            with self.assertRaises(PermissionError):
                method()
        service.capture(token, True)
        self.act(service, token, "help")
        report = service.capture(token, False)
        other = service.create()["token"]
        for operation in ("open", "purge", "compare"):
            with self.assertRaises(PermissionError):
                service.replay(other, operation, {"reference": report["reference"]})
        service.replay(support, "open", {"reference": report["reference"]})
        self.assertEqual(service.replay(token, "open", {"reference": report["reference"]})["index"], -1)
        service.replay(support, "step", {})
        self.assertEqual(service.replay(token, "tick", {})["index"], -1)

    def test_expiry_and_purge_disable_open_replays_without_erasing_unknown_protection(self):
        from ochsner_bob.http_mock import UnknownOutcome
        clock = [1_800_000_000.0]
        service, token = self.configured(wall_clock=lambda: clock[0])
        self.port.outcome = UnknownOutcome()
        service.capture(token, True)
        self.booking(service, token)
        report = service.capture(token, False)
        service.replay(token, "open", {"reference": report["reference"]})
        journal = service.journal_path.read_bytes()
        service.replay(token, "purge", {"reference": report["reference"]})
        self.assertEqual(service.replay(token, "open", {"reference": report["reference"]})["recording"], "expired")
        self.assertEqual(service.diagnostics(token)["recording"], "expired")
        self.assertEqual(service.journal_path.read_bytes(), journal)
        self.act(service, token, "reset")
        self.assertTrue(service.read(token)["booking_blocked"])
        service.capture(token, True)
        self.act(service, token, "help")
        second = service.capture(token, False)
        service.replay(token, "open", {"reference": second["reference"]})
        clock[0] += 86400
        self.assertEqual(service.replay(token, "tick", {})["recording"], "expired")
        self.assertEqual(service.journal_path.read_bytes(), journal)

    def test_maintenance_expires_idle_stored_payloads_and_all_retained_replay_copies(self):
        from ochsner_bob.http_mock import UnknownOutcome
        clock = [1_800_000_000.0]
        service, token = self.configured(wall_clock=lambda: clock[0], limits=replace(Limits(), ttl_seconds=5))
        support = service.join(service.pair(token))
        self.port.outcome = UnknownOutcome()
        service.capture(token, True)
        self.booking(service, token)
        report = service.capture(token, False)
        for capability in (token, support):
            service.replay(capability, "open", {"reference": report["reference"]})
            service.replay(capability, "step", {})
            service.replay(capability, "bookmark", {"name": "retained"})
        retained = [value[0] for value in service._replays.values()]
        path = next(service.recording_directory.glob("rec-*.json"))
        self.assertTrue(json.loads(path.read_text())["recording"]["events"])
        journal, capabilities = service.journal_path.read_bytes(), service.registry.read_bytes()
        budget = service.journal_path.parent / "model-budget.json"
        budget.write_bytes(b"independent-budget-state")
        reads, writes = deepcopy(self.port.reads), deepcopy(self.port.writes)
        revision = service.read(token)["revision"]
        self.assertTrue(callable(getattr(service, "maintain_retention", None)), "idle retention hook missing")
        self.assertEqual(service.maintain_retention()["expired_recordings"], 0)
        self.assertTrue(json.loads(path.read_text())["recording"]["events"])
        clock[0] += 6
        # No capture/replay/read/diagnostic operation drives this expiry.
        maintained = service.maintain_retention()
        self.assertEqual(maintained["status"], "ok")
        self.assertEqual(maintained["expired_recordings"], 1)
        self.assertEqual(maintained["expired_replays"], 2)
        self.assertIsNone(json.loads(path.read_text())["recording"])
        self.assertEqual(service._replays, {})
        for replay in retained:
            self.assertEqual(replay.recording.to_dict()["events"], [])
            self.assertEqual(replay.bookmarks, {})
        self.assertEqual(service.maintain_retention()["expired_recordings"], 0)
        self.assertEqual(service.read(token)["revision"], revision)
        self.assertTrue(service.read(token)["booking_blocked"])
        self.assertEqual(service.read(token)["recording"], "expired")
        self.assertEqual(service.diagnostics(token)["recording"], "expired")
        self.assertEqual(service.replay(token, "open", {"reference": report["reference"]})["recording"], "expired")
        self.assertEqual(service._stored_bytes, maintained["stored_bytes"])
        self.assertEqual((service.journal_path.read_bytes(), service.registry.read_bytes()), (journal, capabilities))
        self.assertEqual(budget.read_bytes(), b"independent-budget-state")
        self.assertEqual((self.port.reads, self.port.writes), (reads, writes))

    def test_maintenance_covers_restored_store_and_active_capture_without_creating_unused_store(self):
        self.assertTrue(callable(getattr(self.service, "maintain_retention", None)), "idle retention hook missing")
        self.assertEqual(self.service.maintain_retention()["status"], "ok")
        self.assertFalse(self.service.recording_directory.exists())
        clock = [1_800_000_000.0]
        limits = replace(Limits(), ttl_seconds=5)
        service, token = self.configured(wall_clock=lambda: clock[0], limits=limits)
        service.capture(token, True)
        self.act(service, token, "help")
        stored = service.capture(token, False)
        service.capture(token, True)
        service.text(token, "synthetic request", service.read(token)["revision"])
        active = next(context["active"] for context in service._contexts.values() if context["active"])
        self.assertTrue(active.to_dict()["events"])
        restored = self.module.InteractionService(lambda: self.port, service.journal_path,
            fixture_catalog=CATALOG, limits=limits, wall_clock=lambda: clock[0])
        clock[0] += 6
        self.assertEqual(restored.maintain_retention()["expired_recordings"], 1)
        self.assertEqual(service.maintain_retention()["expired_captures"], 1)
        self.assertEqual(active.to_dict()["events"], [])
        self.assertEqual(service.maintain_retention()["expired_captures"], 0)
        self.assertEqual(service.read(token)["recording"], "expired")
        self.assertEqual(service.replay(token, "open", {"reference": stored["reference"]})["recording"], "expired")

    def test_maintenance_storage_corruption_is_sanitized_but_does_not_retain_expired_memory(self):
        clock = [1_800_000_000.0]
        service, token = self.configured(wall_clock=lambda: clock[0], limits=replace(Limits(), ttl_seconds=5))
        service.capture(token, True)
        self.act(service, token, "help")
        report = service.capture(token, False)
        service.replay(token, "open", {"reference": report["reference"]})
        retained = next(iter(service._replays.values()))[0]
        path = next(service.recording_directory.glob("rec-*.json"))
        path.write_bytes(b"raw-private-corruption-sentinel")
        clock[0] += 6
        self.assertTrue(callable(getattr(service, "maintain_retention", None)), "idle retention hook missing")
        result = service.maintain_retention()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["error"], "recording_retention_unavailable")
        self.assertEqual(service.diagnostics(token)["retention"],
                         {"status": "unavailable", "error": "recording_retention_unavailable"})
        self.assertEqual(result["expired_replays"], 1)
        self.assertIsNone(result["stored_bytes"])
        self.assertNotIn("raw-private", json.dumps(result))
        self.assertEqual(path.read_bytes(), b"raw-private-corruption-sentinel")
        self.assertEqual(retained.recording.to_dict()["events"], [])
        self.assertEqual(service._replays, {})
        with self.assertRaises(self.module.StoreError):
            service.capture(token, True)
        with self.assertRaises(self.module.StoreError):
            service.replay(token, "import", {"payload": self.import_document(service).export_json(reviewed=True)})
        self.assertEqual(path.read_bytes(), b"raw-private-corruption-sentinel")

    def test_maintenance_callback_contains_unexpected_failures_and_reports_recovery(self):
        service, token = self.configured()
        self.assertFalse(service.journal_path.exists())
        capabilities = service.registry.read_bytes()
        wall_clock = service.wall_clock

        def broken_clock():
            raise RuntimeError("raw-private-clock-error")

        service.wall_clock = broken_clock
        result = service.maintain_retention()
        self.assertEqual(result["status"], "unavailable")
        self.assertEqual(result["error"], "recording_retention_unavailable")
        self.assertNotIn("raw-private", json.dumps(result))
        self.assertEqual(service.diagnostics(token)["retention"],
                         {"status": "unavailable", "error": "recording_retention_unavailable"})
        service.wall_clock = wall_clock
        self.assertEqual(service.maintain_retention()["status"], "ok")
        self.assertEqual(service.diagnostics(token)["retention"], {"status": "ok", "error": None})
        service.capture(token, True)
        service.capture(token, False)
        with patch("ochsner_bob.recording_store.RecordingStore.expire", side_effect=RuntimeError("raw-private-store-error")):
            result = service.maintain_retention()
        self.assertEqual(result["error"], "recording_retention_unavailable")
        self.assertNotIn("raw-private", json.dumps(result))
        self.assertFalse(service.journal_path.exists())
        self.assertEqual(service.registry.read_bytes(), capabilities)
        self.assertEqual(self.port.writes, [])

    def test_overflow_and_storage_failure_are_visible_without_changing_live_result(self):
        service, token = self.configured(limits=replace(Limits(), max_events=1))
        service.capture(token, True)
        self.act(service, token, "help")
        self.assertEqual(self.act(service, token, "medical")["state"], "medical")
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        self.assertGreater(report["dropped"], 0)
        self.assertTrue(report["missing"])
        service, token = self.configured()
        service.capture(token, True)
        with patch("ochsner_bob.recording_store.RecordingStore.save", side_effect=RuntimeError("raw private disk failure")):
            self.assertEqual(self.act(service, token, "help")["state"], "help")
            report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        self.assertFalse(report["stored"])
        self.assertNotIn("raw private disk failure", json.dumps(report))

    def test_recording_toggle_is_strict_and_does_not_reset_the_active_capture(self):
        for bad in (1, "yes", None):
            with self.assertRaises(ValueError):
                self.service.capture(self.token, bad)
        first = self.service.capture(self.token, True)
        second = self.service.capture(self.token, True)
        self.assertEqual(first["reference"], second["reference"])
        self.assertEqual(self.service.read(self.token)["recording"], "capturing")
        self.act(self.service, self.token, "help")
        report = self.service.capture(self.token, False)
        self.assertEqual(self.service.capture(self.token, False)["reference"], report["reference"])

    def test_failed_capture_observers_cannot_change_api_or_language_results(self):
        for observer in ("_api_observation", "_language_observation"):
            with self.subTest(observer=observer):
                language = CountingLanguage()
                service, token = self.configured(language=language)
                service.capture(token, True)
                with patch.object(service, observer, side_effect=RuntimeError("raw private observer error")):
                    result = service.text(token, "Find primary care providers", 0)
                self.assertEqual(result["state"], "providers")
                report = service.capture(token, False)
                self.assertEqual(report["recording"], "incomplete_capture")
                self.assertNotIn("raw private observer error", json.dumps(report))

    def test_provenance_uses_actual_artifacts_and_explicit_override_is_disclosed(self):
        from ochsner_bob.language import _INSTRUCTIONS
        root = Path(__file__).resolve().parents[1]
        report = self.service.diagnostics(self.token)
        self.assertEqual(report["provenance"]["policy"], sha256((root / "policies/bob.json").read_bytes()).hexdigest())
        self.assertEqual(report["provenance"]["prompt"], sha256(_INSTRUCTIONS.encode()).hexdigest())
        self.assertEqual(report["provenance"]["dependencies"], sha256((root / "pyproject.toml").read_bytes()).hexdigest())
        self.assertRegex(report["provenance"]["source_revision"], r"^[0-9a-f]{40}$")
        self.assertIs(type(report["source"]["working_tree_dirty"]), bool)
        self.assertRegex(report["source"]["code_digest"], r"^[0-9a-f]{64}$")
        override = make_provenance("a" * 40, dependencies=b"unit", policy=b"unit", prompt=b"unit", schema=b"unit", fixtures=b"unit")
        service, token = self.configured(provenance=override)
        self.assertEqual(service.diagnostics(token)["provenance"], override)
        self.assertTrue(service.diagnostics(token)["source"]["override"])

    def test_replay_rejects_extra_authority_fields_paths_and_unknown_operations(self):
        self.service.capture(self.token, True)
        self.act(self.service, self.token, "help")
        report = self.service.capture(self.token, False)
        self.service.replay(self.token, "open", {"reference": report["reference"]})
        for operation, data in (("step", {"confirm": True}), ("jump", {"index": True}),
                                ("fork", {"index": 0, "changes": {"verified": True}}),
                                ("open", {"reference": "file:///private/effects.json"}),
                                ("execute", {}), ("step", [])):
            with self.subTest(operation=operation), self.assertRaises((ValueError, PermissionError)):
                self.service.replay(self.token, operation, data)
        self.assertEqual(self.port.writes, [])

    def test_blocked_model_does_not_block_help_other_patient_or_paired_polling(self):
        transport = BlockedLanguageTransport()
        service, token = self.configured(language=LanguageAdapter(transport=transport, environ=ENV))
        other = service.create()["token"]
        support = service.join(service.pair(token))
        service.capture(token, True)

        def timed(call):
            started = perf_counter()
            result = call()
            return result, perf_counter() - started

        with ThreadPoolExecutor(max_workers=5) as pool:
            waiting = pool.submit(service.text, token, "Find primary care providers", 0)
            try:
                self.assertTrue(transport.entered.wait(1), "test never reached the language transport")
                self.assertFalse(waiting.done())
                probes = {
                    "help": pool.submit(timed, lambda: service.command(token, "help", {}, 1)),
                    "other patient": pool.submit(timed, lambda: service.read(other)),
                    "paired poll": pool.submit(timed, lambda: service.read(support)),
                    "diagnostics": pool.submit(timed, lambda: service.diagnostics(token)),
                }
                for name, future in probes.items():
                    with self.subTest(probe=name):
                        try:
                            result, elapsed = future.result(timeout=0.4)
                        except FutureTimeout:
                            self.fail(f"{name} blocked behind a model wait for >=400ms")
                        self.assertLess(elapsed, 0.4)
                        if name == "help":
                            self.assertEqual(result["state"], "help")
                        if name == "other patient":
                            self.assertEqual(result["revision"], 0)
                            self.assertEqual(result["browser_mode"], "live")
                            self.assertFalse(result["submission_pending"])
                        if name == "paired poll":
                            self.assertTrue(result["patient"]["submission_pending"])
                        if name == "diagnostics":
                            self.assertTrue(result["submission_pending"])
                self.assertFalse(waiting.done(), "model transport was released before responsiveness checks")
            finally:
                transport.release.set()
            result = waiting.result(timeout=1)
        self.assertTrue(result.get("stale"))
        self.assertEqual(service.read(token)["state"], "help")
        self.assertFalse(service.read(token)["submission_pending"])
        self.assertEqual(service.read(token)["preferences"], {})
        self.assertEqual((self.port.reads, self.port.writes), ([], []))
        report = service.capture(token, False)
        self.assertEqual(report["recording"], "incomplete_capture")
        self.assertIn("stale_language_result", report["missing"])
        self.assertNotIn("Find primary care providers", json.dumps(service.diagnostics(token)))
        opened = service.replay(token, "open", {"reference": report["reference"]})
        self.assertEqual(opened["browser_mode"], "replay")
        self.assertFalse(opened["submission_pending"])
        for path in service.recording_directory.glob("rec-*.json"):
            self.assertNotIn("submission_pending", path.read_text())
            self.assertNotIn("browser_mode", path.read_text())

    def test_one_model_wait_per_session_preserves_local_text_and_other_session_capture(self):
        transport = BlockedLanguageTransport()
        service, token = self.configured(language=LanguageAdapter(transport=transport, environ=ENV))
        other = service.create()["token"]
        service.capture(token, True)
        service.capture(other, True)
        with ThreadPoolExecutor(max_workers=3) as pool:
            waiting = pool.submit(service.text, token, "Find primary care providers", 0)
            try:
                self.assertTrue(transport.entered.wait(1))
                busy = pool.submit(service.text, token, "Show providers downtown", 1).result(timeout=0.4)
                self.assertEqual(busy["interpretation"]["status"], "unavailable")
                self.assertEqual(len(transport.calls), 1, "overlapping model calls in one session")
                local = pool.submit(service.text, token, "medical", busy["revision"]).result(timeout=0.4)
                self.assertEqual(local["state"], "medical")
                independent = pool.submit(service.text, other, "Show providers uptown", 0).result(timeout=0.4)
                self.assertEqual(independent["state"], "providers")
                self.assertEqual(len(transport.calls), 2)
                self.assertFalse(waiting.done())
            finally:
                transport.release.set()
            self.assertTrue(waiting.result(timeout=1)["stale"])
        first, second = service.capture(token, False), service.capture(other, False)
        self.assertEqual(first["recording"], "incomplete_capture")
        self.assertEqual(second["recording"], "incomplete_capture")
        service.replay(other, "open", {"reference": second["reference"]})
        event = service.replay(other, "inspect", {"index": 0})["event"]
        self.assertEqual(event["input"]["data"]["text"], "Show providers uptown")
        self.assertNotIn("Find primary care providers", json.dumps(event))
        with self.assertRaises(PermissionError):
            service.replay(other, "open", {"reference": first["reference"]})
        self.assertEqual(self.port.writes, [])

    def test_pending_turn_cannot_write_old_text_or_outcome_into_restarted_capture(self):
        transport = BlockedLanguageTransport()
        service, token = self.configured(language=LanguageAdapter(transport=transport, environ=ENV))
        first = service.capture(token, True)
        with ThreadPoolExecutor(max_workers=2) as pool:
            waiting = pool.submit(service.text, token, "Find primary care providers", 0)
            try:
                self.assertTrue(transport.entered.wait(1))
                sealed = pool.submit(service.capture, token, False).result(timeout=0.4)
                self.assertEqual(sealed["recording"], "incomplete_capture")
                self.assertIn("language_pending_at_capture_stop", sealed["missing"])
                restarted = pool.submit(service.capture, token, True).result(timeout=0.4)
                self.assertNotEqual(restarted["reference"], first["reference"])
                help_view = pool.submit(service.text, token, "help", 1).result(timeout=0.4)
                self.assertEqual(help_view["state"], "help")
            finally:
                transport.release.set()
            self.assertTrue(waiting.result(timeout=1)["stale"])
        final = service.capture(token, False)
        opened = service.replay(token, "open", {"reference": final["reference"]})
        self.assertEqual(opened["event_count"], 1)
        self.assertEqual(service.replay(token, "inspect", {"index": 0})["event"]["input"]["action"], "help")
        for path in service.recording_directory.glob("rec-*.json"):
            self.assertNotIn("Find primary care providers", path.read_text())
            self.assertNotIn('"nonce"', path.read_text())
        self.assertEqual(service.diagnostics(token)["model"]["application"], "stale")

    def import_document(self, service, *, now=None):
        recording = Recording(service.provenance, fixture_refs=CATALOG, synthetic=True,
                              now=service.wall_clock() if now is None else now, limits=service.limits)
        recording.append({"action": "preferences", "data": {"location": "downtown"}})
        recording.append({"action": "help", "data": {}})
        recording.seal()
        return recording

    @staticmethod
    def import_wire(document):
        document = deepcopy(document)
        document.pop("digest", None)
        encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
        document["digest"] = sha256(encoded.encode()).hexdigest()
        return json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)

    def test_import_grants_only_the_callers_session_without_any_live_calls_or_revision(self):
        language = CountingLanguage()
        service, token = self.configured(language=language)
        other = service.create()["token"]
        recording = self.import_document(service)
        registry = service.registry.read_bytes()
        imported = service.replay(token, "import", {"payload": recording.export_json(reviewed=True)})
        self.assertTrue(imported["imported"])
        self.assertTrue(imported["simulation_only"])
        self.assertEqual(imported["index"], -1)
        self.assertEqual(imported["event_count"], 2)
        self.assertEqual(service.replay(token, "step", {})["state"]["preferences"], {"location": "downtown"})
        self.assertEqual(service.read(token)["revision"], 0)
        self.assertEqual(service.read(token)["recording"], "off")
        self.assertEqual(service.registry.read_bytes(), registry)
        self.assertEqual((language.calls, self.port.reads, self.port.writes), (0, [], []))
        for operation in ("open", "purge", "compare"):
            with self.assertRaises(PermissionError):
                service.replay(other, operation, {"reference": imported["reference"]})
        exported = service.replay(token, "export", {"reviewed": True})
        self.assertEqual(json.loads(exported["payload"]), recording.to_dict())
        self.assertEqual(exported["export_bytes"], len(exported["payload"].encode()))
        self.assertEqual(exported["import_limit_bytes"], 1024 * 1024)
        self.assertTrue(exported["reimportable"])

    def test_export_requires_literal_review_and_current_authorized_valid_storage(self):
        service, token = self.configured()
        service.capture(token, True)
        self.booking(service, token)
        report = service.capture(token, False)
        service.replay(token, "open", {"reference": report["reference"]})
        for reviewed in (False, 1, "true", None):
            with self.subTest(reviewed=reviewed), self.assertRaises(PermissionError):
                service.replay(token, "export", {"reviewed": reviewed})
        for data in ({}, {"reviewed": True, "reference": report["reference"]}, {"reviewed": True, "path": "private.json"}):
            with self.assertRaises(ValueError):
                service.replay(token, "export", data)
        journal = service.journal_path.read_bytes()
        payload = service.replay(token, "export", {"reviewed": True})["payload"]
        imported = import_recording(payload, fixture_refs=CATALOG, expected_provenance=service.provenance)
        self.assertEqual(imported.availability(), "incomplete_capture")
        for private in ("555-0130", "1978-09-22", "pat_1003", "slot_4001", '"nonce"', '"patientId"'):
            self.assertNotIn(private, payload)
        self.assertEqual(service.journal_path.read_bytes(), journal)
        other = service.create()["token"]
        with self.assertRaises(ValueError):
            service.replay(other, "export", {"reviewed": True})
        with self.assertRaises(PermissionError):
            service.replay(other, "import", {"payload": payload})
        self.assertEqual(service.replay(token, "export", {"reviewed": True})["payload"], payload)
        path = next(service.recording_directory.glob("rec-*.json"))
        path.write_bytes(b"raw-private-corruption")
        unavailable = service.replay(token, "export", {"reviewed": True})
        self.assertEqual(unavailable["recording"], "unavailable")
        self.assertNotIn("payload", unavailable)
        self.assertNotIn("raw-private-corruption", json.dumps(unavailable))
        self.assertEqual(path.read_bytes(), b"raw-private-corruption")

    def test_import_rejects_bad_json_types_authority_fixture_refs_and_limits_without_grants(self):
        service, token = self.configured()
        doc = self.import_document(service).to_dict()
        valid = self.import_wire(doc)
        payloads = [valid.replace('"version":1', '"version":1,"version":1'), '{"version":NaN}',
                    valid.encode(), doc, "{" + "[" * 20, "\ud800"]
        for key, value in (("version", 2), ("endpoint", "https://example.org"), ("consent", True),
                           ("fixture_refs", ["unapproved-person"])):
            changed = deepcopy(doc)
            changed[key] = value
            payloads.append(self.import_wire(changed))
        changed = deepcopy(doc)
        changed["events"][0]["input"] = {"action": "language", "data": {"text": "phone 555-0101"}}
        payloads.append(self.import_wire(changed))
        changed = deepcopy(doc)
        changed["events"][0]["input"] = {"action": "language", "data": {"text": "../private"}}
        payloads.append(self.import_wire(changed))
        for payload in payloads:
            with self.subTest(kind=type(payload).__name__), self.assertRaises(ValueError) as error:
                service.replay(token, "import", {"payload": payload})
            self.assertNotIn("555-0101", str(error.exception))
        for payload in (" " * (1024 * 1024 + 1), "é" * (1024 * 1024 // 2 + 1)):
            with self.assertRaisesRegex(ValueError, "size limit"):
                service.replay(token, "import", {"payload": payload})
        for data in ({"payload": valid, "synthetic": True}, {"payload": valid, "path": "private.json"}, {}):
            with self.assertRaises(ValueError):
                service.replay(token, "import", data)
        with self.assertRaises(PermissionError):
            service.replay(token, "open", {"reference": self.import_document(service).reference(0)})
        self.assertFalse(service.recording_directory.exists())
        self.assertEqual((self.port.reads, self.port.writes), ([], []))

    def test_failed_import_does_not_publish_a_reference_grant_or_replace_current_replay(self):
        from ochsner_bob.recording_store import StoreFull
        service, token = self.configured()
        first = self.import_document(service)
        current = service.replay(token, "import", {"payload": first.export_json(reviewed=True)})
        rejected = self.import_document(service)
        with patch("ochsner_bob.recording_store.RecordingStore.save", side_effect=StoreFull("aggregate")):
            with self.assertRaises(StoreFull):
                service.replay(token, "import", {"payload": rejected.export_json(reviewed=True)})
        with self.assertRaises(PermissionError):
            service.replay(token, "open", {"reference": rejected.reference(0)})
        self.assertEqual(service.replay(token, "tick", {})["reference"], current["reference"])
        self.assertEqual(self.port.writes, [])

    def test_expired_and_incomplete_imports_never_become_full_replay_or_exportable_expired_data(self):
        clock = [1_800_000_000.0]
        service, token = self.configured(wall_clock=lambda: clock[0])
        recording = self.import_document(service, now=clock[0] - 86400)
        expired = service.replay(token, "import", {"payload": recording.export_json(reviewed=True)})
        self.assertEqual(expired["recording"], "expired")
        self.assertNotIn("payload", expired)
        self.assertEqual(service.replay(token, "open", {"reference": expired["reference"]})["recording"], "expired")
        incomplete = Recording(service.provenance, fixture_refs=CATALOG, synthetic=True, now=clock[0])
        incomplete.append({"action": "availability", "data": {}})
        incomplete.seal()
        result = service.replay(token, "import", {"payload": incomplete.export_json(reviewed=True)})
        self.assertEqual(result["recording"], "incomplete_capture")
        self.assertIn("step 1: api", result["missing"])
        clock[0] += 86400
        exported = service.replay(token, "export", {"reviewed": True})
        self.assertEqual(exported["recording"], "expired")
        self.assertNotIn("payload", exported)

    def test_native_export_above_import_limit_is_visible_and_not_truncated(self):
        service, token = self.configured()
        doc = self.import_document(service).to_dict()
        doc["events"] = [doc["events"][0]]
        template = {"seq": 2, "input": {"action": "language", "data": {"text": ""}},
                    "outcomes": {"model": {"category": "clarify", "preferences": {}}},
                    "view": None, "clock": doc["created_at"]}
        while len(self.import_wire(doc).encode()) < 1024 * 1024 - 4200:
            event = deepcopy(template)
            event["seq"] = len(doc["events"]) + 1
            event["input"]["data"]["text"] = ("synthetic " * 410)[:4096]
            doc["events"].append(event)
        tail = deepcopy(template)
        tail["seq"] = len(doc["events"]) + 1
        doc["events"].append(tail)
        padding = 1024 * 1024 - 64 - len(self.import_wire(doc).encode())
        self.assertLessEqual(padding, 4096)
        self.assertGreater(padding, 0)
        tail["input"]["data"]["text"] = ("synthetic " * 410)[:padding]
        payload = self.import_wire(doc)
        self.assertEqual(len(payload.encode()), 1024 * 1024 - 64)
        service.replay(token, "import", {"payload": payload})
        service.replay(token, "fork", {"index": 0, "changes": {"preferences": {"location": "uptown"}}})
        exported = service.replay(token, "export", {"reviewed": True})
        self.assertGreater(exported["export_bytes"], 1024 * 1024)
        self.assertFalse(exported["reimportable"])
        self.assertEqual(len(json.loads(exported["payload"])["events"]), len(doc["events"]))
        with self.assertRaisesRegex(ValueError, "size limit"):
            service.replay(token, "import", {"payload": exported["payload"]})
