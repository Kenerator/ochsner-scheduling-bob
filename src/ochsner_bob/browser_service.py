"""One local authority for all notebook kernels. References are not capabilities."""
from copy import deepcopy
from hashlib import sha256
import json
import math
import os
from pathlib import Path
import re
from secrets import token_urlsafe
import stat
import tempfile
from threading import RLock
from time import monotonic, time

from .session import SchedulingSession


class BrowserService:
    def __init__(self, api_factory, journal_path: Path, *, clock=monotonic):
        self.factory = api_factory
        self.journal_path = journal_path
        self.clock = clock
        self.lock = RLock()
        self.sessions = {}
        self.tokens = {}
        self.grants = {}
        self.leases = {}
        self.suggestions = {}
        self.observed = {}
        # EffectJournal establishes/checks the private directory first.
        from .journal import EffectJournal
        EffectJournal(journal_path)
        self.registry = journal_path.with_name(journal_path.name + ".capabilities.json")
        self._restore()

    @staticmethod
    def _digest(token):
        return sha256(token.encode()).hexdigest()

    def _restore(self):
        try:
            fd = os.open(self.registry, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        except FileNotFoundError:
            if self.journal_path.exists():
                raise RuntimeError("Capability registry missing; start no new effects in this run.") from None
            return
        try:
            info = os.fstat(fd)
            if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or stat.S_IMODE(info.st_mode) != 0o600 or info.st_nlink != 1 or info.st_size > 100000:
                raise ValueError("invalid private registry")
            from .local_transport import _pairs, _reject
            with os.fdopen(fd, "r", encoding="utf-8") as stream:
                fd = None
                data = json.load(stream, object_pairs_hook=_pairs, parse_constant=_reject)
            if type(data) is not dict or set(data) != {"version", "bindings"} or type(data["version"]) is not int or data["version"] != 1 or type(data["bindings"]) is not dict or len(data["bindings"]) > 256:
                raise ValueError("invalid registry schema")
            for digest, entry in data["bindings"].items():
                if (not re.fullmatch(r"[0-9a-f]{64}", digest) or type(entry) is not list or len(entry) != 3
                        or type(entry[0]) is not str or not re.fullmatch(r"[0-9a-f]{32}", entry[0])
                        or entry[1] not in {"patient", "support"} or type(entry[2]) not in {int, float}
                        or not math.isfinite(entry[2])):
                    raise ValueError("invalid registry binding")
                self.tokens[digest] = tuple(entry)
                if entry[0] not in self.sessions:
                    self.sessions[entry[0]] = SchedulingSession(self.factory(), journal_path=self.journal_path, session_id=entry[0])
        except Exception:
            raise RuntimeError("Capability registry corrupt; effects blocked.") from None
        finally:
            if fd is not None:
                os.close(fd)

    def _persist(self):
        temporary = None
        try:
            fd, temporary = tempfile.mkstemp(prefix=".capability-", dir=self.registry.parent)
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump({"version":1,"bindings":self.tokens}, stream, allow_nan=False)
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(temporary, self.registry)
            temporary = None
            from .journal import EffectJournal
            EffectJournal._sync_directory(self.registry.parent)
        finally:
            if temporary:
                os.unlink(temporary)

    def _resolve(self, token, role=None):
        entry = self.tokens.get(self._digest(token)) if type(token) is str and len(token) <= 128 else None
        if not entry or not 0 <= time() - entry[2] <= 86400 or (role and entry[1] != role):
            raise PermissionError("A current local demo capability is required.")
        return self.sessions[entry[0]], entry[1]

    def create(self):
        with self.lock:
            if len(self.sessions) >= 64:
                raise ValueError("Local session limit reached; restart a new demo namespace explicitly.")
            session = SchedulingSession(self.factory(), journal_path=self.journal_path)
            token = token_urlsafe(32)
            self.sessions[session.id] = session
            self.tokens[self._digest(token)] = (session.id, "patient", time())
            self._persist()
            return {"token": token, "view": session.view()}

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
            return view

    def pair(self, token):
        with self.lock:
            session, _ = self._resolve(token, "patient")
            self.grants = {key:value for key,value in self.grants.items() if self.clock() < value[1]}
            if len(self.grants) >= 128:
                raise ValueError("Too many outstanding local pairing grants.")
            grant = token_urlsafe(24)
            self.grants[grant] = (session.id, self.clock() + 300)
            return grant

    def join(self, grant):
        with self.lock:
            entry = self.grants.pop(grant, None) if type(grant) is str else None
            if not entry or self.clock() >= entry[1]:
                raise PermissionError("Pairing grant is invalid, expired or already used.")
            token = token_urlsafe(32)
            if len(self.tokens) >= 256:
                raise ValueError("Local capability limit reached.")
            self.tokens[self._digest(token)] = (entry[0], "support", time())
            self._persist()
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
            if type(receipt) is not dict or set(receipt) != required:
                raise ValueError("Invalid semantic acknowledgement.")
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
            session.acknowledge(receipt)
            observed = session.view()
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
