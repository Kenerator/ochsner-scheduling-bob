"""Runtime policy/accounting regressions; temporary storage and fake transport only."""
from concurrent.futures import ThreadPoolExecutor
import json
import os
from pathlib import Path
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import model_budget
from ochsner_bob.language import LanguageAdapter
from test_model_budget import MODEL, STRONGER, ENV, billed_response, usage
from test_language import FakeTransport


class RuntimeAccountingTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "model-budget.json"

    def runtime(self, **options):
        return model_budget.ModelBudget(self.path, application_runtime=True, **options)

    def state(self):
        return {p.name: (p.read_bytes(), p.stat().st_ino, p.stat().st_mtime_ns)
                for p in self.path.parent.iterdir() if p.is_file()}

    def test_runtime_crosses_old_calls_dollars_and_expiry_without_flag(self):
        budget = self.runtime(clock=lambda: 1791867601)
        for index in range(205):
            self.assertEqual(index + 1, budget.reserve(model=STRONGER))
        view = budget.snapshot()
        self.assertEqual((205, 205), (view["calls"], view["unknown_calls"]))
        self.assertEqual("1078.611600000", view["liability_usd"])
        self.assertEqual("application_runtime_unlimited", view["policy"])
        self.assertIsNone(view["remaining_usd"])
        self.assertEqual(206, self.runtime(clock=lambda: 0).reserve(model=MODEL))

    def test_growth_has_no_cumulative_byte_cutoff_and_keeps_late_reservations(self):
        budget = self.runtime()
        first = budget.reserve(model=MODEL)
        for _ in range(2000):
            budget.settle(budget.reserve(model=MODEL), None)
        self.assertGreater(self.path.stat().st_size, 100000)
        reopened = self.runtime()
        self.assertEqual("known", reopened.settle(first, usage())["status"])
        view = reopened.snapshot()
        self.assertEqual((2001, 1, 2000), (view["calls"], view["known_calls"], view["unknown_calls"]))
        self.assertEqual("604.609065000", view["liability_usd"])
        with self.assertRaises(model_budget.BudgetError):
            reopened.settle(2, usage())  # Already unknown, never refunded.

    def test_json_migration_preserves_history_ids_config_and_unknown_liability(self):
        legacy = model_budget.ModelBudget(self.path, max_calls=3, ceiling_usd="1")
        legacy.settle(legacy.reserve(model=MODEL), usage())
        legacy.settle(legacy.reserve(model=MODEL), None)
        pending = legacy.reserve(model=MODEL)
        before = legacy.snapshot()
        runtime = self.runtime(max_calls=3, ceiling_usd="1")
        after = runtime.snapshot()
        for key in ("calls", "known_calls", "unknown_calls", "known_cost_usd", "liability_usd"):
            self.assertEqual(before[key], after[key])
        self.assertEqual(b"SQLite format 3\x00", self.path.read_bytes()[:16])
        self.assertEqual("known", runtime.settle(pending, usage())["status"])
        self.assertEqual(4, self.runtime(max_calls=3, ceiling_usd="1").reserve(model=MODEL))
        # Generic excluded generation callers do not inherit covered execution.
        with self.assertRaises(model_budget.BudgetError):
            model_budget.ModelBudget(self.path, max_calls=3, ceiling_usd="1").reserve(model=MODEL)

    def test_preflight_accepts_over_cap_legacy_json_without_migration_or_mutation(self):
        legacy = model_budget.ModelBudget(self.path)
        legacy.reserve(model=STRONGER)
        document = json.loads(self.path.read_text())
        document["calls"] *= 4  # Valid historical over-cap JSON, not new dispatch.
        self.path.write_text(json.dumps(document))
        before = self.state()
        model_budget.preflight_budget(self.path, model=STRONGER)
        self.assertEqual(before, self.state())

    def test_sqlite_readiness_is_read_only_and_keeps_ids_and_marker(self):
        budget = self.runtime()
        budget.reserve(model=STRONGER)
        before = self.state()
        model_budget.preflight_budget(self.path, model=STRONGER)
        self.assertEqual(before, self.state())
        self.assertEqual(2, budget.reserve(model=MODEL))

    def test_concurrent_runtime_instances_reserve_unique_durable_ids(self):
        first, second = self.runtime(), self.runtime()
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = list(pool.map(lambda i: (first if i % 2 else second).reserve(model=MODEL), range(30)))
        self.assertEqual(list(range(1, 31)), sorted(ids))
        self.assertEqual((30, 30), (self.runtime().snapshot()["calls"], self.runtime().snapshot()["unknown_calls"]))

    def test_processes_share_flock_and_transactional_reservations(self):
        self.runtime()
        program = (
            "import json,sys; from pathlib import Path; "
            "from ochsner_bob.model_budget import ModelBudget; "
            "b=ModelBudget(Path(sys.argv[1]),application_runtime=True); "
            "print(json.dumps([b.reserve(model='gpt-5.4-mini-2026-03-17') for _ in range(8)]))")
        environ = {name: value for name, value in os.environ.items()
                   if name in {"PATH", "HOME", "TMPDIR", "PYTHONPATH", "PYTHONDONTWRITEBYTECODE"}}
        def worker(_):
            completed = subprocess.run([sys.executable, "-c", program, str(self.path)],
                env=environ, text=True, capture_output=True, timeout=5, check=True)
            return json.loads(completed.stdout)
        with ThreadPoolExecutor(max_workers=4) as pool:
            ids = [identifier for group in pool.map(worker, range(4)) for identifier in group]
        self.assertEqual(list(range(1, 33)), sorted(ids))
        self.assertEqual(32, self.runtime().snapshot()["calls"])

    def test_fake_transport_dispatches_above_legacy_caps_only_in_runtime_mode(self):
        legacy = model_budget.ModelBudget(self.path, max_calls=1)
        legacy.settle(legacy.reserve(model=MODEL), None)
        transport = FakeTransport(billed_response())
        runtime = self.runtime(max_calls=1)
        result = LanguageAdapter(transport=transport, environ=ENV, budget=runtime).interpret("Find providers")
        self.assertEqual("ok", result.status)
        self.assertEqual((2, 1), (runtime.snapshot()["calls"], runtime.snapshot()["known_calls"]))
        denied = LanguageAdapter(transport=FakeTransport(billed_response()), environ=ENV,
            budget=model_budget.ModelBudget(self.path, max_calls=1)).interpret("Find providers")
        self.assertEqual("budget_exceeded", denied.status)

    def test_failed_migration_retains_original_bytes_and_sanitizes_error(self):
        model_budget.ModelBudget(self.path).reserve(model=MODEL)
        before = self.state()
        with patch.object(model_budget.os, "replace", side_effect=OSError("PRIVATE_SENTINEL")):
            with self.assertRaises(model_budget.BudgetError) as caught:
                self.runtime()
        self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
        self.assertEqual(before, self.state())

    def test_private_files_corruption_and_sqlite_sidecars_fail_closed(self):
        self.runtime().reserve(model=MODEL)
        original = self.path.read_bytes()
        for suffix in ("-journal", "-wal", "-shm"):
            sidecar = self.path.with_name(self.path.name + suffix)
            sidecar.write_bytes(b"PRIVATE_SENTINEL"); sidecar.chmod(0o644)
            with self.assertRaises(model_budget.BudgetError) as caught:
                self.runtime()
            self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
            self.assertEqual(original, self.path.read_bytes())
            sidecar.unlink()
        self.path.chmod(0o644)
        with self.assertRaises(model_budget.BudgetError):
            self.runtime()
        self.path.chmod(0o600)
        self.path.write_bytes(b"PRIVATE_SENTINEL")
        with self.assertRaises(model_budget.BudgetError):
            self.runtime()
        self.assertEqual(b"PRIVATE_SENTINEL", self.path.read_bytes())

    def test_sqlite_invalid_row_or_extra_schema_is_not_repaired(self):
        self.runtime().reserve(model=MODEL)
        with sqlite3.connect(self.path) as connection:
            connection.execute("CREATE TABLE injected(value TEXT)")
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            self.runtime()
        self.assertEqual(before, self.state())

    def test_existing_instance_detects_external_malformed_rows_before_dispatch(self):
        budget = self.runtime()
        budget.reserve(model=MODEL)
        with sqlite3.connect(self.path) as connection:
            connection.execute("UPDATE calls SET status='invalid' WHERE id=1")
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=MODEL)
        self.assertEqual(before, self.state())

    def test_migration_rejects_existing_unsafe_companion_without_replacing_json(self):
        model_budget.ModelBudget(self.path).reserve(model=MODEL)
        companion = self.path.with_name(self.path.name + "-journal")
        companion.write_bytes(b"PRIVATE_SENTINEL"); companion.chmod(0o644)
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            self.runtime()
        self.assertEqual(before, self.state())

    def test_failed_directory_sync_after_runtime_commit_preserves_unknown_charge(self):
        budget = self.runtime()
        with patch.object(model_budget.EffectJournal, "_sync_directory", side_effect=OSError("PRIVATE_SENTINEL")):
            with self.assertRaises(model_budget.BudgetError) as caught:
                budget.reserve(model=MODEL)
        self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
        self.assertEqual((1, 1), (self.runtime().snapshot()["calls"], self.runtime().snapshot()["unknown_calls"]))

    def test_runtime_storage_stays_private_and_contains_no_prompt_or_credential(self):
        budget = self.runtime()
        budget.settle(budget.reserve(model=MODEL), usage())
        for path in self.path.parent.iterdir():
            self.assertEqual(0o600, path.stat().st_mode & 0o777)
            raw = path.read_bytes()
            self.assertNotIn(b"synthetic-test-credential", raw)
            self.assertNotIn(b"Find providers", raw)


if __name__ == "__main__":
    unittest.main()
