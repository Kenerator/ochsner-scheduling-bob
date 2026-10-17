"""Small connected-journey runner, with no credential or accounting construction.

load_manifest validates before effects. run_journey owns only its fresh supplied
mock and temporary effect journal; the caller supplies/reuses LanguageAdapter and
owns scheduling, canonical model accounting, opt-in and tranche stop decisions.
All indexes are zero-based. No raw view, dialogue, identity, receipt or error is
returned. The only model observations retained are closed numeric/categorical
LanguageOutcome fields. Fixture transport remains fixture evidence.

Manifest v1: exact top keys schema_version=1, synthetic_only=true,
set=development|holdout, repetitions=1|2, cases (1..16 unique slug IDs).
Cases: id, scenario (supplied allowlist), steps (1..32), expected.
Steps all require expect; text adds text/dispatch, identity adds approved data,
command adds action/data, confirm adds nothing, scenario adds scenario.
Expectations: states, preferences (partial), identity_status, proposal,
result_status, history_statuses, interpretation_status, slot_count,
appointment_count. expected requires post_attempts/booking_completed/
handoff_queued; optionally booking_verified/api_calls/language_calls.
JSON is <=64 KiB, depth <=8, <=4096 nodes; unknown keys/types are rejected.
"""

from datetime import date
import json
from pathlib import Path
import re
from tempfile import TemporaryDirectory
from time import perf_counter

from ochsner_bob.conversation import Conversation
from ochsner_bob.http_mock import ApiError, HttpMockAdapter
from ochsner_bob.language import ACTIONS, LanguageAdapter, LanguageOutcome, _http_transport
from ochsner_bob.session import LOCATIONS, REASONS, SPECIALTIES, SchedulingSession
if __package__:
    from .mock_lifecycle import OwnedMock
else:  # Parent CLI may import this sibling directly from scripts/.
    from mock_lifecycle import OwnedMock


_SCENARIOS = {"happy_path_booking", "provider_lookup", "no_patient_match",
              "multiple_patient_matches", "slot_conflict", "no_availability",
              "api_failure", "unsupported_request"}
_STATES = {"start", "preferences", "providers", "identity_required", "ready", "ambiguous",
           "options", "proposal", "outage", "rejected", "unknown", "error", "help",
           "medical", "unsupported", "declined", "completed", "queued", "failed"}
_RESULTS = {"not_attempted", "attempted", "completed", "queued", "rejected", "failed", "unknown"}
_STATUSES = {"ok", "disabled", "private_input", "invalid_input", "invalid_context", "clarification",
             "invalid_output", "refused", "timeout", "unavailable", "budget_exceeded", "accounting_failed"}
_ACCOUNTING = {"not_requested", "unbudgeted", "known", "unknown", "failed"}
_COUNTS = {"post_attempts", "booking_completed", "handoff_queued", "booking_verified", "api_calls", "language_calls"}
_ROUTES = {"/providers", "/patients/search", "/availability", "/appointments", "/handoffs",
           "/patients/{patientId}/appointments"}
_IDENTITY_VALUES = {"phone": {"", "555-0101", "555-0102", "555-0130", "555-0105", "555-0199"},
                    "dob": {"", "1985-04-12", "1992-06-03", "1978-09-22", "2001-11-09"},
                    "zip": {"", "70112", "70118", "70115", "70005", "70130"}}


def _require(condition):
    if not condition:
        raise ValueError("invalid_manifest")


def _integer(value, upper=256):
    return type(value) is int and 0 <= value <= upper


def _enum(value, allowed):
    return type(value) is str and value in allowed


def _keys(value, required, optional=()):
    return type(value) is dict and set(required) <= value.keys() <= set(required) | set(optional)


