"""Functional qualification reuses runtime policy and exact helper; no paid calls."""
from contextlib import redirect_stdout
import io
import json
import os
from pathlib import Path
import runpy
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.language import LanguageAdapter
from ochsner_bob import language
from ochsner_bob.model_budget import ModelBudget
from test_language import FakeTransport
from test_model_budget import MODEL, ENV, billed_response

ROOT = Path(__file__).resolve().parents[1]
_KEY = "qualification-not-a-real-key"
_OLD = "inherited-not-a-real-key"


def isolated_runner(directory):
    root = Path(directory) / "qualification-project"
    for name in ("poc-launch.json", "tests/live_model_cases.json", "src/ochsner_bob/language.py",
                 "src/ochsner_bob/model_budget.py", "src/ochsner_bob/runtime_accounting.py", "scripts/qualify_live.py",
                 "tools/poc-runtime/credentials.py", "tools/poc-runtime/export-manifest.json"):
        target = root / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT / name, target)
    runner = runpy.run_path(str(ROOT / "scripts/qualify_live.py"), run_name="qualification_test")
    runner["main"].__globals__["ROOT"] = root
    return runner, root


class QualificationPolicyTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.runner, self.root = isolated_runner(self.temp.name)
        self.ledger = self.root / ".bob-local/model-budget.json"
        guard = patch.object(language, "_http_transport", FakeTransport(error=AssertionError("network forbidden")))
        guard.start()
        self.addCleanup(guard.stop)

    def test_covered_qualification_uses_uncapped_policy_and_named_key_not_parent_key(self):
        budget = ModelBudget(self.ledger)
        document = json.loads(self.ledger.read_text())
        document["calls"] = [{"model": MODEL, "max_output_tokens":512,
            "reserved_nanos":302304000, "status":"unknown", "usage":None}] * 201
        self.ledger.write_text(json.dumps(document))
        received = []
        def adapter(**options):
            received.append(options["environ"])
            return LanguageAdapter(transport=FakeTransport(billed_response()), **options)
        output = io.StringIO()
        with patch.dict(os.environ, {**ENV, "OPENAI_API_KEY":_OLD}), \
                patch.dict(self.runner["main"].__globals__, {"LanguageAdapter":adapter,
                    "resolve_qualification_key":lambda:_KEY}), redirect_stdout(output):
            code = self.runner["main"](["--run-live"])
        self.assertEqual(1, code)  # Fixtures are never genuine qualification.
        report = json.loads(output.getvalue())
        self.assertGreater(report["calls_this_run"], 0)
        self.assertEqual("application_runtime_unlimited", report["budget_after"]["policy"])
        self.assertEqual(_KEY, received[0]["OPENAI_API_KEY"])
        self.assertNotIn(_KEY, output.getvalue()); self.assertNotIn(_OLD, output.getvalue())
        for path in self.ledger.parent.iterdir():
            self.assertNotIn(_KEY.encode(), path.read_bytes())

    def test_exact_notes_helper_runs_privately_and_ignores_parent_credential(self):
        self.assertTrue("resolve_qualification_key" in self.runner, "exact private resolver missing")
        credentials = self.runner["resolve_qualification_key"].__globals__["_runtime_credentials"]
        calls = []
        def helper(argv, **options):
            calls.append((argv, options))
            return subprocess.CompletedProcess(argv, 0, stdout=_KEY+"\n", stderr="")
        with patch.dict(os.environ, {"OPENAI_API_KEY":_OLD, "BW_SESSION":_OLD,
                                    "POC_SECRET_HELPER":"/usr/bin/true"}), \
                patch.object(credentials, "bounded_helper", helper):
            self.assertEqual(_KEY, self.runner["resolve_qualification_key"]())
        self.assertEqual(["[Env] (Ochsner PoC) OPENAI_API_KEY", "notes"], calls[0][0][1:])
        self.assertEqual(1, len(calls))
        self.assertNotIn("OPENAI_API_KEY", calls[0][1]["env"])
        self.assertNotIn("BW_SESSION", calls[0][1]["env"])

    def test_help_and_missing_optin_never_resolve_key_or_touch_accounting(self):
        with patch.dict(self.runner["main"].__globals__, {
                "resolve_qualification_key":lambda: self.fail("unexpected lookup")}), redirect_stdout(io.StringIO()):
            with self.assertRaises(SystemExit) as caught:
                self.runner["main"](["--help"])
            self.assertEqual(0, caught.exception.code)
            self.assertEqual(2, self.runner["main"]([]))
        self.assertFalse(self.ledger.exists())

    def test_missing_accounting_does_not_initialize_or_retrieve_credential(self):
        with patch.dict(os.environ, ENV), patch.dict(self.runner["main"].__globals__, {
                "resolve_qualification_key":lambda:self.fail("unexpected lookup")}), redirect_stdout(io.StringIO()):
            self.assertEqual(2, self.runner["main"](["--run-live"]))
        self.assertFalse(self.ledger.exists())

    def test_alternate_ledger_is_rejected_without_helper_or_new_history(self):
        alternate = self.root / "alternate.json"
        with patch.dict(os.environ, ENV), patch.dict(self.runner["main"].__globals__, {
                "resolve_qualification_key":lambda:self.fail("unexpected lookup")}), redirect_stdout(io.StringIO()):
            self.assertEqual(2, self.runner["main"](["--run-live", "--budget", str(alternate)]))
        self.assertFalse(alternate.exists())

    def test_missing_named_helper_cannot_fall_back_to_inherited_key(self):
        ModelBudget(self.ledger)
        output = io.StringIO()
        with patch.dict(os.environ, {**ENV, "POC_SECRET_HELPER":str(self.root / "missing-helper")}), redirect_stdout(output):
            self.assertEqual(2, self.runner["main"](["--run-live"]))
        self.assertNotIn(ENV["OPENAI_API_KEY"], output.getvalue())
        self.assertEqual(0, ModelBudget(self.ledger, application_runtime=True).snapshot()["calls"])


if __name__ == "__main__":
    unittest.main()
