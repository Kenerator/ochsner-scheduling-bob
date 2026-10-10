"""Private local retention for synthetic replay data, never domain authority.

One atomic envelope per opaque recording/branch; no service, adapters, secrets,
capability bindings or effect journal. Only rec-<id>-<branch>.json belongs to this
store. Expiry/purge keeps a tiny payload-free tombstone for stable references.
Tombstones count toward quota; live data is never silently evicted or truncated.
Quota covers committed envelopes (atomic replacement may temporarily use one
extra session's space). Call expire periodically; reads/saves also sweep expiry.
Already-loaded memory copies belong to the caller and cannot be revoked here.
"""

from contextlib import contextmanager
from dataclasses import replace
import fcntl
import json
import math
import os
from pathlib import Path
import re
import stat
import threading
from time import time
from uuid import uuid4

from .replay import Limits, Recording, import_recording


_BRANCH = r"(?:original|[0-9a-f]{32})"
_REFERENCE = re.compile(r"BOB-([0-9a-f]{32})/step/([0-9]{1,4})/branch/(" + _BRANCH + r")\Z")
_FILE = re.compile(r"rec-([0-9a-f]{32})-(" + _BRANCH + r")\.json\Z")
_TEMP = re.compile(r"\.recording-tmp-[0-9a-f]{32}\Z")
_LOCKS_GUARD = threading.Lock()
_LOCKS: dict[Path, threading.RLock] = {}


class StoreError(RuntimeError):
    """Fail-closed storage error with categorical text, never raw OS/JSON data."""


class StoreFull(StoreError):
    def __init__(self, limit):
        self.limit = limit
        super().__init__(f"recording {limit} capacity exceeded; capture was not truncated")


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")


def _now(value):
    value = time() if value is None else value
    if type(value) not in (int, float) or not 0 <= value <= 1e12 or not math.isfinite(value):
        raise ValueError("invalid retention clock")
    return value


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate fields")
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValueError("nonfinite JSON")


