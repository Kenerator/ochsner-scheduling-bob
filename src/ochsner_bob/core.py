"""Small deterministic scheduling core; adapters are intentionally replaceable."""

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any
from uuid import uuid4


class UnknownOutcome(RuntimeError):
    pass


@dataclass(frozen=True)
class Receipt:
    kind: str
    status: str
    detail: str
    id: str


class MockSchedulingApi:
    """Owned synthetic boundary used by tests and the local demo."""

    def __init__(self):
        self.bookings: list[dict[str, Any]] = []
        self.next_booking: Exception | None = None
        self.next_handoff: Exception | None = None

    def providers(self, specialty: str, location: str):
        if specialty.lower() not in {"cardio", "cardiology"}:
            return []
        return [{"id": "provider-1", "name": "Ochsner Cardiology", "location": location}]

    def slots(self, provider_id: str):
        if provider_id != "provider-1":
            return []
        return [{"id": "slot-1", "provider_id": provider_id, "startTime": "2026-10-20T09:00:00-05:00"}]

    def find_identity(self, phone: str, dob: str, zip_code: str):
        if (phone, dob) == ("5045550100", "1980-01-01") and zip_code in {"70112", "70113"}:
            return {"fixture_id": "patient-1", "phone": phone, "dob": dob, "zip": zip_code}
        return None

    def appointments(self, fixture_id: str):
        return [] if fixture_id == "patient-1" else []

    def book(self, fixture_id: str, slot: dict[str, Any]):
        if self.next_booking:
            error, self.next_booking = self.next_booking, None
            raise error
        receipt = {"fixture_id": fixture_id, "slot_id": slot["id"]}
        self.bookings.append(receipt)
        return receipt

    def handoff(self, reason: str):
        if self.next_handoff:
            error, self.next_handoff = self.next_handoff, None
            raise error
        return {"receipt": "handoff-1", "reason": reason, "status": "queued"}


class BobSession:
    def __init__(self, api: MockSchedulingApi):
        self.api = api
        self.identity = None
        self.providers = []
        self.slots = []
        self.proposal = None
        self.confirmed = None
        self.unknown = False
        self.events: list[dict[str, Any]] = []

    def _event(self, kind: str, **data):
        safe = {"kind": kind, "at": datetime.now(timezone.utc).isoformat(), **data}
        self.events.append(safe)
        return safe

    def discover(self, specialty: str, location: str):
        self.providers = self.api.providers(specialty, location)
        self._event("public_discovery", count=len(self.providers))
        return list(self.providers)

    def find_slots(self, provider_id: str):
        self.slots = self.api.slots(provider_id)
        self.proposal = None
        self.confirmed = None
        return list(self.slots)

    def resolve_identity(self, phone: str, dob: str, zip_code: str):
        self.identity = None
        self.proposal = None
        self.confirmed = None
        self.slots = []
        match = self.api.find_identity(phone, dob, zip_code)
        if not match:
            self.identity = None
            self._event("identity_no_match")
            return None
        self.identity = match
        self._event("identity_verified")
        return dict(match)

    def correct_identity(self, phone: str, dob: str, zip_code: str):
        self.identity = None
        self.proposal = None
        self.confirmed = None
        self.slots = []
        self._event("identity_revoked")
        return self.resolve_identity(phone, dob, zip_code)

    def appointments(self):
        if not self.identity:
            return []
        return self.api.appointments(self.identity["fixture_id"])

    def propose(self, slot_id: str):
        slot = next((item for item in self.slots if item["id"] == slot_id), None)
        if slot is None:
            self.proposal = None
            self.confirmed = None
            raise ValueError("select an option returned by availability")
        self.proposal = {"id": str(uuid4()), "slot": dict(slot)}
        self.confirmed = None
        self._event("proposal_created", proposal_id=self.proposal["id"])
        return dict(self.proposal)

    def confirm(self, proposal_id: str):
        if not self.proposal or self.proposal["id"] != proposal_id:
            raise ValueError("proposal is not current")
        self.confirmed = proposal_id
        self._event("confirmation_consumed", proposal_id=proposal_id)

    def book(self):
        if self.unknown:
            raise RuntimeError("unknown booking outcome requires reconciliation")
        if not self.identity or not self.proposal or self.confirmed != self.proposal["id"]:
            raise PermissionError("current identity, proposal, and confirmation are required")
        proposal = self.proposal
        self.proposal = None
        self.confirmed = None
        try:
            result = self.api.book(self.identity["fixture_id"], proposal["slot"])
        except UnknownOutcome as error:
            self.unknown = True
            self._event("booking_unknown")
            return Receipt("booking", "unknown", str(error), str(uuid4()))
        self._event("booking_completed")
        return Receipt("booking", "completed", str(result), str(uuid4()))

    def help(self):
        self._event("help_available")
        return {"kind": "human_help", "status": "available"}

    def handoff(self, reason: str):
        try:
            result = self.api.handoff(reason)
        except UnknownOutcome as error:
            self._event("handoff_unknown")
            return Receipt("handoff", "unknown", str(error), str(uuid4()))
        self._event("handoff_queued")
        return Receipt("handoff", "queued", str(result), str(uuid4()))
