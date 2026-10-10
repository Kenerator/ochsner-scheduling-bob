"""Owned supplied-HTTP demonstrations; unknown is explicitly an adapter-boundary fault."""

import argparse
import json
from pathlib import Path
import tempfile

from ochsner_bob.conversation import Conversation
from ochsner_bob.http_mock import HttpMockAdapter, UnknownOutcome
from ochsner_bob.session import SchedulingSession

if __package__:
    from .mock_lifecycle import OwnedMock
else:
    from mock_lifecycle import OwnedMock


class _HideAcceptedBookingReceipt:
    """Demo fault ONLY: delegate one real write, then simulate its receipt being lost."""
    def __init__(self, delegate):
        self.delegate = delegate
        self.attempts = 0

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def book(self, patient_id, slot):
        self.attempts += 1
        self.delegate.book(patient_id, slot)
        raise UnknownOutcome()


def run_demo(flow):
    if flow not in {"success", "conflict", "unknown"}:
        raise ValueError("Choose a supported demo flow")
    with OwnedMock() as mock, tempfile.TemporaryDirectory(prefix="bob-demo-") as temporary:
        api = HttpMockAdapter(mock.base_url)
        session = SchedulingSession(api, journal_path=Path(temporary) / "effects.json")
        conversation = Conversation(session)
        def say(text):
            return conversation.interpret(text, session.revision)
        def select(slot_id):
            options = session.view()["slots"]
            index = next(i for i, slot in enumerate(options, 1) if slot["slotId"] == slot_id)
            return say(str(index))["proposal"]
        def confirm(proposal):
            return conversation.confirm(proposal["id"], proposal["nonce"], expected_revision=proposal["revision"])
        say("providers primary_care downtown")
        conversation.enter_identity("555-0101", "1985-04-12", "70112", expected_revision=session.revision)
        say("availability")
        proposal = select("slot_conflict_001" if flow == "conflict" else "slot_4001")
        fault = None
        if flow == "unknown":
            fault = _HideAcceptedBookingReceipt(api)
            session.api = fault
        result = confirm(proposal)
        if flow == "conflict":
            if result["current_result"]["status"] != "rejected":
                raise RuntimeError("Conflict demo did not produce a validated rejection")
            say("availability")
            result = confirm(select("slot_4001"))
        report = {"flow": flow, "mode": "offline_commands", "service": "unmodified_vendored_supplied_http",
                  "status": result["current_result"]["status"],
                  "history": [r["status"] for r in result["history"]]}
        if fault:
            say("reset")
            confirm(proposal)
            report["fault"] = "accepted_booking_receipt_hidden_at_adapter_boundary"
            report["retry_blocked"] = session.view()["booking_blocked"] and fault.attempts == 1
        expected = "unknown" if flow == "unknown" else "completed"
        if report["status"] != expected or (fault and not report["retry_blocked"]):
            raise RuntimeError("Demo outcome did not satisfy its synthetic contract")
        return report


def main(argv=None):
    parser = argparse.ArgumentParser(description="Owned supplied HTTP demos; no live model; unknown is a labeled local fault")
    parser.add_argument("--flow", choices=("success", "conflict", "unknown", "all"), default="all")
    args = parser.parse_args(argv)
    for flow in (("success", "conflict", "unknown") if args.flow == "all" else (args.flow,)):
        print(json.dumps(run_demo(flow)), flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
