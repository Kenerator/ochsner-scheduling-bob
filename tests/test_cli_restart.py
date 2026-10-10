"""Actual CLI reentry/locking with an explicit unknown-write unit port.

These tests qualify the launcher namespace, not supplied HTTP acceptance. The
existing supplied-service suites remain separate and unchanged.
"""
import importlib
import importlib.util
import io
import json
import os
from pathlib import Path
import selectors
import stat
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from ochsner_bob import __main__ as cli
from ochsner_bob.http_mock import UnknownOutcome
from ochsner_bob.journal import EffectJournal
from test_session_contract import FixturePort


ROOT = Path(__file__).resolve().parents[1]
BOOK = "providers primary_care downtown\n/identity 555-0130 1978-09-22 70115\navailability\n1\n/confirm\n"


class LostReceiptPort(FixturePort):
    def __init__(self):
        super().__init__()
        self.outcome = UnknownOutcome("explicit synthetic unknown-write boundary")

    def handoff(self, reason, summary):
        self.writes.append((reason, summary))
        raise self.outcome


class CliRestartTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix="bob-cli-restart-")
        self.addCleanup(temporary.cleanup)
        self.directory = Path(temporary.name)
        self.journal = self.directory / "effects.json"
        self.namespace = self.directory / "effects.json.cli-namespace.json"
        self.lock = self.namespace.with_name(self.namespace.name + ".lock")
        self.port = LostReceiptPort()

    def launch(self, turns="/quit\n", *, source=None, journal=None):
        output = io.StringIO()
        with patch.object(cli, "HttpMockAdapter", return_value=self.port):
            code = cli.main(["--journal", str(journal or self.journal)],
                            input_stream=source or io.StringIO(turns), output_stream=output)
        return code, output.getvalue()

    def test_unknown_booking_reentry_and_reset_never_dispatch_a_second_write(self):
        code, first = self.launch(BOOK + "/quit\n")
        self.assertEqual(code, 0)
        self.assertIn("outcome: unknown", first)
        self.assertEqual(len(self.port.writes), 1)
        code, second = self.launch("help\nmedical\nunsupported\nreset\n" + BOOK + "/quit\n")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.port.writes), 1, "same journal must resume the unknown effect namespace")
        self.assertIn("unknown", second.lower())
        self.assertIn("medical", second.lower())
        self.assertNotIn("synthetic appointment was booked", second)

    def test_unknown_handoff_reentry_keeps_help_without_second_write(self):
        self.assertEqual(self.launch("handoff user_requested\n/quit\n")[0], 0)
        self.assertEqual(len(self.port.writes), 1)
        code, output = self.launch("help\nreset\nhandoff user_requested\n/quit\n")
        self.assertEqual(code, 0)
        self.assertEqual(len(self.port.writes), 1)
        self.assertIn("unknown", output.lower())

    def test_namespace_is_opaque_private_stable_and_contains_no_identity(self):
        identities = []
        actual = cli.SchedulingSession
        def observe(*args, **kwargs):
            session = actual(*args, **kwargs)
            identities.append(session.id)
            return session
        with patch.object(cli, "SchedulingSession", side_effect=observe):
            self.assertEqual(self.launch("/identity 555-0130 1978-09-22 70115\n/quit\n")[0], 0)
            self.assertEqual(self.launch()[0], 0)
        self.assertEqual(identities[0], identities[1])
        self.assertTrue(self.namespace.is_file(), "CLI must persist the effect namespace before use")
        payload = json.loads(self.namespace.read_bytes())
        self.assertEqual(set(payload), {"version", "session_id"})
        self.assertEqual(payload["version"], 1)
        self.assertRegex(payload["session_id"], r"^[0-9a-f]{32}$")
        self.assertEqual(payload["session_id"], identities[0])
        for path in (self.namespace, self.lock):
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600)
        self.assertEqual(stat.S_IMODE(self.directory.stat().st_mode), 0o700)
        self.assertEqual(self.lock.read_bytes(), b"1")
        self.assertNotIn("555-0130", self.namespace.read_text())

    def test_reentry_does_not_restore_identity_or_consent(self):
        self.launch("/identity 555-0130 1978-09-22 70115\navailability\n1\n/quit\n")
        reads = len(self.port.reads)
        code, output = self.launch("/confirm\n/quit\n")
        self.assertEqual(code, 0)
        self.assertIn("Identity: missing", output)
        self.assertEqual(self.port.writes, [])
        self.assertEqual(len(self.port.reads), reads)

    def test_new_explicit_journal_is_an_independent_synthetic_run(self):
        self.launch(BOOK + "/quit\n")
        self.assertEqual(self.launch(BOOK + "/quit\n", journal=self.directory / "new-run.json")[0], 0)
        self.assertEqual(len(self.port.writes), 2)

    def test_legacy_random_session_journal_is_not_silently_adopted(self):
        legacy = EffectJournal(self.journal)
        claim = legacy.claim("old-random-session:booking")
        legacy.finish("old-random-session:booking", claim, "unknown")
        before = self.journal.read_bytes()
        code, output = self.launch(BOOK + "/quit\n")
        self.assertEqual(code, 2)
        self.assertEqual(self.port.writes, [])
        self.assertEqual(self.journal.read_bytes(), before)
        self.assertNotIn("old-random-session", output)

    def test_missing_namespace_before_any_effect_fails_closed(self):
        self.launch()
        self.assertTrue(self.namespace.is_file(), "namespace must exist even before first write")
        self.namespace.unlink()
        self.assertEqual(self.launch(BOOK + "/quit\n")[0], 2)
        self.assertEqual(self.port.writes, [])

    def test_missing_or_empty_stable_lock_fails_closed(self):
        self.launch()
        self.assertTrue(self.lock.is_file(), "initialization marker must outlive the namespace file")
        self.lock.unlink()
        self.assertEqual(self.launch()[0], 2)

    def test_empty_marker_cannot_adopt_existing_namespace(self):
        self.launch()
        self.assertTrue(self.lock.is_file())
        self.lock.write_bytes(b"")
        self.assertEqual(self.launch()[0], 2)

    def test_corrupt_and_duplicate_namespace_fields_fail_without_echo(self):
        self.launch()
        self.assertTrue(self.namespace.is_file())
        original = self.namespace.read_bytes()
        values = (b'{"private":"private-sentinel"}', b'{"version":1,"version":1,"session_id":"' + b'a'*32 + b'"}',
                  b'{"version":true,"session_id":"' + b'a'*32 + b'"}', b'[]', b'not-json')
        for value in values:
            with self.subTest(value=value[:20]):
                self.namespace.write_bytes(value)
                code, output = self.launch(BOOK + "/quit\n")
                self.assertEqual(code, 2)
                self.assertNotIn("private-sentinel", output)
                self.assertEqual(self.namespace.read_bytes(), value)
        self.namespace.write_bytes(original)
        self.assertEqual(self.port.writes, [])

    def test_unsafe_namespace_permissions_fail_closed(self):
        self.launch()
        self.assertTrue(self.namespace.is_file())
        self.namespace.chmod(0o644)
        self.assertEqual(self.launch()[0], 2)

    def test_symlink_namespace_is_not_followed(self):
        self.launch()
        self.assertTrue(self.namespace.is_file())
        target = self.directory / "unrelated.json"
        self.namespace.rename(target)
        self.namespace.symlink_to(target)
        before = target.read_bytes()
        self.assertEqual(self.launch()[0], 2)
        self.assertEqual(target.read_bytes(), before)

    def test_lost_journal_after_unknown_does_not_replenish_namespace(self):
        self.launch(BOOK + "/quit\n")
        self.journal.unlink()
        self.assertEqual(self.launch(BOOK + "/quit\n")[0], 2)
        self.assertEqual(len(self.port.writes), 1)

    def test_valid_shaped_namespace_change_cannot_ignore_prior_claims(self):
        self.launch(BOOK + "/quit\n")
        self.assertTrue(self.namespace.is_file())
        value = json.loads(self.namespace.read_bytes())
        value["session_id"] = "0" * 32 if value["session_id"] != "0" * 32 else "1" * 32
        self.namespace.write_text(json.dumps(value))
        self.assertEqual(self.launch(BOOK + "/quit\n")[0], 2)
        self.assertEqual(len(self.port.writes), 1)

    def test_runtime_namespace_corruption_stops_before_next_command(self):
        case = self
        class CorruptingInput(io.StringIO):
            def readline(self, *args):
                case.namespace.write_bytes(b'{"bad":"private-sentinel"}')
                return super().readline(*args)
        code, output = self.launch(source=CorruptingInput("providers primary_care downtown\n/quit\n"))
        self.assertEqual(code, 2)
        self.assertEqual(self.port.reads, [])
        self.assertNotIn("private-sentinel", output)

    def test_concurrent_main_refuses_second_active_cli_then_releases_lock(self):
        entered, release = threading.Event(), threading.Event()
        class WaitingInput(io.StringIO):
            def readline(self, *args):
                entered.set()
                if not release.wait(5):
                    raise AssertionError("test synchronization timed out")
                return super().readline(*args)
        results = []
        worker = threading.Thread(target=lambda: results.append(self.launch(source=WaitingInput("/quit\n"))))
        worker.start()
        try:
            self.assertTrue(entered.wait(5))
            self.assertEqual(self.launch(BOOK + "/quit\n")[0], 2)
            self.assertEqual(self.port.writes, [])
        finally:
            release.set()
            worker.join(5)
        self.assertFalse(worker.is_alive())
        self.assertEqual(results[0][0], 0)
        self.assertEqual(self.launch()[0], 0)

    def test_process_lock_refuses_independent_cli_until_owner_exits(self):
        environment = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "PYTHONPATH": str(ROOT / "src")}
        process = subprocess.Popen([sys.executable, "-m", "ochsner_bob", "--api-url", "http://127.0.0.1:1",
                                    "--journal", str(self.journal)], cwd=ROOT, env=environment,
                                   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   text=True)
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                self.assertTrue(selector.select(5), "CLI startup did not produce its bounded disclosure")
            self.assertIn("Offline deterministic", process.stdout.readline())
            self.assertEqual(self.launch()[0], 2)
            process.communicate("/quit\n", timeout=5)
            self.assertEqual(process.returncode, 0)
            self.assertEqual(self.launch()[0], 0)
        finally:
            if process.poll() is None:
                process.terminate()
            process.communicate(timeout=5)

    def test_namespace_persistence_failure_denies_startup(self):
        self.assertIsNotNone(importlib.util.find_spec("ochsner_bob.cli_namespace"), "private namespace helper missing")
        module = importlib.import_module("ochsner_bob.cli_namespace")
        with patch.object(module.os, "replace", side_effect=OSError("private-sentinel")):
            code, output = self.launch(BOOK + "/quit\n")
        self.assertEqual(code, 2)
        self.assertNotIn("private-sentinel", output)
        self.assertEqual(self.port.writes, [])
        self.assertEqual(self.launch()[0], 2, "failed first persistence cannot be interpreted as a fresh run")
