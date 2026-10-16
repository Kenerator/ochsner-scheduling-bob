"""Categorical handoff observation with ordinary recording-OFF constructors."""
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from ochsner_bob import __main__ as cli
from ochsner_bob.diagnostics import Diagnostics, ObservedAPI
from ochsner_bob.http_mock import ApiError, HttpMockAdapter, UnknownOutcome
from ochsner_bob.interaction_service import InteractionService
from test_interaction_service import CATALOG
from test_replay_live_core import PROVENANCE
from test_session_contract import FixturePort
from http_support import supplied_server


class HandoffPort(FixturePort):
    def handoff(self, reason, summary):
        result = super().handoff(reason, summary)
        if self.outcome:
            raise self.outcome
        return result


class HandoffDiagnosticsTests(unittest.TestCase):
    def service(self, directory, port):
        service = InteractionService(lambda: port, Path(directory) / "effects.json",
                                     fixture_catalog=CATALOG, provenance=PROVENANCE)
        return service, service.create()["token"]

    def test_supplied_http_queued_reason_is_observable_without_recording(self):
        for reason in ("medical_advice", "identity_unclear", "no_availability"):
            with self.subTest(reason=reason), tempfile.TemporaryDirectory() as directory, supplied_server() as server:
                service, token = self.service(directory, HttpMockAdapter(server.base_url))
                view = service.command(token, "handoff", {"reason": reason}, 0)
                diagnostic = service.diagnostics(token)
                self.assertEqual(view["current_result"]["status"], "queued")
                self.assertEqual(view["current_result"]["handoff_reason"], reason)
                self.assertEqual(diagnostic["api_events"][-1]["handoff_reason"], reason)
                self.assertEqual(diagnostic["recording"], "off")
                self.assertEqual([row["reason"] for row in server.store.handoffs], [reason])
                service.diagnostics(token)
                self.assertEqual(len(server.store.handoffs), 1)

    def test_recording_off_retains_reason_for_queued_rejected_failed_and_unknown(self):
        for reason in ("medical_advice", "identity_unclear", "no_availability"):
            for error, expected in ((None, "queued"), (ApiError(409), "rejected"),
                                    (ApiError(503), "failed"), (UnknownOutcome(), "unknown")):
                with self.subTest(reason=reason, status=expected), tempfile.TemporaryDirectory() as directory:
                    port = HandoffPort()
                    port.outcome = error
                    service, token = self.service(directory, port)
                    view = service.command(token, "handoff", {"reason": reason}, 0)
                    diagnostic = service.diagnostics(token)
                    self.assertEqual(view["current_result"]["status"], expected)
                    self.assertEqual(view["current_result"].get("handoff_reason"), reason)
                    self.assertEqual(view["history"][-1].get("handoff_reason"), reason)
                    self.assertEqual(diagnostic["events"][-1].get("handoff_reason"), reason)
                    self.assertEqual(diagnostic["api_events"][-1].get("handoff_reason"), reason)
                    self.assertEqual(diagnostic["recording"], "off")
                    self.assertEqual(len(port.writes), 1)
                    self.assertEqual(service.diagnostics(token), diagnostic)
                    self.assertEqual(len(port.writes), 1)
                    public = json.dumps(diagnostic)
                    for private in ("handoff_9003", "Workflow=", "private_identity", "555-0130"):
                        self.assertNotIn(private, public)

    def test_invalid_or_extra_reason_data_cannot_enter_events_or_dispatch(self):
        for data in ({"reason": "private-reason-sentinel"}, {"reason": None},
                     {"reason": ["medical_advice"]}, {"reason": True},
                     {"reason": "medical_advice", "summary": "private-summary-sentinel"}):
            with self.subTest(data_type=type(data["reason"]).__name__), tempfile.TemporaryDirectory() as directory:
                port = HandoffPort()
                service, token = self.service(directory, port)
                view = service.command(token, "handoff", data, 0)
                diagnostic = service.diagnostics(token)
                self.assertIsNone(view["current_result"])
                self.assertEqual(port.writes, [])
                self.assertEqual(diagnostic["api_events"], [])
                self.assertNotIn("handoff_reason", diagnostic["events"][-1])
                self.assertNotIn("sentinel", json.dumps(diagnostic))

    def test_unknown_reason_and_single_effect_survive_inspection_reset_and_retry(self):
        with tempfile.TemporaryDirectory() as directory:
            port = HandoffPort()
            port.outcome = UnknownOutcome()
            service, token = self.service(directory, port)
            view = service.command(token, "handoff", {"reason": "medical_advice"}, 0)
            for action, data in (("help", {}), ("reset", {}),
                                 ("handoff", {"reason": "user_requested"})):
                view = service.command(token, action, data, view["revision"])
            self.assertEqual(view["current_result"].get("handoff_reason"), "medical_advice")
            self.assertEqual(view["current_result"]["status"], "unknown")
            self.assertEqual(len(view["history"]), 1)
            self.assertEqual(len(port.writes), 1)
            events = service.diagnostics(token)["api_events"]
            self.assertEqual(len(events), 1)
            self.assertEqual(events[0].get("handoff_reason"), "medical_advice")

    def test_cli_normal_result_and_diagnostics_expose_only_categorical_reason(self):
        with tempfile.TemporaryDirectory() as directory:
            output = io.StringIO()
            port = HandoffPort()
            with patch.object(cli, "HttpMockAdapter", return_value=port):
                code = cli.main(["--journal", str(Path(directory) / "effects.json")],
                    input_stream=io.StringIO("handoff identity_unclear\n/diagnostics\n/diagnostics\n/quit\n"),
                    output_stream=output)
            self.assertEqual(code, 0)
            self.assertIn("Handoff reason: identity_unclear", output.getvalue())
            self.assertIn('"handoff_reason": "identity_unclear"', output.getvalue())
            self.assertNotIn("handoff_9003", output.getvalue())
            self.assertNotIn("Workflow=", output.getvalue())
            self.assertEqual(len(port.writes), 1)

    def test_api_observer_drops_invalid_reason_and_all_summary_content(self):
        diagnostic = Diagnostics()
        api = ObservedAPI(HandoffPort(), diagnostic.api)
        api.handoff(reason="medical_advice", summary="private-summary-sentinel")
        api.handoff("private-reason-sentinel", "private-summary-sentinel")
        events = diagnostic.snapshot()["api_events"]
        self.assertEqual(events[0].get("handoff_reason"), "medical_advice")
        self.assertNotIn("handoff_reason", events[1])
        self.assertNotIn("sentinel", json.dumps(events))

    def test_recording_import_and_core_replay_remain_effect_free(self):
        with tempfile.TemporaryDirectory() as directory:
            port = HandoffPort()
            service, token = self.service(directory, port)
            service.capture(token, True)
            service.command(token, "handoff", {"reason": "medical_advice"}, 0)
            sealed = service.capture(token, False)
            service.replay(token, "open", {"reference": sealed["reference"]})
            exported = service.replay(token, "export", {"reviewed": True})
            self.assertTrue(exported["reimportable"])
            service.replay(token, "import", {"payload": exported["payload"]})
            replayed = service.replay(token, "jump", {"index": 0})
            self.assertEqual(replayed["state"]["core"]["certainty"], "queued")
            self.assertEqual(replayed["state"]["core"]["history"], [{"kind": "handoff", "status": "queued"}])
            self.assertNotIn("handoff_reason", exported["payload"])
            self.assertEqual(len(port.writes), 1)
