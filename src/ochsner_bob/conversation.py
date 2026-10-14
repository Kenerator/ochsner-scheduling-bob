"""Shared text orchestration; all identity, policy, consent and effects stay in session.

interpret(text, expected_revision) returns a session view plus categorical
interpretation metadata. Identity and confirmation are separate local controls.
Offline mode accepts explicit commands; it never impersonates model interpretation.
"""

from datetime import date
from contextlib import nullcontext
import re
import unicodedata
from time import perf_counter

from .language import ACTIONS, LOCATIONS, SPECIALTIES, LanguageAdapter, LanguageOutcome


_PREFERENCES = {"specialty", "location", "start_date", "end_date"}
_NOTICE = {
    "private_input": "Use the private identity controls for phone, birth date and ZIP. Help and Medical remain available.",
    "invalid_input": "Use a short public scheduling request or a supported offline command. Help remains available.",
    "clarification": "Use providers, availability, appointments, provider NUMBER, dates START END, or Help. Booking needs the separate confirmation control.",
    "invalid_output": "Language interpretation was invalid. No proposed action was applied. Use local controls or Help.",
    "disabled": "Model interpretation is disabled. Use explicit offline commands or Help; no model fallback was used.",
    "unavailable": "Language interpretation is unavailable. No proposed action was applied. Use local controls or Help.",
    "timeout": "Language interpretation timed out. Review fresh options before confirming; Help remains available.",
    "refused": "Language interpretation was refused. Use local controls or Help.",
    "invalid_context": "Public interpretation context is unavailable. Use local controls or Help.",
    "budget_exceeded": "Model accounting or pre-dispatch validation is unavailable. No model request was sent. Use local controls or Help.",
    "accounting_failed": "Model accounting could not be verified. No proposed action was applied. Use local controls or Help.",
}
_MEDICAL = re.compile(r"\b(?:medical advice|chest pain|symptoms?|diagnos\w*|triage|medication|prescription)\b|\bshould I wait\b", re.I)
_HELP = re.compile(r"\b(?:help|human|agent|staff|support)\b", re.I)
_UNSUPPORTED = re.compile(r"\b(?:reschedul\w*|cancel (?:my |the )?appointment)\b", re.I)


def _calendar(value):
    valid = False
    if type(value) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            valid = date.fromisoformat(value).isoformat() == value
        except ValueError:
            pass
    return valid


