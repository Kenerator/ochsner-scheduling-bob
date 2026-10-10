"""Bounded synthetic recording and data-only replay; no live ports or journal.

Identity/API objects use host-approved fixture references. Hashes detect drift,
not trust. Import never authorizes live actions. Versioned core evidence drives
the actual SchedulingSession through a fixed recorded-only port and private
memory claims. Old recordings remain historical projections, not parity proof.
Use Replay.inspect for escaped display, not the exact raw export document.
"""

from copy import deepcopy
from dataclasses import dataclass
from datetime import date
from hashlib import sha256
from html import escape
import json
import math
import re
from time import time
from uuid import uuid4
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


_ACTIONS = frozenset({"identity_fixture", "preferences", "discover", "availability",
    "select", "confirm", "appointments", "help", "medical", "unsupported", "decline",
    "reset", "handoff", "language", "tick", "takeover", "return", "invalid", "begin_input"})
_API_ACTIONS = frozenset({"discover", "availability", "appointments", "confirm", "handoff"})
_API_STATUS = frozenset({"ok", "empty", "completed", "rejected", "failed", "unknown"})
_MODEL_STATUS = frozenset({"accepted", "clarify", "invalid", "timeout", "unavailable"})
_PROVENANCE = frozenset({"source_revision", "dependencies", "policy", "prompt", "schema", "fixtures"})
_LABEL = re.compile(r"[A-Za-z][A-Za-z0-9_-]{0,63}\Z")
_HEX = re.compile(r"[0-9a-f]{64}\Z")
_UUID = re.compile(r"[0-9a-f]{32}\Z")
_REFERENCE = re.compile(r"BOB-[0-9a-f]{32}/step/[0-9]{1,4}/branch/(?:original|[0-9a-f]{32})\Z")
_UNSAFE_TEXT = re.compile(
    r"(?i)(?:[a-z][a-z0-9+.-]*://|\b(?:file|javascript|data):|www\.|"
    r"(?:^|\s)(?:/|~[/\\]|\.\.?[/\\]|[a-z]:[/\\])|\\|"
    r"\b[\w.-]+/[\w./-]+|<script\b|\b(?:eval|exec|__import__|compile)\s*\(|"
    r"\bon[a-z]+\s*=|\b[A-Za-z_]\w*\(|\$[({]|```|\b(?:python[0-9.]*|bash|sh|curl|wget)\s+-|"
    r"\b(?:import\s+\w|os\.|subprocess\.|pickle\.)|"
    r"\b(?:phone|dob|zip|ssn|password|bearer|patient[_ -]?id|api[_ -]?key)\b|"
    r"\bdate of birth\b|[\w.+-]+@[\w.-]+|\b\d{5}\b|\+?\d[\d ()-]{6,}\d)"
)


@dataclass(frozen=True)
class Limits:
    max_import_bytes: int = 1024 * 1024
    max_events: int = 2000
    max_depth: int = 12
    max_string: int = 4096
    ttl_seconds: int = 24 * 60 * 60
    max_record_bytes: int = 10 * 1024 * 1024

    def __post_init__(self):
        if any(type(value) is not int or value <= 0 for value in vars(self).values()):
            raise ValueError("invalid replay limits")


def _canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False)


def _digest(document):
    return sha256(_canonical({key: value for key, value in document.items()
                              if key != "digest"}).encode("utf-8")).hexdigest()


def _fields(value, required=(), optional=()):
    if (type(value) is not dict or not set(required) <= value.keys()
            or value.keys() - set(required) - set(optional)):
        raise ValueError("unexpected or missing fields")


def _enum(value, allowed):
    if type(value) is not str or value not in allowed:
        raise ValueError("invalid category")


def _number(value, maximum=1e12):
    if type(value) not in (int, float) or not 0 <= value <= maximum or not math.isfinite(value):
        raise ValueError("invalid bounded number")


def _integer(value, maximum=2000):
    if type(value) is not int or not 0 <= value <= maximum:
        raise ValueError("invalid bounded integer")


def _label(value):
    if type(value) is not str or not _LABEL.fullmatch(value):
        raise ValueError("invalid categorical label")


def _text(value, limits):
    if (type(value) is not str or len(value) > limits.max_string
            or any(ord(char) < 32 and char not in "\n\t" for char in value)
            or _UNSAFE_TEXT.search(value)):
        raise ValueError("unsafe or oversized text")


def _tree(value, limits, depth=0):
    if depth > limits.max_depth:
        raise ValueError("nesting depth limit")
    if type(value) is dict:
        for key, item in value.items():
            if type(key) is not str or len(key) > limits.max_string:
                raise ValueError("invalid fields")
            _tree(item, limits, depth + 1)
    elif type(value) is list:
        if len(value) > max(limits.max_events, 32):
            raise ValueError("event/list count limit")
        for item in value:
            _tree(item, limits, depth + 1)
    elif type(value) is str:
        if len(value) > limits.max_string:
            raise ValueError("string size limit")
        try:
            value.encode("utf-8")
        except UnicodeError:
            raise ValueError("invalid Unicode text") from None
    elif type(value) in (float, int):
        if abs(value) > 2**53 or not math.isfinite(value):
            raise ValueError("nonfinite or oversized number")
    elif value is not None and type(value) is not bool:
        raise ValueError("JSON data only")


def _provenance(value):
    _fields(value, _PROVENANCE)
    revision = value["source_revision"]
    if type(revision) is not str or not re.fullmatch(r"[0-9a-f]{40}|[0-9a-f]{64}", revision):
        raise ValueError("invalid source revision")
    for key in _PROVENANCE - {"source_revision"}:
        if type(value[key]) is not str or not _HEX.fullmatch(value[key]):
            raise ValueError("invalid provenance digest")


def make_provenance(source_revision, *, dependencies, policy, prompt, schema, fixtures):
    """Hash supplied artifact bytes; never discover files, environment or secrets."""
    artifacts = {"dependencies": dependencies, "policy": policy, "prompt": prompt,
                 "schema": schema, "fixtures": fixtures}
    if any(type(value) is not bytes for value in artifacts.values()):
        raise ValueError("provenance artifacts must be bytes")
    result = {"source_revision": source_revision,
              **{key: sha256(value).hexdigest() for key, value in artifacts.items()}}
    _provenance(result)
    return result


def _fixture(value, allowed):
    _label(value)
    if value not in allowed:
        raise ValueError("unapproved fixture reference")


