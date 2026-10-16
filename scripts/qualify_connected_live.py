"""One explicitly selected connected holdout tranche; dry-run is key/app-free.

The candidate supplies code; the selected canonical checkout owns accounting.
No arbitrary ledger, model override, generic key, migration or retry is supported.
Live use remains subject to the independent pre-live review and execution grant.
"""
import argparse
from contextlib import contextmanager
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import pwd
import stat
import sys

ROOT = Path(__file__).resolve().parents[1]
# Direct execution must use this candidate, not a canonical editable install.
sys.path.insert(0, str(ROOT / "src"))
from ochsner_bob.conversation import Conversation
from ochsner_bob.language import LanguageAdapter
from ochsner_bob.model_budget import BudgetError, ModelBudget
from ochsner_bob.runtime_accounting import RuntimeLedger
from ochsner_bob.session import SchedulingSession
if __package__:
    from .connected_qualification import load_manifest, run_journey
else:
    from connected_qualification import load_manifest, run_journey

PROJECT = "ochsner-scheduling-bob"
MODEL = "gpt-5.4-2026-03-05"
# This evaluation's selected local owner, derived from the OS account, never HOME
# or an environment-selected budget. Other owners require a separately reviewed change.
_APPROVED_OWNER_ROOT = Path(pwd.getpwuid(os.getuid()).pw_dir) / "codeRepos" / PROJECT
HOLDOUT = ROOT / "tests/fixtures/connected_qualification_holdout.json"
_CREDENTIAL = {"item": "[Env] (Ochsner PoC) OPENAI_API_KEY", "field": "notes",
               "helper_path_env": "POC_SECRET_HELPER", "helper_command": "bw-get-secret"}
_RESOLVER_HASH = "ae126a87d778fdae99368d053aa6e27151cb09f911ff7f0d63872950fda2b0af"


def _read(path, maximum=524288):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_size > maximum:
            raise ValueError("invalid_setup")
        raw = os.read(fd, maximum + 1)
        if len(raw) > maximum:
            raise ValueError("invalid_setup")
        return raw
    finally:
        os.close(fd)


def _pairs(items):
    value = {}
    for key, item in items:
        if key in value:
            raise ValueError("invalid_setup")
        value[key] = item
    return value


def _constant(_):
    raise ValueError("invalid_setup")


def _config(root):
    raw = _read(root / "poc-launch.json", 16384)
    value = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
    if (type(value) is not dict or type(value.get("schema_version")) is not int
            or value["schema_version"] != 1 or value.get("project_id") != PROJECT
            or value.get("adapter") != "bob" or value.get("credential") != _CREDENTIAL
            or value.get("model") != {"default": MODEL, "environment": "BOB_OPENAI_MODEL"}):
        raise ValueError("invalid_setup")
    relevant = {k: value[k] for k in ("schema_version", "project_id", "adapter", "credential", "model")}
    return relevant, sha256(raw).hexdigest()


def _identity(path):
    info = path.stat(follow_symlinks=False)
    if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise ValueError("invalid_setup")
    return info.st_dev, info.st_ino


def source_hashes():
    names = [str(p.relative_to(ROOT)) for p in (ROOT / "src/ochsner_bob").glob("*.py")]
    names += ["scripts/connected_qualification.py", "scripts/qualify_connected_live.py", "scripts/mock_lifecycle.py",
              "tests/fixtures/connected_qualification_holdout.json", "poc-launch.json", "policies/bob.json",
              "tools/poc-runtime/credentials.py", "tools/poc-runtime/export-manifest.json",
              "vendor/reference/mock-api/server.py"]
    names += [str(p.relative_to(ROOT)) for p in (ROOT / "vendor/reference/data").glob("*.json")]
    return {name: sha256(_read(ROOT / name)).hexdigest() for name in sorted(names)}


