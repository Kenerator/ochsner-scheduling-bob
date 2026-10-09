"""Standalone ZEN policy port; an allow never replaces core structural guards."""

from hashlib import sha256
from pathlib import Path

import zen


# Exact transport schema only. Permission rules live in the ZEN decision graph.
_FACTS = {
    "action": frozenset({"discover", "availability", "lookup", "booking", "handoff"}),
    "identity": frozenset({"verified", "missing", "ambiguous", "unknown"}),
    "proposal": frozenset({"current", "none"}),
    "confirmation": frozenset({"current", "none"}),
    "effect": frozenset({"clear", "blocked", "unknown"}),
}
_INVALID_REASON = "Supply exactly the five supported categorical facts."
_ENGINE_REASON = "Policy unavailable; action denied. Try again after policy recovery."


class Policy:
    """Load once and evaluate with actual zen-engine; failures grant no authority.

    The graph path is relative to the installed source, never the working
    directory. This supports the project's editable install. The exact loaded
    bytes are hashed once so later file changes cannot relabel a cached graph.
    """

    def __init__(self):
        self._decision = None
        self._digest = "unavailable"
        try:
            content = (Path(__file__).resolve().parents[2] / "policies" / "bob.json").read_bytes()
            self._digest = sha256(content).hexdigest()
            decision = zen.ZenEngine().create_decision(content.decode("utf-8"))
            decision.validate()
            self._decision = decision
        except Exception:
            # Load/compile errors are private; their details never enter traces.
            pass

    def _result(self, allow: bool, reason: str, rule: str) -> dict:
        return {"allow": allow, "reason": reason, "rule": rule,
                "engine": "zen-engine", "policy_digest": self._digest}

    def evaluate(self, facts) -> dict:
        # Reject rather than coerce/default missing, extra or mistyped facts.
        if (type(facts) is not dict or set(facts) != set(_FACTS)
                or any(type(facts[key]) is not str or facts[key] not in values
                       for key, values in _FACTS.items())):
            return self._result(False, _INVALID_REASON, "invalid_facts")
        try:
            if self._decision is None:
                return self._result(False, _ENGINE_REASON, "engine_error")
            result = self._decision.evaluate(dict(facts))["result"]
            if (type(result) is not dict or set(result) != {"allow", "reason", "rule"}
                    or type(result["allow"]) is not bool
                    or any(type(result[key]) is not str or not result[key]
                           for key in ("reason", "rule"))):
                return self._result(False, _ENGINE_REASON, "engine_error")
            return self._result(result["allow"], result["reason"], result["rule"])
        except Exception:
            # Engine exceptions must not reveal input, paths or native details.
            return self._result(False, _ENGINE_REASON, "engine_error")
