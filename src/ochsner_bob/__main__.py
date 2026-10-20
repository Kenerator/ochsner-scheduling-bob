"""Multi-turn CLI; offline by default, bounded language only on explicit opt-in."""

import argparse
from contextlib import ExitStack
import getpass
import json
from pathlib import Path
import shlex
import sys

from .conversation import Conversation
from .diagnostics import Diagnostics, ObservedAPI
from .cli_namespace import CliNamespace
from .http_mock import HttpMockAdapter
from .language import LanguageAdapter
from .model_budget import ModelBudget
from .session import REASONS, SchedulingSession


ROOT = Path(__file__).resolve().parents[2]
_SCENARIOS = ("happy_path_booking", "provider_lookup", "no_patient_match", "multiple_patient_matches",
              "slot_conflict", "no_availability", "api_failure", "unsupported_request")
_COMMANDS = """Offline deterministic commands (synthetic HTTP data; no model calls):
  providers [primary_care|dermatology] [downtown|uptown|lakeside]
  /identity PHONE YYYY-MM-DD [ZIP]  (private local control; never sent to a model)
  availability | appointments | NUMBER | provider NUMBER
  specialty VALUE | location VALUE | dates START END | start DATE | end DATE
  clear provider|location|specialty|dates|start|end
  /confirm  (separate control for the exact summary just displayed)
  /diagnostics  (sanitized inspection only; no workflow/model/effect command)
  decline | help | medical | unsupported | handoff [REASON] | reset | /quit
"""


def render(view, output):
    """Visible patient projection only: never candidates, identity inputs or nonces."""
    print(view["message"], file=output)
    print("Identity: " + view["identity_status"], file=output)
    if view["preferences"]:
        print("Filters: " + "; ".join(f"{k}={v}" for k, v in view["preferences"].items()), file=output)
    names = {p["providerId"]: p["name"] for p in view["providers"]}
    for index, provider in enumerate(view["providers"], 1):
        print(f"Provider {index}: {provider['name']} | {provider['specialty']} | {', '.join(provider['locations'])}", file=output)
    for index, slot in enumerate(view["slots"], 1):
        print(f"Option {index}: {slot['startTime']} | {slot['specialty']} | {slot['location']} | {names.get(slot['providerId'], slot['providerId'])}", file=output)
    if view["proposal"]:
        slot = view["proposal"]["slot"]
        print(f"Exact summary: {slot['startTime']} | {slot['specialty']} | {slot['location']} | {names.get(slot['providerId'], slot['providerId'])}", file=output)
        print("Use /confirm in a separate turn to submit this exact appointment.", file=output)
    for appointment in view["appointments"]:
        print(f"Appointment: {appointment['startTime']} | {appointment['specialty']} | {appointment['location']} | {appointment['status']}", file=output)
    if view["current_result"]:
        result = view["current_result"]
        print(f"Last {result['kind']} outcome: {result['status']}", file=output)
        reason = result.get("handoff_reason")
        if result["kind"] == "handoff" and type(reason) is str and reason in REASONS:
            print("Handoff reason: " + reason, file=output)
    if view["booking_blocked"] or view["handoff_blocked"]:
        print("Unresolved prior write: outcome unknown or pending. Retrying remains blocked; Help is available.", file=output)
    output.flush()


def main(argv=None, *, input_stream=None, output_stream=None):
    parser = argparse.ArgumentParser(description="Offline synthetic scheduling commands; start an owned mock separately")
    parser.add_argument("--api-url", default="http://127.0.0.1:4010")
    parser.add_argument("--scenario", choices=_SCENARIOS)
    parser.add_argument("--journal", default=".bob-local/cli-effects.json",
                        help="same path resumes its private effect namespace; a new mock run requires an explicit new path")
    parser.add_argument("--openai", action="store_true", help="explicit bounded language opt-in; runtime configuration still required")
    args = parser.parse_args(argv)
    source, output = input_stream or sys.stdin, output_stream or sys.stdout
    if sys.version_info < (3, 11):
        print("Use an explicit Python 3.11+ interpreter.", file=output)
        return 2
    # Holding this stack until every exit keeps the CLI namespace exclusive.
    with ExitStack() as resources:
        return _run(args, source, output, resources)


