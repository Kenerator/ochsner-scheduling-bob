"""Actual launch constructors must expose safe diagnostics without recording."""
import io
import json
from concurrent.futures import ThreadPoolExecutor
from threading import Event
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import __main__ as cli
from ochsner_bob.diagnostics import Diagnostics
from ochsner_bob.http_mock import ApiError, HttpMockAdapter, UnknownOutcome
from ochsner_bob.interaction_service import InteractionService
from ochsner_bob.language import LanguageAdapter, LanguageOutcome
from ochsner_bob.replay import Limits
from test_interaction_service import CATALOG, CountingLanguage
from test_language import ENV, response, proposal
from test_replay_live_core import PROVENANCE
from test_session_contract import FixturePort
from http_support import supplied_server


class LiveDiagnosticsTests(unittest.TestCase):
    def service(self, root, port, language=None):
        service = InteractionService(lambda: port, Path(root) / "effects.json", language=language,
                                     fixture_catalog=CATALOG, provenance=PROVENANCE)
        return service, service.create()["token"]

    def test_browser_constructor_exposes_api_outcome_error_and_timing_with_recording_off(self):
        with tempfile.TemporaryDirectory() as root, supplied_server() as server:
            port = HttpMockAdapter(server.base_url, scenario="api_failure")
            service, token = self.service(root, port)
            result = service.command(token, "discover", {}, 0)
            diagnostic = service.diagnostics(token)
            self.assertEqual(diagnostic["recording"], "off")
            self.assertEqual(result["state"], "outage")
            event = diagnostic["api_events"][-1]
            self.assertEqual((event["method"], event["outcome"], event["error"], event["http_status"]),
                             ("providers", "failed", "downstream_unavailable", 503))
            self.assertGreaterEqual(event["latency_ms"], 0)
            self.assertEqual(service.diagnostics(token), diagnostic)

    def test_browser_model_projection_disposition_timing_off_and_session_isolation(self):
        language = LanguageAdapter(transport=lambda *a, **k: response(proposal(specialty="primary_care")), environ=ENV)
        with tempfile.TemporaryDirectory() as root:
            service, token = self.service(root, FixturePort(), language)
            result = service.text(token, "Find primary care providers", 0)
            diagnostic = service.diagnostics(token)
            model = diagnostic["model"]
            self.assertIsNotNone(model)
            self.assertEqual(model["public_projection"], {"workflow": "start", "preferences": {}})
            self.assertEqual(model["accepted_fields"], ["specialty"])
            self.assertEqual(model["rejected_fields"], [])
            self.assertEqual(model["application"], "applied")
            self.assertGreaterEqual(model["latency_ms"], 0)
            other = service.create()["token"]
            self.assertEqual(service.diagnostics(other)["api_events"], [])
            self.assertIsNone(service.diagnostics(other)["model"])
            before = service.read(token)["revision"]
            service.diagnostics(token)
            self.assertEqual(service.read(token)["revision"], before)
            serialized = json.dumps(diagnostic)
            for private in (ENV["OPENAI_API_KEY"], "Find primary care providers", "private model prose", '"nonce"'):
                self.assertNotIn(private, serialized)
            self.assertEqual(result["state"], "providers")

    def test_malformed_201_diagnostic_is_unknown_not_completed(self):
        port = HttpMockAdapter("http://127.0.0.1:12345")
        with tempfile.TemporaryDirectory() as root:
            service, token = self.service(root, port)
            with patch.object(port, "_wire", return_value=(201, {"private": "sentinel"}, None)):
                service.command(token, "handoff", {}, 0)
            event = service.diagnostics(token)["api_events"][-1]
            self.assertEqual((event["outcome"], event["error"]), ("unknown", "unknown_outcome"))
            self.assertNotIn("sentinel", json.dumps(service.diagnostics(token)))

    def test_cli_diagnostics_command_is_effect_free_and_displays_collected_events(self):
        with tempfile.TemporaryDirectory() as root:
            output = io.StringIO()
            port = FixturePort()
            with patch.object(cli, "HttpMockAdapter", return_value=port):
                code = cli.main(["--journal", str(Path(root) / "effects.json")],
                                input_stream=io.StringIO("providers\n/diagnostics\n/diagnostics\n/quit\n"),
                                output_stream=output)
            self.assertEqual(code, 0)
            self.assertIn('"api_events"', output.getvalue())
            self.assertIn('"outcome": "ok"', output.getvalue())
            self.assertEqual(port.reads, ["public"])
            self.assertEqual(port.writes, [])

    def test_rejected_untrusted_fields_are_categorical_not_values_or_names(self):
        class InvalidLanguage:
            mode = "fixture"
            def interpret(self, text, context):
                return LanguageOutcome("ok", "fixture", "preferences", {"private-field-sentinel": "private-value-sentinel"})
        with tempfile.TemporaryDirectory() as root:
            service, token = self.service(root, FixturePort(), InvalidLanguage())
            result = service.text(token, "Find primary care providers", 0)
            model = service.diagnostics(token)["model"]
            self.assertEqual(result["interpretation"]["status"], "invalid_output")
            self.assertEqual(model["accepted_fields"], [])
            self.assertEqual(model["rejected_fields"], ["structured_output"])
            self.assertEqual(model["application"], "rejected")
            self.assertNotIn("sentinel", json.dumps(model))

    def test_api_history_bound_and_restored_constructor_are_honest(self):
        with tempfile.TemporaryDirectory() as root:
            port = FixturePort()
            service = InteractionService(lambda: port, Path(root) / "effects.json",
                fixture_catalog=CATALOG, provenance=PROVENANCE, limits=Limits(max_events=1))
            token = service.create()["token"]
            service.command(token, "discover", {}, 0)
            service.command(token, "discover", {}, 1)
            diagnostic = service.diagnostics(token)
            self.assertEqual(len(diagnostic["api_events"]), 1)
            self.assertEqual(diagnostic["diagnostic_dropped"], 1)
            restored = InteractionService(lambda: port, Path(root) / "effects.json",
                fixture_catalog=CATALOG, provenance=PROVENANCE)
            restored.command(token, "discover", {}, 0)
            self.assertEqual(restored.diagnostics(token)["api_events"][0]["outcome"], "ok")
            self.assertEqual(restored.diagnostics(token)["recording"], "off")

    def test_write_diagnostics_preserve_core_rejection_failure_unknown_categories(self):
        with tempfile.TemporaryDirectory() as root:
            for index, (error, expected) in enumerate(((ApiError(400), "rejected"), (ApiError(409), "rejected"),
                    (ApiError(404), "failed"), (ApiError(503), "failed"), (UnknownOutcome(), "unknown"))):
                with self.subTest(expected=expected, status=error.status):
                    port = FixturePort()
                    port.outcome = error
                    service, token = self.service(Path(root) / str(index), port)
                    view = service.command(token, "identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"}, 0)
                    view = service.command(token, "preferences", {"specialty": "primary_care"}, view["revision"])
                    view = service.command(token, "availability", {}, view["revision"])
                    view = service.command(token, "select", {"index": 1}, view["revision"])
                    proposal_view = view["proposal"]
                    view = service.command(token, "confirm", {"proposal_id": proposal_view["id"], "nonce": proposal_view["nonce"]}, view["revision"])
                    self.assertEqual(view["current_result"]["status"], expected)
                    self.assertEqual(service.diagnostics(token)["api_events"][-1]["outcome"], expected)

    def test_model_publication_holds_service_freshness_lock(self):
        language = LanguageAdapter(transport=lambda *a, **k: response(proposal(specialty="primary_care")), environ=ENV)
        with tempfile.TemporaryDirectory() as root, ThreadPoolExecutor(max_workers=1) as pool:
            service, token = self.service(root, FixturePort(), language)
            session, _ = service._resolve(token)
            context = service._attach(session)
            original = context["conversation"]._diagnostic_sink
            entered, release = Event(), Event()
            def delayed(**kwargs):
                entered.set()
                if not release.wait(5):
                    raise RuntimeError("test callback timeout")
                original(**kwargs)
            context["conversation"]._diagnostic_sink = delayed
            future = pool.submit(service.text, token, "Find primary care providers", 0)
            try:
                self.assertTrue(entered.wait(5))
                acquired = service.lock.acquire(blocking=False)
                if acquired:
                    service.lock.release()
                self.assertFalse(acquired, "freshness and diagnostics must publish atomically")
            finally:
                release.set()
            first = future.result(timeout=5)
            context["conversation"]._diagnostic_sink = original
            service.text(token, "Find primary care providers", first["revision"])
            self.assertGreater(service.diagnostics(token)["model"]["revision"], 2)

    def test_delayed_older_model_diagnostic_cannot_replace_newer_revision(self):
        diagnostic = Diagnostics()
        metadata = dict(context={"workflow": "start", "preferences": {}}, status="ok",
            accepted=["specialty"], rejected=[], application="applied", elapsed=0)
        diagnostic.language(revision=5, **metadata)
        diagnostic.language(revision=2, **metadata)
        self.assertEqual(diagnostic.snapshot()["model"]["revision"], 5)