def _preferences(value, allowed):
    _fields(value, optional={"specialty", "location", "date_from", "date_to", "provider_ref"})
    for key, item in value.items():
        if item is None:
            continue
        if key in {"date_from", "date_to"}:
            if type(item) is not str or not re.fullmatch(r"\d{4}-\d{2}-\d{2}", item):
                raise ValueError("invalid preference date")
            try:
                date.fromisoformat(item)
            except ValueError:
                raise ValueError("invalid preference date") from None
        elif key == "provider_ref":
            _fixture(item, allowed)
        else:
            _label(item)


def _command(value, allowed, limits):
    _fields(value, {"action", "data"})
    action, data = value["action"], value["data"]
    _enum(action, _ACTIONS)
    if action == "preferences":
        _preferences(data, allowed)
    elif action == "identity_fixture":
        _fields(data, {"fixture_ref"})
        _fixture(data["fixture_ref"], allowed)
    elif action == "select":
        _fields(data, {"index"})
        _integer(data["index"], limits.max_events)
        if data["index"] == 0:
            raise ValueError("choices are one based")
    elif action == "language":
        _fields(data, {"text"})
        _text(data["text"], limits)
    else:
        _fields(data)


def _outcomes(value, allowed, limits):
    _fields(value, optional={"api", "model", "policy"})
    if "api" in value:
        api = value["api"]
        _fields(api, {"status", "fixture_refs", "delay_ms"})
        _enum(api["status"], _API_STATUS)
        _number(api["delay_ms"], 60000)
        if type(api["fixture_refs"]) is not list:
            raise ValueError("invalid fixture references")
        for item in api["fixture_refs"]:
            _fixture(item, allowed)
    if "model" in value:
        model = value["model"]
        _fields(model, {"category", "preferences"}, {"message"})
        _enum(model["category"], _MODEL_STATUS)
        _preferences(model["preferences"], allowed)
        if "message" in model:
            _text(model["message"], limits)
    if "policy" in value:
        policy = value["policy"]
        _fields(policy, {"decision", "reason", "rule_ids"})
        _enum(policy["decision"], {"allow", "deny", "unknown"})
        _label(policy["reason"])
        if type(policy["rule_ids"]) is not list or len(policy["rule_ids"]) > 32:
            raise ValueError("invalid rule references")
        for rule in policy["rule_ids"]:
            _label(rule)


def _view(value, limits):
    if value is None:
        return
    _fields(value, {"revision", "renderer", "visible", "enabled", "validation", "loading"})
    _integer(value["revision"], 2**31)
    _label(value["renderer"])
    for key in ("visible", "enabled"):
        if type(value[key]) is not list or len(value[key]) > 32:
            raise ValueError("invalid view list")
        for item in value[key]:
            _text(item, limits) if key == "visible" else _enum(item, _ACTIONS)
    _text(value["validation"], limits)
    if type(value["loading"]) is not bool:
        raise ValueError("invalid view loading flag")


def _event(value, seq, allowed, limits):
    _fields(value, {"seq", "input", "outcomes", "view", "clock"}, {"core"})
    _integer(value["seq"], limits.max_events)
    if value["seq"] != seq:
        raise ValueError("events must be contiguous and ordered")
    _number(value["clock"])
    _command(value["input"], allowed, limits)
    _outcomes(value["outcomes"], allowed, limits)
    action = value["input"]["action"]
    if "api" in value["outcomes"]:
        if action not in _API_ACTIONS:
            raise ValueError("unexpected API outcome fields")
        statuses = {"completed", "rejected", "failed", "unknown"} if action in {"confirm", "handoff"} else {"ok", "empty", "rejected", "failed", "unknown"}
        _enum(value["outcomes"]["api"]["status"], statuses)
    if "model" in value["outcomes"] and action != "language":
        raise ValueError("unexpected model outcome fields")
    _view(value["view"], limits)
    if "core" in value and value["core"] is not None:
        core = value["core"]
        _core_evidence(core, allowed, limits)
        expected_action = "begin_input" if action == "language" else action
        if core["action"] != expected_action:
            raise ValueError("inconsistent core command")
        if action in {"preferences", "select"} and core["data"] != value["input"]["data"]:
            raise ValueError("inconsistent core command data")
        if action == "identity_fixture" and core["data"]["fixture_ref"] != value["input"]["data"]["fixture_ref"]:
            raise ValueError("inconsistent identity fixture")
        if action in _API_ACTIONS:
            observation = core["api"]
            legacy = value["outcomes"].get("api")
            if (observation is None) != (legacy is None) or (observation is not None and
                    {key: observation[key] for key in ("status", "fixture_refs", "delay_ms")} != legacy):
                raise ValueError("inconsistent API observation")
    elif "core" in value and action != "preferences":
        raise ValueError("invalid projection-only boundary")


def _core_projection(session, catalog):
    """Semantic observation only: no private IDs, proposal tokens or authority."""
    view = session.view()
    preferences = {}
    for key, value in view["preferences"].items():
        key = {"start_date": "date_from", "end_date": "date_to", "provider_id": "provider_ref"}.get(key, key)
        if key == "provider_ref":
            refs = [ref for ref, item in catalog.items() if item["kind"] == "provider"
                    and item["value"].get("providerId") == value]
            if len(refs) != 1:
                raise ValueError("provider binding unavailable")
            value = refs[0]
        preferences[key] = value
    policy = session.last_policy
    return {"revision": view["revision"], "state": view["state"],
            "identity_status": view["identity_status"], "preferences": preferences,
            "provider_count": len(view["providers"]), "slot_count": len(view["slots"]),
            "appointment_count": len(view["appointments"]), "proposal": bool(view["proposal"]),
            "certainty": (view["current_result"] or {}).get("status", "not_attempted"),
            "history": [{"kind": item["kind"], "status": item["status"]} for item in view["history"]],
            "booking_blocked": view["booking_blocked"], "handoff_blocked": view["handoff_blocked"],
            "takeover": view["takeover"],
            "policy": None if policy is None else {"decision": "allow" if policy.get("allow") is True else "deny",
                                                   "rule": policy["rule"]}}


