"""Disposable canonical bindings and schedules; no vault or real HTTPS."""
import contextlib
import copy
import importlib
import importlib.util
import inspect
import io
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.model_budget import BudgetError, ModelBudget

ROOT = Path(__file__).resolve().parents[1]
MODEL = "gpt-5.4-2026-03-05"
USAGE = {"input_tokens": 10, "output_tokens": 5, "cached_input_tokens": 0, "reasoning_output_tokens": 0}


class ExistingStorageWriteTests(unittest.TestCase):
    def setUp(self):
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="connected-policy-"))).resolve()
        self.assertIn("_existing_writes", inspect.signature(ModelBudget).parameters,
                      "Missing existing-SQLite dispatch mode")

    def test_invalid_existing_write_combinations_create_nothing(self):
        combinations = [{"_existing_writes": True}, {"_existing_writes": True, "application_runtime": True},
                        {"_existing_writes": True, "_existing_only": True},
                        {"_existing_writes": 1, "application_runtime": True, "_existing_only": True}]
        for options in combinations:
            with self.assertRaises(BudgetError):
                ModelBudget(self.directory / "missing/model-budget.json", **options)
        self.assertEqual(list(self.directory.iterdir()), [])

    def test_existing_sqlite_writes_are_opt_in_and_readiness_stays_readonly(self):
        path = self.directory / "private/model-budget.json"
        original = ModelBudget(path, application_runtime=True)
        identifier = original.reserve(model=MODEL); original.settle(identifier, None)
        readonly = ModelBudget(path, application_runtime=True, _existing_only=True)
        with self.assertRaises(BudgetError):
            readonly.reserve(model=MODEL)
        with self.assertRaises(BudgetError):
            readonly.settle(identifier, USAGE)
        inode = path.stat().st_ino
        lock_inode = path.with_name(path.name + ".lock").stat().st_ino
        writable = ModelBudget(path, application_runtime=True, _existing_only=True, _existing_writes=True)
        second = writable.reserve(model=MODEL)
        self.assertEqual(second, 2)
        writable.settle(second, USAGE)
        self.assertEqual(writable.snapshot()["unknown_calls"], 1)
        self.assertEqual(writable.snapshot()["known_calls"], 1)
        self.assertEqual(path.stat().st_ino, inode)
        self.assertEqual(path.with_name(path.name + ".lock").stat().st_ino, lock_inode)

    def test_json_missing_and_symlink_never_migrate_or_create(self):
        path = self.directory / "private/model-budget.json"
        ModelBudget(path)
        before = (path.stat().st_ino, path.read_bytes())
        options = {"application_runtime": True, "_existing_only": True, "_existing_writes": True}
        with self.assertRaises(BudgetError):
            ModelBudget(path, **options)
        self.assertEqual((path.stat().st_ino, path.read_bytes()), before)
        saved = path.with_name("saved"); path.rename(saved)
        with self.assertRaises(BudgetError):
            ModelBudget(path, **options)
        self.assertFalse(path.exists())
        path.symlink_to(saved)
        with self.assertRaises(BudgetError):
            ModelBudget(path, **options)
        self.assertEqual(saved.read_bytes(), before[1])


class ConnectedPolicyTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("http.client.HTTPSConnection", side_effect=AssertionError("no real HTTPS")))
        self.assertIsNotNone(importlib.util.find_spec("scripts.qualify_connected_live"), "Missing connected live policy")
        self.policy = importlib.import_module("scripts.qualify_connected_live")
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="connected-policy-"))).resolve()
        self.owner = self.directory / "owner"
        self.owner.mkdir()
        (self.owner / ".git").mkdir()
        self.config = json.loads((ROOT / "poc-launch.json").read_text())
        (self.owner / "poc-launch.json").write_text(json.dumps(self.config))
        (self.owner / ".bob-local").mkdir(mode=0o700)
        self.ledger = self.owner / ".bob-local/model-budget.json"
        budget = ModelBudget(self.ledger, application_runtime=True)
        old = budget.reserve(model=MODEL)
        budget.settle(old, USAGE)
        self.enterContext(patch.object(self.policy, "_APPROVED_OWNER_ROOT", self.owner))
        self.helper = self.enterContext(patch.object(self.policy, "resolve_qualification_key", side_effect=AssertionError("no key lookup")))

    def binding(self, path=None):
        return self.policy.canonical_binding(self.owner if path is None else path)

    def test_existing_sqlite_dispatch_preserves_history_ids_inode_and_lock(self):
        inode = self.ledger.stat().st_ino
        lock = self.ledger.with_name(self.ledger.name + ".lock")
        lock_inode = lock.stat().st_ino
        binding = self.binding()
        before = binding.budget.snapshot()
        identifier = binding.budget.reserve(model=MODEL)
        self.assertEqual(identifier, 2)
        binding.budget.settle(identifier, USAGE)
        after = binding.budget.snapshot()
        self.assertEqual((before["calls"], after["calls"], after["known_calls"]), (1, 2, 2))
        self.assertEqual(self.ledger.stat().st_ino, inode)
        self.assertEqual(lock.stat().st_ino, lock_inode)
        self.assertEqual(lock.read_bytes(), b"1")
        self.helper.assert_not_called()

    def test_missing_foreign_and_symlink_roots_deny_without_creation(self):
        for target in (self.directory / "missing", self.directory):
            with self.subTest(target=target.name), self.assertRaises((ValueError, BudgetError)):
                self.binding(target)
        linked = self.directory / "linked"
        linked.symlink_to(self.owner, target_is_directory=True)
        with self.assertRaises((ValueError, BudgetError)):
            self.binding(linked)
        self.assertFalse((self.directory / "missing").exists())
        self.helper.assert_not_called()

    def test_config_mismatch_duplicate_and_symlink_deny_before_helper(self):
        path = self.owner / "poc-launch.json"
        variants = []
        for key, value in (("project_id", "foreign"), ("adapter", "other"), ("schema_version", True)):
            data = copy.deepcopy(self.config); data[key] = value
            variants.append(json.dumps(data))
        data = copy.deepcopy(self.config); data["model"]["default"] = "gpt-5.4-mini-2026-03-17"
        variants.append(json.dumps(data))
        data = copy.deepcopy(self.config); data["credential"]["field"] = "auto"
        variants.append(json.dumps(data))
        variants += [json.dumps(self.config).replace('"schema_version": 1', '"schema_version": 1, "schema_version": 1'), " " * 16385]
        for raw in variants:
            path.write_text(raw)
            with self.assertRaises((ValueError, BudgetError)):
                self.binding()
        path.unlink(); path.symlink_to(ROOT / "poc-launch.json")
        with self.assertRaises((ValueError, BudgetError)):
            self.binding()
        self.helper.assert_not_called()

    def test_nonfinite_json_config_denies_before_helper(self):
        raw = json.dumps(self.config)[:-1] + ', "unused": NaN}'
        (self.owner / "poc-launch.json").write_text(raw)
        with self.assertRaises(BudgetError):
            self.binding()
        self.helper.assert_not_called()

    def test_missing_marker_ledger_and_symlink_storage_never_initialize(self):
        for name in ("model-budget.json", "model-budget.json.lock"):
            target = self.ledger.with_name(name)
            saved = target.with_name(name + ".saved")
            target.rename(saved)
            with self.assertRaises((ValueError, BudgetError)):
                self.binding()
            self.assertFalse(target.exists())
            target.symlink_to(saved)
            with self.assertRaises((ValueError, BudgetError)):
                self.binding()
            target.unlink(); saved.rename(target)
        self.helper.assert_not_called()

    def test_legacy_json_readiness_never_migrates_and_dispatch_binding_denies(self):
        from ochsner_bob.model_budget import preflight_budget
        legacy = self.directory / "legacy"
        legacy.mkdir(mode=0o700)
        path = legacy / "model-budget.json"
        ModelBudget(path)
        before = (path.stat().st_ino, path.read_bytes())
        with self.assertRaises(BudgetError):
            preflight_budget(path, model=MODEL)
        self.assertEqual((path.stat().st_ino, path.read_bytes()), before)
        self.ledger.write_bytes(path.read_bytes())
        before = (self.ledger.stat().st_ino, self.ledger.read_bytes())
        with self.assertRaises((ValueError, BudgetError)):
            self.binding()
        self.assertEqual((self.ledger.stat().st_ino, self.ledger.read_bytes()), before)
        self.helper.assert_not_called()

    def test_changed_config_marker_or_database_identity_blocks_reservation(self):
        for kind in ("config", "marker", "database"):
            with self.subTest(kind=kind):
                binding = self.binding()
                if kind == "config":
                    target = self.owner / "poc-launch.json"
                    original = target.read_bytes(); target.write_bytes(original + b"\n")
                elif kind == "marker":
                    target = self.ledger.with_name(self.ledger.name + ".lock")
                    original = target.read_bytes(); target.write_bytes(b"")
                else:
                    target = self.ledger
                    original = target.read_bytes()
                    replacement = target.with_name("replacement")
                    replacement.write_bytes(original); replacement.chmod(0o600); replacement.replace(target)
                with self.assertRaises(BudgetError):
                    binding.budget.reserve(model=MODEL)
                target.write_bytes(original)

    def test_candidate_code_and_canonical_billing_ignore_generic_environment(self):
        binding = self.binding()
        with patch.dict(os.environ, {"OPENAI_API_KEY": "wrong-generic", "BOB_OPENAI_MODEL": "wrong-model", "BOB_MODEL_BUDGET_PATH": str(self.directory / "foreign.json")}):
            with patch.object(self.policy, "resolve_qualification_key", return_value="synthetic-fixture-only"):
                adapter = self.policy.create_language(binding)
        self.assertEqual(adapter._budget.path, self.ledger)
        self.assertEqual(adapter._environ["BOB_OPENAI_MODEL"], MODEL)
        self.assertEqual(adapter._environ["OPENAI_API_KEY"], "synthetic-fixture-only")
        # Exercise candidate LanguageAdapter -> real SQLite reserve/settle, with
        # only the external transport replaced and explicitly fixture-labeled.
        adapter.mode = "fixture"
        adapter._transport = lambda *_args, **_kwargs: json.dumps({"status": "completed", "error": None,
            "model": MODEL, "service_tier": "default", "usage": {"input_tokens": 10, "output_tokens": 5,
                "total_tokens": 15, "input_tokens_details": {"cached_tokens": 0},
                "output_tokens_details": {"reasoning_tokens": 0}},
            "output": [{"type": "message", "role": "assistant", "status": "completed", "content": [
                {"type": "output_text", "text": json.dumps({"action": "preferences", "preferences": {"specialty": "primary_care"}})}]}]}).encode()
        outcome = adapter.interpret("I'd prefer primary care.")
        self.assertEqual(outcome.accounting_status, "known")
        self.assertEqual(outcome.cost_usd, "0.000100000")
        self.assertEqual(binding.budget.snapshot()["known_calls"], 2)
        self.assertFalse((self.directory / "foreign.json").exists())
        import ochsner_bob.language
        self.assertEqual(Path(ochsner_bob.language.__file__).resolve(), ROOT / "src/ochsner_bob/language.py")

    def test_preflight_is_read_only_and_dry_run_never_reads_owner(self):
        before = (self.ledger.read_bytes(), self.ledger.stat().st_ino)
        with contextlib.redirect_stdout(io.StringIO()) as output:
            result = self.policy.main(["--preflight", "--canonical-owner-root", str(self.owner)])
        self.assertEqual(result, 0, output.getvalue())
        self.assertEqual((self.ledger.read_bytes(), self.ledger.stat().st_ino), before)
        with patch.object(self.policy, "canonical_binding", side_effect=AssertionError("dry run touched owner")):
            with contextlib.redirect_stdout(io.StringIO()) as output:
                self.assertEqual(self.policy.main(["--dry-run"]), 0)
        self.helper.assert_not_called()
        self.assertNotIn(str(self.owner), output.getvalue())

    def test_schedule_retains_all_sixteen_and_terminal_unrun_without_retry(self):
        case = {"id": "development", "steps": [{"kind": "text", "dispatch": True}]}
        manifest = {"cases": [{**case, "id": "development-" + str(n)} for n in range(8)], "repetitions": 2}
        reports = [{"passed": False, "halt_dispatch": False, "language_calls": 1, "genuine_qualification": False},
                   {"passed": False, "halt_dispatch": True, "language_calls": 1, "genuine_qualification": False}]
        with patch.object(self.policy, "run_journey", side_effect=reports) as run:
            report = self.policy.run_schedule(manifest, None, self.directory)
        self.assertEqual(run.call_count, 2)
        self.assertEqual(len(report["executions"]), 16)
        self.assertEqual(sum(item["status"] == "unrun" for item in report["executions"]), 14)
        self.assertEqual(report["language_calls"], 2)
        self.assertFalse(report["qualified"])

    def test_semantic_failures_do_not_add_retry_repetitions_or_qualify(self):
        manifest = {"cases": [{"id": "development", "steps": []}], "repetitions": 2}
        with patch.object(self.policy, "run_journey", return_value={"passed": False, "halt_dispatch": False,
                "language_calls": 1, "genuine_qualification": False}) as run:
            report = self.policy.run_schedule(manifest, None, self.directory)
        self.assertEqual(run.call_count, 2)
        self.assertEqual([item["repetition_id"] for item in report["executions"]], [1, 2])
        self.assertFalse(report["qualified"])

    def test_unexpected_runner_failure_retains_all_unrun_executions(self):
        manifest = {"cases": [{"id": "development", "steps": []}], "repetitions": 2}
        with patch.object(self.policy, "run_journey", side_effect=OSError("PRIVATE path")):
            report = self.policy.run_schedule(manifest, None, self.directory)
        self.assertEqual(len(report["executions"]), 2)
        self.assertEqual(report["executions"][0]["status"], "failed_before_result")
        self.assertEqual(report["executions"][1]["status"], "unrun")
        self.assertTrue(report["halted"])
        self.assertNotIn("PRIVATE", json.dumps(report))

    def test_private_report_survives_short_writes(self):
        path = self.directory / "report.json"
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL, 0o600)
        original = os.write
        try:
            with patch.object(self.policy.os, "write", side_effect=lambda handle, data: original(handle, data[:7])):
                self.policy._save(fd, {"qualification": "not_run", "executions": []})
        finally:
            os.close(fd)
        self.assertEqual(json.loads(path.read_text()), {"qualification": "not_run", "executions": []})

    def test_interruption_checkpoint_marks_started_execution_not_unrun(self):
        manifest = {"cases": [{"id": "development", "steps": []}], "repetitions": 2}
        checkpoints = []
        with patch.object(self.policy, "run_journey", side_effect=KeyboardInterrupt):
            with self.assertRaises(KeyboardInterrupt):
                self.policy.run_schedule(manifest, None, self.directory,
                    on_execution=lambda items: checkpoints.append(copy.deepcopy(items)))
        self.assertTrue(checkpoints, "Started execution must be saved before model work")
        self.assertEqual(checkpoints[-1][0]["status"], "running")

    def test_live_report_exclusive_creation_prevents_second_tranche(self):
        binding = self.binding()
        manifest = {"cases": [{"id": "development-" + str(n), "steps": []} for n in range(8)], "repetitions": 2}
        plan = {"source_digest": "selected-fixture-digest"}
        candidate = self.directory / "candidate"
        (candidate / "tmp").mkdir(parents=True)
        (candidate / "poc-launch.json").write_bytes((ROOT / "poc-launch.json").read_bytes())
        result = {"passed": False, "halt_dispatch": False, "language_calls": 0, "genuine_qualification": False}
        with patch.object(self.policy, "ROOT", candidate), patch.object(self.policy, "holdout_plan", return_value=(manifest, {}, plan)), \
                patch.object(self.policy, "source_hashes", return_value={}), \
                patch.object(self.policy, "canonical_binding", return_value=binding), \
                patch.object(self.policy, "create_language", return_value=None) as create, \
                patch.object(self.policy, "run_journey", return_value=result) as run, \
                patch.dict(os.environ, {"BOB_ENABLE_OPENAI": "1"}), contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(self.policy.main(["--run-live", "--source-digest", plan["source_digest"]]), 1)
            self.assertEqual(self.policy.main(["--run-live", "--source-digest", plan["source_digest"]]), 2)
        self.assertEqual(create.call_count, 1)
        self.assertEqual(run.call_count, 16)
        evidence = candidate / "tmp/connected-qualification/run.json"
        report = json.loads(evidence.read_text())
        self.assertEqual(len(report["executions"]), 16)
        self.assertEqual(evidence.stat().st_mode & 0o777, 0o600)
        self.assertEqual(evidence.parent.stat().st_mode & 0o777, 0o700)


if __name__ == "__main__":
    unittest.main()
