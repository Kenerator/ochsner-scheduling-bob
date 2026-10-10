"""R01/R03/R15: exercise the bounded adapter, never a live model.

These tests catch private input leakage, invented preferences, delegated
authority, permissive JSON parsing, silent fallback and unbounded/retried I/O.
"""

from copy import deepcopy
import importlib
import importlib.util
import json
from pathlib import Path
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
ENV = {"BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": "test-model",
       "OPENAI_API_KEY": "synthetic-test-credential"}


def proposal(action="discover", **preferences):
    return {"action": action, "preferences": {
        "specialty": None, "location": None, "start_date": None,
        "end_date": None, **preferences}}


def response(value=None, *, text=None, status="completed", output=None):
    if output is None:
        output = [{"id": "msg_test", "type": "message", "role": "assistant",
                   "status": "completed", "content": [{"type": "output_text",
                   "text": text if text is not None else json.dumps(value or proposal()),
                   "annotations": []}]}]
    return json.dumps({"id": "resp_test", "object": "response", "status": status,
                       "error": None, "incomplete_details": None, "output": output}).encode()


class FakeTransport:
    def __init__(self, body=None, error=None):
        self.body = response() if body is None else body
        self.error = error
        self.calls = []

    def __call__(self, payload, *, api_key, timeout, max_body_bytes):
        self.calls.append((json.loads(payload), api_key, timeout, max_body_bytes))
        if self.error:
            raise self.error
        return self.body


class LanguageTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.language"),
                             "Bounded language adapter is missing")
        self.module = importlib.import_module("ochsner_bob.language")

    def adapter(self, body=None, error=None, environ=None, **options):
        transport = FakeTransport(body, error)
        adapter = self.module.LanguageAdapter(transport=transport,
                    environ=ENV if environ is None else environ, **options)
        return adapter, transport

    def assert_closed_failure(self, result, status):
        self.assertIsInstance(result, self.module.LanguageOutcome)
        self.assertEqual(result.status, status)
        self.assertIsNone(result.action)
        self.assertEqual(result.preferences, {})
        self.assertNotIn("PRIVATE_SENTINEL", repr(result))
        self.assertNotIn(ENV["OPENAI_API_KEY"], repr(result))

    def test_optional_runtime_configuration_is_all_required(self):
        for key in ENV:
            env = dict(ENV)
            del env[key]
            adapter, transport = self.adapter(environ=env)
            self.assert_closed_failure(adapter.interpret("Find providers"), "disabled")
            self.assertEqual(transport.calls, [])
        for enabled in ("0", "true", "yes", ""):
            adapter, transport = self.adapter(environ={**ENV, "BOB_ENABLE_OPENAI": enabled})
            self.assert_closed_failure(adapter.interpret("Find providers"), "disabled")
            self.assertEqual(transport.calls, [])

    def test_default_path_has_no_network_without_opt_in(self):
        with patch.object(self.module.os, "environ", {}), patch.object(
                self.module.http.client, "HTTPSConnection", side_effect=AssertionError("network")):
            self.assert_closed_failure(self.module.LanguageAdapter().interpret("Find providers"), "disabled")

    def test_request_has_closed_public_projection_and_no_authority(self):
        adapter, transport = self.adapter(response(proposal(location="uptown")))
        context = {"intent": "discover", "workflow": "providers",
                   "preferences": {"specialty": "primary_care"}}
        before = deepcopy(context)
        result = adapter.interpret("Show providers uptown", context)
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action, "discover")
        self.assertEqual(result.preferences, {"location": "uptown"})
        self.assertEqual(result.mode, "fixture")
        self.assertEqual(context, before)
        payload, credential, timeout, bound = transport.calls[0]
        self.assertEqual(len(transport.calls), 1)
        self.assertEqual(payload["model"], "test-model")
        self.assertIs(payload["store"], False)
        self.assertIs(payload["stream"], False)
        self.assertEqual(payload["tools"], [])
        self.assertEqual(payload["max_output_tokens"], 512)
        self.assertEqual(timeout, 10.0)
        self.assertEqual(bound, 65536)
        self.assertEqual(credential, ENV["OPENAI_API_KEY"])
        self.assertNotIn(credential, json.dumps(payload))
        self.assertNotIn("previous_response_id", payload)
        projection = json.loads(payload["input"][0]["content"])
        self.assertEqual(projection, {"text": "Show providers uptown", "context": context})
        schema = payload["text"]["format"]
        self.assertTrue(schema["strict"])
        self.assertEqual(set(schema["schema"]["properties"]), {"action", "preferences"})
        self.assertFalse(schema["schema"]["additionalProperties"])
        self.assertFalse(schema["schema"]["properties"]["preferences"]["additionalProperties"])

    def test_identity_like_input_never_reaches_transport(self):
        texts = ["My phone is 5045550100", "call (504) 555-0100", "555-0101",
                 "ZIP 70112", "70112", "DOB 1980-01-01", "born January 1, 1980",
                 "date of birth is next week", "email a@example.test", "patientId pat_1001",
                 "slot-1", "my name is PRIVATE_SENTINEL", "SSN 123-45-6789",
                 "api key PRIVATE_SENTINEL", "Bearer PRIVATE_SENTINEL",
                 "phone five zero four five five five zero one zero zero",
                 "５０４５５５０１００", "I need help, my phone is 5045550100"]
        for text in texts:
            with self.subTest(text=text):
                adapter, transport = self.adapter()
                self.assert_closed_failure(adapter.interpret(text), "private_input")
                self.assertEqual(transport.calls, [])

    def test_identity_labels_opaque_ids_and_spelled_phone_are_private(self):
        for text in ('{"identity":"PRIVATE_SENTINEL"}', "my name: PRIVATE_SENTINEL",
                     "patient: PRIVATE_SENTINEL", "MRN: PRIVATE_SENTINEL",
                     "slot_opaque", "pat_opaque", "1980-01-01",
                     "five zero four five five five zero one zero zero"):
            with self.subTest(text=text):
                adapter, transport = self.adapter()
                self.assert_closed_failure(adapter.interpret(text), "private_input")
                self.assertEqual(transport.calls, [])

    def test_scheduling_iso_dates_are_public_but_birth_dates_are_not(self):
        adapter, transport = self.adapter(response(proposal("preferences", start_date="2026-10-20")))
        result = adapter.interpret("Show openings starting 2026-10-20")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.preferences, {"start_date": "2026-10-20"})
        self.assertEqual(len(transport.calls), 1)
        self.assert_closed_failure(adapter.interpret("I was born 2026-10-20"), "private_input")
        self.assertEqual(len(transport.calls), 1)

    def test_unknown_or_private_context_is_not_forwarded(self):
        bad_contexts = [{"identity": {"phone": "PRIVATE_SENTINEL"}},
                        {"transcript": ["PRIVATE_SENTINEL"]},
                        {"preferences": {"patient_id": "PRIVATE_SENTINEL"}},
                        {"preferences": {"location": "PRIVATE_SENTINEL"}},
                        {"intent": "confirm"}, {"workflow": "PRIVATE_SENTINEL"},
                        [], "PRIVATE_SENTINEL"]
        for context in bad_contexts:
            adapter, transport = self.adapter()
            self.assert_closed_failure(adapter.interpret("Find providers", context), "invalid_context")
            self.assertEqual(transport.calls, [])

    def test_invalid_or_excessive_input_stops_before_transport(self):
        for text in (None, True, [], "", "   ", "x" * 2049, "é" * 1025, "hi\x00"):
            adapter, transport = self.adapter()
            self.assert_closed_failure(adapter.interpret(text), "invalid_input")
            self.assertEqual(transport.calls, [])

    def test_authority_and_unknown_fields_are_rejected_at_both_levels(self):
        fields = ("identity", "phone", "dob", "zip", "patient_id", "slot_id", "provider_id",
                  "confirmed", "confirmation", "consent", "allow", "tools", "tool_call",
                  "receipt", "message", "instructions")
        for field in fields:
            for nested in (False, True):
                value = proposal()
                (value["preferences"] if nested else value)[field] = "PRIVATE_SENTINEL"
                adapter, _ = self.adapter(response(value))
                self.assert_closed_failure(adapter.interpret("Find providers"), "invalid_output")
        for action in ("booking", "book", "confirm", "handoff", "identity", "select", "reset", True, None):
            adapter, _ = self.adapter(response(proposal(action)))
            self.assert_closed_failure(adapter.interpret("yes"), "invalid_output")

    def test_wrong_shapes_types_values_and_dates_are_rejected(self):
        values = [{}, [], {"action": "discover"}, {"preferences": {}},
                  {"action": "discover", "preferences": []},
                  proposal(location=True), proposal(specialty="cardiology"),
                  proposal(start_date="2026-02-30"), proposal(start_date="20261020"),
                  proposal(start_date="2026-11-01", end_date="2026-10-01")]
        for value in values:
            adapter, _ = self.adapter(response(text=json.dumps(value)))
            self.assert_closed_failure(adapter.interpret("Find providers"), "invalid_output")

    def test_duplicate_keys_nonfinite_trailing_and_code_fenced_json_are_rejected(self):
        for text in ('{"action":"discover","action":"help","preferences":{}}',
                     '{"action":"discover","preferences":{"location":NaN}}',
                     '```json\n{"action":"help","preferences":{}}\n```',
                     '{"action":"help","preferences":{}} trailing',
                     '["x"]', '{"action":"help","preferences":{"location":"uptown","location":"downtown"}}'):
            adapter, _ = self.adapter(response(text=text))
            self.assert_closed_failure(adapter.interpret("help"), "invalid_output")

    def test_invented_preferences_require_clarification(self):
        for preferences in ({"location": "uptown"}, {"specialty": "dermatology"},
                            {"start_date": "2026-10-20"}):
            adapter, _ = self.adapter(response(proposal(**preferences)))
            self.assert_closed_failure(adapter.interpret("Find providers"), "clarification")
        adapter, _ = self.adapter(response(proposal(location="uptown")))
        self.assertEqual(adapter.interpret("Show more", {"preferences": {"location": "uptown"}}).status, "ok")
        adapter, _ = self.adapter(response(proposal(specialty="primary_care")))
        self.assertEqual(adapter.interpret("Find a family doctor").status, "ok")

    def test_refusal_incomplete_and_tool_outputs_are_not_proposals(self):
        for status in ("incomplete", "failed", "queued", "in_progress"):
            adapter, _ = self.adapter(response(status=status))
            self.assert_closed_failure(adapter.interpret("Find providers"), "invalid_output")
        adapter, _ = self.adapter(response(output=[{"type": "message", "role": "assistant",
                    "content": [{"type": "refusal", "refusal": "PRIVATE_SENTINEL"}]}]))
        self.assert_closed_failure(adapter.interpret("Find providers"), "refused")
        for output in ([{"type": "function_call", "arguments": "PRIVATE_SENTINEL"}], [],
                       [{"type": "reasoning", "summary": []}]):
            adapter, _ = self.adapter(response(output=output))
            self.assert_closed_failure(adapter.interpret("Find providers"), "invalid_output")

    def test_reasoning_item_before_one_message_is_not_used_as_text(self):
        envelope = json.loads(response())
        envelope["output"].insert(0, {"type": "reasoning", "summary": []})
        adapter, _ = self.adapter(json.dumps(envelope).encode())
        self.assertEqual(adapter.interpret("Find providers").status, "ok")

    def test_timeouts_and_transport_errors_are_sanitized_without_retry(self):
        for error, status in ((TimeoutError("PRIVATE_SENTINEL"), "timeout"),
                              (OSError("PRIVATE_SENTINEL"), "unavailable"),
                              (RuntimeError("PRIVATE_SENTINEL"), "unavailable")):
            adapter, transport = self.adapter(error=error)
            self.assert_closed_failure(adapter.interpret("Find providers"), status)
            self.assertEqual(len(transport.calls), 1)

    def test_late_fixture_response_is_timeout_instead_of_a_proposal(self):
        clock = [0.0]
        calls = []

        def late(payload, **options):
            calls.append(payload)
            clock[0] = 11.0
            return response()

        with patch.object(self.module.time, "monotonic", side_effect=lambda: clock[0]):
            result = self.module.LanguageAdapter(transport=late, environ=ENV).interpret("Find providers")
        self.assert_closed_failure(result, "timeout")
        self.assertEqual(len(calls), 1)

    def test_body_and_output_bounds_are_enforced_even_for_fake_transport(self):
        for body in (b"x" * 65537, response(text="x" * 4097), b"\xff", b"{", None):
            # None as a returned body, rather than FakeTransport's default.
            adapter, transport = self.adapter()
            transport.body = body
            self.assert_closed_failure(adapter.interpret("Find providers"), "invalid_output")
            self.assertEqual(len(transport.calls), 1)

    def test_timeout_configuration_is_finite_and_bounded(self):
        for timeout in (0, -1, True, float("inf"), float("nan"), 31, "10"):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.module.LanguageAdapter(timeout=timeout)

    def test_malformed_config_is_disabled_without_echoing_or_network(self):
        for key, value in (("BOB_OPENAI_MODEL", "PRIVATE_SENTINEL\r\n"),
                           ("OPENAI_API_KEY", "PRIVATE_SENTINEL\r\n"),
                           ("BOB_OPENAI_MODEL", "x" * 129)):
            adapter, transport = self.adapter(environ={**ENV, key: value})
            self.assert_closed_failure(adapter.interpret("Find providers"), "disabled")
            self.assertEqual(transport.calls, [])

    def test_r15_manifest_is_pending_synthetic_and_covers_required_families(self):
        manifest = json.loads((ROOT / "tests" / "live_model_cases.json").read_text())
        self.assertEqual(manifest["qualification"], "pending")
        self.assertIs(manifest["synthetic_only"], True)
        self.assertEqual({case["family"] for case in manifest["cases"]},
                         {"paraphrase", "typo", "mixed_correction", "refusal", "privacy", "authority"})
        self.assertEqual(len({case["id"] for case in manifest["cases"]}), len(manifest["cases"]))
        # Fake outputs prove harness contracts, not genuine classification.
        for case in manifest["cases"]:
            adapter, transport = self.adapter(response(case["candidate"]))
            result = adapter.interpret(case["text"], case["context"])
            self.assertEqual(result.status, case["expected_status"], case["id"])
            if result.status == "ok":
                self.assertEqual(result.action, case["expected_action"], case["id"])
            if result.status == "private_input":
                self.assertEqual(transport.calls, [])


