"""Offline reservation, accounting and qualification-runner contracts. No paid calls."""
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import runpy
import stat
import tempfile
import unittest
from unittest.mock import patch

from test_language import FakeTransport, proposal, response


ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-5.4-mini-2026-03-17"
STRONGER = "gpt-5.4-2026-03-05"
ENV = {"BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": MODEL,
       "OPENAI_API_KEY": "synthetic-test-credential"}


def usage(**changes):
    return {"input_tokens": 1000, "output_tokens": 100,
            "cached_input_tokens": 200, "reasoning_output_tokens": 0, **changes}


def billed_response(value=None, **changes):
    envelope = json.loads(response(value))
    envelope.update(model=MODEL, service_tier="default", usage={
        "input_tokens": 1000, "output_tokens": 100, "total_tokens": 1100,
        "input_tokens_details": {"cached_tokens": 200},
        "output_tokens_details": {"reasoning_tokens": 0}})
    envelope.update(changes)
    return json.dumps(envelope).encode()


class ModelBudgetTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.model_budget"),
                             "Durable pre-dispatch budget is missing")
        self.module = importlib.import_module("ochsner_bob.model_budget")
        self.Error = self.module.BudgetError
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "budget.json"

    def budget(self, **options):
        return self.module.ModelBudget(self.path, **options)

    def test_exact_snapshot_rates_and_conservative_maximum(self):
        self.assertEqual(self.module.DEFAULT_MODEL, MODEL)
        budget = self.budget()
        receipt = budget.reserve(model=MODEL, max_output_tokens=512)
        self.assertEqual(receipt, 1)
        view = budget.snapshot()
        self.assertEqual(view["calls"], 1)
        self.assertEqual(view["unknown_calls"], 1)
        self.assertEqual(view["known_cost_usd"], "0.000000000")
        # Full 400k context at uncached input rate, plus the bounded output.
        self.assertEqual(view["liability_usd"], "0.302304000")

    def test_price_verified_stronger_snapshot_shares_same_caps_and_ledger(self):
        budget = self.budget()
        budget.reserve(model=MODEL,max_output_tokens=512)
        reservation = budget.reserve(model=STRONGER,max_output_tokens=512)
        self.assertEqual(budget.snapshot()["liability_usd"],"5.563824000")
        receipt = budget.settle(reservation,usage())
        self.assertEqual(receipt["cost_usd"],"0.003550000")
        reopened = self.budget().snapshot()
        self.assertEqual((reopened["calls"],reopened["unknown_calls"]),(2,1))
        self.assertEqual(reopened["liability_usd"],"0.305854000")

    def test_long_context_uplift_is_reserved_and_accounted_conservatively(self):
        budget = self.budget()
        reservation = budget.reserve(model=STRONGER,max_output_tokens=512)
        self.assertEqual(budget.snapshot()["liability_usd"],"5.261520000")
        # Official full-request >272k uplift; this boundary case has no cache.
        result = budget.settle(reservation,usage(input_tokens=300000,cached_input_tokens=0))
        self.assertEqual(result["cost_usd"],"1.502250000")

    def test_actual_usage_settles_once_without_refunding_call_count(self):
        budget = self.budget(max_calls=1)
        reservation = budget.reserve(model=MODEL, max_output_tokens=512)
        settled = budget.settle(reservation, usage())
        self.assertEqual(settled["cost_usd"], "0.001065000")
        view = self.budget(max_calls=1).snapshot()
        self.assertEqual(view["known_calls"], 1)
        self.assertEqual(view["input_tokens"], 1000)
        self.assertEqual(view["cached_input_tokens"], 200)
        self.assertEqual(view["output_tokens"], 100)
        self.assertEqual(view["liability_usd"], "0.001065000")
        with self.assertRaises(self.Error):
            budget.settle(reservation, usage())
        with self.assertRaises(self.Error):
            budget.reserve(model=MODEL, max_output_tokens=512)

    def test_unknown_and_crash_reservations_never_refund_on_restart(self):
        budget = self.budget()
        reservation = budget.reserve(model=MODEL, max_output_tokens=512)
        budget.settle(reservation, None)
        budget.reserve(model=MODEL, max_output_tokens=512)  # Simulated crash before settlement.
        view = self.budget().snapshot()
        self.assertEqual((view["calls"], view["unknown_calls"]), (2, 2))
        self.assertEqual(view["liability_usd"], "0.604608000")
        with self.assertRaises(self.Error):
            budget.settle(reservation, usage())

    def test_dollar_ceiling_is_checked_before_issuing_a_reservation(self):
        budget = self.budget(ceiling_usd="0.302304")
        budget.reserve(model=MODEL, max_output_tokens=512)
        before = self.path.read_bytes()
        with self.assertRaises(self.Error):
            budget.reserve(model=MODEL, max_output_tokens=512)
        self.assertEqual(self.path.read_bytes(), before)

    def test_all_200_settled_calls_count_against_grant(self):
        budget = self.budget()
        for index in range(200):
            reservation = budget.reserve(model=MODEL, max_output_tokens=512)
            self.assertEqual(reservation, index + 1)
            budget.settle(reservation, usage(input_tokens=1, cached_input_tokens=0, output_tokens=1))
        with self.assertRaises(self.Error):
            self.budget().reserve(model=MODEL, max_output_tokens=512)
        self.assertEqual(budget.snapshot()["calls"], 200)

    def test_reservation_syncs_before_return_and_failed_directory_sync_retains_charge(self):
        budget = self.budget()
        with patch.object(self.module.EffectJournal,"_sync_directory",side_effect=OSError("PRIVATE_SENTINEL")):
            with self.assertRaises(self.Error):
                budget.reserve(model=MODEL,max_output_tokens=512)
        # Replace happened; fsync failure does not authorize dispatch or refund.
        view = self.budget().snapshot()
        self.assertEqual((view["calls"],view["unknown_calls"]),(1,1))

    def test_shared_instances_concurrently_obey_one_call_limit(self):
        first, second = self.budget(max_calls=1), self.budget(max_calls=1)
        def reserve(budget):
            try:
                return budget.reserve(model=MODEL, max_output_tokens=512)
            except self.Error:
                return None
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(reserve, (first, second)))
        self.assertEqual(results.count(1), 1)
        self.assertEqual(self.budget(max_calls=1).snapshot()["calls"], 1)

    def test_hard_grant_limits_and_unpriced_models_fail_closed(self):
        for options in ({"max_calls":201}, {"max_calls":True}, {"max_calls":0},
                        {"ceiling_usd":"20.000001"}, {"ceiling_usd":"NaN"},
                        {"ceiling_usd":"-1"}):
            with self.subTest(options=options), self.assertRaises(self.Error):
                self.budget(**options)
        budget = self.budget()
        for model, output in (("unknown-model",512), (MODEL,0), (MODEL,True), (MODEL,513)):
            with self.subTest(model=model, output=output), self.assertRaises(self.Error):
                budget.reserve(model=model, max_output_tokens=output)
        self.assertEqual(budget.snapshot()["calls"], 0)

    def test_malformed_or_over_bound_usage_retains_full_reservation(self):
        values = [usage(input_tokens=True), usage(output_tokens=513), usage(input_tokens=400001),
                  usage(cached_input_tokens=1001), usage(reasoning_output_tokens=101),
                  usage(extra="PRIVATE_SENTINEL"), {}, usage(output_tokens=-1)]
        budget = self.budget()
        for value in values:
            reservation = budget.reserve(model=MODEL, max_output_tokens=512)
            result = budget.settle(reservation, value)
            self.assertEqual(result["status"], "unknown")
            self.assertNotIn("PRIVATE_SENTINEL", repr(result))
        self.assertEqual(budget.snapshot()["unknown_calls"], len(values))

    def test_private_storage_and_minimal_metadata(self):
        directory = Path(self.temp.name) / "new-private"
        budget = self.module.ModelBudget(directory / "budget.json")
        reservation = budget.reserve(model=MODEL, max_output_tokens=512)
        budget.settle(reservation, usage())
        self.assertEqual(stat.S_IMODE(directory.stat().st_mode), 0o700)
        self.assertEqual(stat.S_IMODE(budget.path.stat().st_mode), 0o600)
        raw = budget.path.read_text()
        for value in ("OPENAI_API_KEY", "synthetic-test-credential", "prompt", "response", "text"):
            self.assertNotIn(value, raw)

    def test_missing_and_corrupt_state_are_not_reset(self):
        budget = self.budget()
        budget.reserve(model=MODEL, max_output_tokens=512)
        original = self.path.read_bytes()
        for raw in (None, b'PRIVATE_SENTINEL', b'{"version":1,"version":1}',
                    b'{"version":1,"calls":[],"extra":true}'):
            with self.subTest(raw=raw):
                self.path.write_bytes(original)
                self.path.chmod(0o600)
                if raw is None:
                    self.path.unlink()
                else:
                    self.path.write_bytes(raw)
                with self.assertRaises(self.Error) as caught:
                    self.budget()
                self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
                if raw is not None:
                    self.assertEqual(self.path.read_bytes(), raw)

    def test_symlink_hardlink_permissions_and_lock_tampering_fail_closed(self):
        budget = self.budget()
        original = self.path.read_bytes()
        target = Path(self.temp.name) / "target"
        target.write_bytes(original)
        target.chmod(0o600)
        for kind in ("symlink", "hardlink", "permissions"):
            with self.subTest(kind=kind):
                self.path.unlink()
                if kind == "symlink":
                    self.path.symlink_to(target)
                elif kind == "hardlink":
                    os.link(target, self.path)
                else:
                    self.path.write_bytes(original)
                    self.path.chmod(0o644)
                with self.assertRaises(self.Error):
                    self.budget()
                self.assertEqual(target.read_bytes(), original)
        self.path.chmod(0o600)
        lock = self.path.with_name(self.path.name + ".lock")
        lock.write_bytes(b"corrupt")
        with self.assertRaises(self.Error):
            budget.reserve(model=MODEL, max_output_tokens=512)

    def test_persistence_failure_never_authorizes_dispatch(self):
        budget = self.budget()
        before = self.path.read_bytes()
        with patch.object(self.module.os, "replace", side_effect=OSError("PRIVATE_SENTINEL")):
            with self.assertRaises(self.Error) as caught:
                budget.reserve(model=MODEL, max_output_tokens=512)
        self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
        self.assertEqual(self.path.read_bytes(), before)
        self.assertEqual(self.budget().snapshot()["calls"], 0)

    def test_configuration_cannot_enlarge_an_existing_budget(self):
        self.budget(max_calls=1, ceiling_usd="1")
        with self.assertRaises(self.Error):
            self.budget()


