"""Partial private corrections retain drafts, never verified authority."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from ochsner_bob.session import SchedulingSession
from test_session_contract import FixturePort


class IdentityDraftRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.port = FixturePort()
        self.session = SchedulingSession(self.port, journal_path=Path(self.temp.name) / "effects.json")

    def act(self, action, data=None):
        return self.session.command(action, data or {}, expected_revision=self.session.revision)

    def prepared(self):
        self.act("identity", {"phone": "555-0130", "dob": "1978-09-22", "zip": "70115"})
        self.act("preferences", {"specialty": "primary_care"})
        self.act("availability")
        self.act("select", {"index": 1})

    def test_each_invalid_partial_discriminator_can_be_corrected_without_reentry_or_io(self):
        for field, invalid, valid in (("zip", "1234", "70115"), ("phone", "bad-phone", "555-0130"),
                                      ("dob", "2026-02-30", "1978-09-22")):
            with self.subTest(field=field):
                self.prepared()
                calls = deepcopy((self.port.reads, self.port.writes))
                failed = self.act("identity", {field: invalid})
                self.assertEqual(failed["identity_status"], "missing")
                self.assertIsNone(self.session.identity)
                self.assertIsNone(failed["proposal"])
                self.assertEqual(failed["slots"], [])
                self.assertEqual(failed["appointments"], [])
                self.assertEqual((self.port.reads, self.port.writes), calls)
                # Another field does not silently reinstate the old valid value.
                other = "phone" if field != "phone" else "zip"
                self.act("identity", {other: "555-0130" if other == "phone" else "70115"})
                self.assertEqual((self.port.reads, self.port.writes), calls)
                recovered = self.act("identity", {field: valid})
                self.assertEqual(recovered["identity_status"], "verified")
                self.assertEqual(self.port.reads, calls[0] + ["identity"])
                self.assertEqual(self.port.writes, calls[1])
                self.assertIsNone(recovered["proposal"])

    def test_oversized_or_unsupported_input_cannot_restore_authority_or_escape_private_draft(self):
        self.prepared()
        calls = deepcopy((self.port.reads, self.port.writes))
        self.act("identity", {"zip": "1" * 5000})
        self.assertLessEqual(sum(len(value) for value in self.session._identity_input.values()), 40)
        self.act("identity", {"phone": "555-0130"})
        self.assertEqual((self.port.reads, self.port.writes), calls)
        self.assertEqual(self.act("identity", {"zip": "70115"})["identity_status"], "verified")
        for bad in ({"extra": "private"}, {"phone": 12345}, {"dob": ["private"]}):
            result = self.act("identity", bad)
            self.assertEqual(result["identity_status"], "missing")
            self.assertIsNone(result["proposal"])
        self.act("reset")
        self.assertEqual(self.session._identity_input, {})
        self.assertEqual(self.act("identity", {"zip": "70115"})["identity_status"], "missing")
        exposed = json.dumps([self.session.view(), self.session.trace()])
        for private in ("555-0130", "1978-09-22", "70115", "pat_1003", "_identity_input"):
            self.assertNotIn(private, exposed)