class FakeResponse:
    def __init__(self, body, *, status=200, headers=None):
        self.body = body
        self.status = status
        self.headers = {"Content-Type": "application/json", **(headers or {})}
        self.read_sizes = []

    def getheader(self, name, default=None):
        return self.headers.get(name, default)

    def read1(self, size):
        self.read_sizes.append(size)
        part, self.body = self.body[:size], self.body[size:]
        return part


class HttpTransportTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.language"),
                             "Bounded language adapter is missing")
        self.module = importlib.import_module("ochsner_bob.language")

    def run_http(self, reply):
        with patch.object(self.module.http.client, "HTTPSConnection") as factory:
            factory.return_value.getresponse.return_value = reply
            adapter = self.module.LanguageAdapter(environ=ENV)
            result = adapter.interpret("Find providers")
        return result, factory

    def test_real_http_path_uses_one_fixed_https_post_and_closes(self):
        result, factory = self.run_http(FakeResponse(response()))
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.mode, "openai")
        self.assertEqual(factory.call_args.args, ("api.openai.com",))
        self.assertEqual(factory.call_count, 1)
        connection = factory.return_value
        args, kwargs = connection.request.call_args
        self.assertEqual(args[:2], ("POST", "/v1/responses"))
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer " + ENV["OPENAI_API_KEY"])
        self.assertEqual(json.loads(kwargs["body"])["model"], "test-model")
        connection.close.assert_called_once()

    def test_redirects_http_errors_and_non_json_are_never_followed_or_retried(self):
        replies = [FakeResponse(b"PRIVATE_SENTINEL", status=status)
                   for status in (301, 302, 307, 401, 429, 500)]
        replies += [FakeResponse(b"PRIVATE_SENTINEL", headers={"Content-Type": "text/html"}),
                    FakeResponse(response(), headers={"Content-Encoding": "gzip"})]
        for reply in replies:
            result, factory = self.run_http(reply)
            self.assertEqual(result.status, "unavailable")
            self.assertIsNone(result.action)
            self.assertNotIn("PRIVATE_SENTINEL", repr(result))
            self.assertEqual(factory.return_value.request.call_count, 1)
            self.assertEqual(reply.read_sizes, [])
            factory.return_value.close.assert_called_once()

    def test_stream_read_has_byte_and_deadline_bounds(self):
        reply = FakeResponse(b"x" * 70000)
        result, factory = self.run_http(reply)
        self.assertEqual(result.status, "invalid_output")
        self.assertEqual(sum(reply.read_sizes), 65537)
        self.assertTrue(all(size <= 8192 for size in reply.read_sizes))
        self.assertTrue(factory.return_value.sock.settimeout.called)
        factory.return_value.close.assert_called_once()

    def test_total_deadline_expiry_cannot_return_a_proposal(self):
        with patch.object(self.module.time, "monotonic", side_effect=[0, 0, 0, 11]), \
                patch.object(self.module.http.client, "HTTPSConnection") as factory:
            result = self.module.LanguageAdapter(environ=ENV).interpret("Find providers")
        self.assertEqual(result.status, "timeout")
        self.assertIsNone(result.action)
        factory.return_value.close.assert_called_once()

    def test_mismatched_declared_body_length_is_not_a_valid_response(self):
        body = response()
        result, factory = self.run_http(FakeResponse(body, headers={"Content-Length": str(len(body) + 3)}))
        self.assertEqual(result.status, "invalid_output")
        self.assertIsNone(result.action)
        factory.return_value.close.assert_called_once()

    def test_complete_length_delimited_response_can_close_its_socket(self):
        body = response()
        reply = FakeResponse(body, headers={"Content-Length": str(len(body))})
        closed = [False]
        original_read = reply.read1

        def read1(size):
            part = original_read(size)
            if not reply.body:
                closed[0] = True
            return part

        def settimeout(_):
            if closed[0]:
                raise OSError("completed response closed its socket")

        reply.read1 = read1
        with patch.object(self.module.http.client, "HTTPSConnection") as factory:
            factory.return_value.getresponse.return_value = reply
            factory.return_value.sock.settimeout.side_effect = settimeout
            result = self.module.LanguageAdapter(environ=ENV).interpret("Find providers")
        self.assertEqual(result.status, "ok")
        self.assertEqual(result.action, "discover")
        factory.return_value.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()
