"""Replay is bounded data inspection/simulation, never scheduling authority."""

from copy import deepcopy
from hashlib import sha256
import json
import socket
import unittest
from unittest.mock import patch

from ochsner_bob import replay


NOW = 1_791_543_600.0
FIXTURES = {"person-a", "person-b", "option-a", "option-b"}


def wire(document):
    """Re-sign adversarial input so schema tests cannot pass on hash failure alone."""
    document = deepcopy(document)
    document.pop("digest", None)
    canonical = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    document["digest"] = sha256(canonical.encode()).hexdigest()
    return json.dumps(document)


class ReplayContractTests(unittest.TestCase):
    def setUp(self):
        self.assertTrue(callable(getattr(replay, "Recording", None)),
                        "strict synthetic Recording contract is missing")
        self.provenance = replay.make_provenance(
            "a" * 40, dependencies=b"lock", policy=b"policy", prompt=b"prompt",
            schema=b"schema", fixtures=b"fixtures",
        )

    def recording(self, **kwargs):
        return replay.Recording(self.provenance, fixture_refs=FIXTURES,
                                synthetic=True, now=NOW, **kwargs)

    def ready_recording(self, outcome="completed"):
        recording = self.recording()
        recording.append({"action": "identity_fixture", "data": {"fixture_ref": "person-a"}})
        recording.append({"action": "preferences", "data": {"specialty": "primary_care", "location": "downtown"}})
        recording.append({"action": "availability", "data": {}},
                         outcomes={"api": {"status": "ok", "fixture_refs": ["option-a"], "delay_ms": 4}})
        recording.append({"action": "select", "data": {"index": 1}})
        recording.append({"action": "confirm", "data": {}},
                         outcomes={"api": {"status": outcome, "fixture_refs": [], "delay_ms": 5}},
                         view={"revision": 5, "renderer": "bob-v1", "visible": ["Synthetic result"],
                               "enabled": ["help"], "validation": "", "loading": False})
        recording.seal()
        return recording

    def load(self, document, **kwargs):
        return replay.import_recording(wire(document), fixture_refs=FIXTURES,
                                       expected_provenance=self.provenance, now=NOW, **kwargs)

    def test_exact_recording_requires_explicit_boolean_synthetic_opt_in(self):
        for opt_in in (False, None, "yes", 1):
            with self.subTest(opt_in=opt_in), self.assertRaises(PermissionError):
                replay.Recording(self.provenance, fixture_refs=FIXTURES, synthetic=opt_in, now=NOW)

    def test_sanitized_trace_never_retains_raw_private_or_language_input(self):
        trace = replay.SanitizedTrace()
        raw = {"action": "confirm", "status": "unknown", "latency_ms": 4,
               "phone": "555-0130", "dob": "1978-09-22", "zip": "70115",
               "patient_id": "pat-secret", "slot_id": "slot-secret", "proposal": "proposal-secret",
               "prompt": "raw prompt", "exception": "private exception", "token": "private token"}
        self.assertTrue(trace.emit(raw))
        snapshot = trace.snapshot()
        text = json.dumps(snapshot)
        for value in ("555-0130", "1978-09-22", "70115", "pat-secret", "slot-secret",
                      "proposal-secret", "raw prompt", "private exception", "private token"):
            self.assertNotIn(value, text)
        self.assertEqual(snapshot[0]["status"], "unknown")
        snapshot.clear()
        self.assertEqual(len(trace.snapshot()), 1)
        self.assertEqual(trace.availability, "sanitized_inspection_only")
        self.assertRegex(trace.reference(0), r"^BOB-[0-9a-f]{32}/step/1/branch/original$")
        # Unrecognized categorical values must not become a privacy escape hatch.
        trace.emit({"action": "555-0130", "status": "pat-secret", "reason": "raw prompt"})
        self.assertNotIn("555-0130", json.dumps(trace.snapshot()))
        self.assertNotIn("pat-secret", json.dumps(trace.snapshot()))

    def test_trace_overflow_and_invalid_evidence_are_nonthrowing(self):
        trace = replay.SanitizedTrace(limits=replay.Limits(max_events=1))
        self.assertTrue(trace.emit({"action": "help"}))
        self.assertFalse(trace.emit({"action": "help"}))
        self.assertFalse(trace.emit(object()))
        self.assertEqual(trace.dropped, 2)
        self.assertEqual(len(trace.snapshot()), 1)

    def test_recording_roundtrip_keeps_exact_approved_inputs_and_provenance(self):
        recording = self.ready_recording()
        with self.assertRaises(PermissionError):
            recording.export_json()
        with self.assertRaises(PermissionError):
            recording.export_json(reviewed="yes")
        imported = replay.import_recording(recording.export_json(reviewed=True),
            fixture_refs=FIXTURES, expected_provenance=self.provenance, now=NOW)
        self.assertEqual(imported.to_dict(), recording.to_dict())
        self.assertEqual(imported.availability(now=NOW), "full_replay")
        self.assertEqual(imported.to_dict()["expires_at"] - NOW, 86400)
        self.assertEqual(self.provenance["policy"], sha256(b"policy").hexdigest())
        self.assertEqual(imported.compatibility["drift"], [])
        with self.assertRaises(RuntimeError):
            imported.append({"action": "help", "data": {}})

    def test_duplicate_fields_are_rejected_at_every_depth(self):
        payload = self.ready_recording().export_json(reviewed=True)
        for changed in (payload.replace('"version":1', '"version":1,"version":1'),
                        payload.replace('"action":"confirm"', '"action":"confirm","action":"confirm"')):
            self.assertNotEqual(changed, payload)
            with self.assertRaisesRegex(ValueError, "duplicate"):
                replay.import_recording(changed, fixture_refs=FIXTURES, now=NOW)

    def test_extra_fields_and_serialized_authority_are_rejected_recursively(self):
        original = self.ready_recording().to_dict()
        mutations = [
            ([], "endpoint", "http://127.0.0.1:4010"),
            (["provenance"], "credentials", "secret"),
            (["events", 0, "input", "data"], "verified_identity", True),
            (["events", 4, "input", "data"], "consent", True),
            (["events", 4, "outcomes", "api"], "receipt", {"success": True}),
            (["events", 4, "outcomes"], "allow", True),
            (["events", 4, "view"], "journal", {"status": "completed"}),
            (["branch"], "live_adapter", "configured"),
        ]
        for path, name, value in mutations:
            doc = deepcopy(original)
            target = doc
            for component in path:
                target = target[component]
            target[name] = value
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "fields"):
                self.load(doc)

    def test_import_rejects_nonfinite_invalid_utf8_and_non_json(self):
        payload = self.ready_recording().export_json(reviewed=True)
        for value in ("NaN", "Infinity", "-Infinity"):
            changed = payload.replace('"delay_ms":5', '"delay_ms":' + value)
            self.assertNotEqual(changed, payload)
            with self.subTest(value=value), self.assertRaises(ValueError):
                replay.import_recording(changed, fixture_refs=FIXTURES, now=NOW)
        for value in (b"\xff", b"PK\x03\x04archive", b"\x80\x04pickle", "[]", "{}"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                replay.import_recording(value, fixture_refs=FIXTURES, now=NOW)

    def test_default_import_event_depth_and_string_bounds_are_enforced(self):
        with self.assertRaisesRegex(ValueError, "size"):
            replay.import_recording(b" " * (1024 * 1024 + 1), fixture_refs=FIXTURES, now=NOW)
        for mutation in ("events", "depth", "string"):
            doc = self.ready_recording().to_dict()
            if mutation == "events":
                doc["events"] = doc["events"][:1] * 2001
            elif mutation == "depth":
                doc["events"][0]["input"]["data"] = {"nested": {"nested": {"nested": {"nested": {"nested": {"nested": {"nested": {"nested": {"nested": {"nested": {"nested": {}}}}}}}}}}}}
            else:
                doc["events"][4]["view"]["visible"] = ["a" * 4097]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                self.load(doc)

    def test_references_must_be_allowed_by_the_host_not_only_the_document(self):
        doc = self.ready_recording().to_dict()
        doc["fixture_refs"].append("forged-person")
        doc["events"][0]["input"]["data"]["fixture_ref"] = "forged-person"
        with self.assertRaisesRegex(ValueError, "fixture"):
            self.load(doc)
        doc = self.ready_recording().to_dict()
        doc["events"][2]["outcomes"]["api"]["fixture_refs"] = ["forged-option"]
        with self.assertRaisesRegex(ValueError, "fixture"):
            self.load(doc)

    def test_path_url_executable_and_private_text_is_rejected_without_echo(self):
        for value in ("https://example.org", "file:///tmp/payload", "/tmp/payload", "../payload",
                      r"C:\private\payload", "folder/payload", "__import__('os')", "<script>alert(1)</script>",
                      "my phone is 555-0130", "ZIP 70115", "a@example.org", "Bearer private-token"):
            doc = self.ready_recording().to_dict()
            doc["events"][4]["view"]["visible"] = [value]
            with self.subTest(value=value):
                with self.assertRaises(ValueError) as error:
                    self.load(doc)
                self.assertNotIn(value, str(error.exception))
        recorder = self.recording()
        with self.assertRaises(ValueError):
            recorder.append({"action": "language", "data": {"text": "my phone is 555-0130"}})
        self.assertEqual(recorder.to_dict()["events"], [])

    def test_invalid_versions_types_order_and_hash_fail_closed(self):
        original = self.ready_recording().to_dict()
        for name, value in (("version", 2), ("version", True), ("complete", "yes"), ("created_at", True)):
            doc = deepcopy(original)
            doc[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                self.load(doc)
        doc = deepcopy(original)
        doc["events"][1]["seq"] = 99
        with self.assertRaises(ValueError):
            self.load(doc)
        doc = deepcopy(original)
        doc["events"][0]["clock"] = -1
        with self.assertRaises(ValueError):
            self.load(doc)
        payload = self.ready_recording().export_json(reviewed=True).replace("downtown", "uptown")
        with self.assertRaisesRegex(ValueError, "digest"):
            replay.import_recording(payload, fixture_refs=FIXTURES, now=NOW)

    def test_provenance_drift_is_comparison_not_claimed_identical_replay(self):
        expected = {**self.provenance, "prompt": "b" * 64}
        imported = replay.import_recording(self.ready_recording().export_json(reviewed=True),
            fixture_refs=FIXTURES, expected_provenance=expected, now=NOW)
        simulation = replay.Replay(imported, now=NOW)
        self.assertEqual(simulation.mode, "comparison")
        self.assertEqual(imported.compatibility["drift"], ["prompt"])
        self.assertEqual(simulation.jump(4)["outcome"], "completed")

    def test_missing_outcomes_are_explicit_and_do_not_manufacture_success(self):
        recording = self.recording()
        recording.append({"action": "availability", "data": {}})
        recording.seal()
        self.assertEqual(recording.availability(now=NOW), "incomplete_capture")
        self.assertIn("step 1: api", recording.missing)
        simulation = replay.Replay(recording, now=NOW)
        self.assertEqual(simulation.step()["outcome"], "missing_data")

    def test_overflow_does_not_mutate_prior_events_or_hide_incomplete_capture(self):
        recording = self.recording(limits=replay.Limits(max_events=1))
        self.assertTrue(recording.append({"action": "help", "data": {}}))
        before = deepcopy(recording.to_dict()["events"])
        self.assertFalse(recording.append({"action": "medical", "data": {}}))
        recording.seal()
        self.assertEqual(recording.to_dict()["events"], before)
        self.assertEqual(recording.availability(now=NOW), "incomplete_capture")

    def test_ttl_expiry_and_purge_preserve_reference_and_disable_replay(self):
        recording = self.ready_recording()
        reference = recording.reference(0)
        self.assertEqual(recording.availability(now=NOW + 86400), "expired")
        with self.assertRaises(ValueError):
            replay.Replay(recording, now=NOW + 86400)
        self.assertTrue(recording.expire(now=NOW + 86400))
        self.assertEqual(recording.to_dict()["events"], [])
        self.assertEqual(recording.reference(0), reference)
        self.assertEqual(recording.availability(now=NOW), "expired")
        second = self.ready_recording()
        second.purge()
        self.assertEqual(second.availability(now=NOW), "expired")

    def test_step_jump_diff_bookmark_and_playback_are_pure_and_isolated(self):
        recording = self.ready_recording()
        original = recording.to_dict()
        simulation = replay.Replay(recording, expected_provenance=self.provenance, now=NOW)
        self.assertEqual(simulation.index, -1)
        self.assertIsNone(simulation.state()["identity_fixture"])
        self.assertFalse(simulation.state()["executable_authority"])
        simulation.step()
        simulation.bookmark("identity selected")
        self.assertEqual(simulation.jump(4)["outcome"], "completed")
        self.assertIsNone(simulation.state()["selection"])
        diff = simulation.before_after(4)
        self.assertEqual(diff["before"]["outcome"], "not_attempted")
        self.assertEqual(diff["after"]["outcome"], "completed")
        self.assertIn("outcome", diff["diff"])
        simulation.go_bookmark("identity selected")
        self.assertEqual(simulation.index, 0)
        simulation.play()
        simulation.tick()
        self.assertEqual(simulation.index, 1)
        simulation.pause()
        simulation.tick()
        self.assertEqual(simulation.index, 1)
        simulation.previous()
        self.assertEqual(simulation.index, 0)
        second = replay.Replay(recording, now=NOW)
        self.assertNotEqual(simulation.namespace, second.namespace)
        self.assertEqual(second.index, -1)
        self.assertEqual(recording.to_dict(), original)
        exposed = simulation.state()
        exposed["preferences"]["specialty"] = "forged"
        self.assertNotEqual(simulation.state()["preferences"].get("specialty"), "forged")

    def test_imported_confirm_and_recorded_success_cannot_supply_authority(self):
        recording = self.recording()
        recording.append({"action": "confirm", "data": {}},
                         outcomes={"api": {"status": "completed", "fixture_refs": [], "delay_ms": 0}})
        recording.seal()
        imported = self.load(recording.to_dict())
        simulation = replay.Replay(imported, now=NOW)
        self.assertEqual(simulation.step()["outcome"], "blocked")
        self.assertFalse(simulation.state()["executable_authority"])

    def test_unknown_blocks_later_simulated_writes_even_after_reset(self):
        recording = self.ready_recording("unknown")
        doc = recording.to_dict()
        additions = [
            ({"action": "reset", "data": {}}, {}),
            ({"action": "confirm", "data": {}}, {"api": {"status": "completed", "fixture_refs": [], "delay_ms": 0}}),
        ]
        for command, outcomes in additions:
            doc["events"].append({"seq": len(doc["events"]) + 1, "input": command,
                                  "outcomes": outcomes, "view": None, "clock": NOW})
        simulation = replay.Replay(self.load(doc), now=NOW)
        self.assertEqual(simulation.jump(6)["outcome"], "blocked")
        self.assertTrue(simulation.state()["unknown"])

    def test_fork_is_immutable_typed_and_recomputes_from_inputs(self):
        recording = self.ready_recording()
        simulation = replay.Replay(recording, now=NOW)
        original = recording.to_dict()
        variant = simulation.fork(4, {"api_status": "unknown", "api_delay_ms": 10})
        self.assertNotEqual(variant.namespace, simulation.namespace)
        self.assertEqual(variant.jump(4)["outcome"], "unknown")
        self.assertEqual(simulation.jump(4)["outcome"], "completed")
        self.assertEqual(recording.to_dict(), original)
        comparison = simulation.compare(variant)
        self.assertTrue(comparison["differences"])
        self.assertEqual(variant.recording.to_dict()["branch"]["parent"], recording.reference(4))
        self.assertEqual(variant.recording.to_dict()["branch"]["parent_digest"], original["digest"])
        for changes in ({"identity_verified": True}, {"allow": True}, {"consent": True},
                        {"receipt": "successful"}, {"ledger": "completed"},
                        {"identity_fixture": "forged"}, {"api_status": "delivered"}):
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                simulation.fork(4, changes)

    def test_typed_preference_identity_clock_model_and_order_variants(self):
        simulation = replay.Replay(self.ready_recording(), now=NOW)
        variant = simulation.fork(1, {"preferences": {"location": "uptown"}, "clock": NOW + 12})
        self.assertEqual(variant.jump(1)["preferences"]["location"], "uptown")
        self.assertEqual(variant.state()["clock"], NOW + 12)
        self.assertEqual(simulation.fork(0, {"identity_fixture": "person-b"}).step()["identity_fixture"], "person-b")
        reordered = simulation.fork(3, {"order": [1, 0]})
        self.assertEqual(reordered.jump(3)["outcome"], "blocked")
        language = self.recording()
        language.append({"action": "language", "data": {"text": "please help"}},
                        outcomes={"model": {"category": "accepted", "preferences": {}}})
        language.seal()
        changed = replay.Replay(language, now=NOW).fork(0, {"model_category": "timeout"})
        self.assertEqual(changed.step()["outcome"], "model_timeout")
        with self.assertRaises(ValueError):
            simulation.fork(3, {"order": [0, 0]})

    def test_regression_proposal_is_reviewed_minimal_data_and_never_executable(self):
        simulation = replay.Replay(self.ready_recording(), now=NOW)
        variant = simulation.fork(2, {"api_status": "failed"})
        for approval in (False, "yes", 1):
            with self.assertRaises(PermissionError):
                variant.regression_proposal(reviewed=approval)
        proposal = variant.regression_proposal(reviewed=True)
        self.assertTrue(proposal["fixture"])
        self.assertTrue(proposal["simulation_only"])
        self.assertTrue(proposal["requires_execution_review"])
        self.assertEqual(len(proposal["events"]), 3)
        self.assertEqual(proposal["parent"], variant.recording.to_dict()["branch"]["parent"])
        self.assertNotIn("code", proposal)

    def test_inspection_escapes_recorded_text_and_reports_api_rules_and_views(self):
        recording = self.recording()
        recording.append({"action": "language", "data": {"text": "<b>help</b>"}},
            outcomes={"model": {"category": "clarify", "preferences": {}},
                      "policy": {"decision": "deny", "reason": "needs_confirmation", "rule_ids": ["R01"]}},
            view={"revision": 1, "renderer": "bob-v1", "visible": ["<b>help</b>"],
                  "enabled": ["help"], "validation": "", "loading": False})
        recording.seal()
        inspected = replay.Replay(recording, now=NOW).inspect(0)
        self.assertEqual(inspected["input"]["data"]["text"], "&lt;b&gt;help&lt;/b&gt;")
        self.assertEqual(inspected["view"]["visible"], ["&lt;b&gt;help&lt;/b&gt;"])
        self.assertEqual(inspected["outcomes"]["policy"]["rule_ids"], ["R01"])

    def test_no_network_live_port_or_model_callback_is_reachable(self):
        recording = self.ready_recording()
        with patch.object(socket, "socket", side_effect=AssertionError("network forbidden")):
            imported = self.load(recording.to_dict())
            simulation = replay.Replay(imported, now=NOW)
            simulation.jump(4)
            simulation.inspect(4)
            variant = simulation.fork(4, {"api_status": "unknown"})
            simulation.compare(variant)
            variant.regression_proposal(reviewed=True)
        for name in ("api", "adapter", "model", "credentials", "journal"):
            with self.subTest(name=name), self.assertRaises(TypeError):
                replay.Replay(recording, now=NOW, **{name: object()})

    def test_navigation_indices_and_bookmarks_are_bounded(self):
        simulation = replay.Replay(self.ready_recording(), now=NOW)
        for index in (True, -2, 5, "1"):
            with self.subTest(index=index), self.assertRaises(ValueError):
                simulation.jump(index)
        with self.assertRaises(ValueError):
            simulation.go_bookmark("missing")

    def test_legacy_helpers_still_make_effect_free_reviewed_proposals(self):
        variant = replay.fork([{"kind": "public_discovery", "phone": "555-0130"}], 0, {"fault": "timeout"})
        self.assertTrue(variant["simulation_only"])
        self.assertNotIn("555-0130", json.dumps(variant))
        self.assertTrue(replay.promote(variant, reviewed=True)["fixture"])
        with self.assertRaises(PermissionError):
            replay.promote(variant, reviewed="yes")

    def test_huge_numbers_and_unpaired_unicode_fail_with_bounded_errors(self):
        for value in (10**400, "\ud800"):
            doc = self.ready_recording().to_dict()
            if type(value) is int:
                doc["created_at"] = value
            else:
                doc["events"][4]["view"]["visible"] = [value]
            with self.subTest(kind=type(value).__name__), self.assertRaises(ValueError):
                self.load(doc)

    def test_delay_and_view_changes_are_visible_even_when_semantic_state_matches(self):
        simulation = replay.Replay(self.ready_recording(), now=NOW)
        variant = simulation.fork(4, {"api_delay_ms": 123})
        differences = simulation.compare(variant)["differences"]
        self.assertEqual(len(differences), 1)
        self.assertEqual(differences[0]["step"], 5)
        self.assertIn("outcomes", differences[0]["event"])
        doc = simulation.recording.to_dict()
        doc["events"][4]["view"]["visible"] = ["Another synthetic label"]
        other = replay.Replay(self.load(doc), now=NOW)
        self.assertIn("view", simulation.compare(other)["differences"][0]["event"])

    def test_read_outcomes_cannot_masquerade_as_completed_writes(self):
        doc = self.ready_recording().to_dict()
        doc["events"][2]["outcomes"]["api"]["status"] = "completed"
        with self.assertRaises(ValueError):
            self.load(doc)
        doc = self.ready_recording().to_dict()
        doc["events"][4]["outcomes"]["api"]["status"] = "ok"
        with self.assertRaises(ValueError):
            self.load(doc)

    def test_model_prose_never_becomes_the_deterministic_receipt_message(self):
        recording = self.recording()
        recording.append({"action": "language", "data": {"text": "please help"}},
                         outcomes={"model": {"category": "accepted", "preferences": {},
                                             "message": "Your appointment was booked"}})
        recording.seal()
        simulation = replay.Replay(recording, now=NOW)
        state = simulation.step()
        self.assertNotIn("was booked", state["message"])
        self.assertEqual(state["history"], [])
        self.assertEqual(simulation.inspect(0)["outcomes"]["model"]["message"], "Your appointment was booked")

    def test_expiring_an_active_replay_erases_its_snapshot_and_stops_controls(self):
        simulation = replay.Replay(self.ready_recording(), now=NOW)
        simulation.jump(4)
        simulation.bookmark("last result")
        reference = simulation.reference()
        self.assertTrue(callable(getattr(simulation, "expire", None)),
                        "active replay needs expiry, not just its source recording")
        self.assertTrue(simulation.expire(now=NOW + 86400))
        self.assertEqual(simulation.recording.to_dict()["events"], [])
        self.assertEqual(simulation.bookmarks, {})
        self.assertEqual(simulation.reference(), reference)
        for action in (simulation.state, simulation.step, lambda: simulation.jump(0),
                       lambda: simulation.inspect(0), lambda: simulation.fork(0, {}),
                       lambda: simulation.regression_proposal(reviewed=True)):
            with self.assertRaises(ValueError):
                action()

    def test_executable_markup_shell_and_python_text_is_not_a_recorded_payload(self):
        for text in ("<img src=x onerror=alert(1)>", "print('payload')", "$(touch payload)",
                     "```python\npass\n```", "python -c payload"):
            doc = self.ready_recording().to_dict()
            doc["events"][4]["view"]["visible"] = [text]
            with self.subTest(text=text), self.assertRaises(ValueError):
                self.load(doc)

    def test_future_creation_cannot_extend_import_retention(self):
        doc = self.ready_recording().to_dict()
        doc["created_at"] = NOW + 86400 * 100
        doc["expires_at"] = doc["created_at"] + 86400
        with self.assertRaises(ValueError):
            self.load(doc)

    def test_open_default_clock_replay_expires_as_wall_time_advances(self):
        recording = self.ready_recording()
        with patch.object(replay, "time", return_value=NOW):
            simulation = replay.Replay(recording)
            simulation.jump(4)
        with patch.object(replay, "time", return_value=NOW + 86400):
            with self.assertRaises(ValueError):
                simulation.state()
            self.assertEqual(simulation.recording.to_dict()["events"], [])

    def test_recording_byte_overflow_drops_without_losing_earlier_capture(self):
        recording = self.recording(limits=replay.Limits(max_record_bytes=1500))
        self.assertTrue(recording.append({"action": "help", "data": {}}))
        original = recording.to_dict()["events"]
        self.assertFalse(recording.append({"action": "language", "data": {"text": "a" * 4096}}))
        self.assertEqual(recording.to_dict()["events"], original)
        self.assertEqual(recording.to_dict()["dropped"], 1)


if __name__ == "__main__":
    unittest.main()
