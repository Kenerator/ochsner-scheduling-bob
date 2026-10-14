"""Execute guide prerequisite metadata, not full browser journeys or prose claims."""
import json
from pathlib import Path
import re
import tempfile
import unittest

from ochsner_bob.browser_service import BrowserService
from ochsner_bob.session import SchedulingSession
from test_session_contract import FixturePort


ROOT = Path(__file__).resolve().parents[1]
SESSION_GUIDES = (
    "select-and-clear-provider", "accept-provider-name-suggestion",
    "text-does-not-confirm", "duplicate-confirmation", "stale-submission",
    "unknown-after-restart", "success-then-conflict", "handoff-failure",
    "unknown-handoff-outcome", "help-during-model-wait",
)
PROPOSAL_GUIDES = ("text-does-not-confirm", "duplicate-confirmation", "success-then-conflict")
STATEFUL = {"specialty", "location", "find-providers", "check-identity",
            "get-availability", "select-option", "confirm-appointment", "help",
            "inspect-diagnostics", "spelling-suggestion", "public-request", "send-request"}


class WalkthroughPrerequisiteTests(unittest.TestCase):
    def guide_steps(self, identifier):
        catalog = json.loads((ROOT / "docs/user/walkthroughs/catalog.json").read_text())
        flow = next(row for row in catalog["flows"] if row["id"] == identifier)
        text = (ROOT / flow["document"]).read_text()
        steps = [json.loads(raw) for raw in re.findall(
            r"<!-- walkthrough-step: (.*?) -->", text)]
        # The executed metadata must be the same ordered plan exposed by the catalog.
        self.assertTrue(steps, identifier)
        self.assertEqual(steps, [{key: value for key, value in step.items() if key != "anchor"}
                                for step in flow["steps"] if step["number"] >= 2])
        return steps

    @staticmethod
    def session_ready(steps, directory):
        service = BrowserService(FixturePort, Path(directory) / "effects.json")
        token = None
        for step in steps:
            for control in step.get("control_ids", []):
                if control == "start-independent-patient":
                    token = service.create()["token"]
                elif control in STATEFUL:
                    try:
                        service.read(token)
                    except PermissionError:
                        return False
        return token is not None

    @staticmethod
    def prepare_proposal(steps, directory):
        # Isolate filter ordering from R1. This is the real session with an existing
        # synthetic identity fixture, not a browser/whole-guide simulation.
        port = FixturePort()
        session = SchedulingSession(port, journal_path=Path(directory) / "effects.json")
        for step in steps:
            for control in step.get("control_ids", []):
                action, data = None, {}
                if control == "check-identity":
                    action, data = "identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"}
                elif control in {"apply-preferences", "find-providers"}:
                    action = "preferences" if control == "apply-preferences" else "discover"
                    data = {"specialty": "primary_care", "location": "downtown"}
                elif control == "get-availability":
                    action = "availability"
                elif control == "select-option":
                    session.command("select", {"index": 1}, expected_revision=session.revision)
                    return session.view(), port
                if action:
                    session.command(action, data, expected_revision=session.revision)
        return session.view(), port

    def test_independent_guide_plans_create_authority_before_stateful_controls(self):
        for identifier in SESSION_GUIDES:
            with self.subTest(guide=identifier), tempfile.TemporaryDirectory() as directory:
                self.assertTrue(self.session_ready(self.guide_steps(identifier), directory), identifier)

    def test_omitting_session_creation_is_rejected_by_actual_service(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertFalse(self.session_ready([{"control_ids": ["help"]}], directory))

    def test_proposal_guide_plans_apply_filters_before_availability(self):
        for identifier in PROPOSAL_GUIDES:
            with self.subTest(guide=identifier), tempfile.TemporaryDirectory() as directory:
                view, port = self.prepare_proposal(self.guide_steps(identifier), directory)
                self.assertIsNotNone(view["proposal"], identifier)
                self.assertEqual(view["preferences"]["specialty"], "primary_care")
                self.assertEqual(view["preferences"]["location"], "downtown")
                self.assertIn("availability", port.reads)
                self.assertEqual(port.writes, [])

    def test_unapplied_dropdown_choices_cannot_produce_a_proposal(self):
        steps = [{"control_ids": ["specialty", "location", "check-identity",
                                  "get-availability", "select-option"]}]
        with tempfile.TemporaryDirectory() as directory:
            view, port = self.prepare_proposal(steps, directory)
            self.assertIsNone(view["proposal"])
            self.assertEqual(view["slots"], [])
            self.assertNotIn("availability", port.reads)
            self.assertEqual(port.writes, [])