def _run(args, source, output, resources):
    diagnostics = Diagnostics()
    try:
        namespace = resources.enter_context(CliNamespace(args.journal))
        api = ObservedAPI(HttpMockAdapter(args.api_url, scenario=args.scenario), diagnostics.api)
        # The selected launcher supplies our named key to this model host only.
        # Keep numeric limits and original private history; no startup model call.
        language = LanguageAdapter(budget=ModelBudget(ROOT / ".bob-local/model-budget.json", application_runtime=False,
            _existing_only=True, _existing_writes=True)) if args.openai else None
        conversation = Conversation(SchedulingSession(api, journal_path=namespace.journal.path,
                                    session_id=namespace.session_id), language=language,
                                    diagnostic_sink=diagnostics.language)
    except (ValueError, RuntimeError, OSError):
        print("Cannot initialize the loopback API, private CLI namespace/journal or shared model budget. "
              "Legacy, lost, corrupt or already active namespace is blocked; no silent migration. Check local setup.", file=output)
        return 2
    print(_COMMANDS, file=output)
    print("Same --journal path resumes effect protection, not identity or consent. "
          "Use an explicit new --journal path only for a new synthetic mock run.", file=output)
    if args.openai:
        print("OpenAI interpretation explicitly requested for public free text. Requires BOB_ENABLE_OPENAI=1, "
              "BOB_OPENAI_MODEL and the reviewed launcher's selected key handoff at runtime. Existing 200-call/$20 limits and all historical liabilities apply. "
              "No silent fallback; local commands remain deterministic. No model call occurs until a public text turn.", file=output)
    try:
        namespace.check()
        view = conversation.view()
        render(view, output)
        while True:
            if source.isatty():
                print("bob> ", end="", file=output, flush=True)
            line = source.readline(4097)
            if not line or line.strip() == "/quit":
                return 0
            if len(line) > 2049:
                print("Input exceeded the local command limit. Session stopped; effects remain protected.", file=output)
                return 2
            text = line.strip()
            if not text:
                continue
            # Input may have waited while files were lost/changed. Validate before
            # any local command or optional language dispatch, not only at startup.
            namespace.check()
            if text == "/diagnostics":
                print(json.dumps({"events": conversation.session.trace(), **diagnostics.snapshot()}, sort_keys=True), file=output)
                output.flush()
                continue
            revision = view["revision"]
            if text == "/confirm":
                # Bind only the snapshot displayed BEFORE this turn. Never fetch
                # the latest nonce to upgrade a stale terminal's authority.
                proposal = view.get("proposal") or {}
                view = conversation.confirm(proposal.get("id", ""), proposal.get("nonce", ""), expected_revision=revision)
            elif text == "/identity" or text.startswith("/identity "):
                try:
                    fields = shlex.split(text)[1:]
                except ValueError:
                    fields = []
                if not fields and source.isatty():
                    fields = [getpass.getpass("Synthetic phone: "), getpass.getpass("Birth date YYYY-MM-DD: "), getpass.getpass("ZIP (optional): ")]
                if len(fields) not in {2, 3}:
                    fields = ["", "", ""]
                view = conversation.enter_identity(fields[0], fields[1], fields[2] if len(fields) == 3 else None,
                                                   expected_revision=revision)
            else:
                view = conversation.interpret(text, revision)
            render(view, output)
    except KeyboardInterrupt:
        print("Stopped. Existing effect outcomes remain protected in the local journal.", file=output)
        return 130
    except (RuntimeError, OSError, ValueError):
        print("Private CLI state unavailable; stopped without retry. Existing outcomes remain protected.", file=output)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
