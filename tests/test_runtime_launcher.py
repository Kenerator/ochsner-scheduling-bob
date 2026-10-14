"""Consumer routing tests use actual BOB constructors, never a live key/model."""
from contextlib import redirect_stderr, redirect_stdout
import hashlib
import importlib
import io
import json
import os
from pathlib import Path
import socket
import shutil
import subprocess
import sys
import tempfile
import urllib.request
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
RUNTIME = ROOT / "tools/poc-runtime"
_CANARY = "canary-not-a-real-key"
_STALE = "stale-parent-canary"
_MODEL = "gpt-5.4-2026-03-05"


def free_ports():
    with socket.socket() as first, socket.socket() as second:
        first.bind(("127.0.0.1", 0)); second.bind(("127.0.0.1", 0))
        return first.getsockname()[1], second.getsockname()[1]


class RuntimeLauncherTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(RUNTIME.is_dir(), "Pinned application runtime is not installed")
        sys.path.insert(0, str(RUNTIME))
        self.addCleanup(sys.path.remove, str(RUNTIME))
        self.launch = importlib.import_module("launch")
        self.adapters = importlib.import_module("adapters")
        self.credentials = importlib.import_module("credentials")
        self.processes = importlib.import_module("processes")
        self.config = self.launch.load_config(ROOT / "poc-launch.json")

    def request(self, *arguments):
        return self.launch.resolve_request(self.config, list(arguments), {})

    def test_managed_bundle_has_exact_reviewed_hashes(self):
        manifest = json.loads((RUNTIME / "export-manifest.json").read_text())
        self.assertEqual(manifest["source_revision"], "17d415766a7dead713ccebcbbf6c36516a64ba3c")
        self.assertEqual(manifest["source_worktree_state"], "clean")
        self.assertEqual(set(manifest["files"]), {"tools/poc-runtime/" + name for name in
                         ("adapters.py", "credentials.py", "launch.py", "processes.py")})
        for name, digest in manifest["files"].items():
            self.assertEqual(hashlib.sha256((ROOT / name).read_bytes()).hexdigest(), digest)

    def test_model_default_and_explicit_override_precedence(self):
        self.assertEqual((self.request().mode, self.request().interface, self.request().model),
                         ("model", "browser", _MODEL))
        environ = {"BOB_OPENAI_MODEL": "gpt-5.4-mini-2026-03-17"}
        self.assertEqual(self.launch.resolve_request(self.config, [], environ).model, environ["BOB_OPENAI_MODEL"])
        self.assertEqual(self.launch.resolve_request(self.config, ["--model", _MODEL], environ).model, _MODEL)
        self.assertEqual(self.config["credential"]["field"], "notes")

    def test_invalid_requests_do_not_silently_change_mode(self):
        for args in (("--offline", "--unlimited-today"), ("--model", " "), ("--bogus",),
                     ("--ui-port", "0")):
            with self.subTest(args=args), self.assertRaises(self.credentials.LaunchError):
                self.request(*args)

    def test_actual_browser_specs_scope_key_and_backend_origin(self):
        request = self.request("--ui-port", "29450", "--transport-port", "29451")
        parent = {"PATH": os.environ.get("PATH", ""), "OPENAI_API_KEY": _CANARY,
                  "BW_SESSION": _CANARY, "GITHUB_TOKEN": _CANARY}
        with patch.dict(os.environ, parent, clear=True):
            specs = self.adapters.process_specs(ROOT, self.config, request, key=_CANARY)
        model, viewer = specs
        self.assertEqual((model.role, viewer.role), ("model", "viewer"))
        self.assertEqual(model.environment["BOB_ENABLE_OPENAI"], "1")
        self.assertEqual(model.environment["BOB_OPENAI_MODEL"], _MODEL)
        self.assertEqual(model.environment["OPENAI_API_KEY"], _CANARY)
        self.assertEqual(viewer.environment["BOB_TRANSPORT_URL"], "http://127.0.0.1:29451")
        self.assertEqual((model.readiness_port, viewer.readiness_port), (29451, 29450))
        self.assertIn("--openai", model.argv); self.assertNotIn("--unlimited-today", model.argv)
        self.assertNotIn("OPENAI_API_KEY", viewer.environment)
        for spec in specs:
            self.assertNotIn("BW_SESSION", spec.environment); self.assertNotIn("GITHUB_TOKEN", spec.environment)
            self.assertNotIn(_CANARY, repr(spec)); self.assertNotIn(_CANARY, " ".join(spec.argv))

    def test_offline_specs_strip_inherited_key_and_model_settings(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": _CANARY, "BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": _MODEL}):
            specs = self.adapters.process_specs(ROOT, self.config, self.request("--offline"), key=_CANARY)
        for spec in specs:
            for name in ("OPENAI_API_KEY", "BOB_ENABLE_OPENAI", "BOB_OPENAI_MODEL"):
                self.assertNotIn(name, spec.environment)
            self.assertNotIn("--openai", spec.argv)

    def test_browser_constructor_uses_real_language_adapter_and_shared_ledger(self):
        sys.path.insert(0, str(ROOT / "scripts"))
        try:
            import serve_browser
        finally:
            sys.path.remove(str(ROOT / "scripts"))
        from ochsner_bob.model_budget import ModelBudget
        spec = self.adapters.process_specs(ROOT, self.config, self.request(), key=_CANARY)[0]
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(serve_browser, "ROOT", root), patch.dict(os.environ, spec.environment, clear=True):
                adapter = serve_browser.language_for_launch("--openai" in spec.argv)
                self.assertEqual(adapter.mode, "openai")
                # Replace only HTTPS transport; the actual adapter still validates,
                # reserves and settles a deliberately unavailable fake request.
                captured = []
                def boundary(payload, **kwargs):
                    captured.append(json.loads(payload))
                    raise OSError("synthetic unavailable")
                adapter._transport = boundary
                result = adapter.interpret("Find primary care downtown")
            self.assertEqual(result.status, "unavailable")
            self.assertEqual(captured[0]["model"], _MODEL)
            self.assertEqual(captured[0]["tools"], [])
            ledger = ModelBudget(root / ".bob-local/model-budget.json")
            self.assertEqual((ledger.snapshot()["calls"], ledger.snapshot()["unknown_calls"]), (1, 1))

    def test_actual_cli_constructor_routes_model_without_dispatch_on_help(self):
        import ochsner_bob.__main__ as cli
        from ochsner_bob.language import LanguageAdapter
        spec = next(spec for spec in self.adapters.process_specs(ROOT, self.config,
                    self.request("--interface", "cli"), key=_CANARY) if spec.role == "model")
        seen = []
        real = LanguageAdapter
        def construct(**kwargs):
            result = real(**kwargs); seen.append(result); return result
        with tempfile.TemporaryDirectory() as temporary:
            args = list(spec.argv[3:]); args[args.index("--journal") + 1] = str(Path(temporary) / "effects.json")
            with patch.object(cli, "ROOT", Path(temporary)), patch.object(cli, "LanguageAdapter", construct), \
                 patch.dict(os.environ, spec.environment, clear=True), \
                 patch("ochsner_bob.language._http_transport", side_effect=AssertionError("model request during local help")):
                output = io.StringIO()
                self.assertEqual(cli.main(args, input_stream=io.StringIO("help\n/quit\n"), output_stream=output), 0)
            self.assertEqual(seen[0].mode, "openai")
            self.assertIn("OpenAI interpretation explicitly requested", output.getvalue())
            self.assertEqual(seen[0]._budget.snapshot()["calls"], 0)

    def test_cli_plan_owns_synthetic_api_and_routes_matching_url(self):
        api, _ = free_ports()
        specs = self.adapters.process_specs(ROOT, self.config, self.request(
            "--offline", "--interface", "cli", "--api-port", str(api)))
        self.assertEqual([spec.role for spec in specs], ["mock", "model"])
        self.assertEqual(specs[0].readiness_port, api)
        self.assertEqual(specs[1].argv[specs[1].argv.index("--api-url") + 1], f"http://127.0.0.1:{api}")
        self.assertNotIn("OPENAI_API_KEY", specs[0].environment)

    def test_normal_offline_cli_launch_runs_provider_read_and_cleans_api(self):
        # Match the documented offline prerequisite in a clean committed export;
        # the app creates only its immediate run namespace, not missing ancestors.
        (ROOT / ".bob-local").mkdir(mode=0o700, exist_ok=True)
        api, _ = free_ports()
        environment = self.credentials.child_environment(os.environ, settings={"PYTHONPATH": str(ROOT / "src")})
        result = subprocess.run([sys.executable, str(RUNTIME / "launch.py"), "--offline", "--interface", "cli",
                                 "--api-port", str(api)], cwd=ROOT, env=environment,
                                input="providers primary_care downtown\n/quit\n", capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("Dr. Elena Brooks", result.stdout)
        self.assertNotIn("OPENAI_API_KEY", result.stdout + result.stderr)
        with self.assertRaises(OSError): socket.create_connection(("127.0.0.1", api), timeout=0.2)

    def test_cli_conflict_leaves_foreign_listener_untouched(self):
        with socket.socket() as foreign:
            foreign.bind(("127.0.0.1", 0)); foreign.listen()
            result = subprocess.run([sys.executable, str(RUNTIME / "launch.py"), "--offline", "--interface", "cli",
                                     "--api-port", str(foreign.getsockname()[1])], cwd=ROOT,
                                    env=self.credentials.child_environment(os.environ, settings={}),
                                    capture_output=True, text=True, timeout=5)
            self.assertEqual(result.returncode, 2)
            self.assertIn("occupied", result.stderr)
            # SO_ACCEPTCONN is unavailable on the selected macOS interpreter;
            # prove the foreign listener still accepts a real connection instead.
            foreign.settimeout(1)
            with socket.create_connection(foreign.getsockname(), timeout=1):
                accepted, _ = foreign.accept()
                accepted.close()

    def test_accounting_preflight_delegates_existing_canonical_path_without_waiver(self):
        from ochsner_bob.model_budget import ModelBudget, preflight_budget
        import ochsner_bob.model_budget as budget_module
        with tempfile.TemporaryDirectory() as temporary:
            ledger = Path(temporary) / "model-budget.json"; budget = ModelBudget(ledger)
            before = ledger.read_bytes(); received = []
            def boundary(path, **kwargs):
                received.append((path, kwargs)); preflight_budget(ledger, **kwargs)
            with patch.object(budget_module, "preflight_budget", boundary):
                self.adapters.check_bob_budget(ROOT, _MODEL)
            self.assertEqual(received, [(ROOT / ".bob-local/model-budget.json", {"model": _MODEL})])
            self.assertEqual(ledger.read_bytes(), before); self.assertEqual(budget.snapshot()["calls"], 0)

    def test_missing_ledger_fails_without_initialization(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            with patch.object(self.adapters, "_regular", return_value=ROOT / "src/ochsner_bob/model_budget.py"):
                with self.assertRaises(self.credentials.LaunchError):
                    self.adapters.check_bob_budget(root, _MODEL)
            self.assertFalse((root / ".bob-local").exists())

    def test_help_never_loads_key_or_starts_services(self):
        with patch.object(self.credentials, "resolve_key", side_effect=AssertionError("key lookup")), \
             patch.object(self.processes, "run_owned", side_effect=AssertionError("service startup")), redirect_stdout(io.StringIO()):
            self.assertEqual(self.launch.main(["--help"]), 0)

    def test_offline_doctor_uses_real_preflight_without_credentials_or_startup(self):
        ui, transport = free_ports()
        with patch.object(self.credentials, "resolve_key", side_effect=AssertionError("key lookup")), \
             patch.object(self.processes, "run_owned", side_effect=AssertionError("service startup")), redirect_stdout(io.StringIO()):
            self.assertEqual(self.launch.main(["--config", str(ROOT / "poc-launch.json"), "--offline", "--doctor",
                                              "--ui-port", str(ui), "--transport-port", str(transport)]), 0)

    def test_model_doctor_fails_missing_budget_without_secret_lookup_or_creation(self):
        self.assertFalse((ROOT / ".bob-local/model-budget.json").exists())
        ui, transport = free_ports(); output = io.StringIO()
        with patch.object(self.credentials, "resolve_key", side_effect=AssertionError("key lookup")), \
             patch.object(self.processes, "run_owned", side_effect=AssertionError("service startup")), redirect_stderr(output):
            self.assertEqual(self.launch.main(["--config", str(ROOT / "poc-launch.json"), "--doctor",
                                              "--ui-port", str(ui), "--transport-port", str(transport)]), 2)
        self.assertIn("no new ledger was created", output.getvalue())
        self.assertFalse((ROOT / ".bob-local/model-budget.json").exists())

    def test_actual_child_environments_receive_only_role_scoped_fake_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": _CANARY, "BW_SESSION": _CANARY, "GITHUB_TOKEN": _CANARY}):
            specs = self.adapters.process_specs(ROOT, self.config, self.request(), key=_CANARY)
        program = "import os,json; print(json.dumps({k:k in os.environ for k in ('OPENAI_API_KEY','BW_SESSION','GITHUB_TOKEN')}))"
        for spec, expected in zip(specs, (True, False)):
            completed = subprocess.run([sys.executable, "-c", program], env=spec.environment,
                                       capture_output=True, text=True, timeout=3)
            self.assertEqual(completed.returncode, 0)
            self.assertEqual(json.loads(completed.stdout), {"OPENAI_API_KEY": expected, "BW_SESSION": False, "GITHUB_TOKEN": False})

    def test_occupied_port_fails_without_stopping_foreign_listener(self):
        with socket.socket() as foreign:
            foreign.bind(("127.0.0.1", 0)); foreign.listen()
            port = foreign.getsockname()[1]
            with self.assertRaises(self.credentials.LaunchError): self.adapters.check_ports([port])
            self.assertEqual(foreign.getsockname()[1], port)

    def test_real_owned_offline_backend_serves_providers_and_is_reaped(self):
        ui, transport = free_ports()
        specs = self.adapters.process_specs(ROOT, self.config, self.request(
            "--offline", "--ui-port", str(ui), "--transport-port", str(transport)))
        children = []
        with tempfile.TemporaryDirectory() as temporary:
            parent = Path(temporary) / ".bob-local"; parent.mkdir(mode=0o700)
            spec = specs[0]; argv = list(spec.argv)
            argv[argv.index("--namespace") + 1] = str(parent / "owned-run")
            spec = self.processes.ProcessSpec(spec.role, tuple(argv), spec.environment, spec.readiness_port)
            def start(*args, **kwargs):
                child = subprocess.Popen(*args, **kwargs); children.append(child); return child
            def inspect(_owned, _specs):
                def post(path, data, token=None):
                    headers = {"Content-Type": "application/json", "Origin": f"http://127.0.0.1:{ui}"}
                    if token: headers["Authorization"] = "Bearer " + token
                    request = urllib.request.Request(f"http://127.0.0.1:{transport}" + path,
                        data=json.dumps(data).encode(), headers=headers)
                    with urllib.request.urlopen(request, timeout=3) as response: return json.load(response)
                created = post("/create", {})
                result = post("/text", {"text": "providers primary_care downtown", "revision": 0}, created["token"])
                self.assertEqual(result["providers"][0]["name"], "Dr. Elena Brooks")
                self.assertEqual(result["interpretation"]["mode"], "offline")
                # Wrong Origin must remain rejected even on a configured pair.
                bad = urllib.request.Request(f"http://127.0.0.1:{transport}/", method="OPTIONS",
                                             headers={"Origin": f"http://127.0.0.1:{ui + 1}"})
                with self.assertRaises(urllib.error.HTTPError) as denied: urllib.request.urlopen(bad, timeout=3)
                self.assertEqual(denied.exception.code, 403)
                return 0
            with patch.object(self.processes, "wait_for_selected_application", inspect):
                self.assertEqual(self.processes.run_owned([spec], popen=start), 0)
            self.assertIsNotNone(children[0].poll())
            with self.assertRaises(OSError): socket.create_connection(("127.0.0.1", transport), timeout=0.2)
            self.assertFalse((parent / "model-budget.json").exists())

    def test_exact_notes_helper_ignores_inherited_credentials(self):
        calls = []
        def boundary(argv, **kwargs):
            calls.append((argv, kwargs["env"]))
            return subprocess.CompletedProcess(argv, 0, stdout=_CANARY + "\n", stderr="")
        with patch.dict(os.environ, {"OPENAI_API_KEY": _STALE, "BW_SESSION": _CANARY,
                                    "POC_SECRET_HELPER": "/usr/bin/true"}), \
             patch.object(self.credentials, "bounded_helper", side_effect=AssertionError("real helper")):
            self.assertEqual(self.credentials.resolve_key(self.config["credential"], run=boundary), _CANARY)
        self.assertEqual(calls[0][0][1:], ["[Env] (Ochsner PoC) OPENAI_API_KEY", "notes"])
        self.assertEqual(len(calls), 1)
        self.assertNotIn("OPENAI_API_KEY", calls[0][1]); self.assertNotIn("BW_SESSION", calls[0][1])

    def test_missing_helper_does_not_fall_back_to_inherited_key(self):
        with patch.dict(os.environ, {"OPENAI_API_KEY": _CANARY, "POC_SECRET_HELPER": "/no/such/helper"}):
            with self.assertRaises(self.credentials.LaunchError): self.credentials.resolve_key(self.config["credential"])


class BackendURLTests(unittest.TestCase):
    def test_shipped_renderer_uses_public_transport_trait(self):
        result = subprocess.run([shutil.which("node"), str(ROOT / "tests/widget_harness.mjs"), "--transport-routing"],
                                capture_output=True, text=True, timeout=5)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_default_transport_remains_compatible(self):
        from ochsner_bob.widget import SchedulingWidget
        with patch.dict(os.environ, {}, clear=True): widget = SchedulingWidget()
        self.addCleanup(widget.close)
        self.assertEqual(widget.backend_url, "http://127.0.0.1:28451")

    def test_launcher_public_url_reaches_synced_trait(self):
        from ochsner_bob.widget import SchedulingWidget
        with patch.dict(os.environ, {"BOB_TRANSPORT_URL": "http://127.0.0.1:29451"}): widget = SchedulingWidget()
        self.addCleanup(widget.close)
        self.assertEqual(widget.get_state()["backend_url"], "http://127.0.0.1:29451")

    def test_later_trait_assignment_cannot_redirect_off_host(self):
        from ochsner_bob.widget import SchedulingWidget
        with patch.dict(os.environ, {}, clear=True): widget = SchedulingWidget()
        self.addCleanup(widget.close)
        with self.assertRaises(ValueError): widget.backend_url = "http://example.com:29451"
        self.assertEqual(widget.backend_url, "http://127.0.0.1:28451")

    def test_non_loopback_and_ambiguous_urls_fail_closed(self):
        from ochsner_bob.widget import SchedulingWidget
        for url in ("https://127.0.0.1:29451", "http://example.com:29451", "http://localhost:29451",
                    "http://127.0.0.1:0", "http://127.0.0.1:65536", "http://127.0.0.1:29451/path",
                    "http://user@127.0.0.1:29451", "http://127.0.0.1:29451?key=x", "http://127.0.0.1:29451#x"):
            with self.subTest(url=url), patch.dict(os.environ, {"BOB_TRANSPORT_URL": url}):
                with self.assertRaises(ValueError): SchedulingWidget()


if __name__ == "__main__":
    unittest.main()