def source_digest(hashes):
    return sha256(json.dumps(hashes, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def holdout_plan():
    manifest = load_manifest(HOLDOUT)
    if manifest["set"] != "holdout" or manifest["repetitions"] != 2 or len(manifest["cases"]) != 8:
        raise ValueError("invalid_setup")
    hashes = source_hashes()
    return manifest, hashes, {"journeys": 8, "repetitions": 2, "executions": 16,
        "maximum_language_calls": 2 * sum(step.get("dispatch", False) for case in manifest["cases"] for step in case["steps"]),
        "local_text_turns": 2 * sum(step["kind"] == "text" and not step["dispatch"] for case in manifest["cases"] for step in case["steps"]),
        "model": MODEL, "max_output_tokens_per_call": 512, "timeout_seconds": 10,
        "tools": [], "retries": 0, "source_digest": source_digest(hashes),
        "holdout_sha256": hashes["tests/fixtures/connected_qualification_holdout.json"]}


class _BoundBudget(ModelBudget):
    def __init__(self, binding):
        self.binding = binding
        super().__init__(binding.ledger, application_runtime=True, _existing_only=True, _existing_writes=True)

    @contextmanager
    def _locked(self):
        # Reuse the same lock once, not nested flock on a second descriptor.
        with super()._locked() as fd:
            self.binding.validate(fd)
            yield fd


class CanonicalBinding:
    def __init__(self, owner):
        self.owner = Path(owner).absolute()
        if self.owner != _APPROVED_OWNER_ROOT or self.owner.resolve(strict=True) != self.owner:
            raise ValueError("invalid_setup")
        if not self.owner.is_dir() or (self.owner / ".git").is_symlink() or not (self.owner / ".git").is_dir():
            raise ValueError("invalid_setup")
        self.root_identity = (self.owner.stat().st_dev, self.owner.stat().st_ino)
        candidate, self.candidate_config_hash = _config(ROOT)
        canonical, self.owner_config_hash = _config(self.owner)
        if canonical != candidate:
            raise ValueError("invalid_setup")
        self.ledger = self.owner / ".bob-local/model-budget.json"
        if self.ledger.parent.resolve(strict=True) != self.ledger.parent:
            raise ValueError("invalid_setup")
        self.ledger_identity = _identity(self.ledger)
        self.lock_identity = _identity(self.ledger.with_name(self.ledger.name + ".lock"))
        if not RuntimeLedger.is_database(self.ledger):
            raise ValueError("invalid_setup")
        # This uses already-existing SQLite, not initialization-capable accounting.
        self.budget = _BoundBudget(self)
        self.hashes = None

    def validate(self, lock_fd=None):
        try:
            if (self.owner.resolve(strict=True) != self.owner
                    or (self.owner.stat().st_dev, self.owner.stat().st_ino) != self.root_identity
                    or _config(ROOT)[1] != self.candidate_config_hash
                    or _config(self.owner)[1] != self.owner_config_hash
                    or self.ledger.parent.resolve(strict=True) != self.ledger.parent
                    or _identity(self.ledger) != self.ledger_identity
                    or _identity(self.ledger.with_name(self.ledger.name + ".lock")) != self.lock_identity):
                raise ValueError()
            if lock_fd is not None:
                info = os.fstat(lock_fd)
                if (info.st_dev, info.st_ino) != self.lock_identity:
                    raise ValueError()
            if getattr(self, "hashes", None) is not None and source_hashes() != self.hashes:
                raise ValueError()
        except Exception:
            raise BudgetError("Selected accounting binding changed; dispatch blocked.") from None


def canonical_binding(owner_root=None):
    # No environment-selected owner or alternate accounting path.
    try:
        return CanonicalBinding(ROOT if owner_root is None else owner_root)
    except (OSError, ValueError, TypeError, KeyError):
        raise BudgetError("Selected canonical accounting unavailable; dispatch blocked.") from None


def resolve_qualification_key():
    path = ROOT / "tools/poc-runtime/credentials.py"
    if sha256(_read(path)).hexdigest() != _RESOLVER_HASH:
        raise ValueError("invalid_setup")
    spec = importlib.util.spec_from_file_location("bob_connected_credentials", path)
    credentials = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(credentials)
    return credentials.resolve_key(_CREDENTIAL, run=credentials.bounded_helper)


def create_language(binding):
    for module, name in ((Conversation, "conversation"), (SchedulingSession, "session"),
                         (LanguageAdapter, "language"), (ModelBudget, "model_budget"), (RuntimeLedger, "runtime_accounting")):
        if Path(sys.modules[module.__module__].__file__).resolve() != ROOT / ("src/ochsner_bob/" + name + ".py"):
            raise ValueError("invalid_setup")
    binding.validate()
    key = resolve_qualification_key()
    binding.validate()  # Helper latency cannot conceal config/storage replacement.
    return LanguageAdapter(environ={"BOB_ENABLE_OPENAI": "1", "BOB_OPENAI_MODEL": MODEL,
                                    "OPENAI_API_KEY": key}, budget=binding.budget)


def run_schedule(manifest, language, effects_dir, *, on_execution=None):
    executions, halted, calls = [], False, 0
    for repetition in range(1, manifest["repetitions"] + 1):
        for case in manifest["cases"]:
            item = {"case_id": case["id"], "repetition_id": repetition, "status": "unrun"}
            executions.append(item)
            if halted:
                item["reason"] = "prior_terminal_failure"
            else:
                item["status"] = "running"
                if on_execution is not None:
                    on_execution(executions)
                try:
                    result = run_journey(case, language, effects_dir, repetition_id=repetition)
                    item.update(status="run", result=result)
                    calls += result["language_calls"]
                    halted = result["halt_dispatch"]
                except Exception:
                    item.update(status="failed_before_result", reason="runner_unavailable", accounting="unknown")
                    halted = True
            if on_execution is not None:
                on_execution(executions)
    return {"executions": executions, "language_calls": calls, "halted": halted,
        "qualified": all(item["status"] == "run" and item["result"]["genuine_qualification"] for item in executions)}


def _save(fd, report):
    raw = json.dumps(report, sort_keys=True).encode()
    os.lseek(fd, 0, os.SEEK_SET)
    offset = 0
    while offset < len(raw):
        written = os.write(fd, raw[offset:])
        if written <= 0:
            raise OSError("private_report_unavailable")
        offset += written
    os.ftruncate(fd, len(raw)); os.fsync(fd)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--dry-run", action="store_true", help="validate frozen inputs/sources only; no owner/key/app access")
    choice.add_argument("--preflight", action="store_true", help="existing canonical SQLite readiness only; no key/app/model")
    choice.add_argument("--run-live", action="store_true", help="ONE reviewed, explicitly authorized paid tranche")
    parser.add_argument("--canonical-owner-root", type=Path, default=ROOT)
    parser.add_argument("--source-digest", help="exact source digest selected by the independent pre-live review")
    args = parser.parse_args(argv)
    fd, report = None, None
    try:
        manifest, hashes, plan = holdout_plan()
        if args.dry_run:
            print(json.dumps({"qualification": "not_run", "plan": plan}, sort_keys=True)); return 0
        binding = canonical_binding(args.canonical_owner_root)
        binding.hashes = hashes
        before = binding.budget.snapshot()
        if args.preflight:
            print(json.dumps({"qualification": "not_run", "readiness": "existing_sqlite_valid"})); return 0
        if os.environ.get("BOB_ENABLE_OPENAI") != "1" or args.source_digest != plan["source_digest"]:
            raise ValueError("invalid_setup")
        output = ROOT / "tmp/connected-qualification"
        try:
            output.mkdir(mode=0o700)
        except FileExistsError:
            pass
        info = output.stat(follow_symlinks=False)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
                or output.resolve(strict=True) != output):
            raise ValueError("invalid_setup")
        # Existing run evidence prevents an accidental second paid tranche. It is
        # not a model ledger/headroom source and is never deleted by this runner.
        fd = os.open(output / "run.json", os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        planned = [{"case_id": case["id"], "repetition_id": repetition, "status": "unrun", "reason": "not_started"}
                   for repetition in (1, 2) for case in manifest["cases"]]
        report = {"qualification": "running", "plan": plan, "source_sha256": hashes,
            "private_binding": {"canonical_owner_root": str(binding.owner), "candidate_root": str(ROOT),
                "canonical_config_sha256": binding.owner_config_hash, "ledger_identity": binding.ledger_identity,
                "lock_identity": binding.lock_identity}, "accounting_before": before, "executions": planned}
        _save(fd, report)
        language = create_language(binding)
        def checkpoint(executions):
            report["executions"] = executions + planned[len(executions):]
            _save(fd, report)
        result = run_schedule(manifest, language, output, on_execution=checkpoint)
        after = binding.budget.snapshot()
        report.update(result, accounting_after=after,
            calls_this_run=after["calls"] - before["calls"],
            qualification="qualified" if result["qualified"] else "failed_or_incomplete")
        if report["calls_this_run"] != result["language_calls"]:
            report.update(qualification="failed_or_incomplete", accounting_correlation="not_exclusive")
        _save(fd, report)
        print(json.dumps({"qualification": report["qualification"], "language_calls": result["language_calls"],
                          "source_digest": plan["source_digest"]}))
        return 0 if report["qualification"] == "qualified" else 1
    except BaseException as error:
        if report is not None and fd is not None:
            report["qualification"] = "failed_or_incomplete"
            report["failure"] = "interrupted" if isinstance(error, KeyboardInterrupt) else "setup_or_accounting_unavailable"
            try:
                _save(fd, report)
            except OSError:
                pass  # Existing run file still prohibits automatic replay.
        if isinstance(error, SystemExit):
            raise
        print(json.dumps({"qualification": "failed_or_incomplete", "reason": "Setup, binding or accounting unavailable; no automatic retry."}))
        return 2
    finally:
        if fd is not None:
            os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