class Conversation:
    """Optional language proposes public actions; it never sees private controls.

    The returned safe notice is presentation data. view() retains it only for its
    current session revision; foreign commands cannot inherit an old notice.
    Model results always apply against the revision captured BEFORE the model wait.
    """

    def __init__(self, session, language=None, *, diagnostic_sink=None):
        self.session = session
        self.language = language
        self._diagnostic_sink = diagnostic_sink
        # Reuse the bounded adapter's privacy/input gate with runtime opt-in absent.
        # This gate cannot call a model, even if the host environment enables one.
        self._privacy = LanguageAdapter(environ={})
        self._presentation = None

    def _decorate(self, view, mode="offline", status="ok"):
        view["interpretation"] = {"mode": mode, "status": status}
        notice = _NOTICE.get(status)
        if notice and not view.get("stale"):
            view["message"] = notice
        if not view.get("stale"):
            self._presentation = (view["revision"], mode, status)
        return view

    def _publication(self):
        return nullcontext()

    def view(self):
        view = self.session.view()
        if self._presentation and self._presentation[0] == view["revision"]:
            return self._decorate(view, *self._presentation[1:])
        return self._decorate(view)

    def enter_identity(self, phone, dob, zip_code=None, *, expected_revision):
        """Local user controls only; never call language or infer identity from chat."""
        data = {"phone": phone, "dob": dob}
        if zip_code is not None:
            data["zip"] = zip_code
        return self._decorate(self.session.command("identity", data, expected_revision=expected_revision))

    def confirm(self, proposal_id, nonce, *, expected_revision):
        """Submit the previously rendered exact snapshot, never fetch fresh authority."""
        return self._decorate(self.session.command("confirm", {"proposal_id": proposal_id, "nonce": nonce},
                                                    expected_revision=expected_revision))

    def _local(self, text, view):
        words = text.casefold().strip().removeprefix("/").split()
        if not words:
            return None
        command, values = words[0], words[1:]
        if command in {"availability", "appointments", "decline", "reset", "medical", "unsupported"} and not values:
            return command, {}
        if command in {"providers", "discover"}:
            if len(values) > 2:
                return "invalid", {}
            data = dict(zip(("specialty", "location"), values))
            return "discover", data
        if command in {"specialty", "location"} and len(values) == 1:
            return "preferences", {command: None if values[0] == "clear" else values[0]}
        if command == "provider" and len(values) == 1:
            if values[0] == "clear":
                return "preferences", {"provider_id": None}
            if values[0].isascii() and values[0].isdigit():
                index = int(values[0])
                if 1 <= index <= len(view["providers"]):
                    return "preferences", {"provider_id": view["providers"][index - 1]["providerId"]}
            return "invalid", {}
        if command in {"start", "end"} and len(values) == 1:
            value = None if values[0] == "clear" else values[0]
            return ("preferences", {command + "_date": value}) if value is None or _calendar(value) else ("invalid", {})
        if command == "dates" and len(values) == 2:
            if all(_calendar(value) for value in values):
                return "preferences", dict(zip(("start_date", "end_date"), values))
            return "invalid", {}
        if command == "clear" and len(values) == 1:
            key = {"provider": "provider_id", "start": "start_date", "end": "end_date"}.get(values[0], values[0])
            if key == "dates":
                return "preferences", {"start_date": None, "end_date": None}
            if key in _PREFERENCES | {"provider_id"}:
                return "preferences", {key: None}
            return "invalid", {}
        if command == "handoff" and len(values) <= 1:
            return "handoff", {"reason": values[0] if values else "user_requested"}
        if command == "select" and len(values) == 1 and values[0].isascii() and values[0].isdigit():
            return "select", {"index": int(values[0])}
        # Longer bare digit strings may be private phone/ZIP input, not choices.
        if len(words) == 1 and len(command) <= 2 and command.isascii() and command.isdigit():
            return "select", {"index": int(command)}
        return None

    @staticmethod
    def _proposal(outcome):
        if (not isinstance(outcome, LanguageOutcome) or type(outcome.mode) is not str
                or outcome.mode not in {"fixture", "openai"} or type(outcome.action) is not str
                or outcome.action not in ACTIONS or type(outcome.preferences) is not dict
                or set(outcome.preferences) - _PREFERENCES):
            return False
        for key, value in outcome.preferences.items():
            if type(value) is not str:
                return False
            if key == "specialty" and value not in SPECIALTIES:
                return False
            if key == "location" and value not in LOCATIONS:
                return False
            if key.endswith("_date") and not _calendar(value):
                return False
        return True

    def interpret(self, text, expected_revision):
        """Public text only. Stale input and delayed model output have no authority."""
        initial = self.session.view()
        if type(expected_revision) is not int or expected_revision != initial["revision"]:
            return self._decorate(self.session.command("begin_input", expected_revision=expected_revision), status="stale")
        if (type(text) is not str or not text.strip() or len(text) > 2048
                or any(unicodedata.category(c) in {"Cc", "Cs", "Cf"} and c not in "\n\t" for c in text)
                or len(text.encode("utf-8")) > 2048):
            return self._decorate(self.session.command("begin_input", expected_revision=expected_revision), status="invalid_input")
        # Local boundary/help routing precedes privacy rejection and all model work.
        safety = "medical" if _MEDICAL.search(text) else "help" if _HELP.search(text) else "unsupported" if _UNSUPPORTED.search(text) else None
        if safety:
            return self._decorate(self.session.command(safety, expected_revision=expected_revision))
        local = self._local(text, initial)
        if local:
            action, data = local
            result = self.session.command(action, data, expected_revision=expected_revision)
            return self._decorate(result, status="invalid_input" if action == "invalid" else "ok")
        gate = self._privacy.interpret(text)
        if gate.status in {"private_input", "invalid_input"}:
            return self._decorate(self.session.command("begin_input", expected_revision=expected_revision), status=gate.status)
        # Every ordinary turn (including yes, malformed output and failures) first
        # revokes the old proposal. Only confirm() can take the consent shortcut.
        prepared = self.session.command("begin_input", expected_revision=expected_revision)
        if prepared.get("stale"):
            return self._decorate(prepared, status="stale")
        revision = prepared["revision"]
        if self.language is None:
            return self._decorate(prepared, status="clarification")
        mode = "openai" if getattr(self.language, "mode", None) == "openai" else "fixture"
        workflow = prepared["state"]
        if workflow in {"ready", "ambiguous", "identity_required"}:
            workflow = "identity"
        elif workflow in {"outage", "failed"}:
            workflow = "error"
        elif workflow in {"medical", "unsupported", "declined", "queued"}:
            workflow = "help"
        elif workflow == "preferences":
            # A correction is public scheduling context, not a language workflow.
            workflow = "start"
        context = {"workflow": workflow, "preferences": {k: v for k, v in prepared["preferences"].items() if k in _PREFERENCES}}
        started = perf_counter()
        try:
            outcome = self.language.interpret(text, context)
        except Exception:
            outcome = None
        model_elapsed = (perf_counter() - started) * 1000

        def publish(view, status="ok", application="not_applied"):
            with self._publication():
                return publish_locked(view, status, application)

        def publish_locked(view, status, application):
            result = self._decorate(view, mode, status)
            valid = isinstance(outcome, LanguageOutcome) and self._proposal(outcome)
            fields = list(outcome.preferences) if valid else []
            model_status = outcome.status if isinstance(outcome, LanguageOutcome) and type(outcome.status) is str else "unavailable"
            if result.get("stale"):
                application = "stale"
            if self._diagnostic_sink:
                try:
                    self._diagnostic_sink(context=context, status=model_status,
                        accepted=fields if application == "applied" else [],
                        rejected=["structured_output"] if not valid and status == "invalid_output" else
                            fields if application in {"rejected", "stale"} else
                            ["structured_output"] if model_status in {"invalid_output", "clarification"} else [],
                        application=application, revision=revision, elapsed=model_elapsed)
                except Exception:
                    pass  # Diagnostics cannot turn a validated effect into failure.
            return result

        if self.session.revision != revision:
            return publish(self.session.command("begin_input", expected_revision=revision), "stale", "stale")
        if outcome is None:
            return publish(prepared, "unavailable")
        if not isinstance(outcome, LanguageOutcome):
            return publish(prepared, "invalid_output")
        if type(outcome.status) is not str:
            return publish(prepared, "invalid_output")
        if outcome.status != "ok":
            return publish(prepared, outcome.status if outcome.status in _NOTICE else "invalid_output")
        if not self._proposal(outcome):
            return publish(prepared, "invalid_output", "rejected")
        if outcome.action == "clarify":
            return publish(prepared, "clarification", "clarification")
        if outcome.preferences:
            desired = {**prepared["preferences"], **outcome.preferences}
            changed = self.session.command("preferences", outcome.preferences, expected_revision=revision)
            if changed.get("stale") or changed["preferences"] != desired or changed["state"] != "preferences":
                return publish(changed, application="rejected")
            prepared, revision = changed, changed["revision"]
        if outcome.action == "preferences":
            return publish(prepared, application="applied")
        return publish(self.session.command(outcome.action, expected_revision=revision), application="applied")