def _semantic_view(value, allowed, limits):
    _fields(value, {"revision", "state", "identity_status", "preferences", "provider_count", "slot_count",
                    "appointment_count", "proposal", "certainty", "history", "booking_blocked",
                    "handoff_blocked", "takeover", "policy"})
    _integer(value["revision"], 2**31)
    _enum(value["state"], {"start", "identity_required", "ready", "ambiguous", "preferences", "providers",
        "options", "proposal", "appointments", "help", "medical", "unsupported", "declined", "outage",
        "rejected", "unknown", "error", "completed", "queued", "failed"})
    _enum(value["identity_status"], {"missing", "verified", "ambiguous"})
    _preferences(value["preferences"], allowed)
    for key in ("provider_count", "slot_count", "appointment_count"):
        _integer(value[key], limits.max_events)
    for key in ("proposal", "booking_blocked", "handoff_blocked", "takeover"):
        if type(value[key]) is not bool:
            raise ValueError("invalid semantic boolean")
    _enum(value["certainty"], {"not_attempted", "attempted", "completed", "queued", "rejected", "failed", "unknown"})
    if type(value["history"]) is not list:
        raise ValueError("invalid semantic history")
    for item in value["history"]:
        _fields(item, {"kind", "status"})
        _enum(item["kind"], {"booking", "handoff"})
        _enum(item["status"], {"completed", "queued", "rejected", "failed", "unknown"})
    if value["policy"] is not None:
        _fields(value["policy"], {"decision", "rule"})
        _enum(value["policy"]["decision"], {"allow", "deny"})
        _label(value["policy"]["rule"])


def _core_evidence(value, allowed, limits):
    _fields(value, {"version", "action", "data", "actor", "api", "view"}, {"model_step"})
    if "model_step" in value:
        _integer(value["model_step"], limits.max_events)
        if value["model_step"] == 0:
            raise ValueError("invalid model cause")
    if type(value["version"]) is not int or value["version"] != 1:
        raise ValueError("unsupported core evidence version")
    action, data = value["action"], value["data"]
    _enum(action, _ACTIONS - {"language", "tick"})
    _enum(value["actor"], {"patient", "support"})
    if action == "identity_fixture":
        _fields(data, {"fixture_ref", "zip_mode"})
        _fixture(data["fixture_ref"], allowed)
        _enum(data["zip_mode"], {"fixture", "omit"})
    elif action in {"preferences", "discover"}:
        _preferences(data, allowed)
    elif action == "confirm":
        _fields(data, {"current"})
        if type(data["current"]) is not bool:
            raise ValueError("invalid confirmation observation")
    elif action == "handoff":
        _fields(data, {"reason"})
        _enum(data["reason"], {"user_requested", "identity_unclear", "unsupported_request", "medical_advice",
                              "api_failure", "no_availability", "other"})
    else:
        _command({"action": action, "data": data}, allowed, limits)
    api = value["api"]
    if api is not None:
        _fields(api, {"method", "status", "fixture_refs", "delay_ms", "error", "http_status"})
        _enum(api["method"], {"search_patients", "providers", "availability", "appointments", "book", "handoff"})
        _enum(api["status"], _API_STATUS)
        _enum(api["error"], {"none", "api", "unknown", "unexpected"})
        if api["http_status"] is not None:
            if type(api["http_status"]) is not int or not 400 <= api["http_status"] <= 599 or api["error"] != "api":
                raise ValueError("invalid recorded HTTP failure")
        _number(api["delay_ms"], 60000)
        if type(api["fixture_refs"]) is not list:
            raise ValueError("invalid fixture references")
        for ref in api["fixture_refs"]:
            _fixture(ref, allowed)
        expected = {"identity_fixture": "search_patients", "discover": "providers", "availability": "availability",
                    "appointments": "appointments", "confirm": "book", "handoff": "handoff"}
        if expected.get(action) != api["method"]:
            raise ValueError("unexpected core API observation")
    _semantic_view(value["view"], allowed, limits)


def _changes(value, allowed, limits):
    _fields(value, optional={"preferences", "identity_fixture", "clock", "model_category",
                            "api_status", "api_delay_ms", "order"})
    if "preferences" in value:
        _preferences(value["preferences"], allowed)
    if "identity_fixture" in value:
        _fixture(value["identity_fixture"], allowed)
    if "clock" in value:
        _number(value["clock"])
    if "model_category" in value:
        _enum(value["model_category"], _MODEL_STATUS)
    if "api_status" in value:
        _enum(value["api_status"], _API_STATUS)
    if "api_delay_ms" in value:
        _number(value["api_delay_ms"], 60000)
    if "order" in value:
        order = value["order"]
        if (type(order) is not list or len(order) > limits.max_events
                or any(type(index) is not int for index in order)
                or sorted(order) != list(range(len(order)))):
            raise ValueError("invalid event ordering")


def _validate(document, allowed, limits):
    _tree(document, limits)
    _fields(document, {"version", "id", "created_at", "expires_at", "timezone", "provenance",
                       "fixture_refs", "events", "complete", "dropped", "purged", "branch", "digest"})
    if type(document["version"]) is not int or document["version"] != 1:
        raise ValueError("unsupported recording version")
    if type(document["id"]) is not str or not _UUID.fullmatch(document["id"]):
        raise ValueError("invalid recording id")
    _number(document["created_at"])
    _number(document["expires_at"])
    if not 0 < document["expires_at"] - document["created_at"] <= limits.ttl_seconds:
        raise ValueError("invalid recording expiry")
    if type(document["timezone"]) is not str:
        raise ValueError("invalid timezone")
    try:
        ZoneInfo(document["timezone"])
    except (ZoneInfoNotFoundError, ValueError):
        raise ValueError("invalid timezone") from None
    _provenance(document["provenance"])
    refs = document["fixture_refs"]
    if type(refs) is not list:
        raise ValueError("invalid fixture references")
    for item in refs:
        _fixture(item, allowed)
    if len(set(refs)) != len(refs):
        raise ValueError("duplicate fixture references")
    declared = frozenset(refs)
    if type(document["events"]) is not list or len(document["events"]) > limits.max_events:
        raise ValueError("event count limit")
    # Validate before cross-event checks so malformed imports cannot leak a
    # Python indexing error instead of the bounded schema error.
    _fields(document["branch"], {"id", "parent", "parent_digest", "at", "changes"})
    for seq, event in enumerate(document["events"], 1):
        _event(event, seq, declared, limits)
        core = event.get("core")
        if isinstance(core, dict) and "model_step" in core:
            cause = core["model_step"]
            if (cause > len(document["events"]) or document["events"][cause - 1]["input"]["action"] != "language"
                    or document["branch"]["id"] == "original" and cause >= seq):
                raise ValueError("invalid recorded model cause")
        if ("core" in event and event["core"] is None and document["complete"]
                and document["branch"]["id"] == "original"):
            following = document["events"][seq].get("core") if seq < len(document["events"]) else None
            if (not isinstance(following, dict) or following.get("action") != "discover"
                    or following.get("data") != event["input"]["data"]):
                raise ValueError("unbound compound-command projection")
    if any(type(document[key]) is not bool for key in ("complete", "purged")):
        raise ValueError("invalid capture flags")
    _integer(document["dropped"], 2**31)
    branch = document["branch"]
    _fields(branch, {"id", "parent", "parent_digest", "at", "changes"})
    _changes(branch["changes"], declared, limits)
    if branch["id"] == "original":
        if any(branch[key] is not None for key in ("parent", "parent_digest", "at")) or branch["changes"]:
            raise ValueError("invalid original branch")
    else:
        if type(branch["id"]) is not str or not _UUID.fullmatch(branch["id"]):
            raise ValueError("invalid branch id")
        if type(branch["parent"]) is not str or not _REFERENCE.fullmatch(branch["parent"]):
            raise ValueError("invalid parent reference")
        if type(branch["parent_digest"]) is not str or not _HEX.fullmatch(branch["parent_digest"]):
            raise ValueError("invalid parent digest")
        _integer(branch["at"], limits.max_events - 1)
    if type(document["digest"]) is not str or document["digest"] != _digest(document):
        raise ValueError("recording digest mismatch")


