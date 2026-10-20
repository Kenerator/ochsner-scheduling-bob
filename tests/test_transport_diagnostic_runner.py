"""Execute diagnostic gates using disposable existing SQLite and fake HTTPS only."""
import contextlib
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.model_budget import ModelBudget
from scripts import qualify_connected_live as policy
from test_language import FakeResponse, response


class DiagnosticRunnerTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("scripts.diagnose_language_transport"),
                             "Missing single-request transport diagnostic runner")
        self.runner = importlib.import_module("scripts.diagnose_language_transport")
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="transport-diagnosis-"))).resolve()
        self.owner = self.directory / "owner"
        self.owner.mkdir()
        (self.owner / ".git").mkdir()
        (self.owner / "poc-launch.json").write_bytes((policy.ROOT / "poc-launch.json").read_bytes())
        self.ledger = self.owner / ".bob-local/model-budget.json"
        self.budget = ModelBudget(self.ledger, application_runtime=True)
        old = self.budget.reserve(model=policy.MODEL)
        self.budget.settle(old, None)
        self.output_root = self.directory / "candidate"
        self.output = self.output_root / "tmp/connected-qualification"
        self.output.mkdir(mode=0o700, parents=True)
        self.old_report = self.output / "run.json"
        self.old_report.write_bytes(b"retained failed tranche")
        self.enterContext(patch.object(self.runner, "ROOT", self.output_root))
        self.enterContext(patch.object(policy, "_APPROVED_OWNER_ROOT", self.owner))
        self.enterContext(patch.dict(os.environ, {"BOB_ENABLE_OPENAI": "1"}))
        self.helper = self.enterContext(patch.object(policy, "resolve_qualification_key", return_value="synthetic"))
        self.factory = self.enterContext(patch("http.client.HTTPSConnection"))
        self.reply = FakeResponse(b"SENSITIVE_CANARY", status=400)
        self.factory.return_value.getresponse.return_value = self.reply
        # A runner that accidentally reuses the full journey path fails locally.
        self.enterContext(patch.object(policy, "run_schedule", side_effect=AssertionError("no scheduling")))
        self.stdout = self.enterContext(contextlib.redirect_stdout(io.StringIO()))

    def run_live(self, digest=None):
        _hashes, plan = self.runner.diagnostic_plan()
        return self.runner.main(["--run-live", "--source-digest", plan["source_digest"] if digest is None else digest])

    def report(self):
        paths = list(self.output.glob("transport-diagnostic-*.json"))
        self.assertEqual(len(paths), 1)
        self.assertEqual(paths[0].stat().st_mode & 0o777, 0o600)
        return json.loads(paths[0].read_text())

    def test_dry_run_is_owner_key_network_and_write_free(self):
        before = self.ledger.read_bytes()
        with patch.object(policy, "canonical_binding", side_effect=AssertionError("owner touched")):
            self.assertEqual(self.runner.main(["--dry-run"]), 0)
        self.assertEqual(self.ledger.read_bytes(), before)
        self.assertEqual(list(self.output.glob("transport-diagnostic-*.json")), [])
        self.helper.assert_not_called()
        self.factory.assert_not_called()
        plan = json.loads(self.stdout.getvalue())["plan"]
        self.assertEqual((plan["maximum_language_calls"], plan["max_output_tokens"], plan["timeout_seconds"],
                          plan["max_input_bytes"], plan["max_request_bytes"], plan["max_response_bytes"],
                          plan["tools"], plan["retries"], plan["scheduling_http"]),
                         (1, 512, 10, 2048, 16384, 65536, [], 0, 0))

    def test_one_400_is_unknown_and_exclusive_report_blocks_a_second_request(self):
        inode = self.ledger.stat().st_ino
        lock = self.ledger.with_name(self.ledger.name + ".lock")
        lock_before = (lock.stat().st_ino, lock.read_bytes())
        self.assertEqual(self.run_live(), 1)
        evidence = self.report()
        self.assertEqual((evidence["outcome"]["status"], evidence["outcome"]["accounting_status"]), ("unavailable", "unknown"))
        self.assertEqual(evidence["transport"], {"category": "http_error", "http_status": 400})
        self.assertEqual(evidence["calls_this_run"], 1)
        self.assertEqual(evidence["accounting_after"]["unknown_calls"], 2)
        self.assertEqual(evidence["semantic_qualification"], "not_run")
        self.assertEqual(evidence["scheduling_http"], 0)
        self.assertNotIn("SENSITIVE_CANARY", json.dumps(evidence) + self.stdout.getvalue())
        self.assertEqual(self.run_live(), 2)
        self.assertEqual(self.factory.return_value.request.call_count, 1)
        self.assertEqual(self.helper.call_count, 1)
        self.assertEqual(self.reply.read_sizes, [])
        self.assertEqual(self.old_report.read_bytes(), b"retained failed tranche")
        self.assertEqual(self.ledger.stat().st_ino, inode)
        self.assertEqual((lock.stat().st_ino, lock.read_bytes()), lock_before)
        self.assertEqual(self.budget.snapshot()["calls"], 2)

    def test_success_is_transport_diagnosis_not_a_scheduling_or_holdout_pass(self):
        body = json.loads(response())
        body.update(model=policy.MODEL, service_tier="default", usage={"input_tokens": 10, "output_tokens": 5,
            "total_tokens": 15, "input_tokens_details": {"cached_tokens": 0},
            "output_tokens_details": {"reasoning_tokens": 0}})
        self.factory.return_value.getresponse.return_value = FakeResponse(json.dumps(body).encode())
        self.assertEqual(self.run_live(), 0)
        evidence = self.report()
        self.assertEqual(evidence["transport"], {"category": "success", "http_status": 200})
        self.assertEqual(evidence["outcome"]["accounting_status"], "known")
        self.assertEqual(evidence["outcome"]["cost_usd"], "0.000100000")
        self.assertNotIn("action", evidence["outcome"])
        self.assertNotIn("preferences", evidence["outcome"])
        self.assertEqual(evidence["semantic_qualification"], "not_run")
        self.assertEqual(self.budget.snapshot()["unknown_calls"], 1)
        request = json.loads(self.factory.return_value.request.call_args.kwargs["body"])
        self.assertEqual((request["model"], request["tools"], request["max_output_tokens"]), (policy.MODEL, [], 512))

    def test_wrong_digest_and_missing_opt_in_stop_before_owner_or_helper(self):
        with patch.object(policy, "canonical_binding", side_effect=AssertionError("owner touched")):
            self.assertEqual(self.run_live("not-selected"), 2)
            with patch.dict(os.environ, {"BOB_ENABLE_OPENAI": "0"}):
                self.assertEqual(self.run_live(), 2)
        self.helper.assert_not_called()
        self.factory.assert_not_called()
        self.assertEqual(list(self.output.glob("transport-diagnostic-*.json")), [])

    def test_missing_lock_stops_before_helper_reserve_or_report(self):
        lock = self.ledger.with_name(self.ledger.name + ".lock")
        lock.unlink()
        self.assertEqual(self.run_live(), 2)
        self.helper.assert_not_called()
        self.factory.assert_not_called()
        self.assertEqual(list(self.output.glob("transport-diagnostic-*.json")), [])
        self.assertFalse(lock.exists())

    def test_public_source_drift_after_binding_blocks_helper(self):
        original = policy.source_hashes
        hashes = original()
        changed = {**hashes, "poc-launch.json": "changed"}
        digest = self.runner.diagnostic_plan()[1]["source_digest"]
        with patch.object(policy, "source_hashes", side_effect=[hashes, changed]):
            self.assertEqual(self.runner.main(["--run-live", "--source-digest", digest]), 2)
        self.helper.assert_not_called()
        self.factory.assert_not_called()
        self.assertEqual(self.budget.snapshot()["calls"], 1)

    def test_helper_failure_checkpoints_incomplete_once_without_raw_message(self):
        self.helper.side_effect = RuntimeError("SENSITIVE_CANARY")
        self.assertEqual(self.run_live(), 2)
        evidence = self.report()
        self.assertEqual(evidence["status"], "failed_or_incomplete")
        self.assertEqual(evidence["transport"], {"category": "not_requested", "http_status": None})
        self.assertNotIn("SENSITIVE_CANARY", json.dumps(evidence) + self.stdout.getvalue())
        self.assertEqual(self.run_live(), 2)
        self.assertEqual(self.helper.call_count, 1)
        self.factory.assert_not_called()

    def test_interruption_preserves_unknown_liability_and_blocks_rerun(self):
        self.factory.return_value.connect.side_effect = KeyboardInterrupt
        self.assertEqual(self.run_live(), 2)
        evidence = self.report()
        self.assertEqual((evidence["status"], evidence["failure"]), ("failed_or_incomplete", "interrupted"))
        self.assertEqual(self.budget.snapshot()["calls"], 2)
        self.assertEqual(self.budget.snapshot()["unknown_calls"], 2)
        self.assertEqual(self.run_live(), 2)
        self.assertEqual(self.helper.call_count, 1)

    def test_output_symlink_or_nonprivate_directory_denies_without_dispatch(self):
        self.output.chmod(0o755)
        self.assertEqual(self.run_live(), 2)
        self.helper.assert_not_called()
        self.factory.assert_not_called()
        self.assertEqual(self.budget.snapshot()["calls"], 1)

    def test_symlink_output_directory_cannot_redirect_evidence_or_dispatch(self):
        saved = self.output.with_name("saved")
        self.output.rename(saved)
        self.output.symlink_to(saved, target_is_directory=True)
        self.assertEqual(self.run_live(), 2)
        self.assertEqual(list(saved.glob("transport-diagnostic-*.json")), [])
        self.helper.assert_not_called()
        self.factory.assert_not_called()

    def test_config_change_during_helper_blocks_request_and_reservation(self):
        def change_config():
            path = self.owner / "poc-launch.json"
            path.write_bytes(path.read_bytes() + b"\n")
            return "synthetic"
        self.helper.side_effect = change_config
        self.assertEqual(self.run_live(), 2)
        self.factory.assert_not_called()
        self.assertEqual(self.budget.snapshot()["calls"], 1)
        self.assertEqual(self.report()["status"], "failed_or_incomplete")

    def test_no_cli_model_owner_or_report_override(self):
        for option in ("--model", "--canonical-owner-root", "--report", "--run-id"):
            with contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit):
                self.runner.main(["--run-live", option, "foreign"])
        self.helper.assert_not_called()
        self.factory.assert_not_called()

    def test_source_closure_includes_actual_diagnostic_entrypoint(self):
        hashes, _plan = self.runner.diagnostic_plan()
        from hashlib import sha256
        self.assertEqual(hashes["scripts/diagnose_language_transport.py"],
            sha256((policy.ROOT / "scripts/diagnose_language_transport.py").read_bytes()).hexdigest())
