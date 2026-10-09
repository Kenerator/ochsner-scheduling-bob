"""Revisioned scheduling authority shared by CLI, patient and support views."""
from copy import deepcopy
from datetime import date
from pathlib import Path
from threading import RLock
from time import perf_counter, time
from uuid import uuid4
import re

from .http_mock import ApiError, UnknownOutcome
from .journal import EffectJournal
from .policy import Policy

SPECIALTIES = ("primary_care", "dermatology")
LOCATIONS = ("downtown", "uptown", "lakeside")
REASONS = ("user_requested", "identity_unclear", "unsupported_request", "medical_advice", "api_failure", "no_availability", "other")


class SchedulingSession:
    """All commands serialize here. Views and model output never execute effects."""
    def __init__(self, api, *, journal_path=None, session_id=None, policy=None, event_sink=None):
        self.api = api
        self.id = session_id or uuid4().hex
        self.journal = EffectJournal(Path(journal_path or ".bob-local/effects.json"))
        self.policy = policy or Policy()
        self._lock = RLock()
        self._sink = event_sink
        self.revision = 0
        self.identity = None
        self.identity_status = "missing"
        self._identity_input = {}
        self.preferences = {}
        self.providers = []
        self.slots = []
        self.appointment_results = []
        self.proposal = None
        self.current_result = None
        self.history = []
        self.events = []
        self.dropped_events = 0
        self.state = "start"
        self.message = "I am an AI scheduling assistant for synthetic data. Find providers, book, or look up appointments. Help is always available."
        self.takeover = False
        self.support_notes = []
        self.suggestions = []
        self.last_policy = None
        self.last_ack = None
        self.ack_at = None

    def _key(self, kind):
        return self.id + ":" + kind

    def _invalidate(self):
        self.proposal = None

    def _safe_state(self):
        return {"revision": self.revision, "state": self.state,
                "identity": self.identity_status, "proposal": bool(self.proposal),
                "provider_count": len(self.providers), "slot_count": len(self.slots),
                "appointment_count": len(self.appointment_results),
                "booking_certainty": (self.current_result or {}).get("status", "not_attempted"),
                "takeover": self.takeover}

    def _event(self, action, before, elapsed):
        # Closed metadata: no patient/slot ids, raw user input, exception or transcript.
        event = {"seq": self.revision, "action": action if action in {
            "identity", "preferences", "discover", "availability", "select", "confirm",
            "appointments", "help", "medical", "unsupported", "decline", "reset",
            "handoff", "takeover", "return", "invalid", "begin_input"} else "invalid",
            "before": before, "after": self._safe_state(), "latency_ms": round(elapsed, 3),
            "policy": deepcopy(self.last_policy)}
        if len(self.events) < 2000:
            self.events.append(event)
        else:
            self.dropped_events += 1
        if self._sink:
            try:
                self._sink(deepcopy(event))
            except Exception:
                self.dropped_events += 1

    def trace(self):
        with self._lock:
            return deepcopy(self.events)

    def view(self):
        with self._lock:
            return deepcopy({"session_id": self.id, "revision": self.revision,
                "state": self.state, "message": self.message,
                "identity_status": self.identity_status, "preferences": self.preferences,
                "providers": self.providers, "slots": self.slots,
                "appointments": self.appointment_results, "proposal": self.proposal,
                "current_result": self.current_result, "history": self.history,
                "booking_blocked": self.journal.blocked(self._key("booking")),
                "handoff_blocked": self.journal.blocked(self._key("handoff")),
                "takeover": self.takeover, "suggestions": self.suggestions,
                "support_notes": self.support_notes, "dropped_events": self.dropped_events,
                "reference": "BOB-" + self.id + "/step/" + str(self.revision) + "/branch/original"})

    def _guard(self, action, *, confirming=False):
        kind = "booking" if action == "booking" else "handoff"
        facts = {"action": action, "identity": "verified" if self.identity else self.identity_status,
                 "proposal": "current" if self.proposal else "none",
                 "confirmation": "current" if confirming else "none",
                 "effect": "blocked" if self.journal.blocked(self._key(kind)) else "clear"}
        self.last_policy = self.policy.evaluate(facts)
        if not self.last_policy.get("allow"):
            raise PermissionError("This action is paused by the scheduling policy.")
        # Engine allow never overrides structural authority.
        if action in {"availability", "lookup", "booking"} and not self.identity:
            raise PermissionError("Enter your synthetic phone and date of birth in the private identity controls.")
        if action == "booking" and (not self.proposal or not confirming):
            raise PermissionError("Select a current returned option and confirm its exact summary.")

    def command(self, action, data=None, *, expected_revision=None, actor="patient"):
        with self._lock:
            data = data or {}
            if type(expected_revision) is not int or expected_revision != self.revision:
                return {**self.view(), "message": "This screen is out of date. Review the current screen before acting.", "stale": True}
            if actor not in {"patient", "support"}:
                return {**self.view(), "message": "Unknown actor.", "stale": True}
            before = self._safe_state()
            started = perf_counter()
            old_proposal = deepcopy(self.proposal)
            self.last_policy = None
            self._invalidate()
            self.revision += 1
            try:
                if not isinstance(data, dict):
                    raise ValueError("Use a supported scheduling control.")
                # Safety and public switching are available even during local takeover.
                if self.takeover and action not in {"help", "medical", "unsupported", "return", "decline", "reset", "discover"} and actor == "patient":
                    raise PermissionError("Demo support currently has control. Return control to continue.")
                if actor == "support" and action in {"identity", "select", "confirm", "availability", "appointments"}:
                    raise PermissionError("Support can suggest preferences; the patient must accept and confirm.")
                if action == "identity":
                    self._identity(data)
                elif action in {"preferences", "discover"}:
                    self._preferences(data)
                    if action == "discover":
                        self._guard("discover")
                        self.providers = self.api.providers(self.preferences.get("specialty"), self.preferences.get("location"))
                        self.state = "providers"
                        self.message = "Choose a provider or refine your search." if self.providers else "No providers matched. Change your search or ask for help."
                elif action == "availability":
                    self._guard("availability")
                    if not self.preferences.get("specialty"):
                        raise ValueError("Choose Primary care or Dermatology first.")
                    self.slots = self.api.availability(self.identity["patientId"],
                        self.preferences["specialty"], self.preferences.get("location"),
                        self.preferences.get("start_date"), self.preferences.get("end_date"))
                    provider = self.preferences.get("provider_id")
                    if provider:
                        self.slots = [s for s in self.slots if s["providerId"] == provider]
                    self.state = "options"
                    self.message = "Choose one numbered option. This does not book it." if self.slots else "No appointments matched these preferences. Refine them or ask for help."
                elif action == "select":
                    self._guard("availability")
                    index = data.get("index")
                    if type(index) is not int or index < 1 or index > len(self.slots):
                        raise ValueError("Choose a number from the current appointment options.")
                    slot = deepcopy(self.slots[index - 1])
                    self.proposal = {"id": uuid4().hex, "nonce": uuid4().hex, "revision": self.revision, "slot": slot}
                    self.state = "proposal"
                    self.message = "Review this exact appointment. Use Confirm appointment in a separate step to book."
                elif action == "confirm":
                    if (not old_proposal or set(data) != {"proposal_id", "nonce"}
                            or data.get("proposal_id") != old_proposal["id"]
                            or data.get("nonce") != old_proposal["nonce"]
                            or old_proposal["revision"] != expected_revision):
                        raise PermissionError("That confirmation is no longer current. Request fresh options and review a new summary.")
                    self.proposal = old_proposal
                    self._guard("booking", confirming=True)
                    self._effect("booking", lambda: self.api.book(self.identity["patientId"], old_proposal["slot"]))
                elif action == "appointments":
                    self._guard("lookup")
                    self.appointment_results = self.api.appointments(self.identity["patientId"])
                    self.state = "appointments"
                    self.message = "Your current synthetic appointments are below." if self.appointment_results else "No existing appointments were found for the verified synthetic identity."
                elif action in {"help", "medical", "unsupported"}:
                    self.state = action
                    self.message = {"help": "I can prepare a mock handoff. No email is required. This browser demo does not provide basic-phone access or real staff contact.",
                        "medical": "I cannot give medical advice or triage. I can prepare a medical-advice handoff request.",
                        "unsupported": "That request is outside supported scheduling. I can prepare a handoff; rescheduling and cancellation are unavailable."}[action]
                elif action == "handoff":
                    reason = data.get("reason", "user_requested")
                    if reason not in REASONS or set(data) - {"reason"}:
                        raise ValueError("Choose a supported handoff reason.")
                    self._guard("handoff")
                    # Categorical current context only. No raw conversation or identity.
                    summary = f"Workflow={self.state}; identity={self.identity_status}; current_booking={(self.current_result or {}).get('status', 'not_attempted')}; prior_completed={sum(r['status']=='completed' for r in self.history)}; missing={'none' if self.identity else 'private_identity'}."
                    self._effect("handoff", lambda: self.api.handoff(reason, summary))
                elif action == "decline":
                    self.state = "declined"
                    self.message = "The pending proposal is cleared. Earlier completed or unknown attempts remain in the history; no cancellation was sent."
                elif action == "reset":
                    self.identity = None
                    self._identity_input = {}
                    self.identity_status = "missing"
                    self.slots = []
                    self.appointment_results = []
                    self.providers = []
                    self.preferences = {}
                    self.state = "start"
                    self.message = "Workflow reset. Receipts and unresolved write protection remain."
                elif action in {"takeover", "return"}:
                    self.takeover = action == "takeover"
                    self.message = "Local demo support has control." if self.takeover else "Control returned to the patient. Review fresh options before confirming."
                elif action == "begin_input":
                    self.message = "Interpreting public scheduling preferences."
                else:
                    raise ValueError("Use a supported scheduling action. Your other valid preferences are retained.")
            except (PermissionError, ValueError) as error:
                self.proposal = None
                self.message = str(error)
            except ApiError as error:
                self.proposal = None
                unavailable = error.status is None or error.status >= 500
                self.state = "outage" if unavailable else "rejected"
                self.message = "The scheduling API is unavailable. A handoff may also fail." if unavailable else "The API rejected the request. Review your information or ask for help."
            except UnknownOutcome:
                self.proposal = None
                self.state = "unknown"
                self.message = "The downstream outcome is unknown. Do not repeat the write."
            except Exception:
                self.proposal = None
                self.state = "error"
                self.message = "The operation could not be verified. Help remains available."
                # Unexpected failures are visible categorically, never raw exception text.
            finally:
                self._event(action, before, (perf_counter() - started) * 1000)
            return self.view()

    def _identity(self, data):
        self.identity = None
        self.identity_status = "missing"
        self.appointment_results = []
        self.slots = []
        # Corrections revoke authority even when the corrected field is invalid.
        merged = {**self._identity_input, **data}
        self._identity_input = {}
        if set(merged) - {"phone", "dob", "zip"}:
            raise ValueError("Identity must come from the private phone, birth date and ZIP controls.")
        phone, dob, zip_code = merged.get("phone", ""), merged.get("dob", ""), merged.get("zip", "")
        if not isinstance(phone, str) or not re.fullmatch(r"[0-9()+ -]{7,20}", phone):
            raise ValueError("Enter the synthetic phone in the private controls.")
        if not isinstance(dob, str) or date.fromisoformat(dob).isoformat() != dob:
            raise ValueError("Enter a calendar-valid birth date as YYYY-MM-DD.")
        if zip_code and (not isinstance(zip_code, str) or not re.fullmatch(r"[0-9]{5}", zip_code)):
            raise ValueError("Enter a five-digit ZIP in the private controls.")
        self._identity_input = merged
        matches = self.api.search_patients(phone, dob)
        if zip_code:
            matches = [p for p in matches if p["zipCode"] == zip_code]
        if len(matches) == 1:
            self.identity = deepcopy(matches[0])
            self.identity_status = "verified"
            self.state = "ready"
            self.message = "Synthetic identity matched. This is not production authentication."
        elif len(matches) > 1:
            self.identity_status = "ambiguous"
            self.state = "ambiguous"
            self.message = "More than one synthetic record matched. Enter your ZIP privately; candidate records are not shown."
        else:
            self.state = "identity_required"
            self.message = "No synthetic identity matched. Correct your private details or request help."

    def _preferences(self, data):
        if set(data) - {"specialty", "location", "start_date", "end_date", "provider_id"}:
            raise ValueError("Only supported public scheduling preferences can be changed.")
        merged = {**self.preferences, **data}
        for key, allowed in (("specialty", SPECIALTIES), ("location", LOCATIONS)):
            value = merged.get(key)
            if value is not None and value not in allowed:
                from .suggestions import suggest
                self.suggestions = [{"field": key, "value": s} for s in suggest(str(value), allowed)]
                raise ValueError("That preference is unsupported. Select a suggestion explicitly or ask for help.")
        for key in ("start_date", "end_date"):
            value = merged.get(key)
            if value is not None and (not isinstance(value, str) or date.fromisoformat(value).isoformat() != value):
                raise ValueError("Use a calendar-valid date as YYYY-MM-DD.")
        if merged.get("start_date") and merged.get("end_date") and merged["start_date"] > merged["end_date"]:
            raise ValueError("The start date must be on or before the end date. The previous valid range is retained.")
        provider = merged.get("provider_id")
        if provider and provider not in {p["providerId"] for p in self.providers}:
            raise ValueError("Select a provider from the current returned providers, or clear the provider filter.")
        self.preferences = {k: v for k, v in merged.items() if v is not None}
        self.slots = []
        self.suggestions = []
        self.state = "preferences"
        self.message = "Preferences updated. Find providers or request current availability."

    def _effect(self, kind, operation):
        key = self._key(kind)
        # Journal fsync completes before any POST. Confirmation is gone before I/O.
        claim = self.journal.claim(key)
        self.proposal = None
        receipt = {"kind": kind, "status": "attempted", "reference": uuid4().hex}
        self.current_result = receipt
        try:
            payload = operation()
        except ApiError as error:
            status = "rejected" if error.status in {400, 409} else "failed"
            self.journal.finish(key, claim, status)
            receipt = {**receipt, "status": status, "http_status": error.status}
            self.message = "The slot was taken. Request new options and confirm a new summary." if error.status == 409 else "The API did not accept this request. Help remains available."
        except Exception:
            # Any possibly submitted write without a validated receipt stays unknown.
            self.journal.finish(key, claim, "unknown")
            receipt = {**receipt, "status": "unknown"}
            self.message = "The write outcome is unknown. It may have succeeded; automatic retry and reset-based retry are blocked."
        else:
            self.journal.finish(key, claim, "completed")
            receipt = {**receipt, "status": "completed" if kind == "booking" else "queued", "receipt": deepcopy(payload)}
            self.message = "The synthetic appointment was booked." if kind == "booking" else "The mock queue receipt was validated. This does not mean a real employee received it or joined."
        self.current_result = deepcopy(receipt)
        self.history.append(deepcopy(receipt))
        self.state = receipt["status"]
        if kind == "booking":
            self.slots = []

    def acknowledge(self, view_receipt):
        """Only semantic browser receipts are mirrored; they confer no authority."""
        with self._lock:
            if not isinstance(view_receipt, dict) or set(view_receipt) - {"revision", "renderer", "visible", "draft", "focus", "scroll", "expanded"}:
                raise ValueError("Invalid view acknowledgement.")
            if view_receipt.get("revision") != self.revision or view_receipt.get("renderer") != "bob-v1":
                raise ValueError("Outdated renderer acknowledgement.")
            import json
            if len(json.dumps(view_receipt)) > 16000:
                raise ValueError("View acknowledgement is too large.")
            self.last_ack = deepcopy(view_receipt)
            self.ack_at = time()

    def support_view(self):
        with self._lock:
            return {"patient": self.view(), "last_observed": deepcopy(self.last_ack),
                    "age_seconds": None if self.ack_at is None else round(time() - self.ack_at, 2),
                    "fresh": bool(self.last_ack and self.last_ack["revision"] == self.revision and time() - self.ack_at < 5),
                    "known": ["synthetic identity verified"] if self.identity else [],
                    "missing": [] if self.identity else ["private identity"],
                    "uncertain": ["booking"] if self.journal.blocked(self._key("booking")) else [],
                    "demo_support": "joined" if self.takeover else "not_joined"}
