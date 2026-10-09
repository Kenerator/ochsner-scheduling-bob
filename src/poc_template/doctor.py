"""Read-only local diagnostics; no assistant invocation, installation or automatic repair."""
import os
from pathlib import Path
import shutil
import socket
import sys
import tempfile

from .bootstrap import normalize_execution
from .bootstrap_workflow import config_for
from .project_git import git_environment
from .spec_kit_assets import verify_assets, verify_runtime
from .speckit_adapter import run_process


def probe_write(parent: Path) -> dict:
    """Explicit exclusive create/remove probe under the caller's real permissions."""
    parent = Path(parent).absolute()
    path = None
    try:
        if parent.is_symlink() or not parent.is_dir():
            raise ValueError("Probe parent must be an existing non-symlink directory")
        descriptor, name = tempfile.mkstemp(prefix=".poc-write-probe-", dir=parent)
        path = Path(name)
        os.close(descriptor)
        return dict(status="ready", parent=str(parent), detail="Owned exclusive write probe passed; caller permissions only")
    except (ValueError, OSError):
        return dict(status="blocked", parent=str(parent), detail="Cannot create owned probe; resolve parent/host permissions")
    finally:
        if path is not None:
            path.unlink()


def inspect_project(root: Path, *, operation: str | None = None, launch: dict | None = None) -> dict:
    if operation is not None and operation not in {"offline", "automatic-stage", "qualification", "delivery"}:
        raise ValueError("Unknown doctor operation")
    root = Path(root).resolve()
    checks = []

    def note(name, status, detail):
        checks.append(dict(name=name, status=status, detail=detail))

    note("python", "ok" if sys.version_info >= (3, 11) else "error",
         f"{sys.executable}: {sys.version.split()[0]}; Python 3.11+ required")
    if not root.is_dir():
        note("project", "error", "Project directory does not exist")
        return dict(project=str(root), status="issues", checks=checks, operation=operation,
                    capabilities=[dict(name="project", required=True, status="blocked", detail="Project missing")])
    config, required = {}, False
    try:
        if (root/".specify/bootstrap.json").exists():
            config = config_for(root)
            normalize_execution(config["integration"], config.get("execution"))
            required = config["through"] > 0 if operation is None else operation == "automatic-stage"
            note("configuration", "ok", f"Cumulative target {config['through']}; {config['integration']}")
        else:
            note("configuration", "warning", "No bound bootstrap configuration; checking Template/offline surface only")
    except (ValueError, OSError, KeyError, TypeError) as error:
        note("configuration", "error", str(error))
    required = required or operation == "automatic-stage"
    operation = operation or ("automatic-stage" if required else "offline")
    launch = launch if launch is not None else config.get("launch", {})
    for name, verifier in (("assets", verify_assets), ("runtime", verify_runtime)):
        try:
            verifier(root)
            note(name, "ok", "Reviewed Spec-Kit pin verified")
        except (ValueError, OSError, KeyError, TypeError) as error:
            note(name, "error" if name == "assets" or required else "warning", str(error))
    integration = config.get("integration", "codex")
    extra = f"SPECKIT_INTEGRATION_{integration.upper()}_EXTRA_ARGS"
    if os.environ.get(extra, "").strip():
        note("environment", "error" if required else "warning",
             extra + " is set; remove it before automatic stages (value withheld)")
    redirects = [key for key in ("SPECIFY_INIT_DIR", "SPECIFY_FEATURE", "SPECIFY_FEATURE_DIRECTORY") if os.environ.get(key)]
    if redirects:
        note("environment", "warning", "Native runner ignores ambient root/feature overrides: " + ", ".join(redirects))
    if required:
        from .runtime_selection import resolve_assistant
        try:
            binding = resolve_assistant(integration, config.get("execution", {}).get("assistant_executable"))
            note("assistant", "ok", f"{binding['executable']}: {binding['version']}; model/account access not tested")
        except (ValueError, OSError) as error:
            note("assistant", "error", str(error))
    else:
        note("assistant", "warning", "Not checked: no automatic stages requested")
    lock = root/".specify/workflows/poc-bootstrap.lock"
    if lock.exists() or lock.is_symlink():
        note("owner_lock", "error" if required else "warning",
             "Bootstrap owner lock exists; inspect its owner before recovery. Doctor never deletes it")
    git = shutil.which("git")
    if git:
        try:
            result = run_process([git, "rev-parse", "--show-toplevel"], root, timeout=10, env=git_environment())
            same_root = result["returncode"] == 0 and Path(result["stdout"].strip()).resolve() == root
            note("git_root", "ok" if same_root else "warning", "Exact local Git root verified" if same_root else "No exact project Git root; do not mutate a parent repository")
            if same_root:
                revision = run_process([git, "rev-parse", "--verify", "HEAD"], root, timeout=10, env=git_environment())
                note("source_commit", "ok" if revision["returncode"] == 0 else "warning",
                     revision["stdout"].strip() if revision["returncode"] == 0 else "Meaningful baseline not committed yet")
        except OSError:
            note("git_root", "warning", "Git inspection could not start; resolve host tool permissions")
    else:
        note("git_root", "warning", "Git executable not found; offline checks continue")
    note("storage", "ok", f"{shutil.disk_usage(root).free // (1024 * 1024)} MiB available; no new storage gate")
    if config:
        from .bootstrap import digest
        from .speckit_adapter import project_path
        from .persona_catalog import Catalog
        try:
            for item in config.get("intake", []):
                if digest(project_path(root, item["path"]).read_bytes()) != item["sha256"]:
                    raise ValueError("Bound input changed; reconcile before running")
            for selection in config.get("personas", []):
                namespace_id, revision = selection.rsplit("@", 1)
                namespace, identifier = namespace_id.split(":", 1)
                snapshot = Catalog(root / "reference/personas/catalog.json").get(identifier, int(revision))
                if snapshot["namespace"] != namespace:
                    raise ValueError("Selected persona namespace changed")
            note("inputs_personas", "ok", "Bound input digests and selected persona revisions verified")
        except (ValueError, OSError, KeyError, TypeError) as error:
            note("inputs_personas", "error", str(error))
    capabilities = []
    for check in checks:
        needed = check["name"] in {"python", "project", "assets", "inputs_personas"} or (
            check["name"] == "configuration" and bool(config)) or (
            required and check["name"] in {"runtime", "assistant", "environment", "owner_lock"}) or (
            operation in {"qualification", "delivery"} and check["name"] in {"git_root", "source_commit"})
        status = "ready" if check["status"] == "ok" else "blocked" if check["status"] == "error" or needed else "not_checked"
        capabilities.append(dict(name=check["name"], required=needed, status=status, detail=check["detail"]))
    for name, port in launch.get("ports", {}).items():
        if type(port) is not int or not 1024 <= port <= 65535:
            raise ValueError("Invalid requested port")
        try:
            with socket.socket() as listener:
                listener.bind(("127.0.0.1", port))
            status, detail = "ready", "Loopback bind available now; advisory until service binds"
        except OSError:
            status, detail = "blocked", "Requested loopback port unavailable; no listener stopped"
        capabilities.append(dict(name="port:" + name, required=True, status=status, detail=detail))
    import importlib.util
    modules = {"marimo": "marimo", "zen": "zen", "clipspy": "clips", "rapidfuzz": "rapidfuzz"}
    for name in launch.get("capabilities", []):
        module = modules.get(name)
        available = module is not None and importlib.util.find_spec(module) is not None
        capabilities.append(dict(name=name, required=True, status="ready" if available else "blocked",
                                 detail="Import available; behavior not qualified" if available else "Selected optional capability unavailable"))
    if operation == "delivery":
        capabilities.append(dict(name="github_delivery", required=True, status="not_checked",
                                 detail="Use authorized private broker to check the requested remote capability; local doctor does not authenticate"))
    return dict(project=str(root), operation=operation, capabilities=capabilities,
                status="issues" if any(c["status"] == "error" for c in checks) or
                any(c["required"] and c["status"] != "ready" for c in capabilities) else "ready", checks=checks)
