"""No-call tests for the fixed Operator-approved BOB budget window."""
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import model_budget
from test_model_budget import MODEL, STRONGER, usage


START = datetime(2026, 10, 12, 5, tzinfo=timezone.utc).timestamp()
END = datetime(2026, 10, 13, 5, tzinfo=timezone.utc).timestamp()


class BudgetWindowTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "budget.json"
        self.now = START + 3600

    def budget(self, **options):
        return model_budget.ModelBudget(self.path, clock=lambda: self.now, **options)

    def test_explicit_opt_in_allows_more_than_200_calls_without_reset(self):
        budget = self.budget(unlimited_today=True)
        for number in range(201):
            reservation = budget.reserve(model=MODEL)
            self.assertEqual(number + 1, reservation)
            budget.settle(reservation, usage(input_tokens=1, output_tokens=1, cached_input_tokens=0))
        snapshot = budget.snapshot()
        self.assertEqual((201, 201, 0), (snapshot["calls"], snapshot["known_calls"], snapshot["unknown_calls"]))
        self.assertEqual("active", snapshot["unlimited_today"]["status"])
        self.assertEqual(200, snapshot["max_calls"])
        self.assertEqual("20.000000000", snapshot["ceiling_usd"])
        self.now = END
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=MODEL)
        self.assertEqual(201, self.budget().snapshot()["calls"])

    def test_dollar_override_preserves_unknown_liability_and_expires(self):
        budget = self.budget(unlimited_today=True)
        for _ in range(4):
            budget.settle(budget.reserve(model=STRONGER), None)
        snapshot = budget.snapshot()
        self.assertEqual("21.046080000", snapshot["liability_usd"])
        self.assertEqual("-1.046080000", snapshot["remaining_usd"])
        self.now = END
        before = self.path.read_bytes()
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=STRONGER)
        self.assertEqual(before, self.path.read_bytes())
        reopened = self.budget().snapshot()
        self.assertEqual((4, 4, "21.046080000"), (reopened["calls"], reopened["unknown_calls"], reopened["liability_usd"]))

    def test_fixed_start_inclusive_end_exclusive_and_no_daily_renewal(self):
        for instant, status, allowed in ((START - .001, "not_started", False),
                                         (START, "active", True),
                                         (END - .001, "active", True),
                                         (END, "expired", False),
                                         (END + 86400, "expired", False)):
            with self.subTest(instant=instant):
                self.path = Path(self.temp.name) / (str(instant) + ".json")
                self.now = instant
                budget = self.budget(unlimited_today=True, max_calls=1)
                budget.reserve(model=MODEL)
                if allowed:
                    self.assertEqual(2, budget.reserve(model=MODEL))
                else:
                    with self.assertRaises(model_budget.BudgetError):
                        budget.reserve(model=MODEL)
                window = budget.snapshot()["unlimited_today"]
                self.assertEqual(status, window["status"])
                self.assertEqual("2026-10-13T05:00:00Z", window["expires_at"])

    def test_default_is_still_bounded_even_during_approved_day(self):
        budget = self.budget(max_calls=1)
        budget.reserve(model=MODEL)
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=MODEL)
        self.assertEqual("disabled", budget.snapshot()["unlimited_today"]["status"])

    def test_expired_opt_in_still_allows_new_reservations_under_ordinary_caps(self):
        budget = self.budget(unlimited_today=True, max_calls=2)
        budget.reserve(model=MODEL)
        self.now = END
        self.assertEqual(2, budget.reserve(model=MODEL))
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=MODEL)
        self.assertEqual("expired", budget.snapshot()["unlimited_today"]["status"])

    def test_over_cap_ledger_reopens_and_settles_after_expiry_without_opt_in(self):
        budget = self.budget(unlimited_today=True, max_calls=1, ceiling_usd="1")
        first = budget.reserve(model=STRONGER)
        second = budget.reserve(model=STRONGER)
        self.now = END + 10
        ordinary = self.budget(max_calls=1, ceiling_usd="1")
        self.assertEqual((2, 2), (ordinary.snapshot()["calls"], ordinary.snapshot()["unknown_calls"]))
        self.assertEqual("known", ordinary.settle(first, usage())["status"])
        self.assertEqual("unknown", ordinary.settle(second, None)["status"])
        final = self.budget(max_calls=1, ceiling_usd="1").snapshot()
        self.assertEqual((2, 1, 1), (final["calls"], final["known_calls"], final["unknown_calls"]))
        self.assertEqual("5.265070000", final["liability_usd"])
        with self.assertRaises(model_budget.BudgetError):
            ordinary.reserve(model=MODEL)

    def test_late_known_settlement_restores_only_real_dollar_headroom_not_calls(self):
        budget = self.budget(unlimited_today=True, max_calls=3, ceiling_usd="1")
        first = budget.reserve(model=STRONGER)
        self.now = END
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=MODEL)
        budget.settle(first, usage())
        self.assertEqual(2, budget.reserve(model=MODEL))
        self.assertEqual(3, budget.reserve(model=MODEL))
        with self.assertRaises(model_budget.BudgetError):
            budget.reserve(model=MODEL)
        self.assertEqual(3, budget.snapshot()["calls"])

    def test_window_does_not_relax_model_bounds_or_persistence_guards(self):
        budget = self.budget(unlimited_today=True)
        for model, output in (("unpriced", 512), (MODEL, 513), (MODEL, True)):
            with self.assertRaises(model_budget.BudgetError):
                budget.reserve(model=model, max_output_tokens=output)
        before = self.path.read_bytes()
        with patch.object(model_budget.os, "replace", side_effect=OSError("PRIVATE_SENTINEL")):
            with self.assertRaises(model_budget.BudgetError) as caught:
                budget.reserve(model=MODEL)
        self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual(0, self.budget(unlimited_today=True).snapshot()["calls"])

    def test_opt_in_is_literal_and_bad_clock_never_authorizes_dispatch(self):
        for flag in (1, "yes", None):
            with self.assertRaises(model_budget.BudgetError):
                self.budget(unlimited_today=flag)
        budget = self.budget(unlimited_today=True)
        before = self.path.read_bytes()
        for instant in (float("nan"), float("inf"), True, "PRIVATE_SENTINEL"):
            self.now = instant
            with self.assertRaises(model_budget.BudgetError):
                budget.reserve(model=MODEL)
            self.assertEqual(before, self.path.read_bytes())

    def test_storage_denial_keeps_ledger_readable_with_late_settlement_headroom(self):
        with patch.object(model_budget, "_MAX_LEDGER_BYTES", 800):
            budget = self.budget(unlimited_today=True)
            reservations = []
            for _ in range(20):
                before = self.path.read_bytes()
                try:
                    reservations.append(budget.reserve(model=MODEL))
                except model_budget.BudgetError as error:
                    self.assertIn("storage capacity", str(error))
                    self.assertEqual(before, self.path.read_bytes())
                    break
            else:
                self.fail("bounded storage never refused a reservation")
            self.assertTrue(reservations)
            self.now = END
            for reservation in reservations:
                budget.settle(reservation, usage(input_tokens=400000, output_tokens=512,
                                                cached_input_tokens=400000, reasoning_output_tokens=512))
            self.assertLessEqual(self.path.stat().st_size, 800)
            self.assertEqual(len(reservations), self.budget().snapshot()["known_calls"])
            self.assertEqual(len(reservations), len(json.loads(self.path.read_text())["calls"]))


if __name__ == "__main__":
    unittest.main()
