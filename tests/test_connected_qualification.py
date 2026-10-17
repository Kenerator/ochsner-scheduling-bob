"""Development-only connected journeys; never dispatch real HTTPS."""

import copy
import importlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.language import LanguageAdapter, LanguageOutcome
from ochsner_bob.http_mock import HttpMockAdapter


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/connected_qualification_development.json"
IDENTITY = {"phone": "555-0101", "dob": "1985-04-12", "zip": "70112"}


def command(action, data=None, expect=None):
    return {"kind": "command", "action": action, "data": data or {}, "expect": expect or {}}


def case(steps, expected=None, scenario="happy_path_booking"):
    return {"id": "development-test", "scenario": scenario, "steps": steps,
            "expected": expected or {"post_attempts": 0, "booking_completed": 0, "handoff_queued": 0}}


def ready():
    return [command("preferences", {"specialty": "primary_care", "location": "downtown"}),
            {"kind": "identity", "data": IDENTITY, "expect": {"identity_status": "verified"}},
            command("availability", expect={"states": ["options"]}),
            command("select", {"index": 1}, {"proposal": True})]


class ConnectedQualificationTests(unittest.TestCase):
    def setUp(self):
        # Install the denial before loading the harness or constructing adapters.
        self.enterContext(patch("http.client.HTTPSConnection", side_effect=AssertionError("real HTTPS forbidden")))
        self.assertIsNotNone(importlib.util.find_spec("scripts.connected_qualification"),
                             "Offline connected qualification harness is missing")
        self.harness = importlib.import_module("scripts.connected_qualification")
        # Clean committed exports have no untracked repo tmp directory.
        self.temp = self.enterContext(tempfile.TemporaryDirectory(prefix="connected-test-"))
        self.effects = Path(self.temp).resolve()

    def language(self, action="preferences", preferences=None, *, raw=None, failure=None):
        # A bounded synthetic model transport exercises the actual LanguageAdapter.
        def transport(payload, *, api_key, timeout, max_body_bytes):
            self.assertLessEqual(len(payload), 16384)
            self.assertEqual(json.loads(payload)["tools"], [])
            self.assertGreater(timeout, 0)
            self.assertEqual(max_body_bytes, 65536)
            if failure:
                raise failure("PRIVATE exception must not escape")
            if raw is not None:
                return raw
            output = {"action": action, "preferences": preferences or {}}
            return json.dumps({"status": "completed", "error": None,
                "model": "development-model", "service_tier": "default",
                "usage": {"input_tokens": 10, "output_tokens": 5, "total_tokens": 15,
                    "input_tokens_details": {"cached_tokens": 0},
                    "output_tokens_details": {"reasoning_tokens": 0}},
                "output": [{"type": "message", "role": "assistant", "status": "completed",
                            "content": [{"type": "output_text", "text": json.dumps(output)}]}]}).encode()
        return LanguageAdapter(transport=transport, environ={"BOB_ENABLE_OPENAI": "1",
            "BOB_OPENAI_MODEL": "development-model", "OPENAI_API_KEY": "synthetic-fixture-only"})

    def run_case(self, value, language=None):
        return self.harness.run_journey(value, language, self.effects)

    def test_real_booking_has_one_post_and_read_back_receipt(self):
        value = case(ready() + [{"kind": "confirm", "expect": {"result_status": "completed",
                                  "history_statuses": ["completed"]}}],
                     {"post_attempts": 1, "booking_completed": 1, "handoff_queued": 0,
                      "booking_verified": 1, "api_calls": 4})
        report = self.run_case(value)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["http"][-1]["route"], "/patients/{patientId}/appointments")
        self.assertEqual(report["effects"]["booking_verified"], 1)
        self.assertEqual(list(self.effects.iterdir()), [])

    def test_text_revokes_proposal_and_never_supplies_consent(self):
        value = case(ready() + [{"kind": "text", "text": "yes", "dispatch": True,
                                "expect": {"proposal": False, "interpretation_status": "clarification"}},
                               {"kind": "confirm", "expect": {}}])
        report = self.run_case(value, self.language("clarify"))
        self.assertFalse(report["passed"])
        self.assertEqual(report["failure"], "missing_proposal")
        self.assertEqual(report["effects"]["post_attempts"], 0)
        self.assertEqual(report["steps"][4]["language"]["usage"]["input_tokens"], 10)
        self.assertEqual(report["mode"], "fixture")
        self.assertFalse(report["genuine_qualification"])

    def test_supplied_conflict_requires_new_selection_and_confirmation(self):
        steps = ready()
        steps[-1] = command("select", {"index": 3}, {"proposal": True})
        steps += [{"kind": "confirm", "expect": {"result_status": "rejected"}},
                  command("availability"), command("select", {"index": 1}),
                  {"kind": "confirm", "expect": {"history_statuses": ["rejected", "completed"]}}]
        report = self.run_case(case(steps, {"post_attempts": 2, "booking_completed": 1,
            "handoff_queued": 0, "booking_verified": 1}, "slot_conflict"))
        self.assertTrue(report["passed"], report)
        self.assertEqual([x["status"] for x in report["http"] if x["method"] == "POST"], [409, 201])

    def test_supplied_outage_and_predeclared_recovery_keep_failed_history(self):
        steps = [command("discover", expect={"states": ["outage"]}),
                 command("handoff", {"reason": "api_failure"}, {"result_status": "failed"}),
                 {"kind": "scenario", "scenario": "happy_path_booking", "expect": {}},
                 command("help", expect={"states": ["help"]}),
                 command("handoff", {"reason": "user_requested"},
                         {"result_status": "queued", "history_statuses": ["failed", "queued"]})]
        report = self.run_case(case(steps, {"post_attempts": 2, "booking_completed": 0,
            "handoff_queued": 1}, "api_failure"))
        self.assertTrue(report["passed"], report)
        self.assertEqual([x["status"] for x in report["http"]], [503, 503, 201])

    def test_help_medical_and_private_text_never_dispatch(self):
        steps = [{"kind": "text", "text": text, "dispatch": False, "expect": expected}
                 for text, expected in [("I need help", {"states": ["help"]}),
                    ("I have chest pain", {"states": ["medical"]}),
                    ("phone=555-0101", {"interpretation_status": "private_input"})]]
        report = self.run_case(case(steps), self.language())
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["language_calls"], 0)
        self.assertEqual(report["http"], [])

    def test_dispatch_false_blocks_unexpected_language_before_transport(self):
        report = self.run_case(case([{"kind": "text", "text": "Find a family doctor",
                    "dispatch": False, "expect": {}}, command("help")]), self.language())
        self.assertEqual(report["failure"], "dispatch_mismatch")
        self.assertEqual(report["language_calls"], 0)
        self.assertEqual(report["unrun_steps"], [1])

    def test_prerequisite_mismatch_retains_failed_step_and_stops(self):
        report = self.run_case(case([command("help", expect={"states": ["completed"]}),
                                    command("handoff")]))
        self.assertEqual(report["failure"], "expectation_mismatch")
        self.assertEqual(report["unrun_steps"], [1])
        self.assertFalse(report["steps"][0]["passed"])
        self.assertEqual(report["effects"]["post_attempts"], 0)

    def test_malformed_timeout_and_unavailable_language_stop_without_retry(self):
        steps = [{"kind": "text", "text": "Find a family doctor", "dispatch": True, "expect": {}},
                 command("handoff")]
        for adapter, failure in [(self.language(raw=b"{}"), "language_invalid_output"),
                (self.language(failure=TimeoutError), "language_timeout"),
                (self.language(failure=OSError), "language_unavailable")]:
            with self.subTest(failure=failure):
                report = self.run_case(case(steps), adapter)
                self.assertEqual(report["failure"], failure)
                self.assertTrue(report["halt_dispatch"])
                self.assertEqual(report["unrun_steps"], [1])
                self.assertEqual(report["language_calls"], 1)

    def test_unknown_accounting_and_malformed_observation_stop(self):
        steps = [{"kind": "text", "text": "Find a family doctor", "dispatch": True, "expect": {}},
                 command("help")]
        for outcome, failure in [(LanguageOutcome("ok", "fixture", "discover", {},
                                 accounting_status="unknown"), "accounting_unknown"),
                                 ({"raw": "PRIVATE"}, "observation_invalid"),
                                 (LanguageOutcome("ok", "fixture", "discover", {}, usage={"raw": "PRIVATE"}),
                                  "observation_invalid")]:
            with patch.object(adapter := self.language(), "interpret", return_value=outcome):
                report = self.run_case(case(steps), adapter)
            self.assertEqual(report["failure"], failure)
            self.assertTrue(report["halt_dispatch"])
            self.assertEqual(report["unrun_steps"], [1])
            self.assertNotIn("PRIVATE", json.dumps(report))

    def test_reports_never_emit_identity_text_keys_ids_bodies_or_exceptions(self):
        report = self.run_case(case(ready() + [{"kind": "confirm", "expect": {}}],
            {"post_attempts": 1, "booking_completed": 1, "handoff_queued": 0}))
        serialized = json.dumps(report)
        for forbidden in [*IDENTITY.values(), "pat_1001", "slot_4001", "appt_", "nonce",
                          "synthetic-fixture-only", "session_id", "receipt\"", "message\""]:
            self.assertNotIn(forbidden, serialized)
        self.assertEqual(list(self.effects.iterdir()), [])

    def test_strict_invalid_manifests_have_no_effects(self):
        valid = {"schema_version": 1, "synthetic_only": True, "set": "development", "repetitions": 1,
                 "cases": [case([command("help")])]}
        invalid = []
        for key, value in [("schema_version", True), ("synthetic_only", False), ("set", "legacy"),
                           ("repetitions", True), ("repetitions", 3), ("cases", []), ("endpoint", "https://example.org")]:
            item = copy.deepcopy(valid)
            item[key] = value
            invalid.append(json.dumps(item))
        invalid += [json.dumps(valid).replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'),
                    '{"x": NaN}', "[" * 100 + "]" * 100, " " * 65537]
        for bad_step in [{"kind": "command", "action": "confirm", "data": {}, "expect": {}},
                         {"kind": "confirm", "nonce": "caller", "expect": {}},
                         {"kind": "identity", "data": {"phone": "real-person"}, "expect": {}},
                         command("select", {"index": True}),
                         command("help", {"unexpected": "secret"})]:
            item = copy.deepcopy(valid)
            item["cases"][0]["steps"] = [bad_step]
            invalid.append(json.dumps(item))
        path = self.effects / "manifest.json"
        with patch.object(self.harness, "OwnedMock", side_effect=AssertionError("validation started effects")):
            for raw in invalid:
                path.write_text(raw)
                with self.assertRaisesRegex(ValueError, "invalid_manifest"):
                    self.harness.load_manifest(path)
            with self.assertRaisesRegex(ValueError, "invalid_manifest"):
                self.run_case({**valid["cases"][0], "steps": [command("takeover")]})

    def test_development_fixture_loads_and_runs_without_genuine_claim(self):
        manifest = self.harness.load_manifest(FIXTURE)
        self.assertEqual(manifest["set"], "development")
        self.assertEqual(manifest["repetitions"], 1)
        for value in manifest["cases"]:
            report = self.run_case(value, self.language("preferences", {"specialty": "primary_care", "location": "downtown"}))
            self.assertTrue(report["passed"], report)
            self.assertFalse(report["genuine_qualification"])

    def test_owned_child_and_journal_cleanup_on_failure(self):
        original = self.harness.OwnedMock
        owned = []
        def track(*args, **kwargs):
            child = original(*args, **kwargs)
            owned.append(child)
            return child
        with patch.object(self.harness, "OwnedMock", side_effect=track):
            report = self.run_case(case([command("help", expect={"proposal": True})]))
        self.assertFalse(report["passed"])
        self.assertIsNotNone(owned[0].process.poll())
        self.assertEqual(list(self.effects.iterdir()), [])

    def test_prior_receipt_is_not_counted_or_read_back_again(self):
        steps = ready() + [{"kind": "confirm", "expect": {"result_status": "completed"}},
                           command("help"), command("reset"),
                           {"kind": "confirm", "expect": {"history_statuses": ["completed"]}}]
        report = self.run_case(case(steps, {"post_attempts": 1, "booking_completed": 1,
            "handoff_queued": 0, "booking_verified": 1, "api_calls": 4}))
        self.assertEqual(report["failure"], "missing_proposal")
        self.assertEqual(report["effects"]["booking_completed"], 1)
        self.assertEqual(sum(e["route"] == "/patients/{patientId}/appointments" for e in report["http"]), 1)

    def test_unexpected_failure_after_booking_keeps_attempt_and_failed_step(self):
        original = self.harness._assertions
        def fail_after_booking(view, expected):
            if (view["current_result"] or {}).get("status") == "completed":
                raise OSError("PRIVATE failure text")
            return original(view, expected)
        steps = ready() + [{"kind": "confirm", "expect": {}}, command("help")]
        with patch.object(self.harness, "_assertions", side_effect=fail_after_booking):
            report = self.run_case(case(steps, {"post_attempts": 1, "booking_completed": 1, "handoff_queued": 0}))
        self.assertEqual(report["failure"], "harness_unavailable")
        self.assertEqual(report["effects"]["post_attempts"], 1)
        self.assertEqual(report["effects"]["booking_completed"], 1)
        self.assertEqual(report["steps"][-1]["index"], 4)
        self.assertFalse(report["steps"][-1]["passed"])
        self.assertEqual(report["unrun_steps"], [5])
        self.assertNotIn("PRIVATE", json.dumps(report))
        self.assertEqual(list(self.effects.iterdir()), [])

    def test_malformed_ok_outcome_cannot_pass_without_expectations(self):
        steps = [{"kind": "text", "text": "Find a family doctor", "dispatch": True, "expect": {}}]
        for outcome in [LanguageOutcome("ok", "fixture"),
                        LanguageOutcome("ok", "fixture", "preferences", {"location": None})]:
            with patch.object(adapter := self.language(), "interpret", return_value=outcome):
                report = self.run_case(case(steps), adapter)
            self.assertEqual(report["failure"], "observation_invalid")
            self.assertTrue(report["halt_dispatch"])

    def test_invalid_direct_case_and_encoded_surrogates_are_sanitized(self):
        invalid = case([{"kind": "text", "text": "\ud800", "dispatch": True, "expect": {}}])
        with self.assertRaisesRegex(ValueError, "invalid_manifest"):
            self.run_case(invalid)
        path = self.effects / "manifest.json"
        path.write_text(json.dumps({"schema_version": 1, "synthetic_only": True, "set": "development",
                                    "repetitions": 1, "cases": [invalid]}))
        with self.assertRaisesRegex(ValueError, "invalid_manifest"):
            self.harness.load_manifest(path)

    def test_known_fixture_accounting_observed_but_never_genuine(self):
        class FixtureAccounting:
            def reserve(self, **_kwargs):
                return 1
            def settle(self, _reservation, usage):
                return {"status": "known", "cost_usd": "0.000010000"}
        adapter = self.language("preferences", {"specialty": "primary_care"})
        adapter._budget = FixtureAccounting()
        report = self.run_case(case([{"kind": "text", "text": "I want primary care", "dispatch": True,
            "expect": {"states": ["preferences"], "preferences": {"specialty": "primary_care"}}}]), adapter)
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["steps"][0]["language"]["accounting_status"], "known")
        self.assertEqual(report["steps"][0]["language"]["cost_usd"], "0.000010000")
        self.assertEqual(report["mode"], "fixture")
        self.assertFalse(report["genuine_qualification"])

    def test_lost_observation_of_real_booking_stops_as_unknown(self):
        original = HttpMockAdapter._wire
        def lose_observation(api, method, path, body):
            status, document, failure = original(api, method, path, body)
            if method == "POST":
                # Real supplied service receives the POST. Only its observed
                # receipt is corrupted at the transport boundary for this test.
                return status, {"unexpected": "PRIVATE receipt"}, failure
            return status, document, failure
        steps = ready() + [{"kind": "confirm", "expect": {"result_status": "unknown"}}, command("help")]
        with patch.object(HttpMockAdapter, "_wire", new=lose_observation):
            report = self.run_case(case(steps, {"post_attempts": 1, "booking_completed": 0, "handoff_queued": 0}))
        self.assertEqual(report["failure"], "effect_unknown")
        self.assertEqual(report["steps"][-1]["history_statuses"], ["unknown"])
        self.assertEqual(report["effects"]["post_attempts"], 1)
        self.assertEqual(report["effects"]["booking_verified"], 0)
        self.assertEqual(report["http"][-1]["status"], 201)
        self.assertTrue(report["halt_dispatch"])
        self.assertEqual(report["unrun_steps"], [5])
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_real_receipt_requires_matching_appointments_read(self):
        original = HttpMockAdapter._wire
        def lose_read_observation(api, method, path, body):
            status, document, failure = original(api, method, path, body)
            if method == "GET" and path.endswith("/appointments"):
                return status, {"appointments": []}, failure
            return status, document, failure
        steps = ready() + [{"kind": "confirm", "expect": {}}, command("help")]
        with patch.object(HttpMockAdapter, "_wire", new=lose_read_observation):
            report = self.run_case(case(steps, {"post_attempts": 1, "booking_completed": 1, "handoff_queued": 0}))
        self.assertEqual(report["failure"], "booking_verification_failed")
        self.assertEqual(report["effects"]["booking_completed"], 1)
        self.assertEqual(report["effects"]["booking_verified"], 0)
        self.assertTrue(report["halt_dispatch"])
        self.assertEqual(report["unrun_steps"], [5])

    def test_repetitions_own_fresh_http_and_effects_without_new_language_accounting(self):
        reservations = []
        class FixtureAccounting:
            def reserve(self, **_kwargs):
                reservations.append(len(reservations) + 1)
                return reservations[-1]
            def settle(self, _reservation, usage):
                return {"status": "known", "cost_usd": "0.000010000"}
        adapter = self.language("preferences", {"specialty": "primary_care", "location": "downtown"})
        adapter._budget = FixtureAccounting()
        value = self.harness.load_manifest(FIXTURE)["cases"][0]
        for repetition in (1, 2):
            report = self.harness.run_journey(value, adapter, self.effects, repetition_id=repetition)
            self.assertTrue(report["passed"], report)
            self.assertEqual(report["repetition_id"], repetition)
            self.assertEqual(report["effects"]["booking_verified"], 1)
        self.assertEqual(reservations, [1, 2])
        self.assertEqual(list(self.effects.iterdir()), [])

    def test_direct_script_import_supports_parent_entrypoint(self):
        import subprocess
        import sys
        result = subprocess.run([sys.executable, "-B", "-c",
            "import http.client; http.client.HTTPSConnection = None; import connected_qualification; "
            "print(callable(connected_qualification.load_manifest))"],
            cwd=ROOT / "scripts", capture_output=True, text=True, timeout=10,
            env={"PYTHONPATH": str(ROOT / "src"), "PYTHONDONTWRITEBYTECODE": "1"})
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), "True")

    def test_http_transport_unavailable_halts_even_when_state_expected(self):
        original = HttpMockAdapter._wire
        def unavailable_observation(api, method, path, body):
            original(api, method, path, body)
            return None, None, "transport_error"
        with patch.object(HttpMockAdapter, "_wire", new=unavailable_observation):
            report = self.run_case(case([command("discover", expect={"states": ["outage"]}), command("help")]))
        self.assertEqual(report["failure"], "scheduling_transport_unavailable")
        self.assertTrue(report["halt_dispatch"])
        self.assertEqual(report["unrun_steps"], [1])

    def test_injected_transport_cannot_be_relabelled_genuine(self):
        adapter = self.language("preferences", {"specialty": "primary_care"})
        adapter.mode = "openai"  # Corrupt observation metadata, not a real transport.
        class FixtureAccounting:
            def reserve(self, **_kwargs):
                return 1
            def settle(self, _reservation, usage):
                return {"status": "known", "cost_usd": "0.000010000"}
        adapter._budget = FixtureAccounting()
        report = self.run_case(case([{"kind": "text", "text": "I want primary care", "dispatch": True,
                                     "expect": {"states": ["preferences"]}}]), adapter)
        self.assertFalse(report["genuine_qualification"])
        self.assertEqual(report["mode"], "fixture")
        self.assertEqual(report["failure"], "observation_invalid")


if __name__ == "__main__":
    unittest.main()