def _preferences(value):
    _require(type(value) is dict and not set(value) - {"specialty", "location", "start_date", "end_date"})
    for key, item in value.items():
        if item is None:
            continue  # Explicit local clear; model null retains its own semantics.
        if key in {"specialty", "location"}:
            _require(_enum(item, SPECIALTIES if key == "specialty" else LOCATIONS))
        else:
            _require(type(item) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", item) is not None)
            try:
                date.fromisoformat(item)
            except ValueError:
                raise ValueError("invalid_manifest") from None


def _expect(value):
    _require(_keys(value, (), {"states", "preferences", "identity_status", "proposal", "result_status",
                              "history_statuses", "interpretation_status", "slot_count", "appointment_count"}))
    for key, item in value.items():
        if key == "states":
            _require(type(item) is list and 1 <= len(item) <= len(_STATES) and all(_enum(v, _STATES) for v in item))
        elif key == "preferences":
            _preferences(item)
        elif key == "identity_status":
            _require(_enum(item, {"missing", "verified", "ambiguous"}))
        elif key == "proposal":
            _require(type(item) is bool)
        elif key == "result_status":
            _require(_enum(item, _RESULTS))
        elif key == "history_statuses":
            _require(type(item) is list and len(item) <= 32 and all(_enum(v, _RESULTS) for v in item))
        elif key == "interpretation_status":
            _require(_enum(item, _STATUSES))
        else:
            _require(_integer(item, 2000))


def _case(value):
    _require(_keys(value, {"id", "scenario", "steps", "expected"}))
    _require(type(value["id"]) is str and re.fullmatch(r"[a-z][a-z0-9-]{0,63}", value["id"]) is not None)
    _require(_enum(value["scenario"], _SCENARIOS))
    _require(type(value["steps"]) is list and 1 <= len(value["steps"]) <= 32)
    _require(_keys(value["expected"], {"post_attempts", "booking_completed", "handoff_queued"}, _COUNTS))
    _require(all(_integer(v) for v in value["expected"].values()))
    for step in value["steps"]:
        _require(type(step) is dict and _enum(step.get("kind"), {"text", "identity", "command", "confirm", "scenario"}))
        kind = step["kind"]
        fields = {"text": {"text", "dispatch"}, "identity": {"data"}, "command": {"action", "data"},
                  "confirm": set(), "scenario": {"scenario"}}[kind]
        _require(_keys(step, {"kind", "expect"} | fields))
        _expect(step["expect"])
        if kind == "text":
            text = step["text"]
            _require(type(text) is str and 0 < len(text.encode("utf-8")) <= 2048 and text.strip() != "")
            _require(not any(ord(c) < 32 and c not in "\n\t" for c in text) and type(step["dispatch"]) is bool)
        elif kind == "identity":
            data = step["data"]
            _require(type(data) is dict and 1 <= len(data) <= 3 and not set(data) - _IDENTITY_VALUES.keys())
            _require(all(_enum(v, _IDENTITY_VALUES[k]) for k, v in data.items()))
        elif kind == "scenario":
            _require(_enum(step["scenario"], _SCENARIOS))
        elif kind == "command":
            action, data = step["action"], step["data"]
            _require(_enum(action, {"availability", "select", "handoff", "help", "medical", "unsupported",
                                    "decline", "preferences", "appointments", "discover", "reset"}))
            _require(type(data) is dict)
            if action == "select":
                _require(_keys(data, {"index"}) and _integer(data["index"], 2000) and data["index"] > 0)
            elif action == "handoff":
                _require(_keys(data, (), {"reason"}) and (not data or _enum(data["reason"], REASONS)))
            elif action in {"preferences", "discover"}:
                _preferences(data)
            else:
                _require(not data)


def _bounded(value):
    pending, count = [(value, 0)], 0
    while pending:
        node, depth = pending.pop()
        count += 1
        _require(depth <= 8 and count <= 4096)
        if type(node) is dict:
            pending.extend((v, depth + 1) for v in node.values())
        elif type(node) is list:
            pending.extend((v, depth + 1) for v in node)


def _pairs(items):
    result = {}
    for key, value in items:
        _require(key not in result)
        result[key] = value
    return result


def _constant(_):
    raise ValueError("invalid_manifest")


def load_manifest(path) -> dict:
    """Read a bounded strict synthetic manifest; no service or journal is started."""
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(65537)
        _require(len(raw) <= 65536)
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_pairs, parse_constant=_constant)
        _bounded(value)
        _require(_keys(value, {"schema_version", "synthetic_only", "set", "repetitions", "cases"}))
        _require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["synthetic_only"] is True)
        _require(_enum(value["set"], {"development", "holdout"}))
        _require(type(value["repetitions"]) is int and value["repetitions"] in {1, 2})
        _require(type(value["cases"]) is list and 1 <= len(value["cases"]) <= 16)
        for item in value["cases"]:
            _case(item)
        _require(len({item["id"] for item in value["cases"]}) == len(value["cases"]))
        return value
    except (OSError, ValueError, TypeError, RecursionError, OverflowError):
        raise ValueError("invalid_manifest") from None


