"""BOB-specific coverage stays here, outside the portable checker contract."""
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class BobWalkthroughInventoryTests(unittest.TestCase):
    def test_bob_control_inventory_retains_all_seven_required_groups(self):
        catalog = json.loads((ROOT / "docs/user/walkthroughs/catalog.json").read_text())
        controls = catalog["controls"]
        self.assertEqual(57, len(controls))
        self.assertEqual({"session-and-public", "private-and-booking", "help-and-outcomes",
                          "support", "developer-recording", "replay-navigation",
                          "replay-variants-and-data"}, {row["group"] for row in controls})
        # Developer Mode is a purpose/disclosure, not another authorization role.
        self.assertEqual({"patient", "support", "both"},
                         {row["role"] for row in controls})
        for row in controls:
            self.assertEqual("docs/user/controls/" + row["group"] + ".md", row["document"])
            self.assertTrue((ROOT / row["document"]).is_file(), row["id"])
            self.assertTrue(row["visual_ids"], row["id"])

    def test_bob_control_visuals_retain_valid_exact_source_layers(self):
        spec = importlib.util.spec_from_file_location(
            "bob_inventory_checker", ROOT / "tools/poc-docs/check_walkthroughs.py")
        checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(checker)
        manifest = json.loads((ROOT / "assets/ui/walkthroughs/manifest.json").read_text())
        visuals, errors = checker._visuals(ROOT, manifest)
        self.assertEqual([], errors)
        catalog = json.loads((ROOT / "docs/user/walkthroughs/catalog.json").read_text())
        for row in catalog["controls"]:
            for identifier in row["visual_ids"]:
                self.assertIn(identifier, visuals)
                self.assertEqual("composite", visuals[identifier]["kind"])


if __name__ == "__main__":
    unittest.main()
