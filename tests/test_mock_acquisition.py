"""Owned-child acquisition cancellation uses real anonymous pipes, no process."""
import os
from pathlib import Path
import subprocess
import sys
import unittest
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import mock_lifecycle


class Child:
    def __init__(self, slow=False):
        self.returncode, self.slow, self.actions = None, slow, []

    def poll(self):
        return self.returncode

    def terminate(self):
        self.actions.append("terminate")

    def wait(self, timeout):
        self.actions.append("wait")
        if self.slow and "kill" not in self.actions:
            raise subprocess.TimeoutExpired("synthetic-owned-child", timeout)
        self.returncode = 0

    def kill(self):
        self.actions.append("kill")


class MockAcquisitionTests(unittest.TestCase):
    def closed(self, descriptors):
        for descriptor in descriptors:
            with self.assertRaises(OSError):
                os.fstat(descriptor)

    def test_cancelled_select_or_read_closes_owned_child_and_pipes_and_reraises(self):
        for stage in ("select", "read"):
            for cancellation in (KeyboardInterrupt(), SystemExit(9)):
                with self.subTest(stage=stage, cancellation=type(cancellation).__name__):
                    descriptors, child = os.pipe(), Child()
                    target = mock_lifecycle.OwnedMock()
                    try:
                        with patch.object(mock_lifecycle.os, "pipe", return_value=descriptors), \
                             patch.object(mock_lifecycle.subprocess, "Popen", return_value=child), \
                             patch.object(mock_lifecycle.select, "select", side_effect=cancellation if stage == "select" else None,
                                          return_value=([descriptors[0]], [], [])), \
                             patch.object(mock_lifecycle.os, "read", side_effect=cancellation if stage == "read" else None):
                            with self.assertRaises(type(cancellation)) as caught:
                                target.__enter__()
                        self.assertIs(caught.exception, cancellation)
                        self.assertEqual(child.actions, ["terminate", "wait"])
                        self.assertEqual(child.returncode, 0)
                        self.assertIsNone(target.base_url)
                        self.closed(descriptors)
                    finally:
                        for descriptor in descriptors:
                            try:
                                os.close(descriptor)
                            except OSError:
                                pass

    def test_timeout_cleanup_and_owned_terminate_kill_fallback(self):
        child = Child(slow=True)
        descriptors = os.pipe()
        with patch.object(mock_lifecycle.os, "pipe", return_value=descriptors), \
             patch.object(mock_lifecycle.subprocess, "Popen", return_value=child), \
             patch.object(mock_lifecycle.select, "select", return_value=([], [], [])):
            with self.assertRaises(RuntimeError):
                mock_lifecycle.OwnedMock().__enter__()
        self.assertEqual(child.actions, ["terminate", "wait", "kill", "wait"])
        self.closed(descriptors)

    def test_successful_acquisition_keeps_child_until_context_exit(self):
        child, descriptors = Child(), os.pipe()
        with patch.object(mock_lifecycle.os, "pipe", return_value=descriptors), \
             patch.object(mock_lifecycle.subprocess, "Popen", return_value=child), \
             patch.object(mock_lifecycle.select, "select", return_value=([descriptors[0]], [], [])), \
             patch.object(mock_lifecycle.os, "read", return_value=b"43210\n"):
            with mock_lifecycle.OwnedMock() as owned:
                self.assertEqual(owned.base_url, "http://127.0.0.1:43210")
                self.assertEqual(child.actions, [])
                self.closed(descriptors)
        self.assertEqual(child.actions, ["terminate", "wait"])
