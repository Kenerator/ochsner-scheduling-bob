"""Post-booking replay against an owned, unchanged supplied HTTP mock."""

from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from http_support import supplied_server
from ochsner_bob.http_mock import HttpMockAdapter
from ochsner_bob.interaction_service import InteractionService, _vendor_catalog
from test_interaction_service import CATALOG
from test_session_contract import FixturePort


class PostBookingReplayTests(unittest.TestCase):
    def test_public_projection_does_not_admit_invalid_private_or_ambiguous_rows(self):
        row = {"appointmentId": "synthetic-receipt", "patientId": "pat_1003", "providerId": "prov_2001",
               "specialty": "primary_care", "location": "downtown", "startTime": CATALOG["option-a"]["value"]["startTime"],
               "status": "scheduled"}
        for case, changes in (("wrong_patient", {"patientId": "unapproved"}),
                              ("invalid_status", {"status": "cancelled"}),
                              ("extra_private_field", {"private_note": "synthetic-private-note"}),
                              ("invalid_receipt", {"appointmentId": "invalid receipt"}),
                              ("duplicate_static", {})):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="bob-private-binding-") as root:
                catalog = deepcopy(CATALOG)
                value = {**row, **changes}
                if case == "duplicate_static":
                    catalog.update({label: {"kind": "appointment", "value": deepcopy(row)}
                                    for label in ("appointment-a", "appointment-b")})
                port = FixturePort()
                port.appointments = lambda patient: [deepcopy(value)]
                service = InteractionService(lambda: port, Path(root) / "effects.json", fixture_catalog=catalog)
                token = service.create()["token"]
                service.capture(token, True)
                identity = service.command(token, "identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"}, 0)
                service.command(token, "appointments", {}, identity["revision"])
                report = service.capture(token, False)
                self.assertEqual(report["recording"], "incomplete_capture")
                self.assertIn("unbound_or_oversized_api_outcome", report["missing"])

    def test_unapproved_or_ambiguous_public_booking_remains_incomplete(self):
        for case in ("unapproved_time", "ambiguous_slot"):
            with self.subTest(case=case), tempfile.TemporaryDirectory(prefix="bob-unbound-") as root, supplied_server() as server:
                catalog = _vendor_catalog()
                if case == "ambiguous_slot":
                    catalog["duplicate-slot"] = deepcopy(catalog["slot-1"])
                service = InteractionService(lambda: HttpMockAdapter(server.base_url), Path(root) / "effects.json",
                                             fixture_catalog=catalog)
                token = service.create()["token"]
                service.capture(token, True)

                def act(action, data=None):
                    return service.command(token, action, data or {}, service.read(token)["revision"])

                act("identity", {"phone": "555-0101", "dob": "1985-04-12", "zip": "70112"})
                act("preferences", {"specialty": "primary_care", "location": "downtown"})
                act("availability")
                proposal = act("select", {"index": 1})["proposal"]
                act("confirm", {"proposal_id": proposal["id"], "nonce": proposal["nonce"]})
                if case == "unapproved_time":
                    server.store.appointments[-1]["time"] = "23:59"
                self.assertEqual(len(act("appointments")["appointments"]), 2)
                report = service.capture(token, False)
                self.assertEqual(report["recording"], "incomplete_capture")
                self.assertIn("unbound_or_oversized_api_outcome", report["missing"])
                self.assertFalse(report["fidelity"]["core_semantic_parity"])

    def test_confirm_then_lookup_seals_and_replays_without_private_rows_or_effects(self):
        # Exact static-row binding drops the newly created appointment observation.
        with tempfile.TemporaryDirectory(prefix="bob-post-booking-") as root, supplied_server() as server:
            service = InteractionService(lambda: HttpMockAdapter(server.base_url), Path(root) / "effects.json")
            token = service.create()["token"]
            service.capture(token, True)

            def act(action, data=None):
                view = service.read(token)
                return service.command(token, action, data or {}, view["revision"])

            act("discover", {"specialty": "primary_care", "location": "downtown"})
            act("identity", {"phone": "555-0101", "dob": "1985-04-12", "zip": "70112"})
            options = act("availability")["slots"]
            index = next(i for i, slot in enumerate(options, 1) if slot["slotId"] == "slot_4001")
            proposal = act("select", {"index": index})["proposal"]
            self.assertEqual(len(server.store.appointments), 2)
            booked = act("confirm", {"proposal_id": proposal["id"], "nonce": proposal["nonce"]})
            self.assertEqual(booked["current_result"]["status"], "completed")
            actual = act("appointments")
            self.assertEqual(actual["state"], "appointments")
            self.assertEqual(len(actual["appointments"]), 2)
            report = service.capture(token, False)
            self.assertEqual(report["recording"], "incomplete_capture", report)
            self.assertTrue(report["missing"])
            self.assertTrue(all("browser acknowledgement" in gap for gap in report["missing"]))

            audits = server.wait_for_audits(5)
            appointments = deepcopy(server.store.appointments)
            journal = service.journal_path.read_bytes()
            registry = service.registry.read_bytes()
            with patch("socket.socket", side_effect=AssertionError("replay network forbidden")), \
                 patch("ochsner_bob.session.EffectJournal", side_effect=AssertionError("disk claims forbidden")), \
                 patch("ochsner_bob.replay._transition", side_effect=AssertionError("legacy replay forbidden")):
                opened = service.replay(token, "open", {"reference": report["reference"]})
                result = service.replay(token, "jump", {"index": opened["event_count"] - 1})
                self.assertEqual(result["state"]["core"]["state"], "appointments")
                self.assertEqual(result["state"]["core"]["appointment_count"], 2)
                self.assertEqual(result["state"]["core"]["revision"], actual["revision"])
                self.assertEqual(result["state"]["core"]["certainty"], "completed")
                self.assertEqual(result["state"]["core"]["history"], [{"kind": "booking", "status": "completed"}])
                self.assertTrue(result["fidelity"]["core_semantic_parity"])
                self.assertFalse(result["fidelity"]["core_renderer_parity"])
                self.assertEqual(result["missing"], report["missing"])
                exported = service.replay(token, "export", {"reviewed": True})
                imported = service.replay(token, "import", {"payload": exported["payload"]})
                self.assertEqual(imported["recording"], "incomplete_capture")

            self.assertEqual(server.audits, audits)
            self.assertEqual(server.store.appointments, appointments)
            self.assertEqual(service.journal_path.read_bytes(), journal)
            self.assertEqual(service.registry.read_bytes(), registry)
            persisted = b"".join(path.read_bytes() for path in service.recording_directory.iterdir() if path.is_file()).decode()
            serialized = json.dumps([report, result, exported, imported]) + persisted
            for private in ("555-0101", "1985-04-12", "70112", "pat_1001", "slot_4001",
                            proposal["id"], proposal["nonce"], *[a["appointmentId"] for a in appointments]):
                self.assertNotIn(private, serialized)
