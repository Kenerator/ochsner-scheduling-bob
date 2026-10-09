"""Local write-ahead effect protection, independent of diagnostic recordings.

Keys must be application-generated opaque action/namespace identifiers, never
identity, slot, proposal text or other user input. Digests avoid persisting raw
keys; they are not anonymization and do not make personal-data keys acceptable.
This guards local attempts, not remote idempotency or exactly-once delivery.
"""

from contextlib import contextmanager
import fcntl
from hashlib import sha256
import json
import os
from pathlib import Path
import re
import secrets
import stat
import tempfile
import threading


_FINAL = frozenset({"completed", "rejected", "failed", "unknown"})
_BLOCKING = frozenset({"attempted", "unknown"})
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_LOCKS_GUARD = threading.Lock()
_LOCKS: dict[Path, threading.RLock] = {}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


class EffectJournal:
    """Serialize read/modify/replace under a shared RLock and stable flock.

    A fresh instance treats persisted attempted claims as unknown. Only the
    instance that issued a claim reports it as currently attempted. Possession
    of the matching token permits finishing an attempted claim; a finished
    unknown cannot be cleared by reset or a second finish.
    """

    def __init__(self, path: Path):
        try:
            path = Path(path).absolute()
            if not path.name:
                raise RuntimeError("journal requires a file path")
            # Resolve directory aliases, but never follow the journal symlink.
            parent = path.parent.resolve()
            try:
                parent.mkdir(mode=0o700)
            except FileExistsError:
                pass
            else:
                self._sync_directory(parent.parent)
            self.path = parent / path.name
            self._lock_path = self.path.with_name(self.path.name + ".lock")
            self._owned: dict[str, str] = {}
            self._seen = False
            with _LOCKS_GUARD:
                self._mutex = _LOCKS.setdefault(self.path, threading.RLock())
            with self._locked():
                self._read()
        except OSError:
            raise RuntimeError("journal storage unavailable; effects blocked") from None

    @staticmethod
    def _key(key: str) -> str:
        if not isinstance(key, str) or not key:
            raise ValueError("an opaque nonempty action key is required")
        return sha256(key.encode("utf-8")).hexdigest()

    @staticmethod
    def _private_file(fd):
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise RuntimeError("journal requires private regular files")

    @staticmethod
    def _sync_directory(path):
        fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(fd)
        finally:
            os.close(fd)

    @contextmanager
    def _locked(self):
        # The lock inode is never replaced or removed: locking the atomically
        # replaced state file itself would let callers lock different inodes.
        with self._mutex:
            try:
                info = self.path.parent.stat()
                if info.st_uid != os.getuid() or info.st_mode & 0o077:
                    raise RuntimeError("journal requires a private local directory")
                fd = os.open(self._lock_path, os.O_RDWR | os.O_CREAT
                             | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
                try:
                    self._private_file(fd)
                    fcntl.flock(fd, fcntl.LOCK_EX)
                    try:
                        marker = os.read(fd, 2)
                        if marker not in (b"", b"1"):
                            raise RuntimeError("journal lock corrupt; effects blocked")
                        self._seen = self._seen or bool(marker)
                        yield fd
                    finally:
                        fcntl.flock(fd, fcntl.LOCK_UN)
                finally:
                    os.close(fd)
            except OSError:
                # Do not expose arbitrary OS paths or exception contents.
                raise RuntimeError("journal storage unavailable; effects blocked") from None

    def _read(self):
        try:
            fd = os.open(self.path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            if self._seen:
                raise RuntimeError("journal state missing; effects blocked") from None
            return {}
        with os.fdopen(fd, "r", encoding="utf-8") as stream:
            self._private_file(stream.fileno())
            self._seen = True
            try:
                data = json.load(stream, object_pairs_hook=_unique_object)
                if (not isinstance(data, dict) or set(data) != {"version", "entries"}
                        or type(data["version"]) is not int or data["version"] != 1
                        or not isinstance(data["entries"], dict)):
                    raise ValueError("invalid journal schema")
                for key, entry in data["entries"].items():
                    if (not _HEX.fullmatch(key) or not isinstance(entry, dict)
                            or set(entry) != {"claim", "status"}
                            or not isinstance(entry["claim"], str)
                            or not _HEX.fullmatch(entry["claim"])
                            or not isinstance(entry["status"], str)
                            or entry["status"] not in _FINAL | {"attempted"}):
                        raise ValueError("invalid journal entry")
                return data["entries"]
            except (ValueError, UnicodeError, RecursionError):
                raise RuntimeError("journal corrupt; effects blocked") from None

    def _write(self, entries, lock_fd):
        temporary = None
        try:
            # A durable initialization marker distinguishes a new journal from
            # deleted/incomplete state on reopening. A crash during first write
            # conservatively blocks instead of interpreting missing state as new.
            if os.fstat(lock_fd).st_size == 0:
                self._seen = True
                os.write(lock_fd, b"1")
                os.fsync(lock_fd)
                self._sync_directory(self.path.parent)
            fd, temporary = tempfile.mkstemp(prefix=".effect-", dir=self.path.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump({"version": 1, "entries": entries}, stream,
                          sort_keys=True, separators=(",", ":"), allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.path)
            temporary = None
            self._seen = True
            self._sync_directory(self.path.parent)
        finally:
            if temporary is not None:
                os.unlink(temporary)

    def status(self, key: str) -> str | None:
        digest = self._key(key)
        with self._locked():
            entry = self._read().get(digest)
            if entry is None:
                return None
            if entry["status"] == "attempted" and self._owned.get(digest) != entry["claim"]:
                return "unknown"
            return entry["status"]

    def blocked(self, key: str) -> bool:
        return self.status(key) in _BLOCKING

    def claim(self, key: str) -> str:
        digest = self._key(key)
        with self._locked() as lock_fd:
            entries = self._read()
            if entries.get(digest, {}).get("status") in _BLOCKING:
                raise RuntimeError("unresolved effect requires reconciliation")
            claim = secrets.token_hex(32)
            entries[digest] = {"claim": claim, "status": "attempted"}
            self._write(entries, lock_fd)
            self._owned[digest] = claim
            return claim

    def finish(self, key: str, claim: str, status: str) -> None:
        digest = self._key(key)
        if not isinstance(status, str) or status not in _FINAL:
            raise ValueError("invalid effect status")
        with self._locked() as lock_fd:
            entries = self._read()
            entry = entries.get(digest)
            if (entry is None or entry["status"] != "attempted"
                    or not isinstance(claim, str)
                    or not _HEX.fullmatch(claim)
                    or not secrets.compare_digest(entry["claim"], claim)):
                raise RuntimeError("claim is invalid or no longer pending")
            entries[digest] = {"claim": claim, "status": status}
            self._write(entries, lock_fd)
            self._owned.pop(digest, None)

    def reset(self) -> None:
        """A UI/service reset never erases durable effect protection.

        New synthetic-service runs use new opaque namespace keys. Recording
        expiry must operate on a separate store, never this file or its lock.
        """
        with self._locked():
            self._read()
