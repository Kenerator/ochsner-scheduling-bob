"""Structural contract only: no app, vault, network or model is started."""
import contextlib
import base64
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch


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
        self.visual = {"id": "discovery", "kind": "schematic", "path": "assets/view.svg",
                       "sha256": hashlib.sha256((self.root / "assets/view.svg").read_bytes()).hexdigest(),
                       "source_revision": "a" * 40, "working_tree_state": "unknown",
                       "scenario": "demo", "action": "Explain discovery controls",
                       "result": "Schematic only; no execution claimed", "role": "patient",
                       "viewport": {"width": 10, "height": 10}, "width": 10, "height": 10,
                       "source_visual_id": None, "placements": [],
                       "limitations": ["Source freshness is unknown; this is a schematic."]}
        self.manifest = {"schema_version": 1, "visuals": [self.visual]}
        self.save_manifest()
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

    def save_manifest(self):
        self.write("assets/ui/walkthroughs/manifest.json", json.dumps(self.manifest))

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
        self.visual["kind"] = "screenshot"
        self.save_manifest()
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

    def test_empty_catalog_cannot_certify_a_collection(self):
        # Accepting no flows would let an empty template claim completion.
        self.catalog["flows"] = []
        self.assertTrue(self.errors())

    def test_executable_flow_cannot_be_only_empty_setup_and_launch(self):
        self.catalog["flows"][0]["steps"] = self.catalog["flows"][0]["steps"][:2]
        self.assertIn("demo: executable flow requires an interactive step", self.errors())

    def test_visual_requires_exact_provenance_fields(self):
        for key in self.visual:
            with self.subTest(missing=key):
                candidate = copy.deepcopy(self.manifest)
                del candidate["visuals"][0][key]
                self.write("assets/ui/walkthroughs/manifest.json", json.dumps(candidate))
                self.assertTrue(self.errors())

    def test_visual_schema_rejects_wrong_types_and_blank_actions(self):
        for key, value in (("width", True), ("height", 0), ("viewport", []),
                           ("action", ""), ("result", ""), ("role", []),
                           ("source_revision", "not-a-revision"), ("sha256", "wrong"),
                           ("working_tree_state", "current"), ("placements", {}),
                           ("limitations", "none")):
            with self.subTest(field=key):
                candidate = copy.deepcopy(self.manifest)
                candidate["visuals"][0][key] = value
                self.write("assets/ui/walkthroughs/manifest.json", json.dumps(candidate))
                self.assertTrue(self.errors())

    def test_asset_hash_and_declared_dimensions_are_verified(self):
        for key, value in (("sha256", "0" * 64), ("width", 11), ("height", 11)):
            self.visual[key] = value
            self.save_manifest()
            self.assertTrue(self.errors())
            self.visual.update(sha256=hashlib.sha256((self.root / "assets/view.svg").read_bytes()).hexdigest(),
                               width=10, height=10)

    def test_renamed_schematic_is_not_a_raster_capture(self):
        (self.root / "assets/fake.png").write_bytes((self.root / "assets/view.svg").read_bytes())
        self.visual.update(kind="screenshot", path="assets/fake.png")
        self.save_manifest()
        self.assertTrue(self.errors())

    def test_annotations_require_a_clean_source_with_matching_dimensions(self):
        layer = copy.deepcopy(self.visual)
        layer.update(id="layer", kind="annotation", source_visual_id="discovery")
        self.manifest["visuals"].append(layer)
        self.save_manifest()
        self.assertTrue(self.errors(), "a schematic is not an executed screenshot source")
        layer["source_visual_id"] = "missing"
        self.save_manifest()
        self.assertTrue(self.errors())

    def test_annotation_placement_is_finite_integer_positive_and_contained(self):
        source = {"width": 1280, "height": 720}
        self.assertEqual([], self.checker.check_placement(source,
                         {"x": 0, "y": 0, "width": 1280, "height": 720}))
        self.assertEqual(["annotation exceeds source bounds"], self.checker.check_placement(source,
                         {"x": 1270, "y": 10, "width": 40, "height": 20}))
        for key, value in (("x", -1), ("x", True), ("y", float("nan")),
                           ("width", 0), ("height", 1.5)):
            rectangle = {"x": 0, "y": 0, "width": 10, "height": 10, key: value}
            self.assertEqual(["invalid annotation placement"], self.checker.check_placement(source, rectangle))

    def test_private_paths_are_rejected_even_when_files_exist(self):
        for private in (".bob-local/private.md", ".env", "docs/product/intake/001.md",
                        "docs/product/RFP/source/assignment.md", "tmp/private.md"):
            self.write(private, "# Private\n")
            self.catalog["flows"][0]["source_ids"] = [private]
            self.assertIn("demo: unresolved source ID", self.errors())

    def test_private_markdown_link_and_symlink_ancestor_are_rejected(self):
        self.write(".bob-local/private.md", "# Private\n")
        self.write(self.document, self.markdown + "\n[Do not publish](../../../.bob-local/private.md)\n")
        self.assertIn("demo: Markdown target unavailable or anchor missing", self.errors())
        (self.root / "alias").symlink_to(self.root / "docs", target_is_directory=True)
        self.catalog["flows"][0]["document"] = "alias/user/walkthroughs/demo.md"
        self.assertIn("demo: document unavailable or unsafe", self.errors())

    def test_stale_source_needs_explicit_historical_limitation(self):
        self.visual.update(working_tree_state="clean", limitations=[])
        self.save_manifest()
        with patch.object(self.checker, "_revision", return_value="b" * 40):
            self.assertIn("discovery: historical source requires an explicit limitation", self.errors())

    def test_svg_active_content_is_not_adopted_as_safe_visual(self):
        self.write("assets/view.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="10" height="10"><script>private-canary</script></svg>')
        self.visual["sha256"] = hashlib.sha256((self.root / "assets/view.svg").read_bytes()).hexdigest()
        self.save_manifest()
        self.assertTrue(self.errors())

    def test_checker_is_read_only_and_never_uses_network_or_application(self):
        before = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        with patch("socket.socket", side_effect=AssertionError("network is prohibited")):
            self.assertEqual([], self.errors())
        after = {p.relative_to(self.root): p.read_bytes() for p in self.root.rglob("*") if p.is_file()}
        self.assertEqual(before, after)

    def test_cli_argument_errors_never_echo_raw_values(self):
        output = io.StringIO()
        with contextlib.redirect_stdout(output), contextlib.redirect_stderr(output):
            code = self.checker.main(["--root", str(self.root), "--catalog", "catalog.json",
                                      "--unknown", "secret-canary"])
        self.assertEqual(2, code)
        self.assertNotIn("secret-canary", output.getvalue())

    def raster_source(self):
        # Fixed one-pixel PNG fixture; header dimensions are independently 1×1.
        pixel = base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+/l1sAAAAASUVORK5CYII=")
        (self.root / "assets/pixel.png").write_bytes(pixel)
        self.visual.update(kind="screenshot", path="assets/pixel.png", width=1, height=1,
                           viewport={"width": 1, "height": 1}, sha256=hashlib.sha256(pixel).hexdigest())
        self.write(self.document, self.markdown.replace("assets/view.svg", "assets/pixel.png"))
        self.write("docs/user/controls/public.md", "# Public\n\n![Capture fixture](../../../assets/pixel.png)\n")
        self.save_manifest()

    def annotation(self, *, composite=False):
        layer = copy.deepcopy(self.visual)
        path = "assets/composite.svg" if composite else "assets/overlay.svg"
        svg = ('<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1">'
               + ('<image href="pixel.png" width="1" height="1"/>' if composite else '')
               + '<rect x="0" y="0" width="1" height="1" fill="none"/></svg>')
        self.write(path, svg)
        layer.update(id="layer", kind="composite" if composite else "annotation", path=path,
                     sha256=hashlib.sha256(svg.encode()).hexdigest(), source_visual_id="discovery",
                     placements=[{"x": 0, "y": 0, "width": 1, "height": 1}])
        self.manifest["visuals"].append(layer)
        self.save_manifest()
        return layer

    def test_real_png_header_and_separate_overlay_are_valid(self):
        self.raster_source()
        self.annotation()
        self.assertEqual([], self.errors())

    def test_composite_svg_may_embed_only_its_declared_local_clean_source(self):
        self.raster_source()
        self.annotation(composite=True)
        self.assertEqual([], self.errors())
        self.write("assets/composite.svg", '<svg xmlns="http://www.w3.org/2000/svg" width="1" height="1"><image href="https://example.invalid/private.png"/></svg>')
        self.assertTrue(self.errors())

    def test_layer_dimensions_and_source_identity_must_match(self):
        for field, value in (("width", 2), ("viewport", {"width": 2, "height": 1}),
                             ("source_revision", "b" * 40), ("role", "support")):
            with self.subTest(field=field):
                self.raster_source()
                self.manifest["visuals"] = [self.visual]
                layer = self.annotation()
                layer[field] = value
                self.save_manifest()
                self.assertIn("layer: annotation/source provenance or dimensions mismatch", self.errors())

    def test_manifest_placement_outside_clean_source_is_rejected(self):
        self.raster_source()
        layer = self.annotation()
        layer["placements"][0]["x"] = 1
        self.save_manifest()
        self.assertIn("layer: annotation exceeds source bounds", self.errors())

    def test_forged_layer_or_cycle_is_not_a_clean_capture(self):
        self.raster_source()
        layer = self.annotation()
        layer["source_visual_id"] = "layer"
        self.save_manifest()
        self.assertIn("layer: annotation requires a clean screenshot source", self.errors())
        self.visual["source_visual_id"] = "layer"
        self.save_manifest()
        self.assertIn("discovery: clean visual cannot name an annotation source", self.errors())

    def test_jpeg_header_dimensions_and_truncated_markers(self):
        # SOF0 says width 3 / height 2; header check is not pixel decoding.
        raw = bytes.fromhex("ffd8 ffc0 000b 08 0002 0003 01 01 1100 ffd9")
        self.assertEqual((3, 2), self.checker._dimensions(Path("fixture.jpg"), raw))
        for broken in (b"", b"\xff\xd8\xff", bytes.fromhex("ffd8 ffe0 ffff 00")):
            with self.assertRaises(ValueError):
                self.checker._dimensions(Path("fixture.jpg"), broken)

    def test_local_git_metadata_freshness_and_unknown_root_are_distinct(self):
        self.assertIsNone(self.checker._revision(self.root))
        self.write(".git/HEAD", "ref: refs/heads/example\n")
        self.write(".git/refs/heads/example", "a" * 40 + "\n")
        self.visual.update(working_tree_state="clean", limitations=[])
        self.save_manifest()
        self.assertEqual([], self.errors())
        self.write(".git/refs/heads/example", "b" * 40 + "\n")
        self.assertIn("discovery: historical source requires an explicit limitation", self.errors())
        self.visual["limitations"] = ["Historical source, not current execution evidence."]
        self.save_manifest()
        self.assertEqual([], self.errors())


if __name__ == "__main__":
    unittest.main()