def _escaped(value):
    if type(value) is str:
        return escape(value, quote=True)
    if type(value) is dict:
        return {key: _escaped(item) for key, item in value.items()}
    if type(value) is list:
        return [_escaped(item) for item in value]
    return value


class SanitizedTrace:
    """Nonthrowing diagnostic sink with categorical fields only; no exact inputs."""
    availability = "sanitized_inspection_only"

    def __init__(self, *, limits=None, provenance=None, rule_ids=()):
        self.limits = limits or Limits()
        self.id = uuid4().hex
        self.dropped = 0
        self._events = []
        self._rules = frozenset(rule_ids)
        for rule in self._rules:
            _label(rule)
        if provenance is not None:
            _provenance(provenance)
        self.provenance = deepcopy(provenance)

    def emit(self, event):
        try:
            if type(event) is not dict or len(self._events) >= self.limits.max_events:
                self.dropped += 1
                return False
            action = event.get("action", event.get("kind"))
            action = {"public_discovery": "discover"}.get(action, action) if type(action) is str else None
            status = event.get("status")
            reason = event.get("reason")
            latency = event.get("latency_ms", 0)
            if type(latency) not in (int, float) or not math.isfinite(latency) or not 0 <= latency <= 60000:
                latency = 0
            safe = {"seq": len(self._events) + 1,
                    "action": action if type(action) is str and action in _ACTIONS else "invalid",
                    "status": status if type(status) is str and status in _API_STATUS | {"attempted", "not_attempted"} else "not_attempted",
                    "reason": reason if type(reason) is str and reason in {"policy_denied", "api_failure", "invalid_input", "unknown_outcome"} else "none",
                    "latency_ms": latency}
            policy = event.get("policy")
            if type(policy) is dict:
                decision = policy.get("decision")
                safe["policy"] = {"decision": decision if type(decision) is str and decision in {"allow", "deny", "unknown"} else "unknown",
                                  "rule_ids": [item for item in policy.get("rule_ids", [])
                                               if type(item) is str and item in self._rules][:32]}
            self._events.append(safe)
            return True
        except Exception:
            # Evidence loss must never change a scheduling command's result.
            self.dropped += 1
            return False

    def snapshot(self):
        return deepcopy(self._events)

    def reference(self, index=0):
        _integer(index, self.limits.max_events - 1)
        return f"BOB-{self.id}/step/{index + 1}/branch/original"


class Recording:
    """Exact approved synthetic typed inputs, bounded outcomes and view receipts.

    Dates/preferences are structured; private identity is represented only by a
    caller-approved fixture reference. Text checks are conservative safeguards,
    not PHI detection or certification. A sealed/imported record cannot append.
    """

    def __init__(self, provenance, *, fixture_refs=(), synthetic=False, now=None,
                 timezone="UTC", limits=None):
        if synthetic is not True:
            raise PermissionError("explicit synthetic recording opt-in required")
        self.limits = limits or Limits()
        self._allowed = frozenset(fixture_refs)
        for ref in self._allowed:
            _label(ref)
        created = time() if now is None else now
        _number(created)
        self._data = {"version": 1, "id": uuid4().hex, "created_at": created,
            "expires_at": created + self.limits.ttl_seconds, "timezone": timezone,
            "provenance": deepcopy(provenance), "fixture_refs": sorted(self._allowed),
            "events": [], "complete": False, "dropped": 0, "purged": False,
            "branch": {"id": "original", "parent": None, "parent_digest": None,
                       "at": None, "changes": {}}}
        self._mutable = True
        self._expected = None
        _validate(self.to_dict(), self._allowed, self.limits)

    @classmethod
    def _restore(cls, document, allowed, limits, expected=None):
        _validate(document, allowed, limits)
        if expected is not None:
            _provenance(expected)
        result = object.__new__(cls)
        result.limits = limits
        result._allowed = frozenset(allowed)
        result._data = deepcopy(document)
        result._mutable = False
        result._expected = deepcopy(expected)
        return result

    @property
    def compatibility(self):
        return {"checked": self._expected is not None,
                "drift": sorted(key for key in _PROVENANCE
                                if self._expected is not None
                                and self._expected[key] != self._data["provenance"][key])}

    @property
    def missing(self):
        missing = []
        for event in self._data["events"]:
            action = event["input"]["action"]
            channel = "api" if action in _API_ACTIONS else "model" if action == "language" else None
            if isinstance(event.get("core"), dict) and event["core"]["api"] is None and channel == "api":
                channel = None  # A structural denial legitimately performs no I/O.
            if channel is not None and channel not in event["outcomes"]:
                missing.append(f"step {event['seq']}: {channel}")
        return missing

    def append(self, command, *, outcomes=None, view=None, clock=None, core=...):
        if not self._mutable or self._data["purged"]:
            raise RuntimeError("recording is sealed, imported or purged")
        if len(self._data["events"]) >= self.limits.max_events:
            self._data["dropped"] += 1
            return False
        event = {"seq": len(self._data["events"]) + 1, "input": command,
                 "outcomes": {} if outcomes is None else outcomes, "view": view,
                 "clock": self._data["created_at"] if clock is None else clock}
        if core is not ...:
            event["core"] = core
        _tree(event, self.limits)
        _event(event, event["seq"], self._allowed, self.limits)
        candidate = self.to_dict()
        candidate["events"].append(deepcopy(event))
        if len(_canonical(candidate).encode("utf-8")) > self.limits.max_record_bytes:
            self._data["dropped"] += 1
            return False
        self._data["events"].append(deepcopy(event))
        return True

    def seal(self):
        self._mutable = False
        self._data["complete"] = True

    def to_dict(self):
        result = deepcopy(self._data)
        result["digest"] = _digest(result)
        return result

    def export_json(self, *, reviewed=False):
        if reviewed is not True:
            raise PermissionError("exact recording export requires explicit review")
        return _canonical(self.to_dict())

    def reference(self, index=0):
        if type(index) is not int or not -1 <= index < self.limits.max_events:
            raise ValueError("invalid reference step")
        return f"BOB-{self._data['id']}/step/{index + 1}/branch/{self._data['branch']['id']}"

    def availability(self, *, now=None):
        if self._data["purged"] or (time() if now is None else now) >= self._data["expires_at"]:
            return "expired"
        if not self._data["complete"] or self._data["dropped"] or self.missing:
            return "incomplete_capture"
        return "full_replay"

    def purge(self):
        """Erase only this memory recording; references remain expired evidence."""
        self._data["events"] = []
        self._data["purged"] = True
        self._data["complete"] = False
        self._mutable = False

    def expire(self, *, now=None):
        if (time() if now is None else now) >= self._data["expires_at"]:
            self.purge()
            return True
        return False


