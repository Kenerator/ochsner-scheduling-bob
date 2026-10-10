"""Bounded in-memory public diagnostics; never exact recording or authority."""
from copy import deepcopy
import math
from time import perf_counter

from .http_mock import ApiError, UnknownOutcome, _ERROR_CODES
from .language import _context, _REASONS


class ObservedAPI:
    """Observe validated adapter outcomes, not HTTP success codes alone."""
    def __init__(self, delegate, observer):
        self._delegate, self._observer = delegate, observer

    def __getattr__(self, name):
        method = getattr(self._delegate, name)
        if name not in {"providers", "search_patients", "availability", "appointments", "book", "handoff"}:
            return method

        def observe(value, error, started):
            try:
                self._observer(name, value, error, (perf_counter() - started) * 1000)
            except Exception:
                pass  # Diagnostics can never change scheduling certainty.

        def call(*args, **kwargs):
            started = perf_counter()
            try:
                result = method(*args, **kwargs)
            except Exception as error:
                observe(None, error, started)
                raise
            observe(result, None, started)
            return result
        return call


def latency(value):
    return round(min(value, 60000), 3) if type(value) in (int, float) and math.isfinite(value) and value >= 0 else 0


class Diagnostics:
    def __init__(self, limit=2000):
        self.limit = limit
        self.api_events = []
        self.model = None
        self.dropped = 0
        self.model_count = 0

    def api(self, method, value, error, elapsed):
        if len(self.api_events) >= self.limit:
            self.dropped += 1
            return
        rejected = {400, 409} if method in {"book", "handoff"} else {400, 404, 409}
        outcome = ("rejected" if isinstance(error, ApiError) and error.status in rejected
                   else "failed" if isinstance(error, ApiError) else "unknown") if error else (
                   "completed" if method in {"book", "handoff"} else "ok" if value else "empty")
        code = getattr(error, "code", None)
        self.api_events.append({"seq": len(self.api_events) + 1, "method": method,
            "outcome": outcome, "error": "none" if error is None else code if type(code) is str and code in _ERROR_CODES else "unexpected",
            "http_status": getattr(error, "status", None) if isinstance(error, (ApiError, UnknownOutcome)) else None,
            "latency_ms": latency(elapsed)})

    def language(self, *, context, status, accepted, rejected, application, revision, elapsed):
        if self.model_count >= self.limit:
            self.dropped += 1
            return
        self.model_count += 1
        # Late completions may be counted, but cannot replace newer evidence.
        if self.model is not None and revision < self.model["revision"]:
            return
        try:
            public = _context(context)
        except Exception:
            public = {}  # Never copy a malformed/unrestricted context.
        fields = {"specialty", "location", "start_date", "end_date", "structured_output"}
        self.model = {"turn": self.model_count, "revision": revision,
            "status": status if status in _REASONS else "invalid_output", "public_projection": public,
            "accepted_fields": sorted(set(accepted) & fields), "rejected_fields": sorted(set(rejected) & fields),
            "application": application if application in {"applied", "not_applied", "stale", "rejected", "clarification"} else "not_applied",
            "latency_ms": latency(elapsed), "text": "withheld_from_diagnostics"}

    def snapshot(self):
        return {"api_events": deepcopy(self.api_events), "model": deepcopy(self.model),
                "diagnostic_dropped": self.dropped}
