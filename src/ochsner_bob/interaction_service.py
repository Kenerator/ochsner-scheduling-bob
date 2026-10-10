"""Thin shared Conversation adapter and private, data-only replay lifecycle.

Capture observes the *actual* SchedulingSession commands and API responses.
The recording's strict core-v1 evidence is replayed by SchedulingSession with
recorded-only fixtures and private memory claims. Semantic projections qualify
core fidelity, not byte-exact transcripts or browser-renderer parity. Compound
discovery retains a labeled projection boundary; private controls become host
fixture bindings, never imported identity/nonce/consent. Gaps stay incomplete.
Reference access grants are memory-only and session-scoped (paired support may
inspect). Restart retains private files, not these grants; it never adopts a file
as authority. Parent owns UI, transport and periodic expiry. No paid calls here.
"""

from copy import deepcopy
from contextlib import contextmanager
from datetime import date, timedelta
from hashlib import sha256
import json
from pathlib import Path
import re
import subprocess
from threading import local
from time import monotonic, perf_counter, time

from .browser_service import BrowserService
from .conversation import Conversation
from .http_mock import ApiError, UnknownOutcome
from .language import LanguageOutcome, _INSTRUCTIONS, _schema
from .recording_store import RecordingStore, StoreError, StoreFull
from .replay import Limits, Recording, Replay, import_recording, make_provenance, _core_projection


_ROOT = Path(__file__).resolve().parents[2]
_SOURCE = ("session.py", "conversation.py", "browser_service.py", "interaction_service.py",
           "replay.py", "recording_store.py", "journal.py", "policy.py", "language.py", "http_mock.py")
_KINDS = {"patient": {"patientId", "firstName", "lastName", "dateOfBirth", "phone", "zipCode", "establishedPatient"},
          "provider": {"providerId", "name", "specialty", "locations", "modalities"},
          "slot": {"slotId", "providerId", "specialty", "location", "startTime", "available"},
          "appointment": {"appointmentId", "patientId", "providerId", "specialty", "location", "startTime", "status"}}
_REF = re.compile(r"BOB-([0-9a-f]{32})/step/([0-9]{1,4})/branch/(original|[0-9a-f]{32})\Z")
_LABEL = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
_FIDELITY = {"core_semantic_parity": False, "core_renderer_parity": False, "representation": "scheduling_core_v1",
    "limitations": ["Compound commands may project into multiple recording steps.",
                    "Fixture references and receipt certainty, not private records or receipt identifiers.",
                    "Server projections are not proof of browser acknowledgement, drafts or focus.",
                    "Full core semantic fidelity is qualified against captured projections on replay."]}


def _json(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode()


def _vendor_catalog():
    result = {}
    for kind, filename in (("patient", "patients"), ("provider", "providers"),
                           ("slot", "slots"), ("appointment", "appointments")):
        values = json.loads((_ROOT / "vendor/reference/data" / (filename + ".json")).read_bytes())
        for index, value in enumerate(values, 1):
            if "daysFromToday" in value:
                value = {**value, "startTime": (date.today() + timedelta(days=value["daysFromToday"])).isoformat()
                         + "T" + value["time"] + ":00-05:00"}
            result[f"{kind}-{index}"] = {"kind": kind, "value": {k: v for k, v in value.items() if k in _KINDS[kind]}}
    return result


def _catalog(value):
    value = deepcopy(_vendor_catalog() if value is None else value)
    if type(value) is not dict or len(value) > 2000 or len(_json(value)) > 1024 * 1024:
        raise ValueError("invalid host fixture catalog")
    for label, item in value.items():
        if (type(label) is not str or not _LABEL.fullmatch(label) or type(item) is not dict
                or set(item) != {"kind", "value"} or type(item["kind"]) is not str
                or item["kind"] not in _KINDS or type(item["value"]) is not dict
                or not item["value"] or set(item["value"]) - _KINDS[item["kind"]]):
            raise ValueError("invalid host fixture binding")
    return value


def build_provenance(fixture_catalog):
    """Fixed local artifacts only; no environment/credentials or arbitrary imports.

    source_revision is HEAD; schema also binds exact working source bytes so dirty
    code is not mislabeled as HEAD-identical. Dependencies hash pinned project
    metadata, not a nonexistent resolved dependency lock. Hashes confer no trust.
    """
    try:
        def git(*arguments):
            return subprocess.run(["git", "--no-optional-locks", "-c", "core.fsmonitor=false", *arguments],
                cwd=_ROOT, capture_output=True, check=True, timeout=3).stdout.strip()
        revision = git("rev-parse", "HEAD").decode("ascii")
        dirty = bool(git("status", "--porcelain", "--untracked-files=normal", "--",
                         "src/ochsner_bob", "policies", "pyproject.toml", "vendor/reference/data"))
        code = b"\0".join(name.encode() + b"\0" + (_ROOT / "src/ochsner_bob" / name).read_bytes() for name in _SOURCE)
        # Canonicalize schema array ordering (enum/required are unordered sets).
        def canonical(value):
            if type(value) is dict:
                return {k: canonical(v) for k, v in value.items()}
            if type(value) is list:
                items = [canonical(v) for v in value]
                return sorted(items, key=lambda v: _json(v))
            return value
        provenance = make_provenance(revision,
            dependencies=(_ROOT / "pyproject.toml").read_bytes(),
            policy=(_ROOT / "policies/bob.json").read_bytes(), prompt=_INSTRUCTIONS.encode(),
            schema=code + b"\0" + _json(canonical(_schema())), fixtures=_json(fixture_catalog))
        return provenance, {"override": False, "working_tree_dirty": dirty,
                            "code_digest": sha256(code).hexdigest(), "dependency_basis": "pinned_project_metadata"}
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError):
        raise RuntimeError("Recording provenance unavailable; capture disabled.") from None