def import_recording(payload, *, fixture_refs=(), expected_provenance=None, now=None, limits=None):
    """Strict bounded JSON only. The document's fixture declarations confer no trust."""
    limits = limits or Limits()
    if type(payload) not in (bytes, str):
        raise ValueError("recording must be JSON bytes or text")
    try:
        size = len(payload) if type(payload) is bytes else len(payload.encode("utf-8"))
    except UnicodeError:
        raise ValueError("invalid JSON encoding") from None
    if size > limits.max_import_bytes:
        raise ValueError("import size limit")

    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate fields")
            result[key] = value
        return result

    def nonfinite(_value):
        raise ValueError("nonfinite JSON number")

    try:
        text = payload.decode("utf-8") if type(payload) is bytes else payload
        document = json.loads(text, object_pairs_hook=unique, parse_constant=nonfinite)
    except (ValueError, UnicodeError, RecursionError) as error:
        message = "duplicate fields" if str(error) == "duplicate fields" else "invalid strict JSON"
        raise ValueError(message) from None
    result = Recording._restore(document, frozenset(fixture_refs), limits, expected_provenance)
    imported_at = time() if now is None else now
    _number(imported_at)
    if document["created_at"] > imported_at:
        raise ValueError("future recording creation cannot extend retention")
    # Expired imports may be inspected as references, but cannot open a Replay.
    result.availability(now=now)
    return result


def _initial(document):
    return {"revision": 0, "identity_fixture": None, "preferences": {}, "providers": [],
            "options": [], "selection": None, "outcome": "not_attempted", "unknown": False,
            "history": [], "clock": document["created_at"], "message": "",
            "simulation_only": True, "executable_authority": False}


def _transition(state, event):
    """Pure bounded interpreter: recorded outcomes are observations, never tools.

    Only fresh ordered typed inputs establish simulated prerequisites. Historical
    policy allow, enabled buttons and success responses cannot establish them.
    Model preference proposals remain inspectable and require a typed preference
    input; they cannot supply identity, selection or confirmation.
    """
    command, outcomes = event["input"], event["outcomes"]
    action, data = command["action"], command["data"]
    state["revision"], state["clock"] = event["seq"], event["clock"]
    if action != "confirm":
        state["selection"] = None
    required = "api" if action in _API_ACTIONS else "model" if action == "language" else None
    if required is not None and required not in outcomes:
        state["outcome"] = "missing_data"
        state["selection"] = None
        return
    api = outcomes.get("api", {})
    if action == "identity_fixture":
        state["identity_fixture"] = data["fixture_ref"]
        state["options"] = []
    elif action == "preferences":
        merged = {key: value for key, value in {**state["preferences"], **data}.items() if value is not None}
        if merged.get("date_from", "") > merged.get("date_to", "9999-12-31"):
            state["outcome"] = "invalid_input"
        else:
            state["preferences"], state["options"] = merged, []
    elif action == "discover":
        state["providers"] = list(api["fixture_refs"]) if api["status"] == "ok" else []
    elif action in {"availability", "appointments"}:
        if not state["identity_fixture"]:
            state["outcome"] = "blocked"
        else:
            if action == "availability":
                state["options"] = list(api["fixture_refs"]) if api["status"] == "ok" else []
            state["outcome"] = "not_attempted" if api["status"] in {"ok", "empty"} else api["status"]
    elif action == "select":
        if state["identity_fixture"] and 1 <= data["index"] <= len(state["options"]):
            state["selection"] = state["options"][data["index"] - 1]
            state["outcome"] = "not_attempted"
        else:
            state["outcome"] = "blocked"
    elif action in {"confirm", "handoff"}:
        denied = outcomes.get("policy", {}).get("decision") in {"deny", "unknown"}
        ready = (action == "handoff" or (state["identity_fixture"] is not None
                 and state["selection"] is not None and state["selection"] in state["options"]))
        state["selection"] = None
        if not ready or state["unknown"] or denied:
            state["outcome"] = "blocked"
        else:
            status = api["status"] if api["status"] in {"completed", "rejected", "failed", "unknown"} else "unknown"
            state["outcome"] = status
            state["unknown"] = status == "unknown"
            state["history"].append({"step": event["seq"], "kind": "booking" if action == "confirm" else "handoff", "status": status})
    elif action == "language":
        state["outcome"] = "model_" + outcomes["model"]["category"]
        state["message"] = "Recorded language result: " + outcomes["model"]["category"]
    elif action == "reset":
        state.update(identity_fixture=None, preferences={}, providers=[], options=[], selection=None)
        state["outcome"] = "unknown" if state["unknown"] else "not_attempted"
    elif action in {"help", "medical", "unsupported", "decline"}:
        state["message"] = action


