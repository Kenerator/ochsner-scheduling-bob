"""Own-key rollout contracts; offline fakes only, no vault/model/canonical state."""
import importlib.util
import contextlib
import io
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob.model_budget import BudgetError, ModelBudget, preflight_budget
from ochsner_bob import __main__ as cli
from scripts import qualify_connected_live as policy

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from scripts import serve_browser
OWN = {"item": "[Env] OPENAI_API_KEY", "field": "notes",
       "helper_path_env": "POC_SECRET_HELPER", "helper_command": "bw-get-secret"}
OLD = {**OWN, "item": "[Env] (Ochsner PoC) OPENAI_API_KEY"}
_VALUE = "synthetic"
_STALE = "stale"


def runtime_module(name):
    spec = importlib.util.spec_from_file_location("own_key_test_" + name,
        ROOT / "tools/poc-runtime" / (name + ".py"))
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


class OwnKeyBindingTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("http.client.HTTPSConnection", side_effect=AssertionError("no network")))
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="own-key-binding-"))).resolve()

    def test_delivered_bob_configuration_selects_own_note_not_paused_note(self):
        self.assertEqual(json.loads((ROOT / "poc-launch.json").read_text())["credential"], OWN)

    def test_qualifier_accepts_own_binding_and_rejects_paused_note_before_helper(self):
        config = json.loads((ROOT / "poc-launch.json").read_text())
        path = self.directory / "poc-launch.json"
        for credential, accepted in ((OWN, True), (OLD, False)):
            config["credential"] = credential
            path.write_text(json.dumps(config))
            try:
                actual, _digest = policy._config(self.directory)
                result = actual["credential"] == OWN
            except ValueError:
                result = False
            self.assertEqual(result, accepted)

    def test_selected_own_note_resolver_is_exact_private_and_has_no_parent_fallback(self):
        credentials = runtime_module("credentials")
        calls = []
        def helper(argv, **options):
            calls.append((argv, options))
            return subprocess.CompletedProcess(argv, 0, "synthetic\n", "")
        try:
            with patch.dict(os.environ, {"POC_SECRET_HELPER": "/usr/bin/true", "OPENAI_API_KEY": _STALE}):
                value = credentials.resolve_key(OWN, run=helper)
        except credentials.LaunchError:
            self.fail("Reviewed shared resolver does not yet support the selected own note")
        self.assertEqual(value, "synthetic")
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][0][1:], ["[Env] OPENAI_API_KEY", "notes"])
        self.assertNotIn("OPENAI_API_KEY", calls[0][1]["env"])


