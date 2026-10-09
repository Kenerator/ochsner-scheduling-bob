"""Bounded adapter contracts. Model output cannot become domain authority."""


def parse_language_output(value):
    allowed = {"intent", "specialty", "location", "date_range", "help", "unsupported"}
    if not isinstance(value, dict) or set(value) - allowed:
        raise ValueError("language output contains authority-bearing or unknown fields")
    return dict(value)


def policy_decision(facts):
    allowed = {"identity_verified", "proposal_current", "confirmation_current", "medical_request"}
    if set(facts) - allowed or any(value not in {True, False, "unknown"} for value in facts.values()):
        return {"allow": False, "reason": "invalid_or_unknown_facts", "provenance": "standalone-policy"}
    if facts.get("medical_request") is True:
        return {"allow": False, "reason": "medical_boundary", "provenance": "standalone-policy"}
    allow = all(facts.get(key) is True for key in ("identity_verified", "proposal_current", "confirmation_current"))
    return {"allow": allow, "reason": "all_guards_satisfied" if allow else "guard_failed", "provenance": "standalone-policy"}