def _difference(before, after):
    return {key: {"before": deepcopy(before.get(key)), "after": deepcopy(after.get(key))}
            for key in sorted(before.keys() | after.keys()) if before.get(key) != after.get(key)}


class _MemoryClaims:
    """Replay-private write protection; never loads or serializes live claims."""
    def __init__(self):
        self._claims = {}

    def blocked(self, key):
        return self._claims.get(key, (None, None))[1] in {"attempted", "unknown"}

    def claim(self, key):
        if self.blocked(key):
            raise RuntimeError("simulation effect unresolved")
        claim = uuid4().hex
        self._claims[key] = claim, "attempted"
        return claim

    def finish(self, key, claim, status):
        if status not in {"completed", "rejected", "failed", "unknown"} or self._claims.get(key) != (claim, "attempted"):
            raise ValueError("invalid simulation claim")
        self._claims[key] = claim, status


class _RecordedPort:
    """Fixed methods only. An unexpected request never falls back to live I/O."""
    def __init__(self, catalog):
        self.catalog, self.observation, self.gap = catalog, None, False

    def arm(self, observation):
        self.observation, self.gap = deepcopy(observation), False

    def _result(self, method, kind=None, patient=None):
        from .http_mock import ApiError, UnknownOutcome
        api, self.observation = self.observation, None
        if api is None or api["method"] != method:
            self.gap = True
            raise RuntimeError("recorded outcome unavailable")
        if api["error"] == "api":
            raise ApiError(api["http_status"])
        if api["error"] == "unknown":
            raise UnknownOutcome("Recorded uncertain outcome.")
        if api["error"] == "unexpected":
            raise RuntimeError("Recorded unverified outcome.")
        if method in {"book", "handoff"}:
            if api["status"] != "completed":
                self.gap = True
                raise UnknownOutcome("Recorded receipt unavailable.")
            return {"status": "booked" if method == "book" else "queued"}
        if api["status"] not in {"ok", "empty"}:
            self.gap = True
            raise RuntimeError("Recorded data unavailable.")
        result = []
        for ref in api["fixture_refs"]:
            item = self.catalog.get(ref)
            if method == "appointments" and item is not None and item["kind"] == "slot":
                # A host-approved slot stands for a validated appointment's
                # public projection. The private receipt never enters replay;
                # this fixed placeholder is confined to the simulation core.
                if not any(entry["kind"] == "patient" and entry["value"].get("patientId") == patient
                           for entry in self.catalog.values()):
                    self.gap = True
                    raise RuntimeError("Approved fixture unavailable.")
                result.append({"appointmentId": "simulation-only", "patientId": patient,
                               **{key: item["value"][key] for key in ("providerId", "specialty", "location", "startTime")},
                               "status": "scheduled"})
                continue
            if item is None or item["kind"] != kind:
                self.gap = True
                raise RuntimeError("Approved fixture unavailable.")
            result.append(deepcopy(item["value"]))
        return result

    def providers(self, specialty=None, location=None):
        return self._result("providers", "provider")

    def search_patients(self, phone, dob):
        return self._result("search_patients", "patient")

    def availability(self, patient, specialty, location=None, start=None, end=None):
        return self._result("availability", "slot")

    def appointments(self, patient):
        return self._result("appointments", "appointment", patient)

    def book(self, patient, slot):
        return self._result("book")

    def handoff(self, reason, summary):
        return self._result("handoff")


