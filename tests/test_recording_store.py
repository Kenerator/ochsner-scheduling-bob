"""Private local retention exercises real temp files, not service hooks."""

from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy
from dataclasses import replace
from hashlib import sha256
import importlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import tempfile
import threading
import unittest
from unittest.mock import patch

from ochsner_bob import replay


NOW = 1_700_000_000.0
REFS = {"person-a", "option-a"}


def wire(document):
    document = deepcopy(document)
    document.pop("digest", None)
    encoded = json.dumps(document, sort_keys=True, separators=(",", ":"), allow_nan=False)
    document["digest"] = sha256(encoded.encode()).hexdigest()
    return json.dumps(document)


class RecordingStoreTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.recording_store"),
                             "private RecordingStore implementation is missing")
        self.module = importlib.import_module("ochsner_bob.recording_store")
        self.Store = self.module.RecordingStore
        self.Error = self.module.StoreError
        self.Full = self.module.StoreFull
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.base = Path(self.temp.name)
        self.root = self.base / "recordings"
        self.provenance = replay.make_provenance("a" * 40, dependencies=b"lock", policy=b"policy",
            prompt=b"prompt", schema=b"schema", fixtures=b"fixtures")
        self.store = self.open_store()

    def open_store(self, root=None, **kwargs):
        return self.Store(root or self.root, fixture_refs=REFS, synthetic=True,
                          expected_provenance=self.provenance, **kwargs)

    def recording(self, *, now=NOW, text=None):
        recording = replay.Recording(self.provenance, fixture_refs=REFS, synthetic=True, now=now)
        if text is None:
            recording.append({"action": "help", "data": {}})
        else:
            recording.append({"action": "language", "data": {"text": text}},
                             outcomes={"model": {"category": "clarify", "preferences": {}}})
        recording.seal()
        return recording

    def saved_path(self):
        return next(self.root.glob("rec-*.json"))

    def test_opt_in_must_be_explicit_and_creates_nothing_when_disabled(self):
        for opt_in in (False, None, "yes", 1):
            root = self.base / ("disabled-" + str(opt_in))
            with self.subTest(opt_in=opt_in), self.assertRaises(PermissionError):
                self.Store(root, fixture_refs=REFS, synthetic=opt_in)
            self.assertFalse(root.exists())

    def test_private_atomic_roundtrip_and_reopening(self):
        original = self.recording()
        reference = self.store.save(original, now=NOW)
        self.assertEqual(reference, original.reference(0))
        self.assertEqual(stat.S_IMODE(self.root.stat().st_mode), 0o700)
        for file in self.root.iterdir():
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        loaded = self.open_store().load(reference, now=NOW)
        self.assertIsInstance(loaded, replay.Recording)
        self.assertEqual(loaded.to_dict(), original.to_dict())
        self.assertEqual(loaded.compatibility["drift"], [])
        self.assertEqual(self.store.status(reference, now=NOW), "full_replay")
        self.assertEqual(self.store.stats(now=NOW)["bytes"], sum(file.stat().st_size for file in self.root.glob("rec-*.json")))
        self.assertEqual(original.to_dict()["expires_at"] - NOW, 86400)

    def test_incomplete_capture_is_preserved_and_not_claimed_full(self):
        recording = replay.Recording(self.provenance, fixture_refs=REFS, synthetic=True, now=NOW)
        recording.append({"action": "availability", "data": {}})
        recording.seal()
        reference = self.store.save(recording, now=NOW)
        self.assertEqual(self.store.status(reference, now=NOW), "incomplete_capture")
        self.assertEqual(self.store.load(reference, now=NOW).missing, ["step 1: api"])

    def test_restoration_validates_with_the_explicit_host_retention_clock(self):
        recording = self.recording()
        reference = self.store.save(recording, now=NOW)
        # Reopening with an injected host clock must not first validate against
        # a different real clock and incorrectly classify valid state as corrupt.
        with patch.object(self.module, "time", return_value=NOW - 100):
            restored = self.open_store(now=NOW)
        self.assertEqual(restored.load(reference, now=NOW).to_dict(), recording.to_dict())

    def test_strict_import_rejects_duplicate_extra_nonfinite_paths_and_authority(self):
        original = self.recording(text="approved synthetic request").to_dict()
        payloads = [wire(original).replace('"version": 1', '"version": 1, "version": 1')]
        for key, value in (("endpoint", "http://127.0.0.1:4010"), ("consent", True)):
            doc = deepcopy(original)
            doc[key] = value
            payloads.append(wire(doc))
        for text in ("../private", "https://example.org", "__import__('os')", "phone 555-0130"):
            doc = deepcopy(original)
            doc["events"][0]["input"]["data"]["text"] = text
            payloads.append(wire(doc))
        payloads.extend([b"\xff", "{\"version\":NaN}", "{\"version\":Infinity}"])
        for payload in payloads:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                self.store.import_json(payload, now=NOW)
        self.assertEqual(list(self.root.glob("rec-*.json")), [])

    def test_import_uses_host_fixture_allowlist(self):
        recording = replay.Recording(self.provenance, fixture_refs={"forged-person"}, synthetic=True, now=NOW)
        recording.append({"action": "identity_fixture", "data": {"fixture_ref": "forged-person"}})
        recording.seal()
        with self.assertRaises(ValueError):
            self.store.import_json(recording.export_json(reviewed=True), now=NOW)
        with self.assertRaises(ValueError):
            self.store.save(recording, now=NOW)

    def test_import_limit_is_one_mib_and_distinct_from_private_session_limit(self):
        with self.assertRaises(ValueError):
            self.store.import_json(b" " * (1024 * 1024 + 1), now=NOW)
        doc = self.recording(text=("synthetic " * 410)[:4096]).to_dict()
        template = doc["events"][0]
        doc["events"] = [{**deepcopy(template), "seq": index + 1} for index in range(270)]
        payload = wire(doc)
        self.assertGreater(len(payload.encode()), 1024 * 1024)
        trusted = replay.import_recording(payload, fixture_refs=REFS, now=NOW,
            limits=replace(replay.Limits(), max_import_bytes=2 * 1024 * 1024))
        reference = self.store.save(trusted, now=NOW)
        self.assertEqual(len(self.open_store().load(reference, now=NOW).to_dict()["events"]), 270)
        with self.assertRaises(ValueError):
            self.store.import_json(payload, now=NOW)

    def test_store_revalidates_event_limit_even_for_a_larger_host_recording(self):
        doc = self.recording().to_dict()
        template = doc["events"][0]
        doc["events"] = [{**deepcopy(template), "seq": index + 1} for index in range(2001)]
        trusted = replay.import_recording(wire(doc), fixture_refs=REFS, now=NOW,
                                         limits=replace(replay.Limits(), max_events=2001))
        with self.assertRaises(ValueError):
            self.store.save(trusted, now=NOW)
        self.assertEqual(list(self.root.glob("rec-*.json")), [])

    def test_session_overflow_is_explicit_without_any_truncation(self):
        store = self.open_store(limits=replace(replay.Limits(), max_record_bytes=1500))
        recording = self.recording(text="a" * 4096)
        before = recording.to_dict()
        with self.assertRaises(self.Full) as error:
            store.save(recording, now=NOW)
        self.assertEqual(error.exception.limit, "session")
        self.assertEqual(recording.to_dict(), before)
        self.assertEqual(list(self.root.glob("rec-*.json")), [])

    def test_aggregate_overflow_preserves_existing_recording_and_is_visible(self):
        first = self.recording()
        reference = self.store.save(first, now=NOW)
        size = self.store.stats(now=NOW)["bytes"]
        bounded = self.open_store(max_total_bytes=2 * size - 1)
        before = self.saved_path().read_bytes()
        with self.assertRaises(self.Full) as error:
            bounded.save(self.recording(), now=NOW)
        self.assertEqual(error.exception.limit, "aggregate")
        self.assertEqual(self.saved_path().read_bytes(), before)
        self.assertEqual(bounded.load(reference, now=NOW).to_dict(), first.to_dict())
        self.assertEqual(bounded.stats(now=NOW)["recordings"], 1)
        self.assertEqual(self.store.max_total_bytes, 100 * 1024 * 1024)
        self.assertEqual(self.store.limits.max_record_bytes, 10 * 1024 * 1024)

    def test_duplicate_save_is_idempotent_but_conflicting_or_expired_reference_cannot_revive(self):
        recording = self.recording()
        reference = self.store.save(recording, now=NOW)
        before = self.saved_path().read_bytes()
        self.assertEqual(self.store.save(recording, now=NOW), reference)
        self.assertEqual(self.saved_path().read_bytes(), before)
        doc = recording.to_dict()
        doc["events"][0]["input"]["action"] = "medical"
        changed = replay.import_recording(wire(doc), fixture_refs=REFS, now=NOW)
        with self.assertRaises(self.Error):
            self.store.save(changed, now=NOW)
        self.store.purge(reference, now=NOW)
        with self.assertRaises(self.Error):
            self.store.save(recording, now=NOW)
        self.assertEqual(self.store.status(reference, now=NOW), "expired")

    def test_ttl_boundary_erases_payload_and_reference_stays_expired_across_reopen(self):
        recording = self.recording(text="approved synthetic payload")
        reference = self.store.save(recording, now=NOW)
        self.assertEqual(self.store.status(reference, now=NOW + 86399), "full_replay")
        self.assertEqual(self.store.status(reference, now=NOW + 86400), "expired")
        self.assertIsNone(self.store.load(reference, now=NOW + 86400))
        payload = self.saved_path().read_text()
        self.assertNotIn("approved synthetic payload", payload)
        self.assertNotIn("person-a", payload)
        self.assertEqual(self.open_store().status(reference, now=NOW), "expired")
        self.assertEqual(self.store.stats(now=NOW)["expired"], 1)

    def test_expiry_frees_capacity_for_new_capture_without_relabeling_old_reference(self):
        old = self.store.save(self.recording(), now=NOW)
        size = self.store.stats(now=NOW)["bytes"]
        bounded = self.open_store(max_total_bytes=2 * size - 1)
        fresh = bounded.save(self.recording(now=NOW + 86400), now=NOW + 86400)
        self.assertEqual(bounded.status(old, now=NOW + 86400), "expired")
        self.assertEqual(bounded.status(fresh, now=NOW + 86400), "full_replay")
        self.assertLessEqual(bounded.stats(now=NOW + 86400)["bytes"], bounded.max_total_bytes)

    def test_purge_and_expiry_never_touch_effect_journal_capabilities_or_unknown_files(self):
        from ochsner_bob.journal import EffectJournal
        journal_path = self.root / "effects.json"
        journal = EffectJournal(journal_path)
        journal.claim("opaque-action")
        journal_bytes = journal_path.read_bytes()
        unrelated = {"capabilities.json": b"synthetic capability registry", "media-original.png": b"media"}
        for name, content in unrelated.items():
            file = self.root / name
            file.write_bytes(content)
            file.chmod(0o600)
        old = self.store.save(self.recording(), now=NOW)
        self.assertEqual(self.store.expire(now=NOW + 86400), 1)
        fresh = self.store.save(self.recording(now=NOW + 86400), now=NOW + 86400)
        self.assertEqual(self.store.purge(now=NOW + 86400), 1)
        for reference in (old, fresh):
            self.assertEqual(self.store.status(reference, now=NOW + 86400), "expired")
        self.assertTrue(journal.blocked("opaque-action"))
        self.assertEqual(journal_path.read_bytes(), journal_bytes)
        for name, content in unrelated.items():
            self.assertEqual((self.root / name).read_bytes(), content)

    def test_unknown_and_missing_steps_are_unavailable_not_filesystem_paths(self):
        recording = self.recording()
        reference = self.store.save(recording, now=NOW)
        self.assertEqual(self.store.status(reference.replace("/step/1/", "/step/2/"), now=NOW), "unavailable")
        self.assertIsNone(self.store.load(reference.replace("/step/1/", "/step/2/"), now=NOW))
        unknown = "BOB-" + "b" * 32 + "/step/1/branch/original"
        self.assertEqual(self.store.status(unknown, now=NOW), "unavailable")
        self.assertIsNone(self.store.load(unknown, now=NOW))
        for invalid in ("../effects.json", "/tmp/private", "https://example.org", reference + "/../effects.json", None):
            for action in (self.store.load, self.store.status, self.store.purge):
                if invalid is None and action == self.store.purge:
                    continue
                with self.subTest(invalid=invalid), self.assertRaises(ValueError):
                    action(invalid, now=NOW)

    def test_corrupt_restoration_fails_closed_without_erasure_or_raw_errors(self):
        reference = self.store.save(self.recording(), now=NOW)
        path = self.saved_path()
        valid = path.read_bytes()
        envelope = json.loads(valid)
        mutations = [b"", b"{private-payload", b"[]", b"\xff", b'{"version":1,"version":1}',
                     valid.replace(b'"version":1', b'"version":NaN', 1)]
        changed = deepcopy(envelope)
        changed["id"] = "b" * 32
        mutations.append(json.dumps(changed).encode())
        changed = deepcopy(envelope)
        changed["endpoint"] = "private-payload"
        mutations.append(json.dumps(changed).encode())
        changed = deepcopy(envelope)
        changed["recording"] = None
        changed["expires_at"] = None
        mutations.append(json.dumps(changed).encode())
        for payload in mutations:
            path.write_bytes(payload)
            for action in (self.open_store, lambda: self.store.load(reference, now=NOW),
                           lambda: self.store.purge(now=NOW), lambda: self.store.expire(now=NOW + 86400)):
                with self.subTest(payload=payload):
                    with self.assertRaises(self.Error) as error:
                        action()
                    self.assertNotIn("private-payload", str(error.exception))
                    self.assertNotIn(str(self.root), str(error.exception))
                    self.assertEqual(path.read_bytes(), payload)

    def test_symlink_directory_lock_and_recording_are_not_followed(self):
        reference = self.store.save(self.recording(), now=NOW)
        target = self.base / "private-target"
        target.write_bytes(b"untouched synthetic target")
        target.chmod(0o600)
        alias = self.base / "alias"
        alias.symlink_to(self.root, target_is_directory=True)
        with self.assertRaises(self.Error):
            self.open_store(alias)
        for path in (self.saved_path(), self.root / ".recordings.lock"):
            original = path.read_bytes()
            path.unlink()
            path.symlink_to(target)
            try:
                with self.assertRaises(self.Error):
                    self.open_store()
                with self.assertRaises(self.Error):
                    self.store.purge(reference, now=NOW)
                self.assertEqual(target.read_bytes(), b"untouched synthetic target")
                self.assertTrue(path.is_symlink())
            finally:
                path.unlink()
                path.write_bytes(original)
                path.chmod(0o600)

    def test_shared_permissions_and_hardlinks_fail_closed(self):
        self.store.save(self.recording(), now=NOW)
        path = self.saved_path()
        path.chmod(0o644)
        with self.assertRaises(self.Error):
            self.open_store()
        path.chmod(0o600)
        os.link(path, self.base / "hardlink")
        with self.assertRaises(self.Error):
            self.open_store()
        (self.base / "hardlink").unlink()
        self.root.chmod(0o755)
        with self.assertRaises(self.Error):
            self.open_store()

    def test_orphaned_owned_temporary_file_requires_recovery_without_erasure(self):
        path = self.root / (".recording-tmp-" + "c" * 32)
        path.write_bytes(b"incomplete private capture")
        path.chmod(0o600)
        with self.assertRaises(self.Error):
            self.open_store()
        self.assertEqual(path.read_bytes(), b"incomplete private capture")

    def test_fsync_order_and_write_failure_preserve_previous_bytes(self):
        events = []
        real_fsync, real_replace = os.fsync, os.replace

        def fsync(fd):
            events.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            return real_fsync(fd)

        def replace_file(source, destination, **kwargs):
            self.assertEqual(events[-1], "file")
            events.append("replace")
            return real_replace(source, destination, **kwargs)

        with patch.object(self.module.os, "fsync", side_effect=fsync), patch.object(self.module.os, "replace", side_effect=replace_file):
            reference = self.store.save(self.recording(), now=NOW)
        self.assertEqual(events[-3:], ["file", "replace", "directory"])
        original = self.saved_path().read_bytes()
        for operation in ("fsync", "replace"):
            with patch.object(self.module.os, operation, side_effect=OSError("private raw disk error")):
                with self.assertRaises(self.Error) as error:
                    self.store.save(self.recording(), now=NOW)
                self.assertNotIn("private raw disk error", str(error.exception))
                with self.assertRaises(self.Error):
                    self.store.purge(reference, now=NOW)
            self.assertEqual(self.saved_path().read_bytes(), original)
            self.assertFalse(any(file.name.startswith(".recording-tmp-") for file in self.root.iterdir()))

    def test_concurrent_instances_cannot_exceed_aggregate_capacity(self):
        self.store.save(self.recording(), now=NOW)
        size = self.store.stats(now=NOW)["bytes"]
        race_root = self.base / "race"
        shared = self.open_store(race_root, max_total_bytes=2 * size - 1)
        barrier = threading.Barrier(8)

        def save(index):
            store = self.open_store(race_root, max_total_bytes=2 * size - 1)
            recording = self.recording()
            barrier.wait(timeout=10)
            try:
                return store.save(recording, now=NOW)
            except self.Full:
                return None

        with ThreadPoolExecutor(max_workers=8) as pool:
            references = list(pool.map(save, range(8)))
        self.assertEqual(sum(reference is not None for reference in references), 1)
        self.assertEqual(shared.stats(now=NOW)["recordings"], 1)
        self.assertLessEqual(shared.stats(now=NOW)["bytes"], shared.max_total_bytes)


if __name__ == "__main__":
    unittest.main()