class _ObservedAPI:
    """Live port is reachable only by the real session, never by Replay."""
    def __init__(self, delegate, observer):
        self._delegate, self._observer = delegate, observer

    def __getattr__(self, name):
        method = getattr(self._delegate, name)
        if name not in {"providers", "search_patients", "availability", "appointments", "book", "handoff"}:
            return method

        def call(*args, **kwargs):
            start = perf_counter()
            try:
                result = method(*args, **kwargs)
            except Exception as error:
                self._observer(name, None, error, (perf_counter() - start) * 1000)
                raise
            self._observer(name, result, None, (perf_counter() - start) * 1000)
            return result
        return call


class _ObservedLanguage:
    def __init__(self, delegate, observer, guard):
        self._delegate, self._observer = delegate, observer
        self._guard = guard
        self.mode = "openai" if getattr(delegate, "mode", None) == "openai" else "fixture"

    def interpret(self, text, context):
        with self._guard():
            try:
                outcome = self._delegate.interpret(text, context)
            except Exception:
                self._observer(None)
                raise
            self._observer(outcome)
            return outcome


class _SharedConversation(Conversation):
    """Serialize presentation publication, not the potentially slow interpreter."""
    def __init__(self, session, language, lock):
        super().__init__(session, language)
        self._service_lock = lock

    def _decorate(self, view, mode="offline", status="ok"):
        with self._service_lock:
            if not view.get("stale") and view["revision"] != self.session.revision:
                view = self.session.command("begin_input", expected_revision=view["revision"])
                status = "stale"
            return super()._decorate(view, mode, status)