class Replay:
    """Fresh isolated simulation with no API/model/callback/credential arguments.

    Core evidence recomputes through SchedulingSession and the fixed private
    recorded port. No API/callback injection, model, credentials, HTTP or disk
    journal. Legacy evidence is inspection-only. Renderer receipts and recorded
    allow bits remain observations, never guards or inherited consent.
    """

    def __init__(self, recording, *, expected_provenance=None, now=None, fixture_catalog=None):
        if not isinstance(recording, Recording):
            raise ValueError("a validated Recording is required")
        if recording.availability(now=now) == "expired":
            raise ValueError("recording expired; reference inspection only")
        # Explicit now is a fixed test clock. The default rechecks wall-clock
        # expiry on every operation, including already-open replay snapshots.
        self._now = now
        expected = recording._expected if expected_provenance is None else expected_provenance
        self._recording = Recording._restore(recording.to_dict(), recording._allowed, recording.limits, expected)
        self.namespace = uuid4().hex
        self.index = -1
        self._playing = False
        self._bookmarks = {}
        if fixture_catalog is not None:
            _tree(fixture_catalog, recording.limits)
        self._catalog = deepcopy(fixture_catalog) if fixture_catalog is not None else None
        self._missing_cache = None
        if self._catalog is not None:
            _tree(self._catalog, recording.limits)
            if type(self._catalog) is not dict:
                raise ValueError("host fixture data required")
            for ref, item in self._catalog.items():
                _fixture(ref, recording._allowed)
                _fields(item, {"kind", "value"})
                _enum(item["kind"], {"patient", "provider", "slot", "appointment"})
                if type(item["value"]) is not dict:
                    raise ValueError("host fixture data required")
        compatibility = self._recording.compatibility
        self.mode = "comparison" if compatibility["drift"] else "recorded_replay" if compatibility["checked"] else "unverified_source"

    @property
    def recording(self):
        return Recording._restore(self._recording.to_dict(), self._recording._allowed,
                                  self._recording.limits, self._recording._expected)

    @property
    def bookmarks(self):
        return deepcopy(self._bookmarks)

    def purge(self):
        self._recording.purge()
        self._bookmarks.clear()
        self._playing = False
        self._missing_cache = None

    @property
    def missing(self):
        if self._missing_cache is not None:
            return list(self._missing_cache)
        missing = list(self._recording.missing)
        events = self._recording._data["events"]
        missing.extend(f"step {event['seq']}: core evidence" for event in events if "core" not in event)
        if self._catalog is None:
            missing.append("approved host fixture data unavailable")
        elif all("core" in event for event in events):
            _state, gaps = self._core_states(len(events) - 1)
            missing.extend(gaps)
        self._missing_cache = list(dict.fromkeys(missing))
        return list(self._missing_cache)

    @property
    def fidelity(self):
        doc = self._recording._data
        return {"core_semantic_parity": bool(doc["complete"] and not doc["purged"] and not doc["dropped"]
                    and doc["branch"]["id"] == "original" and not self.missing
                    and self._recording.compatibility["checked"] and not self._recording.compatibility["drift"]),
                "core_renderer_parity": False, "representation": "scheduling_core_v1",
                "limitations": ["Semantic core projections, not browser drafts, focus or acknowledgement parity.",
                                "Private records and receipt identifiers are omitted.",
                                "Variants recompute core decisions; unchanged recorded API observations are counterfactual stubs."]}

    def _core_states(self, index):
        from .session import SchedulingSession
        port = _RecordedPort(self._catalog)
        session = SchedulingSession(port, session_id=self.namespace, _replay_journal=_MemoryClaims())
        gaps = []
        model_categories = {}
        identity_ref = None
        clock = self._recording._data["created_at"]
        for event in self._recording._data["events"][:index + 1]:
            clock = event["clock"]
            if event["input"]["action"] == "language":
                model_categories[event["seq"]] = event["outcomes"].get("model", {}).get("category")
            evidence = event.get("core")
            if evidence is None:
                continue  # Explicit projection-only compound-command boundary.
            if "model_step" in evidence and model_categories.get(evidence["model_step"]) != "accepted":
                continue  # Changed/stale/invalid model output cannot apply its old proposal.
            action, data = evidence["action"], deepcopy(evidence["data"])
            try:
                if action == "identity_fixture":
                    identity_ref = data["fixture_ref"]
                    fixture = self._catalog[identity_ref]
                    if fixture["kind"] != "patient":
                        raise ValueError("patient fixture required")
                    values = fixture["value"]
                    data = {"phone": values["phone"], "dob": values["dateOfBirth"],
                            "zip": values["zipCode"] if data["zip_mode"] == "fixture" else ""}
                    action = "identity"
                elif action in {"preferences", "discover"}:
                    converted = {}
                    for key, value in data.items():
                        if key == "provider_ref" and value is not None:
                            fixture = self._catalog[value]
                            if fixture["kind"] != "provider":
                                raise ValueError("provider fixture required")
                            value = fixture["value"]["providerId"]
                        converted[{"date_from": "start_date", "date_to": "end_date", "provider_ref": "provider_id"}.get(key, key)] = value
                    data = converted
                elif action == "confirm":
                    proposal = session.proposal
                    # Fresh simulation-only proposal, never imported IDs/nonce.
                    data = ({"proposal_id": proposal["id"], "nonce": proposal["nonce"]}
                            if data["current"] and proposal is not None else {})
                port.arm(evidence["api"])
                session.command(action, data, expected_revision=session.revision, actor=evidence["actor"])
                if action == "reset":
                    identity_ref = None
                if port.gap or (port.observation is not None and self._recording._data["branch"]["id"] == "original"):
                    gaps.append(f"step {event['seq']}: recorded API path mismatch")
                if self._recording._data["branch"]["id"] == "original" and _core_projection(session, self._catalog) != evidence["view"]:
                    gaps.append(f"step {event['seq']}: semantic core mismatch")
            except (KeyError, ValueError, TypeError):
                gaps.append(f"step {event['seq']}: approved fixture binding unavailable")
        core = _core_projection(session, self._catalog)
        state = _initial(self._recording._data)
        view = session.view()
        def refs(kind, values):
            return [ref for value in values for ref, item in self._catalog.items()
                    if item["kind"] == kind and item["value"] == value]
        state.update(revision=core["revision"], core=core, identity_fixture=identity_ref if session.identity else None,
                     preferences=core["preferences"], providers=refs("provider", session.providers),
                     options=refs("slot", session.slots), selection=refs("slot", [session.proposal["slot"]])[0]
                     if session.proposal and refs("slot", [session.proposal["slot"]]) else None,
                     outcome=core["certainty"], unknown=core["booking_blocked"] or core["handoff_blocked"],
                     history=core["history"], clock=clock, message=view["message"])
        return state, gaps

    def expire(self, *, now=None):
        if self._recording.expire(now=self._now if now is None else now):
            self.purge()
            return True
        return False

    def _active(self):
        if self._recording.availability(now=self._now) == "expired":
            self.purge()
            raise ValueError("recording expired; reference inspection only")

    def _index(self, index, *, initial=False):
        self._active()
        if type(index) is not int or not (-1 if initial else 0) <= index < len(self._recording._data["events"]):
            raise ValueError("step outside recording")

    def _state_at(self, index):
        if self._catalog is not None and all("core" in event for event in self._recording._data["events"]):
            return self._core_states(index)[0]
        state = _initial(self._recording._data)
        for event in self._recording._data["events"][:index + 1]:
            _transition(state, event)
        return state

    def state(self):
        self._active()
        return _escaped({**self._state_at(self.index), "namespace": self.namespace})

    def jump(self, index):
        self._index(index, initial=True)
        self.index = index
        return self.state()

    def step(self):
        self._active()
        if self.index + 1 < len(self._recording._data["events"]):
            self.index += 1
        else:
            self._playing = False
        return self.state()

    def previous(self):
        self._active()
        self.index = max(-1, self.index - 1)
        return self.state()

    def play(self):
        self._active()
        self._playing = True

    def pause(self):
        self._active()
        self._playing = False

    def tick(self):
        return self.step() if self._playing else self.state()

    def reference(self, index=None):
        return self._recording.reference(self.index if index is None else index)

    def bookmark(self, name):
        self._active()
        _text(name, self._recording.limits)
        if not name or len(self._bookmarks) >= self._recording.limits.max_events:
            raise ValueError("invalid or excessive bookmarks")
        self._bookmarks[name] = self.index
        return self.reference()

    def go_bookmark(self, name):
        if type(name) is not str or name not in self._bookmarks:
            raise ValueError("bookmark unavailable")
        return self.jump(self._bookmarks[name])

    def before_after(self, index):
        self._index(index)
        before = self._state_at(index - 1)
        after = self._state_at(index)
        return _escaped({"before": before, "after": after, "diff": _difference(before, after)})

    def inspect(self, index):
        self._index(index)
        event = self._recording._data["events"][index]
        return {"reference": self.reference(index), **_escaped(deepcopy(event)),
                **self.before_after(index), "mode": self.mode,
                "missing": [item for item in self._recording.missing if item.startswith(f"step {index + 1}:")],
                "view_captured": event["view"] is not None}

    def fork(self, index, changes):
        self._index(index)
        _tree(changes, self._recording.limits)
        _changes(changes, self._recording._allowed, self._recording.limits)
        doc = self._recording.to_dict()
        event = doc["events"][index]
        action, data = event["input"]["action"], event["input"]["data"]
        if "preferences" in changes:
            if action != "preferences":
                raise ValueError("preference variant requires a preference input")
            data.update(deepcopy(changes["preferences"]))
        if "identity_fixture" in changes:
            if action != "identity_fixture":
                raise ValueError("identity variant requires a fixture input")
            data["fixture_ref"] = changes["identity_fixture"]
        if "clock" in changes:
            event["clock"] = changes["clock"]
        if "model_category" in changes:
            if action != "language":
                raise ValueError("model variant requires a language input")
            event["outcomes"].setdefault("model", {"category": "invalid", "preferences": {}})["category"] = changes["model_category"]
        if "api_status" in changes or "api_delay_ms" in changes:
            if action not in _API_ACTIONS:
                raise ValueError("API variant requires an API observation")
            api = event["outcomes"].setdefault("api", {"status": "unknown", "fixture_refs": [], "delay_ms": 0})
            if "api_status" in changes:
                api["status"] = changes["api_status"]
            if "api_delay_ms" in changes:
                api["delay_ms"] = changes["api_delay_ms"]
        evidence = event.get("core")
        if isinstance(evidence, dict):
            if "preferences" in changes:
                evidence["data"].update(deepcopy(changes["preferences"]))
            if "identity_fixture" in changes:
                evidence["data"]["fixture_ref"] = changes["identity_fixture"]
            if evidence["api"] is not None:
                if "api_delay_ms" in changes:
                    evidence["api"]["delay_ms"] = changes["api_delay_ms"]
                if "api_status" in changes:
                    status = changes["api_status"]
                    evidence["api"].update(status=status, error="api" if status in {"rejected", "failed"} else
                                           "unknown" if status == "unknown" else "none",
                                           http_status=409 if status == "rejected" else 503 if status == "failed" else None)
        elif "preferences" in changes and "core" in event:
            # Compound discover's projected preferences are not a second core
            # command. Its variant belongs to the following actual boundary.
            if index + 1 < len(doc["events"]):
                following = doc["events"][index + 1].get("core")
                if isinstance(following, dict) and following["action"] == "discover":
                    following["data"].update(deepcopy(changes["preferences"]))
        if "order" in changes:
            suffix = doc["events"][index:]
            if len(changes["order"]) != len(suffix):
                raise ValueError("ordering must cover the selected suffix")
            doc["events"][index:] = [suffix[position] for position in changes["order"]]
        reordered = {event["seq"]: seq for seq, event in enumerate(doc["events"], 1)}
        for seq, event in enumerate(doc["events"], 1):
            event["seq"] = seq
            if isinstance(event.get("core"), dict) and "model_step" in event["core"]:
                event["core"]["model_step"] = reordered[event["core"]["model_step"]]
        doc["branch"] = {"id": uuid4().hex, "parent": self.reference(index),
                         "parent_digest": self._recording.to_dict()["digest"],
                         "at": index, "changes": deepcopy(changes)}
        doc["digest"] = _digest(doc)
        child = Recording._restore(doc, self._recording._allowed, self._recording.limits, self._recording._expected)
        return Replay(child, now=self._now, fixture_catalog=self._catalog)

    def compare(self, other):
        self._active()
        if not isinstance(other, Replay):
            raise ValueError("comparison requires an isolated Replay")
        other._active()
        left_events, right_events = self._recording._data["events"], other._recording._data["events"]
        differences = []
        for index in range(max(len(left_events), len(right_events))):
            left = self._state_at(min(index, len(left_events) - 1))
            right = other._state_at(min(index, len(right_events) - 1))
            diff = _difference(left, right)
            left_event = left_events[index] if index < len(left_events) else {}
            right_event = right_events[index] if index < len(right_events) else {}
            event_diff = _difference(left_event, right_event)
            if diff or event_diff:
                differences.append({"step": index + 1, "state": diff,
                                    "event": event_diff})
        drift = sorted(key for key in _PROVENANCE if self._recording._data["provenance"][key] != other._recording._data["provenance"][key])
        return _escaped({"provenance_drift": drift, "differences": differences, "simulation_only": True})

    def regression_proposal(self, *, reviewed=False, through=None):
        self._active()
        if reviewed is not True:
            raise PermissionError("regression proposal requires explicit review")
        doc = self._recording.to_dict()
        at = doc["branch"]["at"]
        if at is None:
            raise ValueError("select a variant before regression promotion")
        last = at if through is None else through
        self._index(last)
        if last < at:
            raise ValueError("regression must include the changed step")
        return {"fixture": True, "simulation_only": True, "requires_execution_review": True,
                "parent": doc["branch"]["parent"], "parent_digest": doc["branch"]["parent_digest"],
                "provenance": doc["provenance"], "changes": doc["branch"]["changes"],
                "events": doc["events"][:last + 1]}


