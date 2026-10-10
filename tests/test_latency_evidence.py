"""Measurement smoke test, not an absolute timing/SLA acceptance gate."""
from pathlib import Path
import sys
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]/"scripts"))


class LatencyEvidenceTests(unittest.TestCase):
    def test_measures_actual_local_public_transport_without_effects(self):
        from measure_local import measure
        result=measure(4)
        self.assertEqual(result["samples"],4)
        self.assertEqual(result["mode"],"offline_commands")
        self.assertEqual(result["live_effects"],0)
        self.assertEqual(result["final_revision"],4)
        self.assertLessEqual(result["p50_ms"],result["p95_ms"])
        self.assertLessEqual(result["p95_ms"],result["max_ms"])
        self.assertIn("not measured",result["browser_feedback"])

    def test_sample_bound_is_explicit(self):
        from measure_local import measure
        for count in (0,201,True,"4"):
            with self.assertRaises(ValueError):
                measure(count)
