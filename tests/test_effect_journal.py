"""Durable effect protection uses real private files and synthetic opaque keys."""

from concurrent.futures import ThreadPoolExecutor
import importlib
import importlib.util
import json
import os
from pathlib import Path
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch


class EffectJournalTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(
            importlib.util.find_spec("ochsner_bob.journal"),
            "the durable EffectJournal implementation is missing",
        )
        self.module = importlib.import_module("ochsner_bob.journal")
        self.EffectJournal = self.module.EffectJournal
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.path = self.root / "effects.json"
        self.key = "opaque-synthetic-action-a"
        self.journal = self.EffectJournal(self.path)

    def test_claim_is_durable_and_blocks_a_second_attempt(self):
        self.assertIsNone(self.journal.status(self.key))
        self.assertFalse(self.journal.blocked(self.key))
        claim = self.journal.claim(self.key)
        self.assertIsInstance(claim, str)
        self.assertTrue(claim)
        self.assertNotEqual(claim, self.key)
        self.assertEqual(self.journal.status(self.key), "attempted")
        self.assertTrue(self.journal.blocked(self.key))
        self.assertTrue(self.path.is_file())
        with self.assertRaises(RuntimeError):
            self.journal.claim(self.key)

    def test_reopened_attempt_is_unknown_without_erasing_the_claim(self):
        claim = self.journal.claim(self.key)
        before = self.path.read_bytes()
        reopened = self.EffectJournal(self.path)
        self.assertEqual(reopened.status(self.key), "unknown")
        self.assertTrue(reopened.blocked(self.key))
        with self.assertRaises(RuntimeError):
            reopened.claim(self.key)
        self.assertEqual(self.path.read_bytes(), before)
        # An observer reopening cannot stop the actual owner recording a receipt.
        self.journal.finish(self.key, claim, "completed")
        self.assertEqual(reopened.status(self.key), "completed")

    def test_unknown_survives_reopen_reset_and_recording_expiry(self):
        claim = self.journal.claim(self.key)
        self.journal.finish(self.key, claim, "unknown")
        recording = self.root / "expired-recording.json"
        recording.write_text("{}", encoding="utf-8")
        recording.unlink()
        for journal in (self.journal, self.EffectJournal(self.path)):
            journal.reset()
            self.assertEqual(journal.status(self.key), "unknown")
            self.assertTrue(journal.blocked(self.key))
            with self.assertRaises(RuntimeError):
                journal.claim(self.key)
            with self.assertRaises(RuntimeError):
                journal.finish(self.key, claim, "failed")

    def test_reset_does_not_clear_an_inflight_attempt(self):
        self.journal.claim(self.key)
        self.journal.reset()
        self.assertTrue(self.journal.blocked(self.key))
        self.assertTrue(self.EffectJournal(self.path).blocked(self.key))

    def test_known_outcomes_allow_fresh_claims_and_reject_stale_tokens(self):
        for status in ("completed", "rejected", "failed"):
            with self.subTest(status=status):
                old = self.journal.claim(self.key)
                self.journal.finish(self.key, old, status)
                reopened = self.EffectJournal(self.path)
                self.assertEqual(reopened.status(self.key), status)
                self.assertFalse(reopened.blocked(self.key))
                fresh = reopened.claim(self.key)
                self.assertNotEqual(old, fresh)
                with self.assertRaises(RuntimeError):
                    reopened.finish(self.key, old, "completed")
                self.assertTrue(reopened.blocked(self.key))
                reopened.finish(self.key, fresh, "rejected")

    def test_invalid_statuses_and_claims_cannot_release_protection(self):
        claim = self.journal.claim(self.key)
        before = self.path.read_bytes()
        for status in ("attempted", "queued", "", None, [], {"completed": True}):
            with self.subTest(status=status), self.assertRaises(ValueError):
                self.journal.finish(self.key, claim, status)
        for token in ("", "forged", "forged-🔒", None, [], {}):
            with self.subTest(token=token), self.assertRaises(RuntimeError):
                self.journal.finish(self.key, token, "completed")
        with self.assertRaises(RuntimeError):
            self.journal.finish("another-action", claim, "completed")
        self.assertEqual(self.path.read_bytes(), before)
        self.journal.finish(self.key, claim, "completed")
        with self.assertRaises(RuntimeError):
            self.journal.finish(self.key, claim, "unknown")

    def test_invalid_keys_are_rejected_without_persisting_input(self):
        for key in ("", None, [], {}):
            for method in (self.journal.claim, self.journal.status, self.journal.blocked):
                with self.subTest(key=key, method=method.__name__):
                    with self.assertRaises(ValueError):
                        method(key)
        self.assertFalse(self.path.exists())

    def test_independent_keys_do_not_block_each_other(self):
        first = self.journal.claim(self.key)
        second = self.journal.claim("opaque-synthetic-action-b")
        self.assertNotEqual(first, second)
        self.journal.finish(self.key, first, "failed")
        self.assertTrue(self.journal.blocked("opaque-synthetic-action-b"))

    def test_private_permissions_and_minimal_metadata(self):
        path = self.root / "private" / "effects.json"
        journal = self.EffectJournal(path)
        journal.claim(self.key)
        self.assertEqual(stat.S_IMODE(path.parent.stat().st_mode), 0o700)
        for file in path.parent.iterdir():
            self.assertEqual(stat.S_IMODE(file.stat().st_mode), 0o600)
        payload = path.read_text(encoding="utf-8")
        self.assertNotIn(self.key, payload)
        self.assertEqual(set(json.loads(payload)), {"version", "entries"})
        for entry in json.loads(payload)["entries"].values():
            self.assertEqual(set(entry), {"claim", "status"})

    def test_shared_directory_is_rejected(self):
        shared = self.root / "shared"
        shared.mkdir(mode=0o755)
        with self.assertRaises(RuntimeError):
            self.EffectJournal(shared / "effects.json")

    def test_symlink_does_not_redirect_journal_or_lock_writes(self):
        target = self.root / "untouched"
        target.write_bytes(b"do not change")
        for name in ("effects.json", "effects.json.lock"):
            with self.subTest(name=name):
                directory = self.root / ("case-" + name)
                directory.mkdir(mode=0o700)
                link = directory / name
                link.symlink_to(target)
                try:
                    with self.assertRaises(RuntimeError):
                        self.EffectJournal(directory / "effects.json").claim(self.key)
                    self.assertEqual(target.read_bytes(), b"do not change")
                finally:
                    link.unlink()

    def test_corrupt_file_fails_closed_without_erasure(self):
        self.journal.claim(self.key)
        valid = json.loads(self.path.read_text(encoding="utf-8"))
        bad_entry = json.loads(json.dumps(valid))
        next(iter(bad_entry["entries"].values()))["status"] = "unrecognized"
        bad_claim = json.loads(json.dumps(valid))
        next(iter(bad_claim["entries"].values()))["claim"] = ""
        for payload in (
            b"", b"{truncated", b"[]", b"{}", b"\xff",
            b'{"version":1,"version":1,"entries":{}}',
            b'{"version":true,"entries":{}}',
            json.dumps(bad_entry).encode(), json.dumps(bad_claim).encode(),
        ):
            with self.subTest(payload=payload):
                self.path.write_bytes(payload)
                for action in (
                    lambda: self.EffectJournal(self.path),
                    lambda: self.journal.claim("fresh-action"),
                    lambda: self.journal.blocked(self.key),
                    lambda: self.journal.status(self.key),
                    self.journal.reset,
                ):
                    with self.assertRaises(RuntimeError):
                        action()
                    self.assertEqual(self.path.read_bytes(), payload)

    def test_missing_previously_written_state_fails_closed_on_reopen(self):
        self.journal.claim(self.key)
        self.path.unlink()
        for action in (
            lambda: self.EffectJournal(self.path),
            lambda: self.journal.claim("fresh-action"),
        ):
            with self.assertRaises(RuntimeError):
                action()

    def test_concurrent_independent_keys_are_not_lost_on_replace(self):
        barrier = threading.Barrier(8)

        def attempt(index):
            journal = self.EffectJournal(self.path)
            barrier.wait(timeout=10)
            journal.claim(f"opaque-action-{index}")

        with ThreadPoolExecutor(max_workers=8) as pool:
            list(pool.map(attempt, range(8)))
        reopened = self.EffectJournal(self.path)
        for index in range(8):
            self.assertTrue(reopened.blocked(f"opaque-action-{index}"))

    def test_directory_sync_failure_after_replace_keeps_attempt_blocked(self):
        real_fsync = os.fsync

        def fail_directory_sync(fd):
            if stat.S_ISDIR(os.fstat(fd).st_mode) and self.path.exists():
                raise OSError("directory sync failure")
            return real_fsync(fd)

        with patch.object(self.module.os, "fsync", side_effect=fail_directory_sync):
            with self.assertRaises(RuntimeError):
                self.journal.claim(self.key)
        self.assertTrue(self.journal.blocked(self.key))
        self.assertTrue(self.EffectJournal(self.path).blocked(self.key))

    def test_threads_and_multiple_instances_have_one_winner(self):
        for multiple in (False, True):
            with self.subTest(multiple=multiple):
                path = self.root / f"race-{multiple}.json"
                shared = self.EffectJournal(path)
                barrier = threading.Barrier(12)

                def attempt(index):
                    journal = self.EffectJournal(path) if multiple else shared
                    barrier.wait(timeout=10)
                    try:
                        return journal.claim(self.key)
                    except RuntimeError:
                        return None

                with ThreadPoolExecutor(max_workers=12) as pool:
                    results = list(pool.map(attempt, range(12)))
                self.assertEqual(sum(token is not None for token in results), 1)
                self.assertTrue(self.EffectJournal(path).blocked(self.key))

    def test_separate_processes_have_one_winner(self):
        code = """
from pathlib import Path
import sys
from ochsner_bob.journal import EffectJournal
journal = EffectJournal(Path(sys.argv[1]))
print('ready', flush=True)
sys.stdin.readline()
try:
    journal.claim('opaque-synthetic-action-a')
except RuntimeError:
    print('blocked')
else:
    print('claimed')
"""
        processes = []
        try:
            for _ in range(4):
                processes.append(subprocess.Popen(
                    [sys.executable, "-B", "-c", code, str(self.path)],
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True,
                ))
            for process in processes:
                self.assertEqual(process.stdout.readline().strip(), "ready")
            for process in processes:
                process.stdin.write("go\n")
                process.stdin.flush()
            results = [process.communicate(timeout=15) for process in processes]
            self.assertEqual([out.strip() for out, _ in results].count("claimed"), 1)
            self.assertEqual([out.strip() for out, _ in results].count("blocked"), 3)
            self.assertTrue(all(process.returncode == 0 for process in processes))
            self.assertTrue(all(not err for _, err in results))
        finally:
            for process in processes:
                if process.poll() is None:
                    process.kill()
                    process.communicate()

    def test_file_and_directory_are_fsynced_around_atomic_replace(self):
        events = []
        real_fsync, real_replace = os.fsync, os.replace

        def fsync(fd):
            events.append("directory" if stat.S_ISDIR(os.fstat(fd).st_mode) else "file")
            return real_fsync(fd)

        def replace(source, destination):
            self.assertEqual(events[-1], "file")
            self.assertEqual(json.loads(Path(source).read_text())["version"], 1)
            events.append("replace")
            return real_replace(source, destination)

        with patch.object(self.module.os, "fsync", side_effect=fsync), patch.object(
            self.module.os, "replace", side_effect=replace
        ):
            claim = self.journal.claim(self.key)
            self.assertEqual(events[-3:], ["file", "replace", "directory"])
            self.journal.finish(self.key, claim, "completed")
            self.assertEqual(events[-3:], ["file", "replace", "directory"])

    def test_write_failure_does_not_return_a_claim_or_destroy_old_state(self):
        claim = self.journal.claim(self.key)
        before = self.path.read_bytes()
        for operation in ("fsync", "replace"):
            with self.subTest(operation=operation):
                with patch.object(self.module.os, operation, side_effect=OSError("disk failure")):
                    with self.assertRaises(RuntimeError):
                        self.journal.claim("fresh-action")
                    with self.assertRaises(RuntimeError):
                        self.journal.finish(self.key, claim, "completed")
                self.assertEqual(self.path.read_bytes(), before)
                self.assertTrue(self.EffectJournal(self.path).blocked(self.key))
                self.assertEqual(
                    {file.name for file in self.root.iterdir()},
                    {"effects.json", "effects.json.lock"},
                )


if __name__ == "__main__":
    unittest.main()
