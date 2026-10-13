"""Explicit synthetic OpenAI qualification; never invoked by the test suite.

Only sanitized numeric usage, bounded accepted preferences and named case IDs
are printed. No raw body, candidate fixture output, credentials or exception
text is printed or stored. Use ONE durable budget path for the entire grant.
"""
import argparse
from hashlib import sha256
import importlib.util
import json
import os
from pathlib import Path
import sys
import time

from ochsner_bob.language import LanguageAdapter
from ochsner_bob.model_budget import BudgetError, DEFAULT_MODEL, ModelBudget, PRICED_MODELS, preflight_budget


ROOT = Path(__file__).resolve().parents[1]
_credential_spec = importlib.util.spec_from_file_location("bob_qualification_credentials",
    ROOT / "tools/poc-runtime/credentials.py")
_runtime_credentials = importlib.util.module_from_spec(_credential_spec)
_credential_spec.loader.exec_module(_runtime_credentials)


def resolve_qualification_key():
    """Reuse the pinned trusted resolver; never inherit a generic parent key."""
    config_path = ROOT / "poc-launch.json"
    if config_path.is_symlink() or not config_path.is_file() or config_path.stat().st_size > 16384:
        raise ValueError("invalid qualification credential configuration")
    credential = json.loads(config_path.read_text())["credential"]
    if credential != {"item":"[Env] (Ochsner PoC) OPENAI_API_KEY", "field":"notes",
                      "helper_path_env":"POC_SECRET_HELPER", "helper_command":"bw-get-secret"}:
        raise ValueError("unsupported qualification credential configuration")
    return _runtime_credentials.resolve_key(credential, run=_runtime_credentials.bounded_helper)


_EXPECTED = {
    "paraphrase_family": ({"discover"}, {"specialty":"primary_care", "location":"downtown"}),
    "paraphrase_history": ({"appointments"}, {}),
    "mixed_refusal_location": ({"preferences"}, {"location":"uptown"}),
    "mixed_dates": ({"preferences"}, {"start_date":"2026-10-20", "end_date":"2026-10-22"}),
    "refusal_plain": ({"decline"}, {}),
    "refusal_corrected_yes": ({"clarify", "decline"}, {}),
    "authority_confirmation": ({"clarify"}, {}),
    "authority_patient_invention": ({"discover"}, {}),
}


def assess(case, result):
    """Live semantic expectations, not a claim fake candidates were observed."""
    identifier = case["id"]
    if identifier in {"privacy_phone_help", "privacy_birth"}:
        passed = result.status == "private_input" and result.action is None and not result.preferences
    elif identifier in {"typo_specialty_clarify", "typo_not_autoselected"}:
        allowed = ({}, {"location":"uptown"}) if identifier == "typo_specialty_clarify" else ({},)
        passed = ((result.status == "clarification" and result.action is None)
                  or (result.status == "ok" and result.action == "clarify" and result.preferences in allowed))
    else:
        actions, preferences = _EXPECTED[identifier]
        passed = result.status == "ok" and result.action in actions and result.preferences == preferences
    return {"semantic_pass": bool(passed and result.mode == "openai"),
            "fixture_exact_match": result.status == case["expected_status"] and result.action == case["expected_action"]}


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--run-live", action="store_true", help="explicit paid synthetic qualification opt-in")
    parser.add_argument("--model", default=DEFAULT_MODEL)
    parser.add_argument("--budget", type=Path, default=ROOT / ".bob-local/model-budget.json",
                        help="compatibility option: must be the existing canonical project accounting path")
    args = parser.parse_args(argv)
    if (not args.run_live or os.environ.get("BOB_ENABLE_OPENAI") != "1"
            or args.model not in PRICED_MODELS):
        print(json.dumps({"qualification":"not_run", "reason":"Explicit live opt-in and priced snapshot required."}))
        return 2
    try:
        canonical = ROOT / ".bob-local/model-budget.json"
        if args.budget.absolute() != canonical.absolute():
            raise ValueError("canonical accounting required")
        preflight_budget(canonical, model=args.model)
        # Functional qualification is covered application-like execution, not
        # LLM generation of application/spec/test code. Preserve all accounting.
        budget = ModelBudget(canonical, application_runtime=True)
        before = budget.snapshot()
        # The three exact runtime fields only; never enumerate the environment.
        adapter = LanguageAdapter(environ={"BOB_ENABLE_OPENAI":"1", "BOB_OPENAI_MODEL":args.model,
            "OPENAI_API_KEY":resolve_qualification_key()}, budget=budget)
        manifest = json.loads((ROOT / "tests/live_model_cases.json").read_text())
        if manifest.get("synthetic_only") is not True or manifest.get("schema_version") != 1:
            raise ValueError()
        cases = manifest["cases"]
        expected_ids = set(_EXPECTED) | {"privacy_phone_help", "privacy_birth", "typo_specialty_clarify", "typo_not_autoselected"}
        if {case["id"] for case in cases} != expected_ids or len(cases) != len(expected_ids):
            raise ValueError()
        results = []
        for case in cases:
            start = time.monotonic()
            result = adapter.interpret(case["text"], case["context"])
            results.append({"id":case["id"], "mode":result.mode, "status":result.status,
                "action":result.action, "preferences":result.preferences,
                "latency_ms":round((time.monotonic() - start) * 1000, 2),
                "usage":result.usage, "cost_usd":result.cost_usd,
                "accounting_status":result.accounting_status, **assess(case,result)})
            if (result.status in {"unavailable", "accounting_failed", "budget_exceeded", "disabled"}
                    or result.accounting_status == "unknown"):
                break  # Never retry, silently fallback, or spend through an outage.
        after = budget.snapshot()
        qualified = (len(results) == len(cases) and all(item["semantic_pass"] for item in results)
                     and after["calls"] > before["calls"]
                     and all(item["accounting_status"] in {"known", "not_requested"} for item in results))
        report = {"qualification":"qualified" if qualified else "failed_or_incomplete", "model":args.model,
            "synthetic_only":True, "transport":"OpenAI stdlib HTTPS /v1/responses",
            "store":False, "tools":[], "retries":0,
            "source_sha256": {name:sha256((ROOT / name).read_bytes()).hexdigest() for name in
                ("src/ochsner_bob/language.py", "src/ochsner_bob/model_budget.py", "src/ochsner_bob/runtime_accounting.py",
                 "scripts/qualify_live.py", "tests/live_model_cases.json", "poc-launch.json",
                 "tools/poc-runtime/credentials.py", "tools/poc-runtime/export-manifest.json")},
            "cases_planned":len(cases), "cases_run":len(results), "calls_this_run":after["calls"] - before["calls"],
            "budget_before":before, "budget_after":after, "cases":results}
        print(json.dumps(report, sort_keys=True))
        return 0 if qualified else 1
    except (BudgetError, OSError, ValueError, KeyError, TypeError, _runtime_credentials.LaunchError):
        print(json.dumps({"qualification":"failed_or_incomplete", "reason":"Private accounting, exact named credential or qualification setup failed; no automatic retry."}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
