"""Private transport observations only; the external HTTPS boundary is synthetic."""
import inspect
from pathlib import Path
import ssl
import tempfile
import unittest
from unittest.mock import patch
from urllib.error import URLError

from ochsner_bob import language
from ochsner_bob.model_budget import ModelBudget
from test_language import ENV, FakeResponse, FakeTransport, response


class TransportDiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.assertIn("transport_observer", inspect.signature(language.LanguageAdapter).parameters,
                      "Missing private transport diagnostic seam")
        self.factory = self.enterContext(patch.object(language.http.client, "HTTPSConnection"))
        self.connection = self.factory.return_value
        self.connection.getresponse.return_value = FakeResponse(response())

    def interpret(self, observer, **options):
        return language.LanguageAdapter(environ=ENV, transport_observer=observer, **options).interpret("Find providers")

    def test_http_status_is_observed_once_without_reading_error_body_or_retry(self):
        # A non-200 body must never be read just to diagnose the status.
        for status in (301, 400, 401, 403, 404, 429, 500, 503, 599):
            with self.subTest(status=status):
                reply = FakeResponse(b"SENSITIVE_CANARY", status=status)
                self.connection.getresponse.return_value = reply
                observations = []
                outcome = self.interpret(observations.append)
                self.assertEqual(observations, [{"category": "http_error", "http_status": status}])
                self.assertEqual(outcome.status, "unavailable")
                self.assertIsNone(outcome.action)
                self.assertEqual(reply.read_sizes, [])
                self.assertNotIn("SENSITIVE_CANARY", repr((observations, outcome)))
                self.assertEqual(self.connection.request.call_count, 1)
                self.connection.close.assert_called_once()
                self.connection.reset_mock()

    def test_transport_success_does_not_add_fields_to_language_outcome(self):
        observations = []
        observed = self.interpret(observations.append)
        self.connection.getresponse.return_value = FakeResponse(response())
        ordinary = language.LanguageAdapter(environ=ENV).interpret("Find providers")
        self.assertEqual(observed, ordinary)
        self.assertEqual(observations, [{"category": "success", "http_status": 200}])
        self.assertNotIn("transport", repr(observed))
        self.assertIs(language.LanguageAdapter(environ=ENV)._transport, language._http_transport)

    def test_exception_category_uses_type_only_never_message(self):
        cases = [(TimeoutError("SENSITIVE_CANARY"), "timeout", "timeout"),
                 (ssl.SSLError("SENSITIVE_CANARY"), "tls_error", "unavailable"),
                 (URLError("SENSITIVE_CANARY"), "url_error", "unavailable"),
                 (ConnectionError("SENSITIVE_CANARY"), "network_error", "unavailable"),
                 (language.http.client.HTTPException("SENSITIVE_CANARY"), "protocol_error", "unavailable"),
                 (ValueError("SENSITIVE_CANARY"), "other", "unavailable")]
        for error, category, status in cases:
            with self.subTest(category=category):
                self.connection.connect.side_effect = error
                seen = []
                outcome = self.interpret(seen.append)
                self.assertEqual(seen, [{"category": category, "http_status": None}])
                self.assertEqual(outcome.status, status)
                self.assertNotIn("SENSITIVE_CANARY", repr((seen, outcome)))
                self.assertEqual(self.connection.request.call_count, 0)
                self.connection.close.assert_called_once()
                self.connection.reset_mock()

    def test_constructor_and_close_errors_each_emit_once(self):
        seen = []
        self.factory.side_effect = ssl.SSLError("SENSITIVE_CANARY")
        self.assertEqual(self.interpret(seen.append).status, "unavailable")
        self.assertEqual(seen, [{"category": "tls_error", "http_status": None}])
        self.factory.side_effect = None
        self.connection.close.side_effect = OSError("SENSITIVE_CANARY")
        seen.clear()
        self.assertEqual(self.interpret(seen.append).status, "unavailable")
        self.assertEqual(seen, [{"category": "network_error", "http_status": 200}])

    def test_protocol_and_body_bounds_stay_distinct_from_semantic_validation(self):
        for reply, category, outcome in (
            (FakeResponse(b"SENSITIVE_CANARY", headers={"Content-Type": "text/html"}), "protocol_error", "unavailable"),
            (FakeResponse(b"{}", headers={"Content-Length": "3"}), "invalid_response", "invalid_output"),
            (FakeResponse(b"{}", headers={"Content-Length": "bad"}), "invalid_response", "invalid_output"),
            (FakeResponse(b"x" * 65537), "invalid_response", "invalid_output"),
            (FakeResponse(b"not json"), "success", "invalid_output"),
        ):
            with self.subTest(category=category, outcome=outcome):
                self.connection.getresponse.return_value = reply
                seen = []
                self.assertEqual(self.interpret(seen.append).status, outcome)
                self.assertEqual(seen, [{"category": category, "http_status": 200}])

    def test_observer_failure_cannot_mask_success_failure_or_cause_retry(self):
        def broken(_event):
            raise RuntimeError("SENSITIVE_CANARY")
        for status, expected in ((200, "ok"), (401, "unavailable")):
            self.connection.getresponse.return_value = FakeResponse(response(), status=status)
            self.connection.reset_mock()
            result = self.interpret(broken)
            self.assertEqual(result.status, expected)
            self.assertEqual(self.connection.request.call_count, 1)
            self.assertNotIn("SENSITIVE_CANARY", repr(result))

    def test_sanitizer_rejects_arbitrary_types_and_status_values(self):
        seen = []
        for category, status in (({}, 200), ("SENSITIVE_CANARY", True), (None, 600), ([], "401")):
            language._observe_transport(seen.append, category, status)
        self.assertEqual(seen, [{"category": "other", "http_status": 200},
                                *[{"category": "other", "http_status": None}] * 3])
        self.connection.getresponse.return_value = FakeResponse(b"SENSITIVE_CANARY", status="401")
        seen.clear()
        self.assertEqual(self.interpret(seen.append).status, "unavailable")
        self.assertEqual(seen, [{"category": "other", "http_status": None}])

    def test_invalid_input_and_context_do_not_dispatch_or_observe(self):
        seen = []
        adapter = language.LanguageAdapter(environ=ENV, transport_observer=seen.append)
        for text, context in ((None, None), ("x" * 2049, None), ("Find providers", {"private": "SENSITIVE_CANARY"})):
            self.assertIn(adapter.interpret(text, context).status, ("invalid_input", "invalid_context"))
        self.assertEqual(seen, [])
        self.factory.assert_not_called()

    def test_injected_fixture_transport_keeps_original_protocol_and_mode(self):
        seen = []
        transport = FakeTransport()
        result = language.LanguageAdapter(environ=ENV, transport=transport,
            transport_observer=seen.append).interpret("Find providers")
        self.assertEqual((result.status, result.mode), ("ok", "fixture"))
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(seen, [])
        self.factory.assert_not_called()

    def test_http_400_preserves_full_unknown_reservation_and_previous_history(self):
        with tempfile.TemporaryDirectory() as directory:
            budget = ModelBudget(Path(directory) / "private/budget", application_runtime=True)
            model = "gpt-5.4-2026-03-05"
            first = budget.reserve(model=model)
            budget.settle(first, None)
            before = budget.snapshot()
            self.connection.getresponse.return_value = FakeResponse(b"SENSITIVE_CANARY", status=400)
            seen = []
            result = language.LanguageAdapter(environ={**ENV, "BOB_OPENAI_MODEL": model},
                budget=budget, transport_observer=seen.append).interpret("Find providers")
            after = budget.snapshot()
            self.assertEqual((result.status, result.accounting_status, result.cost_usd), ("unavailable", "unknown", None))
            self.assertEqual((after["calls"], after["unknown_calls"], after["known_calls"]), (2, 2, 0))
            self.assertEqual(seen, [{"category": "http_error", "http_status": 400}])
            self.assertNotEqual(before, after)
            self.assertEqual(budget.reserve(model=model), 3)