class OwnKeyBoundedAccountingTests(unittest.TestCase):
    def setUp(self):
        self.enterContext(patch("http.client.HTTPSConnection", side_effect=AssertionError("no network")))
        self.directory = Path(self.enterContext(tempfile.TemporaryDirectory(prefix="own-key-budget-"))).resolve()
        self.owner = self.directory / "owner"
        self.owner.mkdir()
        (self.owner / ".git").mkdir()
        (self.owner / "poc-launch.json").write_bytes((ROOT / "poc-launch.json").read_bytes())
        self.ledger = self.owner / ".bob-local/model-budget.json"
        # Existing historical Ochsner policy creates a fixture above the ordinary
        # own-account limit. New bounded callers must read, not discard it.
        history = ModelBudget(self.ledger, application_runtime=True)
        for _ in range(4):
            identifier = history.reserve(model=policy.MODEL)
            history.settle(identifier, None)
        self.before = history.snapshot()
        self.inode = self.ledger.stat().st_ino
        self.lock = self.ledger.with_name(self.ledger.name + ".lock")
        self.lock_before = (self.lock.stat().st_ino, self.lock.read_bytes())

    def assert_preserved(self):
        current = ModelBudget(self.ledger, application_runtime=True, _existing_only=True).snapshot()
        self.assertEqual(current, self.before)
        self.assertEqual(self.ledger.stat().st_ino, self.inode)
        self.assertEqual((self.lock.stat().st_ino, self.lock.read_bytes()), self.lock_before)

    def test_bounded_existing_sqlite_dispatch_denies_consumed_allowance_without_reset(self):
        try:
            budget = ModelBudget(self.ledger, application_runtime=False,
                _existing_only=True, _existing_writes=True)
        except BudgetError:
            self.fail("Missing bounded existing-SQLite dispatch mode")
        self.assertEqual((budget.max_calls, budget.ceiling), (200, 20_000_000_000))
        with self.assertRaises(BudgetError):
            budget.reserve(model=policy.MODEL)
        self.assert_preserved()

    def test_browser_own_key_mode_cannot_inherit_uncapped_accounting(self):
        with patch.object(serve_browser, "ROOT", self.owner), patch.dict(os.environ,
                {"BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": policy.MODEL, "OPENAI_API_KEY": _VALUE}):
            result = serve_browser.language_for_launch(True).interpret("Find providers")
        self.assertEqual(result.status, "budget_exceeded")
        self.assert_preserved()

    def test_connected_qualifier_own_binding_cannot_bypass_existing_numeric_limits(self):
        with patch.object(policy, "_APPROVED_OWNER_ROOT", self.owner), \
                patch.object(policy, "resolve_qualification_key", return_value="synthetic") as helper:
            binding = policy.canonical_binding(self.owner)
            with self.assertRaises(BudgetError):
                policy.create_language(binding)
            helper.assert_not_called()
        self.assert_preserved()

    def test_numeric_preflight_denies_without_mutating_historical_sqlite(self):
        with self.assertRaises(BudgetError):
            preflight_budget(self.ledger, model=policy.MODEL)
        self.assert_preserved()

    def test_browser_model_start_cannot_initialize_a_fresh_ledger(self):
        fresh = self.directory / "missing-browser"
        fresh.mkdir()
        with patch.object(serve_browser, "ROOT", fresh):
            with self.assertRaises(BudgetError):
                serve_browser.language_for_launch(True)
        self.assertFalse((fresh / ".bob-local").exists())

    def test_cli_model_start_cannot_initialize_a_fresh_ledger(self):
        fresh = self.directory / "missing-cli"
        fresh.mkdir(mode=0o700)
        (fresh / ".bob-local").mkdir(mode=0o700)
        with patch.object(cli, "ROOT", fresh):
            result = cli.main(["--openai", "--journal", str(fresh / ".bob-local/effects.json")],
                input_stream=io.StringIO("/quit\n"), output_stream=io.StringIO())
        self.assertEqual(result, 2)
        self.assertFalse((fresh / ".bob-local/model-budget.json").exists())
        self.assertFalse((fresh / ".bob-local/model-budget.json.lock").exists())

    def test_late_pending_settlement_remains_possible_without_refunding_unknowns(self):
        historical = ModelBudget(self.ledger, application_runtime=True, _existing_only=True, _existing_writes=True)
        pending = historical.reserve(model=policy.MODEL)
        bounded = ModelBudget(self.ledger, application_runtime=False, _existing_only=True, _existing_writes=True)
        usage = {"input_tokens": 10, "output_tokens": 5, "cached_input_tokens": 0, "reasoning_output_tokens": 0}
        receipt = bounded.settle(pending, usage)
        self.assertEqual((pending, receipt["status"]), (5, "known"))
        state = bounded.snapshot()
        self.assertEqual((state["calls"], state["unknown_calls"], state["known_calls"]), (5, 4, 1))
        with self.assertRaises(BudgetError):
            bounded.settle(1, usage)
        with self.assertRaises(BudgetError):
            bounded.reserve(model=policy.MODEL)
        self.assertEqual(self.ledger.stat().st_ino, self.inode)
        self.assertEqual((self.lock.stat().st_ino, self.lock.read_bytes()), self.lock_before)

    def test_legacy_json_cannot_pass_own_key_model_readiness_before_helper(self):
        path = self.directory / "legacy/budget.json"
        ModelBudget(path)
        lock = path.with_name(path.name + ".lock")
        before = (path.read_bytes(), path.stat().st_ino, lock.read_bytes(), lock.stat().st_ino)
        with self.assertRaises(BudgetError):
            preflight_budget(path, model=policy.MODEL)
        self.assertEqual((path.read_bytes(), path.stat().st_ino, lock.read_bytes(), lock.stat().st_ino), before)

    def test_connected_public_preflight_denies_exhausted_numeric_allowance(self):
        with patch.object(policy, "_APPROVED_OWNER_ROOT", self.owner), \
                patch.object(policy, "resolve_qualification_key", side_effect=AssertionError("no lookup")) as helper, \
                contextlib.redirect_stdout(io.StringIO()):
            code = policy.main(["--preflight", "--canonical-owner-root", str(self.owner)])
        self.assertEqual(code, 2)
        helper.assert_not_called()
        self.assert_preserved()
