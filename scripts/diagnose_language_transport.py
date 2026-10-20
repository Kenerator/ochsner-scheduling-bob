"""One separately selected private transport diagnosis, NOT holdout qualification.

Dry-run reads public sources only. Live use requires independent affected-code
review and exact-candidate selection; this script confers no execution authority.
No scheduling service, mock, Session command, retry or accounting reset is used.
"""
import argparse
from hashlib import sha256
import json
import os
from pathlib import Path
import stat
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
if __package__:
    from . import qualify_connected_live as policy
else:
    import qualify_connected_live as policy
from ochsner_bob.language import _observe_transport

RUN_ID = "transport-diagnostic-20261019"
_TEXT = "Find primary care doctors downtown."
_CONTEXT = {"workflow": "start", "preferences": {}}


def diagnostic_plan():
    hashes = policy.source_hashes()
    public_input = json.dumps({"text": _TEXT, "context": _CONTEXT}, sort_keys=True).encode()
    return hashes, {"run_id": RUN_ID, "source_digest": policy.source_digest(hashes),
        "input_sha256": sha256(public_input).hexdigest(), "model": policy.MODEL,
        "maximum_language_calls": 1, "max_output_tokens": 512, "timeout_seconds": 10,
        "max_input_bytes": 2048, "max_request_bytes": 16384, "max_response_bytes": 65536,
        "tools": [], "retries": 0, "scheduling_http": 0}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    choice = parser.add_mutually_exclusive_group(required=True)
    choice.add_argument("--dry-run", action="store_true")
    choice.add_argument("--run-live", action="store_true")
    parser.add_argument("--source-digest", help="exact digest selected after independent review")
    args = parser.parse_args(argv)
    fd, report, binding = None, None, None
    try:
        hashes, plan = diagnostic_plan()
        if args.dry_run:
            print(json.dumps({"diagnosis": "not_run", "plan": plan}, sort_keys=True))
            return 0
        if os.environ.get("BOB_ENABLE_OPENAI") != "1" or args.source_digest != plan["source_digest"]:
            raise ValueError("invalid_setup")
        binding = policy.canonical_binding(policy._APPROVED_OWNER_ROOT)
        binding.hashes = hashes
        before = binding.budget.snapshot()  # Validates the pinned sources under the original lock.
        output = ROOT / "tmp/connected-qualification"
        info = output.stat(follow_symlinks=False)
        if (not stat.S_ISDIR(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077
                or output.resolve(strict=True) != output):
            raise ValueError("invalid_setup")
        # Fixed exclusive evidence is deliberately separate from the consumed
        # tranche's run.json. Even an interrupted diagnosis cannot silently repeat.
        fd = os.open(output / (RUN_ID + ".json"), os.O_RDWR | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
        report = {"run_id": RUN_ID, "status": "started", "semantic_qualification": "not_run",
            "plan": plan, "source_sha256": hashes, "scheduling_http": 0,
            "private_binding": {"canonical_owner_root": str(binding.owner), "candidate_root": str(ROOT),
                "canonical_config_sha256": binding.owner_config_hash, "ledger_identity": binding.ledger_identity,
                "lock_identity": binding.lock_identity}, "accounting_before": before,
            "transport": {"category": "not_requested", "http_status": None}}
        policy._save(fd, report)

        def observe(event):
            # Defense in depth: the private report accepts only the same two
            # finite primitives, not arbitrary observer data or provider fields.
            if type(event) is dict and set(event) == {"category", "http_status"}:
                _observe_transport(lambda safe: report.update(transport=safe), event["category"], event["http_status"])
            else:
                report["transport"] = {"category": "other", "http_status": None}

        language = policy.create_language(binding, transport_observer=observe)
        started = time.monotonic()
        outcome = language.interpret(_TEXT, _CONTEXT)
        elapsed = round((time.monotonic() - started) * 1000, 3)
        after = binding.budget.snapshot()
        # Actual LanguageOutcome has already validated categorical/numeric fields.
        # No action/preferences, reason, body or exception is retained here.
        report.update(status="complete", accounting_after=after,
            calls_this_run=after["calls"] - before["calls"], latency_ms=elapsed,
            outcome={"status": outcome.status, "mode": outcome.mode, "usage": outcome.usage,
                     "accounting_status": outcome.accounting_status, "cost_usd": outcome.cost_usd})
        if report["calls_this_run"] != 1 or outcome.mode != "openai":
            report.update(status="failed_or_incomplete", failure="accounting_correlation_unavailable")
        policy._save(fd, report)
        print(json.dumps({"diagnosis": report["status"], "transport": report["transport"],
                          "source_digest": plan["source_digest"], "semantic_qualification": "not_run"}))
        return 0 if (report["status"] == "complete" and outcome.status == "ok"
                     and outcome.accounting_status == "known") else 1
    except BaseException as error:
        if report is not None and fd is not None:
            report.update(status="failed_or_incomplete",
                failure="interrupted" if isinstance(error, KeyboardInterrupt) else "setup_or_accounting_unavailable")
            try:
                policy._save(fd, report)
            except OSError:
                pass  # The exclusive file remains, even if final evidence is incomplete.
        if isinstance(error, SystemExit):
            raise
        print(json.dumps({"diagnosis": "failed_or_incomplete", "reason": "Diagnostic unavailable; no automatic retry."}))
        return 2
    finally:
        if fd is not None:
            os.close(fd)


if __name__ == "__main__":
    raise SystemExit(main())
