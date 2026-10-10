"""Private CLI effect namespace; same journal resumes, never migrates old claims.

Only an opaque session ID is retained. The stable lock is held for the entire
CLI lifetime so two terminals cannot independently operate the same namespace.
This is local crash/duplicate protection, not remote exactly-once delivery.
"""
import fcntl
import json
import os
import re
import tempfile
from uuid import uuid4

from .journal import EffectJournal


_ERROR = "CLI namespace unavailable or already active; effects blocked."


class CliNamespace:
    def __init__(self, journal_path):
        self._path = journal_path
        self._fd = None

    def __enter__(self):
        try:
            self.journal = EffectJournal(self._path)
            self.path = self.journal.path.with_name(self.journal.path.name + ".cli-namespace.json")
            self.lock_path = self.path.with_name(self.path.name + ".lock")
            self._fd = os.open(self.lock_path, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            EffectJournal._private_file(self._fd)
            fcntl.flock(self._fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            marker = os.read(self._fd, 2)
            if marker == b"":
                # No adoption of a preexisting namespace OR legacy journal. A
                # deleted/recreated lock must not reinterpret old data as fresh.
                if self.path.exists() or self.path.is_symlink() or self.journal.path.exists():
                    raise ValueError()
                self.session_id = uuid4().hex
                self._raw = json.dumps({"version": 1, "session_id": self.session_id},
                                       sort_keys=True, separators=(",", ":")).encode()
                # Marker first: interrupted first persistence permanently denies
                # reopening missing state rather than minting another namespace.
                os.write(self._fd, b"1")
                os.fsync(self._fd)
                EffectJournal._sync_directory(self.path.parent)
                self._write()
            elif marker == b"1":
                self._raw = self._read()
                self.session_id = self._decode(self._raw)
            else:
                raise ValueError()
            self.check()
            return self
        except Exception:
            self.close()
            raise RuntimeError(_ERROR) from None

    @staticmethod
    def _decode(raw):
        def pairs(items):
            value = {}
            for key, item in items:
                if key in value:
                    raise ValueError()
                value[key] = item
            return value
        value = json.loads(raw, object_pairs_hook=pairs)
        if (type(value) is not dict or set(value) != {"version", "session_id"}
                or type(value["version"]) is not int or value["version"] != 1
                or type(value["session_id"]) is not str
                or not re.fullmatch(r"[0-9a-f]{32}", value["session_id"])):
            raise ValueError()
        return value["session_id"]

    def _read(self):
        fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            EffectJournal._private_file(fd)
            raw = os.read(fd, 1025)
            if len(raw) > 1024 or os.fstat(fd).st_size != len(raw):
                raise ValueError()
            self._decode(raw)
            return raw
        finally:
            os.close(fd)

    def _write(self):
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".cli-namespace-", dir=self.path.parent)
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(self._raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
            EffectJournal._sync_directory(self.path.parent)
        finally:
            if temporary is not None:
                os.unlink(temporary)

    def check(self):
        """Recheck immutable binding/lock and journal membership before a turn."""
        try:
            EffectJournal._private_file(self._fd)
            actual, linked = os.fstat(self._fd), self.lock_path.lstat()
            if (actual.st_dev, actual.st_ino) != (linked.st_dev, linked.st_ino):
                raise ValueError()
            os.lseek(self._fd, 0, os.SEEK_SET)
            if os.read(self._fd, 2) != b"1" or self._read() != self._raw:
                raise ValueError()
            # Use the journal's existing locked schema/private-file validation.
            # A valid-shaped edited ID must not hide claims from another ID.
            with self.journal._locked():
                entries = self.journal._read()
                allowed = {self.journal._key(self.session_id + ":" + kind)
                           for kind in ("booking", "handoff")}
                if set(entries) - allowed:
                    raise ValueError()
        except Exception:
            raise RuntimeError(_ERROR) from None

    def close(self):
        if self._fd is not None:
            os.close(self._fd)
            self._fd = None

    def __exit__(self, *_args):
        self.close()