def _observation(outcome, mode, elapsed):
    if (not isinstance(outcome, LanguageOutcome) or not _enum(outcome.mode, {mode})
            or not _enum(outcome.status, _STATUSES) or not _enum(outcome.accounting_status, _ACCOUNTING)
            or outcome.action is not None and not _enum(outcome.action, ACTIONS)):
        return None
    try:
        _preferences(outcome.preferences)
    except ValueError:
        return None
    if (any(value is None for value in outcome.preferences.values())
            or outcome.status == "ok" and outcome.action is None
            or outcome.status != "ok" and (outcome.action is not None or outcome.preferences)):
        return None
    usage = outcome.usage
    limits = {"input_tokens": 400000, "output_tokens": 512, "cached_input_tokens": 400000,
              "reasoning_output_tokens": 512}
    if usage is not None and (not _keys(usage, limits) or
            any(not _integer(v, limits[k]) for k, v in usage.items()) or
            usage["cached_input_tokens"] > usage["input_tokens"] or
            usage["reasoning_output_tokens"] > usage["output_tokens"]):
        return None
    cost = outcome.cost_usd
    if cost is not None and (type(cost) is not str or re.fullmatch(r"(?:0|[1-9][0-9]?)\.[0-9]{9}", cost) is None
                             or int(cost.replace(".", "")) > 20_000_000_000):
        return None
    if outcome.accounting_status == "known" and (usage is None or cost is None):
        return None
    if outcome.accounting_status != "known" and cost is not None:
        return None
    return {"mode": mode, "status": outcome.status, "accounting_status": outcome.accounting_status,
            "usage": None if usage is None else dict(usage), "cost_usd": cost,
            "latency_ms": round(elapsed, 3)}


class _ObservedLanguage:
    """Interpose only observation/dispatch gating; never store text or outcomes."""
    def __init__(self, language):
        self.language = language
        # Bind genuine mode to this source's actual uninjected adapter/transport,
        # not a mutable label on a fixture or a substitute interpret() subclass.
        self.mode = ("offline" if language is None else "openai"
                     if type(language) is LanguageAdapter and language.mode == "openai"
                     and language._transport is _http_transport else "fixture")
        self.calls = 0
        self.allow = False
        self.observation = None
        self.failure = None

    def interpret(self, text, context):
        if not self.allow or self.language is None:
            self.failure = "dispatch_mismatch"
            return LanguageOutcome("unavailable", "fixture")
        self.calls += 1
        started = perf_counter()
        try:
            outcome = self.language.interpret(text, context)
        except Exception:
            self.failure = "language_unavailable"
            return LanguageOutcome("unavailable", self.mode)
        self.observation = _observation(outcome, self.mode, (perf_counter() - started) * 1000)
        if self.observation is None:
            self.failure = "observation_invalid"
        elif outcome.status in {"timeout", "unavailable", "disabled", "budget_exceeded", "accounting_failed", "invalid_output"}:
            self.failure = "language_" + outcome.status
        elif outcome.accounting_status in {"unknown", "failed"}:
            self.failure = "accounting_" + outcome.accounting_status
        elif self.mode == "openai" and outcome.accounting_status != "known":
            self.failure = "accounting_unavailable"
        if self.failure:
            # Stop before Conversation can apply any otherwise plausible proposal.
            return LanguageOutcome("unavailable", self.mode)
        return outcome


def _projection(view):
    return {"state": view["state"], "identity_status": view["identity_status"],
            "proposal": bool(view["proposal"]),
            "preferences": {k: v for k, v in view["preferences"].items() if k in {"specialty", "location"}},
            "result_status": (view["current_result"] or {}).get("status", "not_attempted"),
            "history_statuses": [r["status"] for r in view["history"]],
            "slot_count": len(view["slots"]), "appointment_count": len(view["appointments"]),
            "interpretation_status": view.get("interpretation", {}).get("status", "ok")}


def _assertions(view, expected):
    projected = _projection(view)
    result = {}
    for key, value in expected.items():
        if key == "states":
            result[key] = projected["state"] in value
        elif key == "preferences":
            result[key] = all(view["preferences"].get(k) == v for k, v in value.items())
        else:
            result[key] = projected[key] == value
    return result


