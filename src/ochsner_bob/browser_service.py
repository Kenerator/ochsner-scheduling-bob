"""One local authority for all notebook kernels. References are not capabilities."""
from copy import deepcopy
from contextlib import contextmanager
from datetime import date
import fcntl
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
from secrets import token_urlsafe
import tempfile
from threading import RLock
from time import monotonic, time

from .journal import EffectJournal
from .session import LOCATIONS, SPECIALTIES, SchedulingSession


class BrowserService:
    def __init__(self, api_factory, journal_path: Path, *, clock=monotonic):
        self.factory = api_factory
        self.journal_path = EffectJournal(journal_path).path
        self.clock = clock
        self.lock = RLock()
        self.sessions = {}
        self.tokens = {}
        self.grants = {}
        self.leases = {}
        self.suggestions = {}
        self.observed = {}
        self.delivered = {}
        self._blocked = False
        self._seen = False
        self._registry_digest = None
        self.registry = self.journal_path.with_name(self.journal_path.name + ".capabilities.json")
        self._registry_lock = self.registry.with_name(self.registry.name + ".lock")
        self._restore()

    @staticmethod
    def _digest(token):
        return sha256(token.encode()).hexdigest()

    @contextmanager
    def _storage(self):
        """A durable marker distinguishes first use from lost capability state."""
        if self._blocked:
            raise RuntimeError("Capability storage unavailable; effects blocked.")
        fd = None
        try:
            info = self.registry.parent.stat()
            if info.st_uid != os.getuid() or info.st_mode & 0o077:
                raise ValueError("private directory required")
            fd = os.open(self._registry_lock, os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_NONBLOCK, 0o600)
            EffectJournal._private_file(fd)
            fcntl.flock(fd, fcntl.LOCK_EX)
            marker = os.read(fd, 2)
            if marker not in (b"", b"1") or (self._seen and marker != b"1"):
                raise ValueError("invalid initialization marker")
            self._seen = self._seen or marker == b"1"
            yield fd
        except Exception:
            # Storage failure latches closed, even if atomic replacement already
            # happened but its directory fsync failed. Never expose OS details.
            self._blocked = True
            raise RuntimeError("Capability storage unavailable; effects blocked.") from None
        finally:
            if fd is not None:
                os.close(fd)

    def _read_registry(self):
        try:
            fd = os.open(self.registry, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            if self._seen or self.journal_path.exists():
                raise ValueError("missing registry") from None
            return None
        try:
            EffectJournal._private_file(fd)
            info = os.fstat(fd)
            raw = os.read(fd, 100001)
            if info.st_size > 100000 or len(raw) > 100000:
                raise ValueError("registry too large")
            return raw
        finally:
            os.close(fd)

    @staticmethod
    def _bindings(raw):
        def pairs(items):
            result = {}
            for key, value in items:
                if key in result:
                    raise ValueError("duplicate registry field")
                result[key] = value
            return result

        def reject(_):
            raise ValueError("invalid registry constant")

        data = json.loads(raw, object_pairs_hook=pairs, parse_constant=reject)
        if (type(data) is not dict or set(data) != {"version", "bindings"}
                or type(data["version"]) is not int or data["version"] != 1
                or type(data["bindings"]) is not dict or len(data["bindings"]) > 256):
            raise ValueError("invalid registry schema")
        now = time()
        sessions = set()
        for digest, entry in data["bindings"].items():
            if (not re.fullmatch(r"[0-9a-f]{64}", digest) or type(entry) is not list or len(entry) != 3
                    or type(entry[0]) is not str or not re.fullmatch(r"[0-9a-f]{32}", entry[0])
                    or type(entry[1]) is not str or entry[1] not in {"patient", "support"}
                    or type(entry[2]) not in {int, float} or not math.isfinite(entry[2])
                    or not 0 <= entry[2] <= now):
                raise ValueError("invalid registry binding")
            sessions.add(entry[0])
        if len(sessions) > 64:
            raise ValueError("too many registry sessions")
        return {digest: tuple(entry) for digest, entry in data["bindings"].items()}

    def _check_registry(self):
        raw = self._read_registry()
        digest = sha256(raw).hexdigest() if raw is not None else None
        if digest != self._registry_digest:
            # Another service must not silently overwrite this instance's state.
            raise ValueError("registry changed")

    def _restore(self):
        with self._storage():
            raw = self._read_registry()
            bindings = self._bindings(raw) if raw is not None else {}
            self._registry_digest = sha256(raw).hexdigest() if raw is not None else None
        # Validate the whole file before constructing any API/session objects.
        self.tokens = bindings
        for sid in {entry[0] for entry in self._active_bindings().values()}:
            self.sessions[sid] = SchedulingSession(self.factory(), journal_path=self.journal_path, session_id=sid)
        self._persist(bindings)

    def _persist(self, bindings):
        with self._storage() as marker:
            self._check_registry()
            if not self._seen:
                os.lseek(marker, 0, os.SEEK_SET)
                os.write(marker, b"1")
                os.fsync(marker)
                EffectJournal._sync_directory(self.registry.parent)
                self._seen = True
            self._write_registry(bindings)

    def _write_registry(self, bindings):
        temporary = None
        try:
            raw = json.dumps({"version": 1, "bindings": bindings}, allow_nan=False).encode("utf-8")
            fd, temporary = tempfile.mkstemp(prefix=".capability-", dir=self.registry.parent)
            with os.fdopen(fd, "wb") as stream:
                os.fchmod(stream.fileno(), 0o600)
                stream.write(raw)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.registry)
            temporary = None
            EffectJournal._sync_directory(self.registry.parent)
            self._registry_digest = sha256(raw).hexdigest()
        finally:
            if temporary:
                os.unlink(temporary)

    def _active_bindings(self):
        now = time()
        return {key: value for key, value in self.tokens.items() if 0 <= now - value[2] < 86400}

    def _resolve(self, token, role=None):
        with self.lock:
            with self._storage():
                self._check_registry()
            entry = self.tokens.get(self._digest(token)) if type(token) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", token) else None
            if not entry or not 0 <= time() - entry[2] < 86400 or (role and entry[1] != role):
                raise PermissionError("A current local demo capability is required.")
            return self.sessions[entry[0]], entry[1]

    def create(self):
        with self.lock:
            with self._storage():
                self._check_registry()
            bindings = self._active_bindings()
            active_sessions = {entry[0] for entry in bindings.values()}
            if len(active_sessions) >= 64:
                raise ValueError("Local session limit reached; restart a new demo namespace explicitly.")
            if len(bindings) >= 256:
                raise ValueError("Local capability limit reached.")
            session = SchedulingSession(self.factory(), journal_path=self.journal_path)
            token = token_urlsafe(32)
            bindings[self._digest(token)] = (session.id, "patient", time())
            self._persist(bindings)
            self.tokens = bindings
            self.sessions = {sid: value for sid, value in self.sessions.items() if sid in active_sessions}
            self.sessions[session.id] = session
            for cache in (self.leases, self.suggestions, self.observed, self.delivered):
                for sid in set(cache) - active_sessions:
                    cache.pop(sid)
            return {"token": token, "view": self.read(token)}

    def _expire_lease(self, session):
        if session.takeover and self.clock() >= self.leases.get(session.id, 0):
            session.command("return", expected_revision=session.revision, actor="support")

    def read(self, token):
        with self.lock:
            session, role = self._resolve(token)
            self._expire_lease(session)
            view = session.support_view() if role == "support" else session.view()
            target = view["patient"] if role == "support" else view
            target["support_suggestion"] = deepcopy(self.suggestions.get(session.id))
            if role == "support":
                # Never deliver a usable confirmation nonce to a mirror.
                if target.get("proposal"):
                    target["proposal"].pop("nonce", None)
                view["lease_seconds"] = max(0, round(self.leases.get(session.id, 0) - self.clock()))
                view["observed_patient"] = deepcopy(self.observed.get(session.id))
            else:
                # Receipt snapshots must come from a patient response, never
                # an unseen current state reconstructed during acknowledgement.
                self.delivered[session.id] = deepcopy(view)
            return view

    def pair(self, token):
        with self.lock:
            session, _ = self._resolve(token, "patient")
            self.grants = {key:value for key,value in self.grants.items() if self.clock() < value[1]}
            if len(self.grants) >= 128:
                raise ValueError("Too many outstanding local pairing grants.")
            grant = token_urlsafe(24)
            self.grants[grant] = (session.id, self.clock() + 300, self._digest(token))
            return grant

    def join(self, grant):
        with self.lock:
            with self._storage():
                self._check_registry()
            entry = self.grants.pop(grant, None) if type(grant) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", grant) else None
            if not entry or self.clock() >= entry[1]:
                raise PermissionError("Pairing grant is invalid, expired or already used.")
            bindings = self._active_bindings()
            if entry[2] not in bindings:
                raise PermissionError("Pairing grant is invalid, expired or already used.")
            token = token_urlsafe(32)
            if len(bindings) >= 256:
                raise ValueError("Local capability limit reached.")
            bindings[self._digest(token)] = (entry[0], "support", time())
            self._persist(bindings)
            self.tokens = bindings
            return token

    def command(self, token, action, data, revision):
        with self.lock:
            session, role = self._resolve(token)
            self._expire_lease(session)
            if role == "support":
                if action not in {"takeover", "return", "help", "medical", "unsupported"}:
                    raise PermissionError("Support cannot issue patient transactions.")
                if action == "takeover" and not session.support_view()["fresh"]:
                    raise PermissionError("A fresh patient acknowledgement is required before takeover.")
            elif action in {"takeover", "return"}:
                raise PermissionError("Only paired demo support can change its control lease.")
            result = session.command(action, data, expected_revision=revision, actor=role)
            if action == "takeover" and role == "support" and not result.get("stale"):
                self.leases[session.id] = self.clock() + 300
            view = self.read(token)
            if result.get("stale"):
                view["stale"] = True
                view["message"] = result["message"]
            return view

    def ack(self, token, receipt):
        with self.lock:
            session, _ = self._resolve(token, "patient")
            required = {"revision", "renderer", "visible", "draft", "focus", "scroll", "expanded"}
            if type(receipt) is not dict or set(receipt) not in (required,required|{"presentation"}):
                raise ValueError("Invalid semantic acknowledgement.")
            if "presentation" in receipt:
                presentation=receipt["presentation"]
                if (type(presentation) is not dict or set(presentation) not in ({"notice","pending","dirty"},{"notice","pending","dirty","can_confirm"})
                        or type(presentation["notice"]) is not str or presentation["notice"] not in {
                            "none","domain","working","ready","stale","pairing","grant","invalid","unavailable","ack_unavailable"}
                        or type(presentation["pending"]) is not bool or type(presentation["dirty"]) is not bool
                        or ("can_confirm" in presentation and type(presentation["can_confirm"]) is not bool)):
                    raise ValueError("Invalid categorical presentation acknowledgement.")
            if type(receipt["revision"]) is not int or receipt["renderer"] != "bob-v1":
                raise ValueError("Invalid acknowledgement revision or renderer.")
            for key in ("visible", "expanded"):
                if type(receipt[key]) is not list or len(receipt[key]) > 40 or any(type(v) is not str or len(v) > 128 for v in receipt[key]):
                    raise ValueError("Invalid semantic control identifiers.")
            if type(receipt["draft"]) is not dict or set(receipt["draft"]) - {"message", "specialty", "location", "start_date", "end_date"}:
                raise ValueError("Private identity controls are never mirrored.")
            if any(type(v) is not str or len(v) > 2000 for v in receipt["draft"].values()):
                raise ValueError("Invalid draft values.")
            if receipt["focus"] is not None and (type(receipt["focus"]) is not str or len(receipt["focus"]) > 128):
                raise ValueError("Invalid focus identifier.")
            if type(receipt["scroll"]) is not int or not 0 <= receipt["scroll"] <= 1000000:
                raise ValueError("Invalid scroll acknowledgement.")
            from .language import _private_input
            strings = [value if key not in {"start_date", "end_date"} else "appointment date " + value
                       for key, value in receipt["draft"].items()]
            strings.extend([*receipt["visible"], *receipt["expanded"]])
            if receipt["focus"] is not None:
                strings.append(receipt["focus"])
            proposal = session.view().get("proposal")
            nonce = proposal.get("nonce") if proposal else None
            if any(_private_input(value) or re.search(r"\b[0-9a-f]{32}\b", value)
                   or (nonce and nonce in value) for value in strings):
                raise ValueError("Private values are never mirrored.")
            delivered = self.delivered.get(session.id)
            if not delivered or delivered["revision"] != receipt["revision"]:
                raise ValueError("Only a delivered patient revision can be acknowledged.")
            session.acknowledge(receipt)
            observed = deepcopy(delivered)
            if observed.get("proposal"):
                observed["proposal"].pop("nonce", None)
            self.observed[session.id] = observed
            return {"acknowledged": session.revision}

    def suggest(self, token, preferences, revision):
        with self.lock:
            session, _ = self._resolve(token, "support")
            self._expire_lease(session)
            if not session.takeover or revision != session.revision:
                raise PermissionError("Current demo-support lease and revision required.")
            if type(preferences) is not dict or not preferences or set(preferences) - {"specialty", "location", "start_date", "end_date"}:
                raise ValueError("Suggest only public scheduling preferences.")
            if any(type(v) is not str or len(v) > 64 for v in preferences.values()):
                raise ValueError("Invalid preference suggestion.")
            for key, choices in (("specialty", SPECIALTIES), ("location", LOCATIONS)):
                if key in preferences and preferences[key] not in choices:
                    raise ValueError("Suggest only supported public preferences.")
            merged = {**session.view()["preferences"], **preferences}
            for key in ("start_date", "end_date"):
                if key in preferences:
                    value = preferences[key]
                    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
                        raise ValueError("Suggest only public scheduling dates.")
                    date.fromisoformat(value)
            if merged.get("start_date") and merged.get("end_date") and merged["start_date"] > merged["end_date"]:
                raise ValueError("Scheduling date range is inverted.")
            # A suggestion is not adoption and does not touch domain preferences.
            session.command("begin_input", expected_revision=revision, actor="support")
            self.suggestions[session.id] = {"id": token_urlsafe(16), "preferences": deepcopy(preferences)}
            return self.read(token)

    def accept(self, token, suggestion_id, revision):
        with self.lock:
            session, _ = self._resolve(token, "patient")
            self._expire_lease(session)
            suggestion = self.suggestions.get(session.id)
            if session.takeover or revision != session.revision or not suggestion or suggestion["id"] != suggestion_id:
                raise PermissionError("Review the current suggestion after control returns.")
            self.suggestions.pop(session.id)
            session.command("preferences", suggestion["preferences"], expected_revision=revision)
            return self.read(token)