class RecordingStore:
    """Immutable private snapshots of Recording, with a host-owned fixture catalog.

    save(recording)/import_json(payload) return a BOB reference. load returns a
    fresh Recording or None; status returns full_replay, incomplete_capture,
    expired or unavailable. purge(reference=None) and expire return counts.
    Corruption raises StoreError and is never erased; callers can display
    unavailable. StoreFull.limit distinguishes session/aggregate overflow.
    Parent owns capture opt-in, scheduling hooks, UI and periodic cleanup.
    """

    def __init__(self, directory: Path, *, fixture_refs=(), synthetic=False,
                 expected_provenance=None, limits=None, max_total_bytes=100 * 1024 * 1024, now=None):
        if synthetic is not True:
            raise PermissionError("explicit synthetic recording storage opt-in required")
        if type(max_total_bytes) is not int or max_total_bytes <= 0:
            raise ValueError("invalid aggregate recording limit")
        self.limits = limits or Limits()
        self.max_total_bytes = max_total_bytes
        self._refs = frozenset(fixture_refs)
        self._expected = expected_provenance
        # Reuse the public schema validator for trusted configuration too.
        probe = Recording(expected_provenance or {
            "source_revision": "0" * 40, **{key: "0" * 64 for key in
            ("dependencies", "policy", "prompt", "schema", "fixtures")}},
            fixture_refs=self._refs, synthetic=True, limits=self.limits)
        del probe
        self._local_limits = replace(self.limits, max_import_bytes=self.limits.max_record_bytes)
        self._identity = None
        try:
            path = Path(directory).absolute()
            self.directory = path.parent.resolve() / path.name
            try:
                self.directory.mkdir(mode=0o700)
            except FileExistsError:
                pass
            else:
                fd = os.open(self.directory.parent, os.O_RDONLY | os.O_DIRECTORY)
                try:
                    os.fsync(fd)
                finally:
                    os.close(fd)
            with _LOCKS_GUARD:
                self._mutex = _LOCKS.setdefault(self.directory, threading.RLock())
            with self._guard() as fd:
                # Restoration and the caller's first sweep must share a clock.
                self._scan(fd, _now(now))
        except OSError:
            raise StoreError("recording storage unavailable") from None

    @staticmethod
    def _private_file(fd):
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1):
            raise StoreError("unsafe recording storage; unavailable") from None
        return info

    @contextmanager
    def _guard(self):
        with self._mutex:
            try:
                fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
                try:
                    info = os.fstat(fd)
                    identity = (info.st_dev, info.st_ino)
                    if (info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o700
                            or self._identity is not None and self._identity != identity):
                        raise StoreError("unsafe recording directory; unavailable") from None
                    self._identity = identity
                    lock = os.open(".recordings.lock", os.O_RDWR | os.O_CREAT
                                   | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600, dir_fd=fd)
                    try:
                        if self._private_file(lock).st_size:
                            raise StoreError("corrupt recording lock; unavailable") from None
                        fcntl.flock(lock, fcntl.LOCK_EX)
                        try:
                            yield fd
                        finally:
                            fcntl.flock(lock, fcntl.LOCK_UN)
                    finally:
                        os.close(lock)
                finally:
                    os.close(fd)
            except OSError:
                raise StoreError("recording storage unavailable") from None

    def _reference(self, reference):
        match = _REFERENCE.fullmatch(reference) if type(reference) is str else None
        if match is None or int(match[2]) > self.limits.max_events:
            raise ValueError("invalid opaque recording reference")
        return f"rec-{match[1]}-{match[3]}.json", int(match[2])

    def _parse_recording(self, payload, now, *, local):
        return import_recording(payload, fixture_refs=self._refs,
            expected_provenance=self._expected, now=now,
            limits=self._local_limits if local else self.limits)

    def _read(self, fd, name, now):
        handle = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK, dir_fd=fd)
        with os.fdopen(handle, "rb") as stream:
            size = self._private_file(stream.fileno()).st_size
            # The envelope adds a fixed small header outside the session budget.
            maximum = self.limits.max_record_bytes + 1024
            if size > maximum:
                raise StoreError("oversized recording storage; unavailable") from None
            payload = stream.read(maximum + 1)
        try:
            envelope = json.loads(payload.decode("utf-8"), object_pairs_hook=_unique,
                                  parse_constant=_nonfinite)
            if (type(envelope) is not dict or set(envelope) !=
                    {"version", "id", "branch", "expires_at", "recording"}
                    or type(envelope["version"]) is not int or envelope["version"] != 1):
                raise ValueError("invalid envelope fields")
            match = _FILE.fullmatch(name)
            if envelope["id"] != match[1] or envelope["branch"] != match[2]:
                raise ValueError("envelope does not match opaque name")
            if envelope["expires_at"] is None:
                raise ValueError("missing expiry")
            _now(envelope["expires_at"])
            recording = None
            if envelope["recording"] is not None:
                inner = _encode(envelope["recording"])
                if len(inner) > self.limits.max_record_bytes:
                    raise ValueError("session size limit")
                recording = self._parse_recording(inner, now, local=True)
                doc = recording.to_dict()
                if (doc["id"] != envelope["id"] or doc["branch"]["id"] != envelope["branch"]
                        or doc["expires_at"] != envelope["expires_at"]):
                    raise ValueError("recording metadata mismatch")
            return envelope, recording, len(payload)
        except (ValueError, UnicodeError, RecursionError, OverflowError, TypeError):
            raise StoreError("corrupt recording storage; unavailable") from None

    def _scan(self, fd, now):
        entries = {}
        for name in os.listdir(fd):
            if _TEMP.fullmatch(name):
                # A crash left an incomplete private write. Preserve it for
                # deliberate recovery rather than silently erasing evidence.
                raise StoreError("incomplete recording write; recovery required") from None
            if _FILE.fullmatch(name):
                entries[name] = self._read(fd, name, now)
        if sum(entry[2] for entry in entries.values()) > self.max_total_bytes:
            raise StoreFull("aggregate")
        return entries

    def _atomic(self, fd, name, payload):
        temporary = ".recording-tmp-" + uuid4().hex
        handle = os.open(temporary, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW,
                         0o600, dir_fd=fd)
        try:
            with os.fdopen(handle, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(payload)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, name, src_dir_fd=fd, dst_dir_fd=fd)
            temporary = None
            os.fsync(fd)
        finally:
            if temporary is not None:
                os.unlink(temporary, dir_fd=fd)

    def _tombstone(self, fd, name, entries):
        envelope, recording, _size = entries[name]
        if recording is None:
            return 0
        envelope = {**envelope, "recording": None}
        payload = _encode(envelope)
        self._atomic(fd, name, payload)
        entries[name] = envelope, None, len(payload)
        return 1

    def _expire(self, fd, entries, now):
        return sum(self._tombstone(fd, name, entries) for name, (envelope, recording, _) in
                   list(entries.items()) if recording is not None and
                   (envelope["expires_at"] <= now or recording.availability(now=now) == "expired"))

    def save(self, recording: Recording, *, now=None):
        """Persist a private immutable snapshot; this is not an external export.

        Re-saving identical content is idempotent. Changed content requires a
        fresh recording/branch, and tombstoned references cannot be revived.
        """
        if type(recording) is not Recording:
            raise ValueError("a synthetic Recording is required")
        now = _now(now)
        document = recording.to_dict()
        payload = _encode(document)
        if len(payload) > self.limits.max_record_bytes:
            raise StoreFull("session")
        validated = self._parse_recording(payload, now, local=True)
        reference = validated.reference(0 if document["events"] else -1)
        name, _step = self._reference(reference)
        envelope = {"version": 1, "id": document["id"], "branch": document["branch"]["id"],
                    "expires_at": document["expires_at"], "recording": document}
        if validated.availability(now=now) == "expired":
            envelope["recording"] = None
        encoded = _encode(envelope)
        with self._guard() as fd:
            entries = self._scan(fd, now)
            self._expire(fd, entries, now)
            if name in entries:
                if entries[name][0] == envelope and envelope["recording"] is not None:
                    return reference
                raise StoreError("recording reference already stored or expired") from None
            if sum(entry[2] for entry in entries.values()) + len(encoded) > self.max_total_bytes:
                raise StoreFull("aggregate")
            self._atomic(fd, name, encoded)
        return reference

    def import_json(self, payload, *, now=None):
        now = _now(now)
        recording = self._parse_recording(payload, now, local=False)
        return self.save(recording, now=now)

    def _lookup(self, reference, now):
        name, step = self._reference(reference)
        with self._guard() as fd:
            entries = self._scan(fd, now)
            self._expire(fd, entries, now)
            if name not in entries:
                return "unavailable", None
            _envelope, recording, _size = entries[name]
            if recording is None:
                return "expired", None
            if step > len(recording.to_dict()["events"]):
                return "unavailable", None
            return recording.availability(now=now), recording

    def load(self, reference, *, now=None):
        return self._lookup(reference, _now(now))[1]

    def status(self, reference, *, now=None):
        return self._lookup(reference, _now(now))[0]

    def expire(self, *, now=None):
        now = _now(now)
        with self._guard() as fd:
            entries = self._scan(fd, now)
            return self._expire(fd, entries, now)

    def purge(self, reference=None, *, now=None):
        selected = None if reference is None else self._reference(reference)
        with self._guard() as fd:
            entries = self._scan(fd, _now(now))
            if selected is None:
                return sum(self._tombstone(fd, name, entries) for name in entries)
            name, step = selected
            if name not in entries or entries[name][1] is None:
                return 0
            if step > len(entries[name][1].to_dict()["events"]):
                return 0
            return self._tombstone(fd, name, entries)

    def stats(self, *, now=None):
        now = _now(now)
        with self._guard() as fd:
            entries = self._scan(fd, now)
            self._expire(fd, entries, now)
            return {"bytes": sum(entry[2] for entry in entries.values()),
                    "recordings": sum(entry[1] is not None for entry in entries.values()),
                    "expired": sum(entry[1] is None for entry in entries.values()),
                    "max_bytes": self.max_total_bytes}
