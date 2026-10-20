"""Readiness validates existing private bytes; it never initializes a budget."""
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import model_budget
from test_budget_window import START, END
from test_model_budget import MODEL, STRONGER, usage


class BudgetPreflightTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(model_budget, "preflight_budget", None)),
                        "public read-only budget readiness API is missing")
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "budget.json"
        self.marker = self.path.with_name("budget.json.lock")
        self.now = START + 3600

    def budget(self):
        return model_budget.ModelBudget(self.path, application_runtime=True,
            unlimited_today=True, clock=lambda: self.now)

    def state(self):
        return [(path.read_bytes(), path.stat().st_dev, path.stat().st_ino, path.stat().st_mtime_ns)
                for path in (self.path, self.marker)]

    def preflight(self, **options):
        with patch.object(model_budget.time, "time", return_value=self.now):
            return model_budget.preflight_budget(self.path, model=options.pop("model", MODEL), **options)

    def test_valid_existing_budget_has_unchanged_bytes_identity_and_count(self):
        budget = self.budget()
        budget.settle(budget.reserve(model=MODEL), None)
        before = self.state()
        self.assertIsNone(self.preflight())
        self.assertEqual(before, self.state())
        self.assertEqual((1, 1), (budget.snapshot()["calls"], budget.snapshot()["unknown_calls"]))

    def test_missing_budget_or_parent_is_not_created(self):
        for path in (self.path, Path(self.temp.name) / "absent" / "budget.json"):
            with self.subTest(path=path):
                self.path = path
                with self.assertRaises(model_budget.BudgetError):
                    self.preflight()
                self.assertFalse(path.exists())
                self.assertFalse(path.with_name(path.name + ".lock").exists())
        self.assertFalse((Path(self.temp.name) / "absent").exists())

    def test_missing_marker_is_not_initialized_or_budget_changed(self):
        self.budget()
        self.marker.unlink()
        before = (self.path.read_bytes(), self.path.stat().st_ino)
        with self.assertRaises(model_budget.BudgetError):
            self.preflight()
        self.assertEqual(before, (self.path.read_bytes(), self.path.stat().st_ino))
        self.assertFalse(self.marker.exists())

    def test_empty_or_corrupt_marker_is_not_repaired(self):
        self.budget()
        for raw in (b"", b"corrupt"):
            self.marker.write_bytes(raw)
            before = self.state()
            with self.assertRaises(model_budget.BudgetError):
                self.preflight()
            self.assertEqual(before, self.state())

    def test_corrupt_private_ledger_is_not_changed_or_echoed(self):
        self.budget()
        for raw in (b"PRIVATE_SENTINEL", b'{"version":1,"version":1}', b'[]'):
            self.path.write_bytes(raw)
            before = self.state()
            with self.assertRaises(model_budget.BudgetError) as caught:
                self.preflight()
            self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
            self.assertEqual(before, self.state())

    def test_own_key_readiness_enforces_dollars_but_keeps_late_settlement(self):
        budget = self.budget()
        for _ in range(4):
            budget.reserve(model=STRONGER)
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            self.preflight(model=STRONGER)
        self.now = END
        with self.assertRaises(model_budget.BudgetError):
            self.preflight(model=STRONGER)
        self.assertEqual(before, self.state())
        for reservation in range(1, 5):
            budget.settle(reservation, usage())
        before = self.state()
        self.assertIsNone(self.preflight(model=STRONGER))
        self.assertEqual(before, self.state())

    def test_own_key_readiness_preserves_history_and_enforces_call_cap(self):
        budget = self.budget()
        for _ in range(200):
            budget.settle(budget.reserve(model=MODEL), usage(input_tokens=1, output_tokens=1, cached_input_tokens=0))
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            self.preflight()
        self.now = END
        with self.assertRaises(model_budget.BudgetError):
            self.preflight()
        self.assertEqual(before, self.state())

    def test_unpriced_model_and_insecure_storage_fail_without_mutation(self):
        self.budget()
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            self.preflight(model="unpriced-private-sentinel")
        self.assertEqual(before, self.state())
        self.path.chmod(0o644)
        before = self.state()
        with self.assertRaises(model_budget.BudgetError):
            self.preflight()
        self.assertEqual(before, self.state())
        self.assertEqual(0o644, self.path.stat().st_mode & 0o777)

    def test_legacy_capacity_state_is_retained_but_not_model_ready(self):
        with patch.object(model_budget, "_MAX_LEDGER_BYTES", 800):
            budget = model_budget.ModelBudget(self.path, unlimited_today=True, clock=lambda: self.now)
            for _ in range(20):
                try:
                    budget.reserve(model=MODEL)
                except model_budget.BudgetError:
                    break
            else:
                self.fail("bounded ledger did not fill")
            before = self.state()
            with self.assertRaises(model_budget.BudgetError):
                self.preflight()
            self.assertEqual(before, self.state())
            self.assertEqual(budget.snapshot()["calls"], len(json.loads(self.path.read_text())["calls"]))


if __name__ == "__main__":
    unittest.main()
