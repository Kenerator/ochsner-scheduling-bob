"""Authority contracts independent of reactive browser kernels."""
import tempfile
import unittest
from pathlib import Path
from copy import deepcopy
import json
import os
from unittest.mock import patch

from test_session_contract import FixturePort


class BrowserServiceTests(unittest.TestCase):
    def setUp(self):
        from ochsner_bob.browser_service import BrowserService
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.ports = []
        self.tick = [0.0]
        def factory():
            port = FixturePort()
            self.ports.append(port)
            return port
        self.factory = factory
        self.service = BrowserService(factory, Path(self.temp.name) / "effects.json", clock=lambda: self.tick[0])
        self.patient = self.service.create()

    def receipt(self, revision=0, **changes):
        return {"revision": revision, "renderer": "bob-v1", "visible": ["start"],
                "draft": {}, "focus": None, "scroll": 0, "expanded": [], **changes}

    def restart(self):
        from ochsner_bob.browser_service import BrowserService
        return BrowserService(self.factory, Path(self.temp.name) / "effects.json", clock=lambda: self.tick[0])

    def command(self, action, **data):
        token = self.patient["token"]
        return self.service.command(token, action, data, self.service.read(token)["revision"])

    def ready(self):
        self.command("identity", phone="555-0130", dob="1978-09-22", zip="70115")
        self.command("preferences", specialty="primary_care", location="downtown")
        self.command("availability")
        return self.command("select", index=1)

    def replace_registry(self, raw):
        # Test-only mutations of the disposable private registry.
        self.service.registry.write_bytes(raw)
        self.service.registry.chmod(0o600)

    def test_capability_is_not_session_or_trace_reference(self):
        view = self.service.read(self.patient["token"])
        for bad in (view["session_id"], view["reference"], "", "unknown"):
            with self.assertRaises(PermissionError):
                self.service.read(bad)

    def test_two_sessions_and_polling_do_not_share_or_execute(self):
        other = self.service.create()
        self.service.command(self.patient["token"], "identity", {"phone":"555-0101", "dob":"1985-04-12"}, 0)
        self.assertEqual(self.service.read(other["token"])["identity_status"], "missing")
        for _ in range(5):
            self.service.read(self.patient["token"])
        self.assertEqual(self.ports[0].writes, [])
        self.assertEqual(self.service.read(self.patient["token"])["revision"], 1)

    def test_pairing_requires_single_use_patient_grant(self):
        grant = self.service.pair(self.patient["token"])
        support = self.service.join(grant)
        with self.assertRaises(PermissionError):
            self.service.join(grant)
        with self.assertRaises(PermissionError):
            self.service.pair(support)
        self.assertEqual(self.service.read(support)["patient"]["revision"], 0)
        with self.assertRaises(PermissionError):
            self.service.command(support, "identity", {}, 0)

    def test_ack_mirror_and_stale_submission_are_effect_free(self):
        support = self.service.join(self.service.pair(self.patient["token"]))
        receipt = {"revision":0,"renderer":"bob-v1","visible":["start"],
                   "draft":{"message":"public draft"},"focus":"message","scroll":0,"expanded":[]}
        self.service.ack(self.patient["token"], receipt)
        mirror = self.service.read(support)
        self.assertTrue(mirror["fresh"])
        self.assertEqual(mirror["last_observed"]["draft"]["message"], "public draft")
        self.service.command(self.patient["token"], "help", {}, 0)
        stale = self.service.command(self.patient["token"], "handoff", {}, 0)
        self.assertTrue(stale["stale"])
        self.assertFalse(self.service.read(support)["fresh"])
        self.assertEqual(self.ports[0].writes, [])

    def test_support_lease_expiry_and_suggestion_require_patient_acceptance(self):
        support = self.service.join(self.service.pair(self.patient["token"]))
        with self.assertRaises(PermissionError):
            self.service.command(support, "takeover", {}, 0)
        self.service.ack(self.patient["token"], {"revision":0,"renderer":"bob-v1","visible":["start"],"draft":{},"focus":None,"scroll":0,"expanded":[]})
        self.service.command(support, "takeover", {}, 0)
        self.service.suggest(support, {"specialty":"dermatology"}, 1)
        view = self.service.read(self.patient["token"])
        self.assertEqual(view["preferences"], {})
        self.assertIsNone(view["proposal"])
        self.service.command(support, "return", {}, view["revision"])
        view = self.service.read(self.patient["token"])
        self.service.accept(self.patient["token"], view["support_suggestion"]["id"], view["revision"])
        self.assertEqual(self.service.read(self.patient["token"])["preferences"]["specialty"], "dermatology")
        self.assertEqual(self.ports[0].writes, [])

    def test_restart_recovers_effect_namespace_but_not_identity_or_consent(self):
        from ochsner_bob.browser_service import BrowserService
        token = self.patient["token"]
        session, _ = self.service._resolve(token)
        session.journal.claim(session._key("booking"))
        original_id = session.id
        restarted = BrowserService(FixturePort, Path(self.temp.name) / "effects.json")
        view = restarted.read(token)
        self.assertEqual(view["session_id"], original_id)
        self.assertTrue(view["booking_blocked"])
        self.assertEqual(view["identity_status"], "missing")
        self.assertIsNone(view["proposal"])

    def test_ack_schema_rejects_private_fields_and_nested_authority(self):
        for receipt in ({"revision":0,"renderer":"bob-v1","draft":{"phone":"555-0101"}},
                        {"revision":0,"renderer":"bob-v1","draft":{"message":{"confirm":True}}}):
            with self.assertRaises(ValueError):
                self.service.ack(self.patient["token"], receipt)

    def test_missing_registry_before_any_effect_does_not_start_a_fresh_namespace(self):
        self.assertFalse(self.service.journal_path.exists())
        self.service.registry.unlink()
        with self.assertRaises(RuntimeError):
            self.restart()

    def test_deleted_or_changed_registry_blocks_existing_service_before_commands(self):
        token = self.patient["token"]
        original = self.service.registry.read_bytes()
        for raw in (None, b'{"version":1,"bindings":{}}'):
            with self.subTest(raw=raw):
                self.replace_registry(original)
                service = self.restart()
                if raw is None:
                    service.registry.unlink()
                else:
                    service.registry.write_bytes(raw)
                with self.assertRaises(RuntimeError):
                    service.command(token, "handoff", {}, 0)
                self.assertEqual(service.sessions[self.patient["view"]["session_id"]].api.writes, [])

    def test_registry_corruption_is_sanitized_and_does_not_create_sessions(self):
        token = self.patient["token"]
        session_id = self.patient["view"]["session_id"]
        digest = self.service._digest(token)
        documents = [b'PRIVATE_SENTINEL', b'{"version":1,"version":1,"bindings":{}}',
                     b'{"version":1,"bindings":{},"extra":"PRIVATE_SENTINEL"}',
                     json.dumps({"version":1,"bindings":{digest:[session_id,"admin",1]}}).encode(),
                     json.dumps({"version":1,"bindings":{digest:[session_id,"patient",float("nan")]}}).encode()]
        for raw in documents:
            with self.subTest(raw=raw):
                self.replace_registry(raw)
                before = len(self.ports)
                with self.assertRaises(RuntimeError) as caught:
                    self.restart()
                self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
                self.assertEqual(len(self.ports), before)
                self.assertEqual(self.service.registry.read_bytes(), raw)

    def test_restore_rejects_over_session_cap_before_instantiating_any(self):
        from ochsner_bob import browser_service as module
        bindings = {f"{index:064x}":[f"{index:032x}","patient",module.time()]
                    for index in range(65)}
        self.replace_registry(json.dumps({"version":1,"bindings":bindings}).encode())
        before = len(self.ports)
        with self.assertRaises(RuntimeError):
            self.restart()
        self.assertEqual(len(self.ports), before)

    def test_restore_rejects_future_issue_times_instead_of_eventually_reviving_them(self):
        from ochsner_bob import browser_service as module
        document = json.loads(self.service.registry.read_bytes())
        next(iter(document["bindings"].values()))[2] = module.time() + 1000
        self.replace_registry(json.dumps(document).encode())
        with self.assertRaises(RuntimeError):
            self.restart()

    def test_registry_symlink_hardlink_and_permissions_fail_closed_on_restore(self):
        registry = self.service.registry
        original = registry.read_bytes()
        target = Path(self.temp.name) / "private-target"
        target.write_bytes(original)
        target.chmod(0o600)
        for kind in ("symlink", "hardlink", "permissions"):
            with self.subTest(kind=kind):
                registry.unlink()
                if kind == "symlink":
                    registry.symlink_to(target)
                elif kind == "hardlink":
                    os.link(target, registry)
                else:
                    registry.write_bytes(original)
                    registry.chmod(0o644)
                with self.assertRaises(RuntimeError):
                    self.restart()
                self.assertEqual(target.read_bytes(), original)
        registry.chmod(0o600)

    def test_live_registry_symlink_is_not_silently_replaced_by_create(self):
        registry = self.service.registry
        target = Path(self.temp.name) / "private-target"
        target.write_bytes(registry.read_bytes())
        target.chmod(0o600)
        registry.unlink()
        registry.symlink_to(target)
        with self.assertRaises(RuntimeError):
            self.service.create()
        self.assertTrue(registry.is_symlink())
        self.assertEqual(len(self.service.sessions), 1)

    def test_persistence_failure_does_not_publish_a_memory_only_capability(self):
        from ochsner_bob import browser_service as module
        tokens, sessions = dict(self.service.tokens), dict(self.service.sessions)
        original = self.service.registry.read_bytes()
        with patch.object(module.os, "replace", side_effect=OSError("PRIVATE_SENTINEL")):
            with self.assertRaises(RuntimeError) as caught:
                self.service.create()
        self.assertNotIn("PRIVATE_SENTINEL", str(caught.exception))
        self.assertEqual(self.service.tokens, tokens)
        self.assertEqual(self.service.sessions, sessions)
        self.assertEqual(self.service.registry.read_bytes(), original)
        self.assertEqual(list(self.service.registry.parent.glob(".capability-*")), [])
        with self.assertRaises(RuntimeError):
            self.service.command(self.patient["token"], "handoff", {}, 0)

    def test_capability_cap_also_applies_to_patient_creation(self):
        # Real issuance reaches the boundary; a second patient must not exceed it.
        for _ in range(255):
            self.service.join(self.service.pair(self.patient["token"]))
        self.assertEqual(len(self.service.tokens), 256)
        before = self.service.registry.read_bytes()
        with self.assertRaises(ValueError):
            self.service.create()
        self.assertEqual(len(self.service.tokens), 256)
        self.assertEqual(self.service.registry.read_bytes(), before)

    def test_pairing_cap_expiry_and_restart_keep_grants_one_use(self):
        grants = [self.service.pair(self.patient["token"]) for _ in range(128)]
        with self.assertRaises(ValueError):
            self.service.pair(self.patient["token"])
        self.tick[0] = 300
        with self.assertRaises(PermissionError):
            self.service.join(grants[0])
        new_grant = self.service.pair(self.patient["token"])
        support = self.service.join(new_grant)
        self.assertEqual(self.service.read(support)["patient"]["session_id"], self.patient["view"]["session_id"])
        with self.assertRaises(PermissionError):
            self.service.join(new_grant)
        outstanding = self.service.pair(self.patient["token"])
        with self.assertRaises(PermissionError):
            self.restart().join(outstanding)

    def test_patient_expiry_also_invalidates_unconsumed_pairing(self):
        from ochsner_bob import browser_service as module
        issued = next(iter(self.service.tokens.values()))[2]
        with patch.object(module, "time", return_value=issued + 86399):
            grant = self.service.pair(self.patient["token"])
        with patch.object(module, "time", return_value=issued + 86401):
            with self.assertRaises(PermissionError):
                self.service.join(grant)

    def test_expired_capabilities_do_not_renew_on_restart_or_erase_unknown(self):
        from ochsner_bob import browser_service as module
        token = self.patient["token"]
        session, _ = self.service._resolve(token)
        session.journal.claim(session._key("booking"))
        issued = next(iter(self.service.tokens.values()))[2]
        with patch.object(module, "time", return_value=issued + 86401):
            restarted = self.restart()
            with self.assertRaises(PermissionError):
                restarted.read(token)
            restarted.create()
        self.assertTrue(session.journal.blocked(session._key("booking")))
        self.assertEqual(self.ports[0].writes, [])

    def test_actual_lease_expiry_returns_control_once_without_writes(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        self.service.ack(token, self.receipt())
        self.service.command(support, "takeover", {}, 0)
        self.tick[0] = 299.9
        self.assertTrue(self.service.read(token)["takeover"])
        self.tick[0] = 300
        returned = self.service.read(token)
        self.assertFalse(returned["takeover"])
        self.assertEqual(returned["revision"], 2)
        self.assertEqual(self.service.read(token)["revision"], 2)
        with self.assertRaises(PermissionError):
            self.service.suggest(support, {"location":"uptown"}, 2)
        self.assertEqual(self.ports[0].writes, [])
        self.assertEqual(self.command("help")["state"], "help")

    def test_last_observed_snapshot_does_not_advance_on_unacknowledged_commands(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        self.assertIsNone(self.service.read(support)["observed_patient"])
        self.service.ack(token, self.receipt())
        before = self.service.read(support)["observed_patient"]
        self.command("help")
        mirror = self.service.read(support)
        self.assertEqual(mirror["observed_patient"], before)
        self.assertEqual(mirror["observed_patient"]["state"], "start")
        self.assertFalse(mirror["fresh"])
        mirror["observed_patient"]["state"] = "forged"
        self.assertEqual(self.service.read(support)["observed_patient"], before)

    def test_unserved_current_revision_cannot_be_acknowledged_as_seen(self):
        token = self.patient["token"]
        session, _ = self.service._resolve(token)
        session.command("help", expected_revision=0)
        with self.assertRaises(ValueError):
            self.service.ack(token, self.receipt(1))

    def test_observed_snapshot_contains_exact_delivered_suggestion(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        self.service.ack(token, self.receipt())
        self.service.command(support, "takeover", {}, 0)
        self.service.suggest(support, {"location":"uptown"}, 1)
        self.service.command(support, "return", {}, 2)
        delivered = self.service.read(token)
        self.service.ack(token, self.receipt(delivered["revision"]))
        observed = self.service.read(support)["observed_patient"]
        self.assertEqual(observed["support_suggestion"], delivered["support_suggestion"])

    def test_confirmation_nonce_never_reaches_either_support_snapshot(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        delivered = self.ready()
        nonce = delivered["proposal"]["nonce"]
        self.service.ack(token, self.receipt(delivered["revision"]))
        self.assertNotIn(nonce, json.dumps(self.service.read(support)))
        with self.assertRaises(ValueError):
            self.service.ack(token, self.receipt(delivered["revision"], draft={"message":nonce}))

    def test_valid_shape_ack_rejects_private_values_and_preserves_prior_observation(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        self.service.ack(token, self.receipt())
        before = self.service.read(support)
        for draft in ({"phone":"555-0130"}, {"message":"my phone is 555-0130"},
                      {"message":"DOB 1978-09-22"}, {"location":"555-0130"}):
            with self.subTest(draft=draft), self.assertRaises(ValueError):
                self.service.ack(token, self.receipt(draft=draft))
        self.assertEqual(self.service.read(support), before)

    def test_public_calendar_drafts_remain_mirrored(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        draft = {"start_date": "2026-10-12", "end_date": "2026-10-15"}
        self.service.ack(token, self.receipt(draft=draft))
        self.assertEqual(self.service.read(support)["last_observed"]["draft"], draft)

    def test_invalidated_confirmation_nonce_cannot_be_mirrored_as_draft(self):
        token = self.patient["token"]
        nonce = self.ready()["proposal"]["nonce"]
        delivered = self.command("help")
        with self.assertRaises(ValueError):
            self.service.ack(token, self.receipt(delivered["revision"], draft={"message": nonce}))

    def test_invalid_suggestions_do_not_enter_mirror_or_change_revision(self):
        token = self.patient["token"]
        support = self.service.join(self.service.pair(token))
        self.service.ack(token, self.receipt())
        self.service.command(support, "takeover", {}, 0)
        for preferences in ({"location":"555-0130"}, {"specialty":"PRIVATE_SENTINEL"},
                            {"start_date":"2026-02-30"},
                            {"start_date":"2026-11-01", "end_date":"2026-10-01"}):
            with self.subTest(preferences=preferences), self.assertRaises(ValueError):
                self.service.suggest(support, preferences, 1)
        view = self.service.read(token)
        self.assertEqual(view["revision"], 1)
        self.assertIsNone(view["support_suggestion"])

    def test_registry_and_trace_contain_no_raw_capabilities_or_identity(self):
        token = self.patient["token"]
        grant = self.service.pair(token)
        support = self.service.join(grant)
        self.ready()
        session, _ = self.service._resolve(token)
        serialized = self.service.registry.read_text() + json.dumps(session.trace())
        for private in (token, support, grant, "555-0130", "1978-09-22", "70115", "pat_1003", "slot_4001"):
            self.assertNotIn(private, serialized)

    def test_safety_routes_reachable_from_partial_duplicate_proposal_success_unknown_and_takeover(self):
        from ochsner_bob.http_mock import UnknownOutcome
        token = self.patient["token"]
        transitions = [lambda: self.command("identity", phone="555-0130"),
                       lambda: self.command("identity", phone="555-0130", dob="1978-09-22"),
                       self.ready]
        def finish(unknown=False):
            delivered = self.ready()
            self.ports[0].outcome = UnknownOutcome("synthetic") if unknown else None
            self.service.command(token, "confirm", {"proposal_id":delivered["proposal"]["id"],
                                 "nonce":delivered["proposal"]["nonce"]}, delivered["revision"])
        transitions += [lambda: finish(), lambda: finish(True)]
        for transition in transitions:
            transition()
            count = len(self.ports[0].writes)
            for route in ("help", "medical", "unsupported", "discover"):
                self.command(route)
                self.assertEqual(len(self.ports[0].writes), count)
        support = self.service.join(self.service.pair(token))
        view = self.service.read(token)
        self.service.ack(token, self.receipt(view["revision"]))
        self.service.command(support, "takeover", {}, view["revision"])
        count = len(self.ports[0].writes)
        for route in ("help", "medical", "unsupported", "discover"):
            self.command(route)
            self.assertEqual(len(self.ports[0].writes), count)


if __name__ == "__main__":
    unittest.main()
