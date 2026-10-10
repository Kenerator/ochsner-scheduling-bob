"""Source exports retain bounded provenance, never Git/identifier authority."""
from hashlib import sha256
import io
from pathlib import Path
import shutil
import subprocess
import tarfile
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import interaction_service as module
from test_interaction_service import CATALOG
from test_session_contract import FixturePort


ROOT = Path(__file__).resolve().parents[1]
REVISION = "a" * 40


class SourceProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="bob-source-provenance-")
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name) / "export"
        self.root.mkdir()
        for relative in ["pyproject.toml", "policies/bob.json"] + [
                "src/ochsner_bob/" + name for name in module._SOURCE]:
            target = self.root / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / relative, target)
        self.metadata = self.root / ".git_archival.txt"
        self.metadata.write_text("revision=" + REVISION + "\n", encoding="ascii")

    def provenance(self):
        with patch.object(module, "_ROOT", self.root):
            return module.build_provenance(CATALOG)

    def test_git_free_export_starts_offline_and_qualifies_capture_honestly(self):
        port = FixturePort()
        with patch.object(module, "_ROOT", self.root):
            service = module.InteractionService(lambda: port, self.root / "private" / "effects.json",
                                                fixture_catalog=CATALOG)
            token = service.create()["token"]
            self.assertEqual(service.read(token)["interpretation"]["mode"], "offline")
            service.capture(token, True)
            result = service.text(token, "help", 0)
            self.assertEqual(result["state"], "help")
            report = service.capture(token, False)
            self.assertEqual(report["recording"], "incomplete_capture", report)
            service.replay(token, "open", {"reference": report["reference"]})
            replayed = service.replay(token, "step", {})
            self.assertEqual(replayed["state"]["core"]["state"], "help")
            self.assertTrue(replayed["fidelity"]["core_semantic_parity"])
            diagnostic = service.diagnostics(token)
            self.assertEqual(diagnostic["provenance"]["source_revision"], REVISION)
            self.assertEqual(diagnostic["source"]["revision_basis"], "git_archive")
            self.assertEqual(diagnostic["source"]["working_tree_state"], "unknown")
            self.assertTrue(diagnostic["source"]["working_tree_dirty"])
            self.assertFalse(diagnostic["source"]["override"])
            self.assertEqual(port.writes, [])

    def test_archive_identifier_does_not_mask_modified_actual_source_bytes(self):
        first, source = self.provenance()
        self.assertEqual(source["dependency_basis"], "pinned_project_metadata")
        code = b"\0".join(name.encode() + b"\0" + (self.root / "src/ochsner_bob" / name).read_bytes()
                           for name in module._SOURCE)
        self.assertEqual(source["code_digest"], sha256(code).hexdigest())
        target = self.root / "src/ochsner_bob/session.py"
        target.write_bytes(target.read_bytes() + b"\n# synthetic export modification\n")
        second, modified = self.provenance()
        self.assertEqual(first["source_revision"], second["source_revision"])
        self.assertNotEqual(first["schema"], second["schema"])
        self.assertNotEqual(source["code_digest"], modified["code_digest"])
        self.assertEqual(modified["working_tree_state"], "unknown")
        self.assertTrue(modified["working_tree_dirty"])

    def test_ancestor_repository_head_is_never_used_for_an_export(self):
        parent = self.root.parent
        self.git(parent, "init", "-q")
        self.git(parent, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                 "commit", "--allow-empty", "-qm", "synthetic ancestor")
        parent_head = self.git(parent, "rev-parse", "HEAD").decode().strip()
        provenance, source = self.provenance()
        self.assertNotEqual(parent_head, REVISION)
        self.assertEqual(provenance["source_revision"], REVISION)
        self.assertEqual(source["revision_basis"], "git_archive")
        self.metadata.unlink()
        with self.assertRaisesRegex(RuntimeError, "Recording provenance unavailable"):
            self.provenance()

    def test_export_works_without_a_git_executable(self):
        with patch.object(module.subprocess, "run", side_effect=FileNotFoundError("synthetic unavailable Git")):
            provenance, source = self.provenance()
        self.assertEqual(provenance["source_revision"], REVISION)
        self.assertEqual(source["working_tree_state"], "unknown")

    def test_invalid_unsubstituted_missing_or_nonregular_metadata_fails_closed(self):
        bad = (b"revision=$Format:%H$\n", b"revision=" + b"a" * 39 + b"\n",
               b"revision=" + b"A" * 40 + b"\n", b"revision=" + b"0" * 40 + b"\n",
               b"revision=" + b"a" * 40 + b"\nextra=authority\n", b"private-sentinel" * 100,
               b"revision=../private-sentinel\n", b"revision=https://private-sentinel\n", b"\xff")
        for value in bad:
            with self.subTest(value=value[:16]):
                self.metadata.write_bytes(value)
                with self.assertRaisesRegex(RuntimeError, "^Recording provenance unavailable; capture disabled\\.$") as caught:
                    self.provenance()
                self.assertNotIn("private-sentinel", str(caught.exception))
        self.metadata.unlink()
        with self.assertRaises(RuntimeError):
            self.provenance()
        self.metadata.mkdir()
        with self.assertRaises(RuntimeError):
            self.provenance()

    def test_symlink_and_hardlink_metadata_are_rejected_without_following(self):
        target = self.root / "private-sentinel"
        target.write_text("revision=" + REVISION + "\n", encoding="ascii")
        self.metadata.unlink()
        self.metadata.symlink_to(target)
        with self.assertRaises(RuntimeError):
            self.provenance()
        self.metadata.unlink()
        self.metadata.hardlink_to(target)
        with self.assertRaises(RuntimeError):
            self.provenance()
        self.assertEqual(target.read_text(), "revision=" + REVISION + "\n")

    def test_git_checkout_uses_own_head_and_actual_dirty_status_not_archive(self):
        self.git(self.root, "init", "-q")
        self.git(self.root, "add", "--", "src", "policies", "pyproject.toml")
        self.git(self.root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                 "commit", "-qm", "synthetic source")
        provenance, source = self.provenance()
        self.assertEqual(provenance["source_revision"], self.git(self.root, "rev-parse", "HEAD").decode().strip())
        self.assertEqual(source["revision_basis"], "git")
        self.assertEqual(source["working_tree_state"], "clean")
        self.assertFalse(source["working_tree_dirty"])
        target = self.root / "src/ochsner_bob/session.py"
        target.write_bytes(target.read_bytes() + b"\n# synthetic dirty source\n")
        changed, source = self.provenance()
        self.assertEqual(changed["source_revision"], provenance["source_revision"])
        self.assertNotEqual(changed["schema"], provenance["schema"])
        self.assertEqual(source["working_tree_state"], "dirty")
        self.assertTrue(source["working_tree_dirty"])

    def test_real_git_archive_substitutes_only_the_revision_metadata(self):
        for name in (".gitattributes", ".git_archival.txt"):
            shutil.copyfile(ROOT / name, self.root / name)
        source = self.metadata.read_bytes()
        self.assertRegex(source, rb"\Arevision=(?:\$Format:%H\$|[0-9a-f]{40}|[0-9a-f]{64})\n\Z")
        # The suite also runs *inside* an archive, whose template is already
        # substituted. Seed a new local test template to exercise Git itself.
        self.metadata.write_bytes(b"revision=$Format:%H$\n")
        self.git(self.root, "init", "-q")
        self.git(self.root, "add", "--", ".gitattributes", ".git_archival.txt")
        self.git(self.root, "-c", "user.name=Synthetic", "-c", "user.email=synthetic@example.invalid",
                 "commit", "-qm", "synthetic export metadata")
        head = self.git(self.root, "rev-parse", "HEAD").strip()
        payload = self.git(self.root, "archive", "--format=tar", "HEAD")
        with tarfile.open(fileobj=io.BytesIO(payload)) as archive:
            actual = archive.extractfile(".git_archival.txt").read()
        self.assertEqual(actual, b"revision=" + head + b"\n")
        self.assertIn(b"$Format:%H$", self.metadata.read_bytes())

    @staticmethod
    def git(root, *arguments):
        return subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *arguments],
                              cwd=root, capture_output=True, check=True, timeout=5).stdout
