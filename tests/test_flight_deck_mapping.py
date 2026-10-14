"""BOB consumer mapping tests use the exact exported Ruby implementation."""
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools/aeos-dashboard"
CONFIG = "docs/internal/flight-deck/project.yaml"
PUBLIC_FILES = (
    "specs/001-ochsner-scheduling-assistant/spec.md",
    "specs/001-ochsner-scheduling-assistant/tasks.md",
    "docs/product/next-steps.md", "docs/internal/persona-story-test-index.md",
    "docs/internal/performance-notes.md", "docs/internal/live-qualification.md",
    "docs/internal/ui-assets.md", "docs/internal/security.md",
    "docs/user/walkthroughs/index.md", "docs/user/controls/support.md",
    "docs/internal/as-built/architecture.md",
)
PROBE = r'''
require ARGV.shift
begin
  root = Pathname.new(ARGV.shift).realpath
  config = root.join("docs/internal/flight-deck/project.yaml")
  operation = ARGV.shift
  if operation == "keyword-load"
    # Current Psych accepts one positional YAML value plus keywords. Keep the
    # real parser while removing only the obsolete positional compatibility.
    parser = YAML.method(:safe_load)
    YAML.singleton_class.send(:define_method, :safe_load) do |yaml, permitted_classes: [], permitted_symbols: [], aliases: false|
      parser.call(yaml, permitted_classes: permitted_classes,
                  permitted_symbols: permitted_symbols, aliases: aliases)
    end
  end
  if operation == "config"
    puts JSON.generate(AeosDashboard::PocPaths.structured(config))
  else
    data = AeosDashboard::PocInput.new(project_root: root, config_path: config).load
    result = data.select { |key, _| %w[project requirements capabilities elements diagnostics].include?(key) }
    result["sdk_loaded"] = AeosDashboard.const_defined?(:Loader, false)
    puts JSON.generate(result)
  end
rescue AeosDashboard::Error, SystemCallError, ArgumentError
  puts JSON.generate({"error" => "rejected"})
  exit 2
end
'''


class FlightDeckMappingTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue((ROOT / CONFIG).is_file(), "BOB's six-element mapping is missing")
        self.ruby = shutil.which("ruby")
        self.assertIsNotNone(self.ruby, "The approved Flight Deck consumer requires Ruby")
        self.environ = {key: value for key, value in os.environ.items()
                        if key not in {"OPENAI_API_KEY", "BW_SESSION", "GH_TOKEN", "GITHUB_TOKEN",
                                       "POC_SECRET_HELPER", "BOB_ENABLE_OPENAI"}}
        result = self.probe(ROOT, "config")
        self.assertEqual(0, result.returncode)
        self.config = json.loads(result.stdout)
        directory = tempfile.TemporaryDirectory(prefix="bob-flight-deck-")
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        # Fixed public allowlist only; never discover or copy private app state.
        for relative in PUBLIC_FILES:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.write_config(self.config)

    def probe(self, root, operation="load"):
        return subprocess.run([self.ruby, "--disable-gems", "-e", PROBE,
                               str(RUNTIME / "lib/aeos_dashboard/poc_runtime.rb"), str(root), operation],
                              capture_output=True, text=True, env=self.environ, timeout=20)

    def write_config(self, config):
        path = self.root / CONFIG
        path.parent.mkdir(parents=True, exist_ok=True)
        # JSON is valid YAML; the real exported YAML parser consumes this fixture.
        path.write_text(json.dumps(config), encoding="utf-8")

    def loaded(self):
        result = self.probe(self.root)
        self.assertEqual(0, result.returncode)
        return json.loads(result.stdout)

    def test_native_mapping_has_six_elements_and_only_known_native_ids(self):
        data = self.loaded()
        self.assertEqual({"functional", "ux", "safety", "verification", "training", "readiness"},
                         {row["id"] for row in data["elements"]})
        definitions = set(re.findall(r"\*\*(FR-\d+[a-z]?)(?:\s+[^*]+)?\*\*:",
                                     (self.root / PUBLIC_FILES[0]).read_text()))
        self.assertEqual(definitions, {row["id"] for row in data["requirements"]})
        self.assertTrue(all(row["native_definition_known"] for row in data["requirements"]))
        self.assertFalse(any("unknown native task" in item or "unmapped requirement" in item
                             for item in data["diagnostics"]))
        self.assertFalse(data["sdk_loaded"])

    def test_unknown_native_requirement_and_task_never_become_complete(self):
        for field, value in (("id", "FR-999"), ("task_ids", ["T999"])):
            with self.subTest(field=field):
                changed = copy.deepcopy(self.config)
                changed["requirements"][0][field] = value
                self.write_config(changed)
                data = self.loaded()
                self.assertEqual("UNKNOWN", data["requirements"][0]["lifecycle"]["implementation"]["status"])
                self.assertTrue(data["diagnostics"])

    def test_private_source_path_is_rejected_without_disclosing_its_content(self):
        private = self.root / ".bob-local/hidden.md"
        private.parent.mkdir()
        private.write_text("synthetic-private-canary-must-not-enter-dashboard")
        changed = copy.deepcopy(self.config)
        changed["sources"]["tasks"] = ".bob-local/hidden.md"
        self.write_config(changed)
        result = self.probe(self.root)
        self.assertEqual(2, result.returncode)
        self.assertEqual({"error": "rejected"}, json.loads(result.stdout))
        self.assertNotIn("synthetic-private-canary", result.stdout + result.stderr)

    def test_real_parser_with_current_keyword_only_signature_loads_mapping(self):
        # A removed legacy argument API must not make the standard CI consumer
        # unusable. This is a signature fixture, not real Ruby3 qualification.
        result = self.probe(self.root, "keyword-load")
        self.assertEqual(0, result.returncode,
                         "shared YAML caller depends on removed positional arguments")
        self.assertEqual(6, len(json.loads(result.stdout)["elements"]))

    def test_reviewed_bundle_files_and_source_pin_are_unchanged(self):
        manifest = json.loads((RUNTIME / "export-manifest.json").read_text())
        self.assertEqual("ea7cfea9405f593a56b54c782212ccd9539bd178", manifest["source_revision"])
        self.assertEqual("CLEAN", manifest["working_tree_state"])
        self.assertEqual(24, len(manifest["files"]))
        self.assertEqual("2f326defb7665826bed041047a5c892386f972d230d5fbf5caf73ca402430ebe",
                         hashlib.sha256((RUNTIME / "export-manifest.json").read_bytes()).hexdigest())
        for item in manifest["files"]:
            self.assertEqual(item["sha256"], hashlib.sha256((RUNTIME / item["path"]).read_bytes()).hexdigest())

    def test_actual_generator_retains_unknown_evidence_and_six_artifacts(self):
        destination = self.root / "tools/aeos-dashboard"
        destination.mkdir(parents=True)
        manifest = json.loads((RUNTIME / "export-manifest.json").read_text())
        for relative in ["export-manifest.json"] + [row["path"] for row in manifest["files"]]:
            target = destination / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(RUNTIME / relative, target)
        (self.root / ".gitignore").write_text("tmp/aeos-dashboards/\n")
        for args in (["init", "-q"], ["add", "."], ["-c", "user.name=Synthetic fixture",
                     "-c", "user.email=synthetic@example.invalid", "commit", "-qm", "consumer fixture"]):
            result = subprocess.run(["git", "-C", str(self.root), *args], capture_output=True,
                                    text=True, env=self.environ, timeout=20)
            self.assertEqual(0, result.returncode)
        result = subprocess.run([self.ruby, "--disable-gems", str(destination / "poc-flight-deck"),
                                 "generate", "--root", str(self.root)], capture_output=True,
                                text=True, env=self.environ, timeout=30)
        self.assertEqual(0, result.returncode)
        index = Path(result.stdout.strip())
        self.assertEqual(6, len(list(index.parent.iterdir())))
        snapshot = subprocess.run([self.ruby, "--disable-gems", "-ryaml", "-rjson", "-e",
            "puts JSON.generate(YAML.safe_load(File.read(ARGV.fetch(0)), permitted_classes: [], permitted_symbols: [], aliases: false))",
            str(index.parent / "snapshot.yaml")], capture_output=True, text=True,
            env=self.environ, timeout=10)
        self.assertEqual(0, snapshot.returncode)
        data = json.loads(snapshot.stdout)
        self.assertIsNone(data["summary"]["completion_percent"])
        self.assertTrue(all(row["lifecycle"]["verification"]["status"] == "UNKNOWN"
                            and row["lifecycle"]["acceptance"]["status"] == "UNKNOWN"
                            for row in data["requirements"]))


if __name__ == "__main__":
    unittest.main()