class AdapterBudgetTests(unittest.TestCase):
    def setUp(self):
        self.language = importlib.import_module("ochsner_bob.language")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)

    def test_budget_hook_is_called_before_transport_and_receives_only_usage(self):
        events = []
        class Hook:
            def reserve(self, **kwargs):
                events.append(("reserve", kwargs))
                return 1
            def settle(self, reservation, value):
                events.append(("settle", reservation, value))
                return {"status":"known", "cost_usd":"0.001065000"}
        def fake(payload, **kwargs):
            events.append(("transport", json.loads(payload)))
            return billed_response()
        adapter = self.language.LanguageAdapter(transport=fake, environ=ENV, budget=Hook())
        result = adapter.interpret("Find providers")
        self.assertEqual(result.mode, "fixture")
        self.assertEqual(result.status, "ok")
        self.assertEqual([event[0] for event in events], ["reserve", "transport", "settle"])
        self.assertEqual(events[0][1], {"model":MODEL, "max_output_tokens":512})
        self.assertEqual(events[2][2], usage())
        self.assertEqual(result.usage, usage())
        self.assertEqual(result.accounting_status, "known")
        self.assertNotIn("synthetic-test-credential", repr(result))
        self.assertEqual(events[1][1]["service_tier"], "default")
        self.assertFalse(events[1][1]["store"])
        self.assertEqual(events[1][1]["tools"], [])

    def test_budget_denial_and_private_rejection_never_dispatch(self):
        class Hook:
            def reserve(self, **kwargs):
                raise RuntimeError("PRIVATE_SENTINEL")
        transport = FakeTransport()
        adapter = self.language.LanguageAdapter(transport=transport, environ=ENV, budget=Hook())
        self.assertEqual(adapter.interpret("Find providers").status, "budget_exceeded")
        self.assertEqual(adapter.interpret("my phone is 555-0130").status, "private_input")
        self.assertEqual(transport.calls, [])

    def test_timeout_unknown_usage_and_settlement_failure_never_refund_or_expose(self):
        module = importlib.import_module("ochsner_bob.model_budget")
        budget = module.ModelBudget(Path(self.temp.name) / "budget.json")
        for body, error, status in ((None,TimeoutError("PRIVATE_SENTINEL"),"timeout"),
                                    (billed_response(usage=None),None,"ok"),
                                    (billed_response(status="incomplete"),None,"invalid_output")):
            adapter = self.language.LanguageAdapter(transport=FakeTransport(body,error), environ=ENV, budget=budget)
            result = adapter.interpret("Find providers")
            self.assertEqual(result.status, status)
            self.assertNotIn("PRIVATE_SENTINEL", repr(result))
        view = budget.snapshot()
        self.assertEqual((view["calls"],view["unknown_calls"],view["known_calls"]), (3,2,1))
        with patch.object(budget,"settle",side_effect=RuntimeError("PRIVATE_SENTINEL")):
            result = self.language.LanguageAdapter(transport=FakeTransport(billed_response()),environ=ENV,budget=budget).interpret("Find providers")
        self.assertEqual(result.status,"accounting_failed")
        self.assertIsNone(result.action)
        self.assertNotIn("PRIVATE_SENTINEL",repr(result))
        self.assertEqual(budget.snapshot()["unknown_calls"],3)

    def test_wrong_model_tier_or_malformed_usage_stays_unknown(self):
        module = importlib.import_module("ochsner_bob.model_budget")
        budget = module.ModelBudget(Path(self.temp.name) / "budget.json")
        for changes in ({"model":"unexpected"}, {"service_tier":"priority"},
                        {"usage":{"input_tokens":True,"output_tokens":1,"total_tokens":2}}):
            result = self.language.LanguageAdapter(transport=FakeTransport(billed_response(**changes)),environ=ENV,budget=budget).interpret("Find providers")
            self.assertEqual(result.accounting_status,"unknown")
            self.assertIsNone(result.usage)
        self.assertEqual(budget.snapshot()["unknown_calls"],3)

    def test_hook_receipt_cannot_echo_unrestricted_cost_or_fake_known_usage(self):
        class Hook:
            def reserve(self, **kwargs):
                return 1
            def settle(self, reservation, value):
                return {"status":"known", "cost_usd":"PRIVATE_SENTINEL"}
        result = self.language.LanguageAdapter(transport=FakeTransport(billed_response()),environ=ENV,budget=Hook()).interpret("Find providers")
        self.assertEqual(result.status,"accounting_failed")
        self.assertNotIn("PRIVATE_SENTINEL",repr(result))

    def test_full_responses_envelope_echoing_schema_accepts_output_and_billing(self):
        def official_shape(payload, **kwargs):
            envelope = json.loads(billed_response())
            # Responses returns the request text-format metadata, including
            # nested JSON-schema enums. This is not nested model output.
            envelope["text"] = json.loads(payload)["text"]
            return json.dumps(envelope).encode()
        result = self.language.LanguageAdapter(transport=official_shape,environ=ENV).interpret("Find providers")
        self.assertEqual(result.status,"ok")
        self.assertEqual(result.usage,usage())

    def test_request_distinguishes_history_and_correction_only_routes(self):
        fake = FakeTransport(billed_response())
        adapter = self.language.LanguageAdapter(transport=fake,environ=ENV)
        adapter.interpret("What appointments do I already have?")
        adapter.interpret("Instead use 2026-10-20 through 2026-10-22",{"workflow":"providers"})
        for payload, *_ in fake.calls:
            self.assertIn("appointments means existing appointment history",payload["instructions"])
            self.assertIn("Use preferences for correction-only requests",payload["instructions"])

    def test_stronger_model_cost_over_one_dollar_is_not_an_accounting_failure(self):
        module = importlib.import_module("ochsner_bob.model_budget")
        budget = module.ModelBudget(Path(self.temp.name) / "strong-budget.json")
        body = billed_response(model=STRONGER,usage={"input_tokens":300000,"output_tokens":100,
            "total_tokens":300100,"input_tokens_details":{"cached_tokens":0},
            "output_tokens_details":{"reasoning_tokens":0}})
        result = self.language.LanguageAdapter(transport=FakeTransport(body),
            environ={**ENV,"BOB_OPENAI_MODEL":STRONGER},budget=budget).interpret("Find providers")
        self.assertEqual(result.status,"ok")
        self.assertEqual(result.cost_usd,"1.502250000")

    def test_runner_accepts_only_price_verified_model_override(self):
        from test_qualification_policy import isolated_runner
        runner, root = isolated_runner(self.temp.name)
        ledger = root / ".bob-local/model-budget.json"
        importlib.import_module("ochsner_bob.model_budget").ModelBudget(ledger, application_runtime=True)
        original = self.language.LanguageAdapter
        def offline_adapter(**options):
            return original(transport=FakeTransport(billed_response(model=STRONGER)),**options)
        output = io.StringIO()
        with patch.dict(os.environ,ENV),patch.dict(runner["main"].__globals__,{"LanguageAdapter":offline_adapter,
                "resolve_qualification_key":lambda:ENV["OPENAI_API_KEY"]}),patch("sys.stdout",output):
            code = runner["main"](["--run-live","--model",STRONGER])
        self.assertEqual(code,1)  # Fixtures cannot qualify, even matching semantics.
        self.assertEqual(json.loads(output.getvalue())["model"],STRONGER)

    def test_runner_uses_real_default_and_does_not_reuse_fake_expected_output(self):
        runner = runpy.run_path(str(ROOT / "scripts/qualify_live.py"), run_name="qualification_test")
        language = self.language
        result = language.LanguageOutcome("ok","openai","clarify",{},"public")
        case = json.loads((ROOT / "tests/live_model_cases.json").read_text())["cases"][3]
        self.assertTrue(runner["assess"](case,result)["semantic_pass"])
        self.assertFalse(runner["assess"](case,result)["fixture_exact_match"])
        authority = json.loads((ROOT / "tests/live_model_cases.json").read_text())["cases"][10]
        result = language.LanguageOutcome("ok","openai","clarify",{},"public")
        self.assertTrue(runner["assess"](authority,result)["semantic_pass"])
        self.assertFalse(runner["assess"](case,language.LanguageOutcome("unavailable","openai"))["semantic_pass"])

    def test_runner_preserves_evidenced_location_while_clarifying_typo(self):
        runner = runpy.run_path(str(ROOT / "scripts/qualify_live.py"), run_name="qualification_test")
        case = json.loads((ROOT / "tests/live_model_cases.json").read_text())["cases"][2]
        result = self.language.LanguageOutcome("ok","openai","clarify",{"location":"uptown"})
        self.assertTrue(runner["assess"](case,result)["semantic_pass"])

    def test_runner_stops_after_unknown_billing_without_retry(self):
        from test_qualification_policy import isolated_runner
        runner, root = isolated_runner(self.temp.name)
        importlib.import_module("ochsner_bob.model_budget").ModelBudget(root / ".bob-local/model-budget.json", application_runtime=True)
        original = self.language.LanguageAdapter
        def offline_adapter(**options):
            return original(transport=FakeTransport(),**options)
        output = io.StringIO()
        with patch.dict(os.environ,ENV), patch.dict(runner["main"].__globals__,{"LanguageAdapter":offline_adapter,
                "resolve_qualification_key":lambda:ENV["OPENAI_API_KEY"]}), patch("sys.stdout",output):
            code = runner["main"](["--run-live"])
        self.assertEqual(code,1)
        report = json.loads(output.getvalue())
        self.assertEqual(report["cases_run"],1)
        self.assertEqual(report["calls_this_run"],1)
        self.assertNotIn("synthetic-test-credential",output.getvalue())


if __name__ == "__main__":
    unittest.main()