def reference(events, index=0):
    """Legacy sanitized inspection only; this is not an exact replay recording."""
    if type(events) is not list or len(events) > 2000:
        raise ValueError("invalid legacy trace")
    if not events:
        return {"index": 0, "event": None}
    _integer(index, len(events) - 1)
    trace = SanitizedTrace()
    trace.emit(events[index])
    snapshot = trace.snapshot()
    return {"index": index, "event": snapshot[0] if snapshot else None}


def fork(events, index, changes):
    """Compatibility for the old timeout example; exact variants use Replay.fork."""
    _fields(changes, {"fault"})
    _enum(changes["fault"], {"timeout", "unavailable", "invalid"})
    source = reference(events, index)
    trace = SanitizedTrace()
    for event in events[:index + 1]:
        trace.emit(event)
    return {"source": source, "changes": deepcopy(changes), "simulation_only": True,
            "events": trace.snapshot()}


def promote(variant, reviewed=False):
    if reviewed is not True:
        raise PermissionError("variant requires explicit review")
    _fields(variant, {"source", "changes", "simulation_only", "events"})
    _fields(variant["source"], {"index", "event"})
    if variant["simulation_only"] is not True:
        raise ValueError("simulation proposal required")
    safe = fork(variant["events"], variant["source"]["index"], variant["changes"])
    return {"fixture": True, "source": safe["source"], "changes": safe["changes"],
            "simulation_only": True, "requires_execution_review": True}
