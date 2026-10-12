"""Structural contract only: no app, vault, network or model is started."""
import contextlib
import copy
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest


CHECKER = Path(__file__).resolve().parents[1] / "tools/poc-docs/check_walkthroughs.py"


class WalkthroughContractTests(unittest.TestCase):
    def setUp(self):
        # Removing path/schema/step validation must make these tests fail.
        self.assertTrue(CHECKER.is_file(), "reusable walkthrough checker is missing")
        spec = importlib.util.spec_from_file_location("walkthrough_checker", CHECKER)
        self.checker = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.checker)
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.write("specs/example/spec.md", "# Example\n\n### User Story 1 - Find care\n\nFR-001\n")
        self.write("docs/gaps.md", "# Gaps\n\n## Pending\n\nNot executed.\n")
        self.document = "docs/user/walkthroughs/demo.md"
        self.markdown = ("# Demo\n\n## Step 0 — Install and set up\n\nInstall.\n\n"
                         "## Step 1 — Launch\n\nLaunch.\n\n## Step 2 — Find providers\n\n"
                         "Schematic, not executed UI.\n\n![Discovery schematic](../../../assets/view.svg)\n")
        self.write(self.document, self.markdown)
        self.write("docs/user/controls/public.md", "# Public\n\nSchematic.\n\n![Discovery schematic](../../../assets/view.svg)\n")
        self.write("assets/view.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"/>')
        self.write("assets/ui/walkthroughs/manifest.json", json.dumps({
            "schema_version": 1, "visuals": [{"id": "discovery", "kind": "schematic", "path": "assets/view.svg"}]}))
        self.catalog = {"schema_version": 1, "flows": [{
            "id": "demo", "source_ids": ["US1"], "document": self.document,
            "status": "unverified", "mode": "offline", "gap_refs": ["docs/gaps.md#pending"],
            "evidence_refs": [], "steps": [
                {"number": 0, "anchor": "step-0--install-and-set-up", "interactive": False},
                {"number": 1, "anchor": "step-1--launch", "interactive": False},
                {"number": 2, "anchor": "step-2--find-providers", "interactive": True,
                 "visual_ids": ["discovery"], "control_ids": ["find-providers"]}]}],
            "controls": [{"id": "find-providers", "label": "Find providers", "role": "patient",
                          "group": "session-and-public", "document": "docs/user/controls/public.md",
                          "visual_ids": ["discovery"]}]}

    def write(self, relative, text):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")

    def errors(self):
        return self.checker.check_catalog(self.root, self.catalog)

    def test_valid_minimal_contract(self):
        self.assertEqual([], self.errors())

    def test_interaction_without_visual_is_rejected(self):
        self.catalog["flows"][0]["steps"][2]["visual_ids"] = []
        self.assertIn("demo: step 2 requires a visual", self.errors())

    def test_missing_install_or_launch_step(self):
        for index in (0, 1):
            with self.subTest(index=index):
                original = copy.deepcopy(self.catalog)
                self.catalog["flows"][0]["steps"].pop(index)
                self.assertIn("demo: steps must start at 0 and be consecutive", self.errors())
                self.catalog = original

    def test_distinct_flows_cannot_share_one_document(self):
        second = copy.deepcopy(self.catalog["flows"][0])
        second["id"] = "different"
        self.catalog["flows"].append(second)
        self.assertIn("different: document already assigned to another flow", self.errors())

    def test_unknown_control_and_visual_ids(self):
        self.catalog["flows"][0]["steps"][2].update(control_ids=["unknown"], visual_ids=["unknown"])
        errors = self.errors()
        self.assertIn("demo: step 2 has unresolved control", errors)
        self.assertIn("demo: step 2 has unresolved visual", errors)

    def test_missing_asset(self):
        (self.root / "assets/view.svg").unlink()
        self.assertIn("discovery: visual asset unavailable", self.errors())

    def test_alt_text_is_required(self):
        self.write(self.document, self.markdown.replace("![Discovery schematic]", "![]"))
        self.assertIn("demo: image requires alt text", self.errors())

    def test_visual_must_be_in_its_interactive_section(self):
        self.write(self.document, self.markdown.replace("## Step 2 — Find providers", "## Other"))
        self.assertIn("demo: step 2 anchor unavailable", self.errors())

    def test_paths_reject_traversal_absolute_and_symlink(self):
        for value in ("../outside.md", str(self.root / self.document), "docs/link.md"):
            with self.subTest(value=value):
                link = self.root / "docs/link.md"
                if not link.exists():
                    link.symlink_to(self.root / self.document)
                self.catalog["flows"][0]["document"] = value
                self.assertIn("demo: document unavailable or unsafe", self.errors())

    def test_gap_status_requires_reference(self):
        for status in ("unverified", "partial", "unsupported"):
            self.catalog["flows"][0].update(status=status, gap_refs=[])
            self.assertIn("demo: gap status requires a gap reference", self.errors())

    def test_schematic_cannot_be_claimed_as_screenshot(self):
        self.write("assets/ui/walkthroughs/manifest.json", json.dumps({
            "schema_version": 1, "visuals": [{"id": "discovery", "kind": "screenshot", "path": "assets/view.svg"}]}))
        self.assertIn("discovery: screenshot must be a raster capture", self.errors())

    def test_schematic_label_is_required_at_point_of_use(self):
        self.write(self.document, self.markdown.replace("Schematic, not executed UI.", "Actual screenshot.").replace("Discovery schematic", "Actual screenshot"))
        self.assertIn("demo: step 2 schematic must be labeled", self.errors())

    def test_unknown_source_id(self):
        self.catalog["flows"][0]["source_ids"] = ["US999"]
        self.assertIn("demo: unresolved source ID", self.errors())

    def test_supplied_scenario_ids_are_resolved_without_app_imports(self):
        self.write("tests/fixtures/supplied_scenarios.json", json.dumps({"scenario_ids": ["supplied_case"]}))
        self.catalog["flows"][0]["source_ids"] = ["supplied_case"]
        self.assertEqual([], self.errors())

    def test_broken_reference_anchor(self):
        self.catalog["flows"][0]["evidence_refs"] = ["docs/gaps.md#absent"]
        self.assertIn("demo: reference unavailable or anchor missing", self.errors())

    def test_broken_markdown_reference(self):
        self.write(self.document, self.markdown + "\n[Missing](../../gaps.md#absent)\n")
        self.assertIn("demo: Markdown target unavailable or anchor missing", self.errors())

    def test_schema_rejects_extra_fields_wrong_types_and_duplicate_ids(self):
        for mutation in (lambda c: c.update(passed=True),
                         lambda c: c["flows"][0].update(steps="not steps"),
                         lambda c: c["flows"][0].update(status=[]),
                         lambda c: c["controls"][0].update(group={}),
                         lambda c: c["flows"][0]["steps"][0].update(interactive=1),
                         lambda c: c["controls"].append(copy.deepcopy(c["controls"][0]))):
            original = copy.deepcopy(self.catalog)
            mutation(self.catalog)
            self.assertTrue(self.errors())
            self.catalog = original

    def test_manifest_rejects_unknown_fields_and_duplicate_json(self):
        for payload in (json.dumps({"schema_version": 1, "visuals": [{"id": "discovery", "kind": "schematic", "path": "assets/view.svg", "passed": True}]}),
                        '{"schema_version":1,"visuals":[],"visuals":[]}'):
            self.write("assets/ui/walkthroughs/manifest.json", payload)
            self.assertTrue(self.errors())

    def test_cli_rejects_duplicate_and_malformed_json_without_echoing_values(self):
        for payload in ('{"schema_version":1,"schema_version":"secret-canary"}', '{"private":"secret-canary"', '{"schema_version":NaN}'):
            self.write("catalog.json", payload)
            output = io.StringIO()
            with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
                code = self.checker.main(["--root", str(self.root), "--catalog", "catalog.json"])
            self.assertEqual(2, code)
            self.assertNotIn("secret-canary", output.getvalue())

    def test_cli_success_is_structural_not_workflow_certification(self):
        self.write("catalog.json", json.dumps(self.catalog))
        output = io.StringIO()
        with contextlib.redirect_stdout(output):
            code = self.checker.main(["--root", str(self.root), "--catalog", "catalog.json"])
        self.assertEqual(0, code)
        self.assertEqual("structural check passed\n", output.getvalue())

    def test_errors_do_not_echo_untrusted_ids(self):
        self.catalog["flows"][0]["id"] = "secret-canary\nnot-an-id"
        self.assertNotIn("secret-canary", "\n".join(self.errors()))


if __name__ == "__main__":
    unittest.main()