def run_journey(case, language, effects_dir: Path, *, repetition_id=1) -> dict:
    """Run one scheduled journey; reuse the supplied adapter/accounting unchanged.

    effects_dir must already exist. A private owned child directory is removed on
    every return. Confirm binds exclusively to the immediately prior returned view.
    Actual completed bookings get one supplied appointments read for verification;
    it is evidence I/O (included in api_calls), never a retry or session mutation.
    """
    try:
        _bounded(case)
        _require(len(json.dumps(case, allow_nan=False).encode("utf-8")) <= 65536)
        _case(case)
        _require(type(repetition_id) is int and repetition_id in {1, 2})
        _require(language is None or isinstance(language, LanguageAdapter) and _enum(language.mode, {"fixture", "openai"}))
    except (ValueError, TypeError, RecursionError, OverflowError, UnicodeError):
        raise ValueError("invalid_manifest") from None
    observer = _ObservedLanguage(language)
    report = {"case_id": case["id"], "repetition_id": repetition_id, "mode": observer.mode,
              "genuine_qualification": False, "passed": False, "failure": None,
              "halt_dispatch": False, "steps": [], "unrun_steps": [], "http": [],
              "language_calls": 0, "effects": {k: 0 for k in _COUNTS - {"language_calls"}},
              "assertions": {}}
    session, view, index, kind = None, None, None, None

    def audit(event):
        if (type(event) is dict and _enum(event.get("method"), {"GET", "POST"})
                and _enum(event.get("route"), _ROUTES)
                and (event.get("status") is None or type(event["status"]) is int and 100 <= event["status"] <= 599)):
            report["http"].append({k: event[k] for k in ("method", "route", "status")})
            if event["status"] is None:
                observer.failure = "effect_unknown" if event["method"] == "POST" else "scheduling_transport_unavailable"
        else:
            observer.failure = "observation_invalid"

    try:
        with TemporaryDirectory(prefix="connected-effects-", dir=effects_dir) as temporary, OwnedMock(port=0) as mock:
            api = HttpMockAdapter(mock.base_url, scenario=case["scenario"], event_sink=audit)
            session = SchedulingSession(api, journal_path=Path(temporary) / "effects.json")
            conversation = Conversation(session, observer)
            view = conversation.view()
            for index, step in enumerate(case["steps"]):
                observer.allow = step.get("dispatch", False)
                observer.observation = None
                observer.failure = None
                before = observer.calls
                prior_history = len(view["history"])
                failure = None
                kind = step["kind"]
                if kind == "text":
                    view = conversation.interpret(step["text"], view["revision"])
                    if (observer.calls - before) != int(step["dispatch"]):
                        failure = "dispatch_mismatch"
                elif kind == "identity":
                    # Partial synthetic drafts intentionally exercise real validation.
                    view = session.command("identity", step["data"], expected_revision=view["revision"])
                elif kind == "command":
                    view = session.command(step["action"], step["data"], expected_revision=view["revision"])
                elif kind == "scenario":
                    # A new HTTP client changes only the supplied local scenario header.
                    api = HttpMockAdapter(mock.base_url, scenario=step["scenario"], event_sink=audit)
                    session.api = api
                    view = conversation.view()
                elif not view.get("proposal") or not report["steps"] or report["steps"][-1]["type"] == "scenario":
                    failure = "missing_proposal"
                else:
                    proposal = view["proposal"]
                    view = conversation.confirm(proposal["id"], proposal["nonce"], expected_revision=view["revision"])
                failure = observer.failure or failure
                current = view["current_result"] or {}
                # Only a newly completed booking is verified, never an old receipt
                # observed during a later step/reset or a failed/uncertain attempt.
                if (kind == "confirm" and len(view["history"]) > prior_history
                        and current.get("kind") == "booking" and current.get("status") == "completed" and not failure):
                    try:
                        matches = api.appointments(session.identity["patientId"])
                        verified = sum(item == current["receipt"] for item in matches) == 1
                    except ApiError:
                        verified = False
                    report["effects"]["booking_verified"] += int(verified)
                    if not verified:
                        failure = "booking_verification_failed"
                failure = observer.failure or failure
                if current.get("status") in {"unknown", "attempted"} or view["state"] in {"unknown", "error"}:
                    failure = failure or "effect_unknown"
                assertions = _assertions(view, step["expect"])
                if not all(assertions.values()):
                    failure = failure or "expectation_mismatch"
                report["steps"].append({"index": index, "type": kind, **_projection(view),
                    "language": observer.observation, "assertions": assertions,
                    "passed": failure is None, "failure": failure})
                if failure:
                    report["failure"] = failure
                    report["unrun_steps"] = list(range(index + 1, len(case["steps"])))
                    break
    except Exception:
        # Startup, filesystem and cleanup errors are categorical; never dump paths,
        # response bodies, identity or exception messages into the evidence.
        report["failure"] = "harness_unavailable"
        if index is not None and len(report["steps"]) == index:
            report["steps"].append({"index": index, "type": kind, **(_projection(view) if view else {}),
                "language": observer.observation, "assertions": {}, "passed": False,
                "failure": "harness_unavailable"})
        report["unrun_steps"] = list(range(len(report["steps"]), len(case["steps"])))
    # Retain observed attempts even if verification, storage or cleanup failed.
    history = view["history"] if view is not None else []
    report["effects"].update({"post_attempts": sum(e["method"] == "POST" for e in report["http"]),
        "api_calls": len(report["http"]),
        "booking_completed": sum(r["kind"] == "booking" and r["status"] == "completed" for r in history),
        "handoff_queued": sum(r["kind"] == "handoff" and r["status"] == "queued" for r in history)})
    report["language_calls"] = observer.calls
    actual = {**report["effects"], "language_calls": observer.calls}
    report["assertions"] = {k: actual[k] == v for k, v in case["expected"].items()}
    if not all(report["assertions"].values()):
        report["failure"] = report["failure"] or "expectation_mismatch"
    report["halt_dispatch"] = report["failure"] not in {None, "expectation_mismatch", "dispatch_mismatch", "missing_proposal"}
    report["passed"] = report["failure"] is None
    report["genuine_qualification"] = (report["passed"] and observer.mode == "openai" and observer.calls > 0)
    return report
