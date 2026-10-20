"""Catch consent inferred from text, private model input and sketch-only CLI demos."""

import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.http_mock import HttpMockAdapter
from ochsner_bob.language import LanguageAdapter, LanguageOutcome
from ochsner_bob.session import SchedulingSession
from http_support import HostileServer, supplied_server


ROOT = Path(__file__).resolve().parents[1]


class ProposedLanguage:
    mode = "fixture"

    def __init__(self, outcome=None, callback=None):
        self.calls = []
        self.outcome = outcome or LanguageOutcome("ok", "fixture", "discover", {"specialty": "primary_care", "location": "downtown"})
        self.callback = callback

    def interpret(self, text, context):
        self.calls.append((text, context))
        if self.callback:
            self.callback()
        return self.outcome


class ConversationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.conversation"), "Shared Conversation orchestration is missing")
        self.Conversation = importlib.import_module("ochsner_bob.conversation").Conversation
        temporary = tempfile.TemporaryDirectory(prefix="bob-conversation-")
        self.addCleanup(temporary.cleanup)
        self.server = self.enterContext(supplied_server())
        self.session = SchedulingSession(HttpMockAdapter(self.server.base_url), journal_path=Path(temporary.name) / "effects.json")
        self.conversation = self.Conversation(self.session)

    def say(self, text):
        return self.conversation.interpret(text, self.session.revision)

    def identify(self):
        return self.conversation.enter_identity("555-0101", "1985-04-12", "70112", expected_revision=self.session.revision)

    def ready(self):
        self.say("providers primary_care downtown")
        self.identify()
        self.say("availability")
        return self.say("1")["proposal"]

    def confirm(self, proposal):
        return self.conversation.confirm(proposal["id"], proposal["nonce"], expected_revision=proposal["revision"])

    def test_offline_public_lookup_needs_no_identity_or_model(self):
        view = self.say("providers primary_care downtown")
        self.assertEqual(view["identity_status"], "missing")
        self.assertEqual([p["providerId"] for p in view["providers"]], ["prov_2001", "prov_2002"])
        self.assertEqual(view["interpretation"]["mode"], "offline")
        self.assertEqual(self.server.wait_for_audits(1), [{"method": "GET", "route": "/providers", "status": 200}])

    def test_number_selects_but_only_dedicated_snapshot_confirmation_books(self):
        proposal = self.ready()
        self.assertIsNone(self.session.view()["current_result"])
        self.assertEqual([a["method"] for a in self.server.wait_for_audits(3)], ["GET"] * 3)
        completed = self.confirm(proposal)
        self.assertEqual(completed["current_result"]["status"], "completed")
        self.assertEqual(completed["current_result"]["receipt"]["startTime"], proposal["slot"]["startTime"])
        self.confirm(proposal)
        self.assertEqual([a["method"] for a in self.server.wait_for_audits(4)].count("POST"), 1)

    def test_yes_and_textual_confirm_revoke_without_consent(self):
        for text in ("yes", "confirm", "/confirm please", "yes but uptown instead"):
            with self.subTest(text=text):
                proposal = self.ready()
                self.say(text)
                self.assertIsNone(self.session.view()["proposal"])
                self.confirm(proposal)
                self.assertEqual(self.session.view()["history"], [])

    def test_help_and_medical_route_before_private_data_or_language(self):
        language = ProposedLanguage(callback=lambda: self.fail("safety route reached language"))
        self.conversation = self.Conversation(self.session, language=language)
        for text, state in (("My phone is 555-0101; I need a human", "help"),
                            ("DOB 1985-04-12; I have chest pain, should I wait?", "medical")):
            view = self.say(text)
            self.assertEqual(view["state"], state)
        self.assertEqual(language.calls, [])
        self.assertEqual(self.server.audits, [])

    def test_private_chat_never_becomes_identity_or_reaches_language(self):
        language = ProposedLanguage(callback=lambda: self.fail("private input reached language"))
        self.conversation = self.Conversation(self.session, language=language)
        for text in ("phone=555-0101 dob=1985-04-12 zip=70112", "5550101", "pat_1001", "my name is Maya Chen"):
            view = self.say(text)
            self.assertEqual(view["identity_status"], "missing")
            self.assertEqual(view["interpretation"]["status"], "private_input")
        self.assertEqual(language.calls, [])
        self.assertEqual(self.server.audits, [])
        self.assertNotIn("555-0101", json.dumps(self.session.trace()))

    def test_local_identity_control_never_calls_language(self):
        language = ProposedLanguage(callback=lambda: self.fail("local identity reached language"))
        self.conversation = self.Conversation(self.session, language=language)
        self.assertEqual(self.identify()["identity_status"], "verified")
        self.assertEqual(language.calls, [])
        self.assertEqual(len(self.server.wait_for_audits(1)), 1)

    def test_stale_text_has_no_model_call_or_authority_change(self):
        proposal = self.ready()
        language = ProposedLanguage()
        self.conversation = self.Conversation(self.session, language=language)
        result = self.conversation.interpret("Find a family doctor", proposal["revision"] - 1)
        self.assertTrue(result["stale"])
        self.assertEqual(self.session.view()["proposal"], proposal)
        self.assertEqual(language.calls, [])

    def test_provider_selection_correction_and_clear_preserve_other_filters(self):
        self.say("providers primary_care downtown")
        view = self.say("provider 2")
        self.assertEqual(view["preferences"]["provider_id"], "prov_2002")
        self.say("provider 99")
        self.assertEqual(self.session.view()["preferences"]["provider_id"], "prov_2002")
        self.identify()
        slots = self.say("availability")["slots"]
        self.assertTrue(slots)
        self.assertTrue(all(s["providerId"] == "prov_2002" for s in slots))
        self.say("clear provider")
        self.assertEqual(self.session.view()["preferences"], {"specialty": "primary_care", "location": "downtown"})

    def test_date_correction_validates_merged_range_before_http(self):
        self.say("providers primary_care downtown")
        self.say("dates 2099-01-01 2099-01-31")
        view = self.say("start 2099-02-01")
        self.assertEqual(view["preferences"]["start_date"], "2099-01-01")
        self.assertEqual(len(self.server.wait_for_audits(1)), 1)
        self.say("end 2099-02-28")
        self.say("start 2099-02-01")
        cleared = self.say("clear dates")
        self.assertEqual(cleared["preferences"], {"specialty": "primary_care", "location": "downtown"})
        self.assertEqual(len(self.server.audits), 1)

    def test_model_gets_only_public_projection_after_proposal_revocation(self):
        self.ready()
        language = ProposedLanguage(callback=lambda: self.assertIsNone(self.session.view()["proposal"]))
        self.conversation = self.Conversation(self.session, language=language)
        result = self.say("Which family doctors are downtown?")
        self.assertEqual(result["state"], "providers")
        self.assertEqual(result["interpretation"]["mode"], "fixture")
        text, context = language.calls[0]
        self.assertEqual(text, "Which family doctors are downtown?")
        self.assertEqual(set(context), {"workflow", "preferences"})
        for private in ("555-0101", "1985-04-12", "70112", "pat_1001", "slot_4001"):
            self.assertNotIn(private, json.dumps(context))

    def test_disabled_real_language_has_no_fallback_and_revokes_proposal(self):
        proposal = self.ready()
        self.conversation = self.Conversation(self.session, language=LanguageAdapter(environ={}))
        result = self.say("Find a family doctor")
        self.assertEqual(result["interpretation"]["status"], "disabled")
        self.assertIsNone(result["proposal"])
        self.confirm(proposal)
        self.assertEqual(self.session.view()["history"], [])

    def test_real_bounded_language_fixture_works_after_public_correction(self):
        self.identify()
        self.say("location uptown")
        payloads = []
        def fixture(payload, **_bounds):
            payloads.append(json.loads(payload))
            proposal = {"action": "discover", "preferences": {"specialty": "primary_care", "location": "uptown", "start_date": None, "end_date": None}}
            return json.dumps({"status": "completed", "output": [{"type": "message", "role": "assistant", "content": [
                {"type": "output_text", "text": json.dumps(proposal)}]}]}).encode()
        # Synthetic fixture labels only; no runtime environment/credentials/network.
        language = LanguageAdapter(transport=fixture, environ={"BOB_ENABLE_OPENAI": "1",
            "BOB_OPENAI_MODEL": "fixture-model", "OPENAI_API_KEY": "synthetic-placeholder"})
        self.conversation = self.Conversation(self.session, language=language)
        result = self.say("Find primary care providers uptown")
        self.assertEqual(result["state"], "providers")
        self.assertEqual([p["providerId"] for p in result["providers"]], ["prov_2001"])
        self.assertEqual(result["interpretation"], {"mode": "fixture", "status": "ok"})
        self.assertEqual(len(payloads), 1)
        for token in ("555-0101", "1985-04-12", "70112", "pat_1001"):
            self.assertNotIn(token, json.dumps(payloads))

    def test_mistyped_language_outcome_fails_closed_without_raw_exception(self):
        for outcome in (LanguageOutcome([], "fixture"), LanguageOutcome("ok", {}, "discover"),
                        LanguageOutcome("ok", "fixture", "discover", [])):
            with self.subTest(outcome=outcome):
                self.conversation = self.Conversation(self.session, language=ProposedLanguage(outcome=outcome))
                result = self.say("Find primary care providers downtown")
                self.assertEqual(result["interpretation"]["status"], "invalid_output")
                self.assertEqual(result["providers"], [])

    def test_language_failure_never_echoes_exception_or_reuses_confirmation(self):
        proposal = self.ready()
        def fail():
            raise TimeoutError("555-0101 secret")
        self.conversation = self.Conversation(self.session, language=ProposedLanguage(callback=fail))
        view = self.say("Find a family doctor")
        self.assertEqual(view["interpretation"]["status"], "unavailable")
        self.assertNotIn("secret", json.dumps(view))
        self.assertIsNone(view["proposal"])
        self.confirm(proposal)
        self.assertEqual(self.session.view()["history"], [])

    def test_language_budget_failures_remain_safe_categorical_noncompletion(self):
        for status in ("budget_exceeded", "accounting_failed"):
            proposal = self.ready()
            self.conversation = self.Conversation(self.session,
                language=ProposedLanguage(outcome=LanguageOutcome(status, "fixture")))
            view = self.say("Find a family doctor")
            self.assertEqual(view["interpretation"]["status"], status)
            self.assertIsNone(view["proposal"])
            self.confirm(proposal)
            self.assertEqual(self.session.view()["history"], [])

    def test_forged_language_fields_or_action_never_supply_authority(self):
        for outcome in (LanguageOutcome("ok", "fixture", "confirm", {}),
                        LanguageOutcome("ok", "fixture", "preferences", {"patientId": "pat_1001"}),
                        {"action": "discover", "preferences": {}}):
            self.conversation = self.Conversation(self.session, language=ProposedLanguage(outcome=outcome))
            result = self.say("Please do that")
            self.assertEqual(result["interpretation"]["status"], "invalid_output")
            self.assertEqual(result["identity_status"], "missing")
        self.assertEqual(self.server.audits, [])

    def test_model_return_after_another_revision_cannot_overwrite_new_preferences(self):
        def intervening_turn():
            self.session.command("preferences", {"location": "uptown"}, expected_revision=self.session.revision)
        self.conversation = self.Conversation(self.session, language=ProposedLanguage(callback=intervening_turn))
        result = self.say("Which family doctors are downtown?")
        self.assertTrue(result["stale"])
        self.assertEqual(self.session.view()["preferences"], {"location": "uptown"})
        self.assertEqual(self.server.audits, [])

    def test_invalid_input_revokes_proposal_without_language_or_http(self):
        for text in (None, 3, "x" * 2049, "\ud800"):
            proposal = self.ready()
            result = self.say(text)
            self.assertEqual(result["interpretation"]["status"], "invalid_input")
            self.assertIsNone(result["proposal"])
            self.confirm(proposal)
        self.assertEqual(self.session.view()["history"], [])

    def test_unknown_write_stays_blocked_after_reset_through_conversation(self):
        proposal = self.ready()
        with HostileServer(action="disconnect") as hostile:
            self.session.api = HttpMockAdapter(hostile.base_url)
            result = self.confirm(proposal)
            self.assertEqual(result["current_result"]["status"], "unknown")
            self.say("reset")
            self.assertTrue(self.session.view()["booking_blocked"])
            self.confirm(proposal)
            self.assertEqual(len(hostile.wait_for_requests(1)), 1)


class CliAndOwnedMockTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bob-cli-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.environment = dict(os.environ, PYTHONPATH=str(ROOT / "src"), PYTHONDONTWRITEBYTECODE="1")

    def cli(self, url, turns):
        return subprocess.run([sys.executable, "-m", "ochsner_bob", "--api-url", url,
                               "--journal", str(self.directory / "effects.json")],
                              input=turns, text=True, capture_output=True, cwd=ROOT,
                              env=self.environment, timeout=10)

    def owned_mock(self, **kwargs):
        self.assertIsNotNone(importlib.util.find_spec("scripts.mock_lifecycle"), "Owned vendored mock subprocess lifecycle is missing")
        return importlib.import_module("scripts.mock_lifecycle").OwnedMock(**kwargs)

    def test_cli_is_interactive_offline_and_books_only_dedicated_confirm(self):
        with supplied_server() as server:
            process = self.cli(server.base_url, "providers primary_care downtown\n/identity 555-0101 1985-04-12 70112\navailability\n1\n/confirm\n/confirm\n/quit\n")
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("Offline deterministic commands", process.stdout)
            self.assertIn("completed", process.stdout)
            self.assertEqual([a["method"] for a in server.wait_for_audits(4)].count("POST"), 1)

    def test_cli_yes_plus_correction_and_plain_yes_are_not_confirmation(self):
        with supplied_server() as server:
            process = self.cli(server.base_url, "providers primary_care downtown\n/identity 555-0101 1985-04-12 70112\navailability\n1\nyes\n/confirm\n/quit\n")
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertEqual([a["method"] for a in server.wait_for_audits(3)], ["GET"] * 3)

    def test_cli_never_displays_duplicate_patient_candidates(self):
        with supplied_server() as server:
            process = self.cli(server.base_url, "/identity 555-0130 1978-09-22\nappointments\n/quit\n")
            self.assertEqual(process.returncode, 0, process.stderr)
            for token in ("pat_1003", "pat_1004", "Avery", "70115", "70005"):
                self.assertNotIn(token, process.stdout + process.stderr)
            self.assertEqual(len(server.wait_for_audits(1)), 1)

    def test_cli_outage_reports_failed_handoff_without_completion(self):
        with supplied_server() as server:
            process = subprocess.run([sys.executable, "-m", "ochsner_bob", "--api-url", server.base_url,
                                      "--scenario", "api_failure", "--journal", str(self.directory / "outage.json")],
                                     input="providers primary_care downtown\nhandoff api_failure\n/quit\n",
                                     text=True, capture_output=True, cwd=ROOT, env=self.environment, timeout=10)
            self.assertEqual(process.returncode, 0, process.stderr)
            self.assertIn("failed", process.stdout)
            self.assertNotIn("handoff: queued", process.stdout)
            self.assertEqual([a["status"] for a in server.wait_for_audits(2)], [503, 503])

    def run_cli_main(self, turns, *, openai=True):
        from ochsner_bob import __main__ as cli
        output = io.StringIO()
        arguments = ["--api-url", "http://127.0.0.1:1", "--journal", str(self.directory / "cli-journal.json")]
        if openai:
            arguments.append("--openai")
            from ochsner_bob.model_budget import ModelBudget
            # Current model hosts require already-existing SQLite. This fixture
            # setup is not a product initialization/headroom operation.
            ModelBudget(self.directory / ".bob-local/model-budget.json", application_runtime=True)
        with patch.object(cli, "ROOT", self.directory.resolve(), create=True):
            try:
                code = cli.main(arguments, input_stream=io.StringIO(turns), output_stream=output)
            except SystemExit as error:
                code = error.code
        return code, output.getvalue()

    def test_cli_openai_disabled_is_explicit_and_never_falls_back(self):
        from ochsner_bob import language
        from ochsner_bob.model_budget import ModelBudget
        with patch.dict(os.environ, {}, clear=True), patch.object(language, "_http_transport") as transport:
            code, output = self.run_cli_main("Find primary care providers downtown\n/quit\n")
        self.assertEqual(code, 0)
        self.assertIn("OpenAI interpretation explicitly requested", output)
        self.assertIn("Model interpretation is disabled", output)
        self.assertNotIn("Provider 1:", output)
        transport.assert_not_called()
        snapshot = ModelBudget(self.directory / ".bob-local/model-budget.json").snapshot()
        self.assertEqual((snapshot["calls"], snapshot["max_calls"], snapshot["ceiling_usd"]), (0, 200, "20.000000000"))

    def test_cli_opt_in_construction_and_initial_view_do_not_dispatch(self):
        from ochsner_bob import language
        from ochsner_bob.model_budget import ModelBudget, DEFAULT_MODEL
        synthetic = {"BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": DEFAULT_MODEL,
                     "OPENAI_API_KEY": "synthetic-not-a-runtime-credential"}
        with patch.dict(os.environ, synthetic, clear=True), patch.object(language, "_http_transport") as transport:
            code, output = self.run_cli_main("/quit\n")
        self.assertEqual(code, 0)
        transport.assert_not_called()
        self.assertNotIn(synthetic["OPENAI_API_KEY"], output)
        self.assertEqual(ModelBudget(self.directory / ".bob-local/model-budget.json").snapshot()["calls"], 0)

    def test_cli_default_offline_does_not_construct_optional_budget(self):
        from ochsner_bob import model_budget
        with patch.object(model_budget.ModelBudget, "__init__", side_effect=AssertionError("unrequested budget")):
            code, output = self.run_cli_main("Find primary care providers downtown\n/quit\n", openai=False)
        self.assertEqual(code, 0)
        self.assertIn("Offline deterministic commands", output)
        self.assertNotIn("OpenAI interpretation explicitly requested", output)
        self.assertFalse((self.directory / ".bob-local/model-budget.json").exists())

    def test_cli_explicit_language_uses_the_canonical_shared_budget(self):
        from ochsner_bob import __main__ as cli
        from ochsner_bob import language
        from ochsner_bob.model_budget import ModelBudget, DEFAULT_MODEL
        synthetic = {"BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": DEFAULT_MODEL,
                     "OPENAI_API_KEY": "synthetic-not-a-runtime-credential"}
        # A real bounded adapter with injected response bytes; never a live call.
        from test_language import proposal, response
        def fixture_adapter(**kwargs):
            return language.LanguageAdapter(transport=lambda *_a, **_k: response(proposal(action="clarify")),
                                            environ=synthetic, **kwargs)
        with patch.object(cli, "LanguageAdapter", side_effect=fixture_adapter, create=True) as constructor:
            code, output = self.run_cli_main("Please clarify the supported choices\n/quit\n")
        self.assertEqual(code, 0)
        constructor.assert_called_once()
        budget = constructor.call_args.kwargs["budget"]
        self.assertEqual(budget.path, (self.directory / ".bob-local/model-budget.json").resolve())
        self.assertEqual(ModelBudget(budget.path).snapshot()["calls"], 1)
        self.assertNotIn(synthetic["OPENAI_API_KEY"], output)

    def test_owned_mock_ephemeral_lifecycle_and_independent_instances(self):
        with self.owned_mock() as first, self.owned_mock() as second:
            self.assertNotEqual(first.base_url, second.base_url)
            self.assertEqual(len(HttpMockAdapter(first.base_url).providers()), 3)
            first.close()
            self.assertIsNotNone(first.process.poll())
            self.assertEqual(len(HttpMockAdapter(second.base_url).providers()), 3)
        self.assertIsNotNone(second.process.poll())

    def test_occupied_port_does_not_kill_or_reconfigure_existing_mock(self):
        with self.owned_mock() as running:
            port = int(running.base_url.rsplit(":", 1)[1])
            with self.assertRaises(RuntimeError):
                with self.owned_mock(port=port):
                    self.fail("occupied port was unexpectedly stolen")
            self.assertEqual(len(HttpMockAdapter(running.base_url).providers()), 3)

    def test_startup_timeout_terminates_only_its_owned_child(self):
        mock = self.owned_mock(startup_timeout=0.000001)
        with self.assertRaises(RuntimeError):
            mock.__enter__()
        self.assertIsNotNone(mock.process.poll())

    def test_demos_run_supplied_success_conflict_and_labeled_unknown_fault(self):
        process = subprocess.run([sys.executable, "scripts/demo_booking.py", "--flow", "all"],
                                 cwd=ROOT, env=self.environment, text=True, capture_output=True, timeout=20)
        self.assertEqual(process.returncode, 0, process.stderr)
        results = [json.loads(line) for line in process.stdout.splitlines()]
        self.assertEqual([r["flow"] for r in results], ["success", "conflict", "unknown"])
        self.assertEqual([r["status"] for r in results], ["completed", "completed", "unknown"])
        self.assertEqual(results[1]["history"], ["rejected", "completed"])
        self.assertEqual(results[2]["fault"], "accepted_booking_receipt_hidden_at_adapter_boundary")
        self.assertTrue(results[2]["retry_blocked"])


if __name__ == "__main__":
    unittest.main()