class InteractionService(BrowserService):
    def __init__(self, api_factory, journal_path: Path, *, language=None, fixture_catalog=None,
                 provenance=None, limits=None, max_total_bytes=100 * 1024 * 1024,
                 clock=monotonic, wall_clock=time):
        self._language = language
        self._catalog = _catalog(fixture_catalog)
        self.limits = limits or Limits()
        self.max_total_bytes = max_total_bytes
        self.wall_clock = wall_clock
        self.provenance, self.source = (build_provenance(self._catalog) if provenance is None else
            (deepcopy(provenance), {"override": True, "working_tree_dirty": True, "code_digest": None,
                                    "dependency_basis": "host_override"}))
        Recording(self.provenance, fixture_refs=self._catalog, synthetic=True, limits=self.limits)
        self._contexts, self._records, self._replays = {}, {}, {}
        self._turns = local()
        self._store_instance = None
        self._stored_bytes = 0
        self._retention_status = {"status": "ok", "error": None}
        super().__init__(api_factory, journal_path, clock=clock)
        self.recording_directory = self.journal_path.parent / (self.journal_path.name + ".recordings")
        for session in self.sessions.values():
            self._attach(session)

    def _store(self):
        if self._store_instance is None:
            self._store_instance = RecordingStore(self.recording_directory, synthetic=True,
                fixture_refs=self._catalog, expected_provenance=self.provenance,
                limits=self.limits, max_total_bytes=self.max_total_bytes, now=self.wall_clock())
        return self._store_instance

    def maintain_retention(self):
        """Safe service_actions callback; ordinary failures never stop the host.

        Return categorical status/counts, also exposing status in diagnostics.
        No raw exceptions/logging or external timer. Successful later sweeps
        clear the failure category; the host may separately latch a UI notice.
        """
        with self.lock:
            try:
                result = self._maintain_retention()
            except Exception:
                # This is an observability/retention boundary, not the domain
                # authority path. Do not let an unexpected host/clock failure
                # escape service_actions and terminate serve_forever.
                result = {"status": "unavailable", "expired_recordings": 0,
                          "expired_replays": 0, "expired_captures": 0, "stored_bytes": None}
            result["error"] = None if result["status"] == "ok" else "recording_retention_unavailable"
            self._retention_status = {"status": result["status"], "error": result["error"]}
            return result

    def _maintain_retention(self):
        """Host-scheduled TTL sweep; no capability, journal, budget or API work.

        Call periodically even with no browser traffic. Expired files retain
        only atomic payload-free tombstones. Memory is swept first so corrupt
        storage cannot keep expired replay data alive; unavailable storage is
        reported categorically and preserved for explicit recovery.
        """
        with self.lock:
            now = self.wall_clock()
            result = {"status": "ok", "expired_recordings": 0, "expired_replays": 0,
                      "expired_captures": 0, "stored_bytes": self._stored_bytes}
            for capability, (replay, _key) in list(self._replays.items()):
                if replay.expire(now=now):
                    self._replays.pop(capability)
                    result["expired_replays"] += 1
            for context in self._contexts.values():
                active = context["active"]
                if active is not None and active.availability(now=now) == "expired":
                    if not active.to_dict()["purged"]:
                        result["expired_captures"] += 1
                    active.purge()
                    context["bytes"] = 0
                if context["last"] and now >= context["last"]["expires_at"]:
                    context["last"]["recording"] = "expired"
            for metadata in self._records.values():
                if now >= metadata["report"]["expires_at"]:
                    metadata["report"]["recording"] = "expired"
            try:
                # Reopened services must sweep existing files, but a completely
                # unused service must not silently opt into recording storage.
                if (self._store_instance is not None or self.recording_directory.exists()
                        or self.recording_directory.is_symlink()):
                    store = self._store()
                    result["expired_recordings"] = store.expire(now=now)
                    self._stored_bytes = store.stats(now=now)["bytes"]
                result["stored_bytes"] = self._stored_bytes
            except (StoreError, OSError):
                result.update(status="unavailable", stored_bytes=None)
            return result

    @staticmethod
    def _gap(context, reason):
        if reason not in context["gaps"] and len(context["gaps"]) < 32:
            context["gaps"].append(reason)
        context["dropped"] += 1

    def _observe(self, context, observer, *arguments):
        try:
            observer(context, *arguments)
        except Exception:
            # Observability is never on the authority/result path.
            self._gap(context, "capture_observer_failed")

    def _current_turn(self, context):
        turn = getattr(self._turns, "current", None)
        return turn if turn is not None and turn["context"] is context else None

    @contextmanager
    def _language_wait(self, session, context):
        with self.lock:
            turn = self._current_turn(context)
            if turn is None or context["language_pending"] is not None:
                raise RuntimeError("Language interpretation already pending; local controls remain available.")
            self._resolve(turn["token"], "patient")
            if session.revision != turn["revision"]:
                raise RuntimeError("Language request is stale.")
            context["language_pending"] = turn
        try:
            # In particular, do NOT hold the global/session lock across yield.
            yield
        finally:
            with self.lock:
                if context["language_pending"] is turn:
                    context["language_pending"] = None

    def _observe_language(self, session, context, outcome):
        with self.lock:
            turn = self._current_turn(context)
            if turn is None or not turn["pending"]:
                return
            # Bind evidence to the recording enabled at submission, not a new
            # capture started while the old transport was waiting.
            if context["active"] is None or context["active"] is not turn["capture"]:
                turn["pending"] = False
                return
            if session.revision != turn["revision"]:
                self._gap(context, "stale_language_result")
                turn["pending"] = False
                return
            self._observe(context, self._language_observation, outcome)

    def _attach(self, session):
        if session.id in self._contexts:
            return self._contexts[session.id]
        context = {"active": None, "last": None, "gaps": [], "dropped": 0, "bytes": 0,
                   "observations": None, "language_pending": None, "model": None}
        self._contexts[session.id] = context
        session.api = _ObservedAPI(session.api, lambda *args: self._observe(context, self._api_observation, *args))
        language = None if self._language is None else _ObservedLanguage(self._language,
            lambda outcome: self._observe_language(session, context, outcome),
            lambda: self._language_wait(session, context))
        context["conversation"] = _SharedConversation(session, language, self.lock)
        original = session.command

        def command(action, data=None, *, expected_revision=None, actor="patient"):
            # Model waits run outside the lock. Each actual core command and
            # its API/capture boundary still serialize with local controls.
            with self.lock:
                before = session.view() if context["active"] is not None else None
                context["observations"] = []
                context["identity_matches"] = None
                try:
                    result = original(action, data, expected_revision=expected_revision, actor=actor)
                    turn = self._current_turn(context)
                    if action == "begin_input" and turn is not None and not result.get("stale"):
                        turn["revision"] = result["revision"]
                    if before is not None and not result.get("stale"):
                        try:
                            self._capture_command(session, context, action, data or {}, before, result, actor)
                        except Exception:
                            self._gap(context, "unrepresentable_command")
                    return result
                finally:
                    context["observations"] = None
                    context["identity_matches"] = None
        session.command = command
        return context

    def _binding(self, kind, value):
        matches = [ref for ref, item in self._catalog.items() if item["kind"] == kind and item["value"] == value]
        if len(matches) != 1:
            raise ValueError("unbound fixture outcome")
        return matches[0]

    def _api_observation(self, context, method, value, error, delay):
        if context["active"] is None or context["observations"] is None:
            return
        try:
            refs = []
            if error is not None:
                status = "rejected" if isinstance(error, ApiError) and error.status in {400, 404, 409} else "failed" if isinstance(error, ApiError) else "unknown"
            elif method in {"book", "handoff"}:
                status = "completed"
            elif method == "search_patients":
                # Transient private data remains inside this serialized command.
                # Binding happens after the core applies its exact ZIP filter.
                context["identity_matches"] = deepcopy(value)
                status = "ok" if value else "empty"
            else:
                if type(value) is not list:
                    raise ValueError("unbound fixture outcome")
                kind = {"providers": "provider", "availability": "slot", "appointments": "appointment"}[method]
                refs = [self._binding(kind, item) for item in value]
                status = "ok" if value else "empty"
            if delay > 60000:
                raise ValueError("outcome delay exceeds recording bound")
            context["observations"].append({"method": method, "status": status, "fixture_refs": refs, "delay_ms": delay,
                "error": "none" if error is None else "api" if isinstance(error, ApiError) else
                         "unknown" if isinstance(error, UnknownOutcome) else "unexpected",
                "http_status": error.status if isinstance(error, ApiError) else None})
        except Exception:
            self._gap(context, "unbound_or_oversized_api_outcome")

    def _append(self, context, command, *, outcomes=None, view=None, core=None):
        recording = context["active"]
        if recording is None or recording.availability(now=self.wall_clock()) == "expired":
            return
        try:
            candidate = recording.to_dict()
            candidate["events"].append({"seq": len(candidate["events"]) + 1, "input": command,
                "outcomes": outcomes or {}, "view": view, "clock": self.wall_clock(), "core": core})
            size = len(_json(candidate))
            active_bytes = sum(c["bytes"] for c in self._contexts.values() if c is not context)
            if self._stored_bytes + active_bytes + size > self.max_total_bytes:
                self._gap(context, "aggregate_overflow")
                return
            if not recording.append(command, outcomes=outcomes, view=view, clock=self.wall_clock(), core=core):
                self._gap(context, "capture_overflow")
            context["bytes"] = len(_json(recording.to_dict()))
        except Exception:
            self._gap(context, "unrepresentable_input_or_outcome")

    def _preferences(self, values):
        result = {}
        for key, value in values.items():
            key = {"start_date": "date_from", "end_date": "date_to", "provider_id": "provider_ref"}.get(key, key)
            if key == "provider_ref" and value is not None:
                matches = [ref for ref, item in self._catalog.items() if item["kind"] == "provider" and item["value"].get("providerId") == value]
                if len(matches) != 1:
                    raise ValueError("provider binding unavailable")
                value = matches[0]
            result[key] = value
        return result

    def _capture_command(self, session, context, action, data, before, after, actor):
        recording = context["active"]
        if recording.availability(now=self.wall_clock()) == "expired":
            return
        turn = self._current_turn(context)
        if action == "begin_input" and turn is not None:
            turn["pending"] = True
            turn["core"] = {"version": 1, "action": "begin_input", "data": {}, "actor": actor,
                            "api": None, "view": _core_projection(session, self._catalog)}
            return
        view = {"revision": after["revision"], "renderer": "core-v1", "visible": [after["state"]],
                "enabled": [], "validation": "", "loading": False}
        outcomes = {}
        core_data = {}
        policy = session.last_policy
        if policy:
            rule = policy.get("rule")
            if type(rule) is str and _LABEL.fullmatch(rule):
                outcomes["policy"] = {"decision": "allow" if policy.get("allow") is True else "deny",
                                      "reason": rule, "rule_ids": [rule]}
            else:
                self._gap(context, "unrepresentable_policy")
        if action == "identity":
            controls = session._identity_input
            candidates = [ref for ref, item in self._catalog.items() if item["kind"] == "patient"
                          and item["value"].get("phone") == controls.get("phone")
                          and item["value"].get("dateOfBirth") == controls.get("dob")
                          and (not controls.get("zip") or item["value"].get("zipCode") == controls["zip"])]
            if not candidates:
                self._gap(context, "identity_binding_unavailable")
                return
            ref = self._binding("patient", session.identity) if session.identity else sorted(candidates)[0]
            fixture = self._catalog[ref]["value"]
            if (controls.get("phone") != fixture.get("phone") or controls.get("dob") != fixture.get("dateOfBirth")
                    or controls.get("zip") and controls["zip"] != fixture.get("zipCode")):
                raise ValueError("private controls lack fixture binding")
            command = {"action": "identity_fixture", "data": {"fixture_ref": ref}}
            core_data = {"fixture_ref": ref, "zip_mode": "fixture" if controls.get("zip") else "omit"}
            if context["identity_matches"] is not None:
                matches = context["identity_matches"]
                if controls.get("zip"):
                    matches = [item for item in matches if item["zipCode"] == controls["zip"]]
                observation = context["observations"][0]
                observation["fixture_refs"] = [self._binding("patient", item) for item in matches]
                observation["status"] = "ok" if matches else "empty"
        elif action in {"preferences", "discover"}:
            preferences = self._preferences(data)
            core_data = deepcopy(preferences)
            if action == "discover" and preferences:
                self._append(context, {"action": "preferences", "data": preferences}, view=view)
            command = {"action": action, "data": preferences if action == "preferences" else {}}
        elif action == "select":
            command = {"action": action, "data": {"index": data.get("index")}}
            core_data = deepcopy(command["data"])
        elif action in {"availability", "appointments", "confirm", "handoff", "help", "medical", "unsupported", "decline", "reset", "takeover", "return", "invalid", "begin_input"}:
            command = {"action": action, "data": {}}
            if action == "confirm":
                proposal = before.get("proposal")
                core_data = {"current": bool(proposal and set(data) == {"proposal_id", "nonce"}
                    and data.get("proposal_id") == proposal["id"] and data.get("nonce") == proposal["nonce"]
                    and proposal["revision"] == before["revision"])}
            elif action == "handoff":
                core_data = {"reason": data.get("reason", "user_requested")}
                if set(data) - {"reason"}:
                    raise ValueError("unsupported handoff data")
            elif data:
                raise ValueError("unsupported command fields")
        else:
            self._gap(context, "unsupported_core_command")
            return
        observation = None
        if action in {"identity", "discover", "availability", "appointments", "confirm", "handoff"}:
            if len(context["observations"]) == 1:
                observation = context["observations"][0]
                if action != "identity":
                    outcomes["api"] = {key: observation[key] for key in ("status", "fixture_refs", "delay_ms")}
            elif context["observations"]:
                self._gap(context, "unexpected_api_observation_count")
        core = {"version": 1, "action": command["action"], "data": core_data, "actor": actor,
                "api": observation, "view": _core_projection(session, self._catalog)}
        if turn is not None and turn.get("model_step") is not None:
            core["model_step"] = turn["model_step"]
        self._append(context, command, outcomes=outcomes, view=view, core=core)

    def _language_observation(self, context, outcome):
        pending = self._current_turn(context)
        if pending is None or not pending["pending"]:
            return
        category, preferences = "unavailable", {}
        if isinstance(outcome, LanguageOutcome):
            if outcome.status == "ok" and Conversation._proposal(outcome):
                category = "clarify" if outcome.action == "clarify" else "accepted"
                preferences = self._preferences(outcome.preferences)
            elif type(outcome.status) is str:
                category = {"clarification": "clarify", "timeout": "timeout", "disabled": "unavailable",
                            "unavailable": "unavailable"}.get(outcome.status, "invalid")
        context["model"] = {"category": category, "preferences": deepcopy(preferences)}
        self._append(context, {"action": "language", "data": {"text": pending["value"]}},
                     outcomes={"model": context["model"]}, core=pending.get("core"))
        pending["model_step"] = len(context["active"].to_dict()["events"])
        pending["pending"] = False

    def _summary(self, session):
        context = self._attach(session)
        recording = context["active"]
        if recording is not None:
            expired = recording.expire(now=self.wall_clock())
            return {"recording": "expired" if expired or recording.availability(now=self.wall_clock()) == "expired" else "capturing",
                    "reference": recording.reference(0 if recording.to_dict()["events"] else -1),
                    "missing": list(context["gaps"]), "dropped": context["dropped"], "stored": False}
        if context["last"]:
            report = deepcopy(context["last"])
            if self.wall_clock() >= report["expires_at"]:
                report["recording"] = "expired"
            return report
        return {"recording": "off", "reference": session.view()["reference"], "missing": [], "dropped": 0, "stored": False}

    def read(self, token):
        with self.lock:
            session, role = self._resolve(token)
            context = self._attach(session)
            view = super().read(token)
            target = view["patient"] if role == "support" else view
            presentation = context["conversation"].view()
            # Conversation notices are categorical local presentation, never
            # raw typed text or model prose. Preserve them until revision change.
            target["message"] = presentation["message"]
            target["interpretation"] = presentation["interpretation"]
            target["browser_mode"] = "live"
            target["submission_pending"] = context["language_pending"] is not None
            summary = self._summary(session)
            target["recording"], target["recording_reference"] = summary["recording"], summary["reference"]
            if role == "patient":
                # Base read publishes too early for subclass fields. Ack must
                # copy the completed patient response, never a support poll.
                self.delivered[session.id] = deepcopy(view)
            return view

    def command(self, token, action, data, revision):
        with self.lock:
            view = super().command(token, action, data, revision)
            session, role = self._resolve(token)
            if role == "patient":
                # The base command may add a stale warning after calling read.
                self.delivered[session.id] = deepcopy(view)
            return view

    def text(self, token, text, revision):
        with self.lock:
            session, _ = self._resolve(token, "patient")
            context = self._attach(session)
            self._expire_lease(session)
            turn = {"context": context, "capture": context["active"], "token": token,
                    "value": text, "pending": False, "revision": None}
        previous = getattr(self._turns, "current", None)
        self._turns.current = turn
        try:
            result = context["conversation"].interpret(text, revision)
            with self.lock:
                if turn["pending"]:
                    status = result["interpretation"]["status"]
                    self._observe_language(session, context, LanguageOutcome(status, "fixture", None, {}))
                view = self.read(token)
                if result["revision"] != view["revision"]:
                    result = session.command("begin_input", expected_revision=result["revision"])
                    result["interpretation"] = {"mode": "offline", "status": "stale"}
                for key in ("message", "interpretation", "stale"):
                    if key in result:
                        view[key] = result[key]
                self.delivered[session.id] = deepcopy(view)
                return view
        finally:
            turn["value"], turn["token"] = None, None
            self._turns.current = previous

    def diagnostics(self, token):
        with self.lock:
            session, _ = self._resolve(token)
            context = self._attach(session)
            return {**self._summary(session), "events": session.trace(), "provenance": deepcopy(self.provenance),
                    "source": deepcopy(self.source), "fidelity": deepcopy(_FIDELITY), "model": deepcopy(context["model"]),
                    "trace_dropped": session.dropped_events, "simulation_only": False,
                    "retention": deepcopy(self._retention_status),
                    "browser_mode": "live", "submission_pending": context["language_pending"] is not None}

    def capture(self, token, enabled, synthetic=True):
        if type(enabled) is not bool:
            raise ValueError("recording toggle must be boolean")
        with self.lock:
            session, _ = self._resolve(token, "patient")
            context = self._attach(session)
            if enabled:
                if synthetic is not True:
                    raise PermissionError("Explicit synthetic recording opt-in is required.")
                if context["active"] is not None:
                    return self._summary(session)
                self._stored_bytes = self._store().stats(now=self.wall_clock())["bytes"]
                context.update(active=Recording(self.provenance, fixture_refs=self._catalog,
                    synthetic=True, now=self.wall_clock(), limits=self.limits), gaps=[], dropped=0)
                context["bytes"] = len(_json(context["active"].to_dict()))
                if session.revision or session.view()["booking_blocked"] or session.view()["handoff_blocked"]:
                    self._gap(context, "capture_started_after_initial_state")
                if not self.source["override"] and session.policy._digest != self.provenance["policy"]:
                    self._gap(context, "loaded_policy_drift")
                return self._summary(session)
            recording = context["active"]
            if recording is None:
                return self._summary(session)
            waiting = context["language_pending"]
            if waiting is not None and waiting["capture"] is recording:
                self._gap(context, "language_pending_at_capture_stop")
            if not context["gaps"]:
                recording.seal()
            document = recording.to_dict()
            reference = recording.reference(0 if document["events"] else -1)
            report = {"reference": reference, "recording": recording.availability(now=self.wall_clock()),
                "missing": list(context["gaps"]) + recording.missing, "dropped": context["dropped"] + document["dropped"],
                "stored": False, "expires_at": document["expires_at"], "fidelity": deepcopy(_FIDELITY)}
            if report["recording"] != "expired":
                self._qualify_report(Replay(recording, expected_provenance=self.provenance,
                    now=self.wall_clock(), fixture_catalog=self._catalog), report)
            try:
                self._store().save(recording, now=self.wall_clock())
                report["stored"] = True
                self._stored_bytes = self._store().stats(now=self.wall_clock())["bytes"]
            except Exception as error:
                report["recording"] = "incomplete_capture"
                report["missing"].append(error.limit + "_overflow" if isinstance(error, StoreFull) else "storage_unavailable")
            self._records[self._reference_key(reference)] = {"sid": session.id, "report": deepcopy(report)}
            context.update(active=None, bytes=0, last=report)
            return deepcopy(report)

    @staticmethod
    def _reference_key(reference):
        match = _REF.fullmatch(reference) if type(reference) is str else None
        if match is None:
            raise ValueError("invalid opaque recording reference")
        return match[1], match[3]

    def _authorized(self, session, reference):
        key = self._reference_key(reference)
        metadata = self._records.get(key)
        if metadata is None or metadata["sid"] != session.id:
            raise PermissionError("Recording reference is not granted to this local session.")
        return key, metadata

    @staticmethod
    def _qualify_report(replay, report):
        report["missing"] = list(dict.fromkeys(report["missing"] + replay.missing))
        report["fidelity"] = replay.fidelity
        if report["missing"] and report["recording"] != "expired":
            report["recording"] = "incomplete_capture"
            report["fidelity"]["core_semantic_parity"] = False

    def _replay_response(self, replay, metadata, **extra):
        self._qualify_report(replay, metadata["report"])
        return {"simulation_only": True, "index": replay.index, "reference": replay.reference(),
                "browser_mode": "replay", "submission_pending": False,
                "state": replay.state(), "recording": metadata["report"]["recording"],
                "event_count": len(replay.recording.to_dict()["events"]), "missing": metadata["report"]["missing"],
                "fidelity": deepcopy(metadata["report"]["fidelity"]), "compatibility": replay.recording.compatibility,
                "bookmarks": replay.bookmarks, **extra}

    def _import_replay(self, session, digest, payload, now):
        # This explicit import opts into synthetic data only, not fixture or
        # capability authority. Reject before even creating the private store.
        if type(payload) is not str:
            raise ValueError("recording payload must be JSON text")
        try:
            size = len(payload.encode("utf-8"))
        except UnicodeError:
            raise ValueError("invalid JSON encoding") from None
        if size > min(self.limits.max_import_bytes, 1024 * 1024):
            raise ValueError("import size limit")
        recording = import_recording(payload, fixture_refs=self._catalog,
            expected_provenance=self.provenance, now=now, limits=self.limits)
        document = recording.to_dict()
        reference = recording.reference(0 if document["events"] else -1)
        key = self._reference_key(reference)
        previous = self._records.get(key)
        if previous is not None and previous["sid"] != session.id:
            raise PermissionError("Recording reference is not granted to this local session.")
        status = recording.availability(now=now)
        missing = recording.missing
        if not document["complete"]:
            missing.append("capture_incomplete")
        if document["dropped"]:
            missing.append("capture_dropped")
        report = {"reference": reference, "recording": status, "missing": missing,
            "dropped": document["dropped"], "stored": True, "expires_at": document["expires_at"],
            "fidelity": deepcopy(_FIDELITY)}
        # Keep richer local capture gap explanations on an idempotent re-import.
        if previous is not None:
            report = {**deepcopy(previous["report"]), "stored": True, "recording": status}
        self._store().save(recording, now=now)
        self._stored_bytes = self._store().stats(now=now)["bytes"]
        metadata = {"sid": session.id, "report": report}
        self._records[key] = metadata
        if status == "expired":
            current = self._replays.pop(digest, None)
            if current:
                current[0].purge()
            return {"simulation_only": True, "imported": True, "recording": status,
                "reference": reference, "index": -1, "browser_mode": "replay",
                "submission_pending": False, "fidelity": deepcopy(_FIDELITY),
                "compatibility": recording.compatibility}
        replay = Replay(recording, expected_provenance=self.provenance, now=now, fixture_catalog=self._catalog)
        self._replays[digest] = replay, key
        return self._replay_response(replay, metadata, imported=True)

    def replay(self, token, operation, data):
        """Pure controls; no live domain/model/API calls or executable output.

        Simulation commands run only in the isolated SchedulingSession, with
        a fixed recorded port and private in-memory journal.

        open/compare/purge: reference; inspect/jump/beforeafter: index;
        fork: index, changes; bookmark/go_bookmark: name; promote: reviewed,
        optional through. import: payload (JSON text, at most 1 MiB);
        export: reviewed (literal True), current stored snapshot as JSON text.
        Exports above the import bound report reimportable=False, never truncate.
        step/previous/play/pause/tick/close: empty data.
        """
        fields = {"open": ({"reference"}, set()), "compare": ({"reference"}, set()),
            "purge": ({"reference"}, set()), "inspect": (set(), {"index"}),
            "jump": ({"index"}, set()), "beforeafter": ({"index"}, set()),
            "before_after": ({"index"}, set()), "fork": ({"index", "changes"}, set()),
            "bookmark": ({"name"}, set()), "go_bookmark": ({"name"}, set()),
            "promote": ({"reviewed"}, {"through"}), "promote-reviewed": ({"reviewed"}, {"through"}),
            "import": ({"payload"}, set()), "export": ({"reviewed"}, set()),
            **{name: (set(), set()) for name in ("step", "previous", "play", "pause", "tick", "close")}}
        if (type(operation) is not str or operation not in fields or type(data) is not dict
                or not fields[operation][0] <= data.keys() or data.keys() - set.union(*fields[operation])):
            raise ValueError("invalid replay operation fields")
        with self.lock:
            session, _ = self._resolve(token)
            digest = self._digest(token)
            now = self.wall_clock()
            if operation == "import":
                return self._import_replay(session, digest, data["payload"], now)
            selected = self._authorized(session, data["reference"]) if "reference" in data else None
            if operation == "close":
                current = self._replays.pop(digest, None)
                if current:
                    current[0].purge()
                return {"simulation_only": True, "recording": "closed"}
            if operation in {"open", "purge"}:
                key, metadata = selected
                if operation == "purge":
                    self._store().purge(data["reference"], now=now)
                    metadata["report"]["recording"] = "expired"
                    context = self._contexts.get(session.id)
                    if context and context["last"] and self._reference_key(context["last"]["reference"]) == key:
                        context["last"]["recording"] = "expired"
                    for capability, (replay, owned_key) in list(self._replays.items()):
                        if owned_key == key:
                            replay.purge()
                            self._replays.pop(capability)
                    self._stored_bytes = self._store().stats(now=now)["bytes"]
                try:
                    status = self._store().status(data["reference"], now=now)
                    recording = self._store().load(data["reference"], now=now)
                except StoreError:
                    status, recording = "unavailable", None
                if recording is None:
                    previous = self._replays.pop(digest, None)
                    if previous:
                        previous[0].purge()
                    return {"simulation_only": True, "recording": status, "reference": data["reference"], "index": -1}
                replay = Replay(recording, expected_provenance=self.provenance, now=now, fixture_catalog=self._catalog)
                self._replays[digest] = replay, key
                metadata["report"]["recording"] = status
                return self._replay_response(replay, metadata)
            current = self._replays.get(digest)
            if current is None:
                raise ValueError("Open an authorized recording first.")
            replay, key = current
            metadata = self._records[key]
            if operation == "export" and data["reviewed"] is not True:
                raise PermissionError("exact recording export requires explicit review")
            try:
                status = self._store().status(replay.reference(), now=now)
            except StoreError:
                status = "unavailable"
            if status in {"expired", "unavailable"} or replay.expire(now=now):
                replay.purge()
                self._replays.pop(digest)
                return {"simulation_only": True, "recording": status, "reference": replay.reference(), "index": -1}
            extra = {}
            if operation == "export":
                # Never export the cached replay if its private persisted copy
                # has expired, disappeared, or become corrupt since opening.
                try:
                    recording = self._store().load(replay.reference(), now=now)
                except StoreError:
                    recording = None
                if recording is None:
                    replay.purge()
                    self._replays.pop(digest)
                    return {"simulation_only": True, "recording": "unavailable",
                            "reference": replay.reference(), "index": -1}
                payload = recording.export_json(reviewed=data["reviewed"])
                size = len(payload.encode("utf-8"))
                limit = min(self.limits.max_import_bytes, 1024 * 1024)
                extra.update(payload=payload, export_bytes=size, import_limit_bytes=limit,
                             reimportable=size <= limit)
            elif operation in {"step", "previous", "play", "pause", "tick"}:
                getattr(replay, operation)()
            elif operation == "jump":
                replay.jump(data["index"])
            elif operation == "inspect":
                extra["event"] = replay.inspect(data.get("index", max(0, replay.index)))
            elif operation in {"beforeafter", "before_after"}:
                extra["inspection"] = replay.before_after(data["index"])
            elif operation in {"bookmark", "go_bookmark"}:
                getattr(replay, operation)(data["name"])
            elif operation == "fork":
                replay = replay.fork(data["index"], data["changes"])
                reference = self._store().save(replay.recording, now=now)
                key = self._reference_key(reference)
                metadata = {"sid": session.id, "report": {**deepcopy(metadata["report"]), "reference": reference}}
                self._records[key] = metadata
                self._replays[digest] = replay, key
            elif operation == "compare":
                other = self._store().load(data["reference"], now=now)
                if other is None:
                    raise ValueError("Comparison recording expired or unavailable.")
                extra["comparison"] = replay.compare(Replay(other, expected_provenance=self.provenance, now=now,
                                                            fixture_catalog=self._catalog))
            elif operation in {"promote", "promote-reviewed"}:
                extra["proposal"] = replay.regression_proposal(reviewed=data["reviewed"], through=data.get("through"))
            return self._replay_response(replay, metadata, **extra)
