"""Real owned synthetic children must not inherit the model host's secrets."""
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mock_lifecycle

_CANARY = "canary-not-a-real-credential"


class MockChildEnvironmentTests(unittest.TestCase):
    def observe_child(self, parent, public):
        # Keep the actual Popen/readiness/vendor/cleanup boundary. Instrument only
        # the child runner to report booleans into a private temporary file.
        with tempfile.TemporaryDirectory() as temporary:
            report = Path(temporary) / "presence.json"
            probe = (
                "import json, os\n"
                f"names = {tuple(parent)!r}\n"
                f"public = {public!r}\n"
                "result = {'private_present': {name: name in os.environ for name in names if name not in public},\n"
                "          'public_matches': {name: os.environ.get(name) == value for name, value in public.items()},\n"
                "          'bytecode_disabled': os.environ.get('PYTHONDONTWRITEBYTECODE') == '1'}\n"
                f"fd = os.open({str(report)!r}, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)\n"
                "with os.fdopen(fd, 'w') as stream: json.dump(result, stream)\n"
            )
            with patch.dict(os.environ, parent, clear=True), \
                 patch.object(mock_lifecycle, "_RUNNER", probe + mock_lifecycle._RUNNER):
                with mock_lifecycle.OwnedMock() as owned:
                    self.assertTrue(owned.base_url.startswith("http://127.0.0.1:"))
                    result = json.loads(report.read_text())
                    self.assertEqual(report.stat().st_mode & 0o777, 0o600)
                    self.assertIsNone(owned.process.poll())
                self.assertIsNotNone(owned.process.poll())
            return result

    def test_real_mock_child_excludes_model_vault_and_unrelated_canaries(self):
        public = {"PATH": os.environ.get("PATH", "/usr/bin:/bin"),
                  "LANG": "C", "TZ": "America/Chicago", "TMPDIR": tempfile.gettempdir()}
        parent = {**public, "OPENAI_API_KEY": _CANARY,
                  "BW_SESSION": _CANARY, "GITHUB_TOKEN": _CANARY,
                  "UNRELATED_APP_PASSWORD": _CANARY,
                  "BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": "canary-public-model",
                  "PYTHONPATH": "/nonexistent/canary-import-path"}
        observed = self.observe_child(parent, public)
        self.assertEqual(observed["private_present"], {
            "OPENAI_API_KEY": False, "BW_SESSION": False, "GITHUB_TOKEN": False,
            "UNRELATED_APP_PASSWORD": False, "BOB_ENABLE_OPENAI": False,
            "BOB_OPENAI_MODEL": False, "PYTHONPATH": False})
        self.assertEqual(observed["public_matches"], {"PATH": True, "LANG": True, "TZ": True, "TMPDIR": True})
        self.assertTrue(observed["bytecode_disabled"])

    def test_real_mock_starts_without_optional_parent_runtime_variables(self):
        observed = self.observe_child({}, {})
        self.assertEqual(observed, {"private_present": {}, "public_matches": {}, "bytecode_disabled": True})


if __name__ == "__main__":
    unittest.main()
