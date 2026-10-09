"""Strict client for the supplied synthetic service, independent of domain authority.

The caller owns identity, confirmation and durable effect claims. This adapter never
retries and only a matching, validated 201 establishes a completed write.
"""

from datetime import date, datetime
from http.client import HTTPConnection, HTTPException
import json
import math
import re
import socket
from threading import Timer
from time import monotonic
from urllib.parse import urlencode


_MAX_BYTES = 256_000
_SPECIALTIES = {"primary_care", "dermatology"}
_LOCATIONS = {"downtown", "uptown", "lakeside"}
_REASONS = {"user_requested", "identity_unclear", "unsupported_request", "medical_advice",
            "api_failure", "no_availability", "other"}
_SCENARIOS = {"happy_path_booking", "provider_lookup", "no_patient_match", "multiple_patient_matches",
              "slot_conflict", "no_availability", "api_failure", "unsupported_request"}
_ERROR_CODES = {"invalid_request", "invalid_response", "transport_error", "unknown_outcome",
                "missing_parameter", "invalid_parameter", "invalid_json", "unknown_patient",
                "unknown_slot", "confirmation_required", "slot_taken", "patient_not_found",
                "downstream_unavailable"}


class ApiError(RuntimeError):
    """Only categorical status/code are retained, never service messages or URLs."""

    def __init__(self, status=None, code="invalid_response"):
        self.status = status if type(status) is int and 100 <= status <= 599 else None
        self.code = code if type(code) is str and code in _ERROR_CODES else "invalid_response"
        super().__init__(f"Scheduling API {self.code} (status {self.status})")


class UnknownOutcome(RuntimeError):
    """A write may have succeeded. Reconciliation is required before another attempt."""

    def __init__(self, status=None):
        # Keep separate from ApiError so a definite-failure handler cannot catch it.
        self.status = status if type(status) is int and 100 <= status <= 599 else None
        self.code = "unknown_outcome"
        super().__init__(f"Scheduling API {self.code} (status {self.status}); do not retry")


def _text(value, limit=4096):
    # Reject lone JSON surrogates before they can reach URL encoding or consumers.
    return type(value) is str and 0 < len(value) <= limit and not any(
        ord(c) < 32 or 0xD800 <= ord(c) <= 0xDFFF for c in value
    )


def _identifier(value):
    return type(value) is str and re.fullmatch(r"[A-Za-z0-9_-]{1,128}", value) is not None


def _day(value):
    valid = False
    if type(value) is str and re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", value):
        try:
            date.fromisoformat(value)
            valid = True
        except ValueError:
            pass
    return valid


def _timestamp(value):
    valid = False
    if type(value) is str and len(value) <= 64 and re.fullmatch(
        r"[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}(?:\.[0-9]{1,6})?(?:Z|[+-](?:[01][0-9]|2[0-3]):[0-5][0-9])", value
    ):
        try:
            parsed = datetime.fromisoformat(value)
            valid = parsed.utcoffset() is not None
        except ValueError:
            pass
    return valid


def _enum(allowed):
    return lambda value: type(value) is str and value in allowed


def _array(check):
    return lambda value: type(value) is list and len(value) <= 2000 and all(check(v) for v in value)


def _object(value, fields):
    return type(value) is dict and value.keys() == fields.keys() and all(check(value[key]) for key, check in fields.items())


_PATIENT = {"patientId": _identifier, "firstName": _text, "lastName": _text, "dateOfBirth": _day,
            "phone": lambda v: _text(v, 128), "zipCode": lambda v: type(v) is str and re.fullmatch(r"[0-9]{5}", v) is not None,
            "establishedPatient": lambda v: type(v) is bool}
_PROVIDER = {"providerId": _identifier, "name": _text, "specialty": _enum(_SPECIALTIES),
             "locations": _array(_enum(_LOCATIONS)), "modalities": _array(_text)}
_SLOT = {"slotId": _identifier, "providerId": _identifier, "specialty": _enum(_SPECIALTIES),
         "location": _enum(_LOCATIONS), "startTime": _timestamp, "available": lambda v: v is True}
_APPOINTMENT = {"appointmentId": _identifier, "patientId": _identifier, "providerId": _identifier,
                "specialty": _enum(_SPECIALTIES), "location": _enum(_LOCATIONS),
                "startTime": _timestamp, "status": lambda v: v == "scheduled"}
_HANDOFF = {"handoffId": _identifier, "status": lambda v: v == "queued"}


def _unique_object(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate JSON key")
        result[key] = value
    return result


def _nonfinite(_value):
    raise ValueError("nonfinite JSON number")


def _abort(sock):
    # A socket timeout alone can be extended indefinitely by trickling bytes.
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except OSError:
        pass


class HttpMockAdapter:
    """Loopback-only supplied API port; optional sink receives four safe fields."""

    def __init__(self, base_url, scenario=None, timeout=2, *, event_sink=None):
        match = re.fullmatch(r"http://127\.0\.0\.1:([0-9]{1,5})/?", base_url) if type(base_url) is str else None
        if match is None or not 1 <= int(match[1]) <= 65535:
            raise ValueError("Expected an owned http://127.0.0.1:numeric-port origin")
        if type(timeout) not in (int, float) or not math.isfinite(timeout) or not 0 < timeout <= 60:
            raise ValueError("Expected a finite timeout in (0, 60] seconds")
        if scenario is not None and (type(scenario) is not str or scenario not in _SCENARIOS):
            raise ValueError("Unsupported mock scenario")
        if event_sink is not None and not callable(event_sink):
            raise ValueError("Expected a callable event sink")
        self._port = int(match[1])
        self._timeout = float(timeout)
        self._scenario = scenario
        self._event_sink = event_sink

    def _wire(self, method, path, body):
        """Return categorical failure instead of chaining raw transport exceptions."""
        status, document, failure = None, None, "transport_error"
        started = monotonic()
        connection = HTTPConnection("127.0.0.1", self._port, timeout=self._timeout)
        watchdog = None
        try:
            # Direct HTTPConnection ignores environment proxies and never redirects.
            connection.connect()
            remaining = self._timeout - (monotonic() - started)
            if remaining <= 0:
                return status, document, failure
            watchdog = Timer(remaining, _abort, args=(connection.sock,))
            watchdog.daemon = True
            watchdog.start()
            headers = {"Accept": "application/json", "Connection": "close"}
            if body is not None:
                headers["Content-Type"] = "application/json"
            if self._scenario is not None:
                headers["X-Mock-Scenario"] = self._scenario
            connection.request(method, path, body=body, headers=headers)
            response = connection.getresponse()
            status = response.status
            failure = "invalid_response"
            lengths = response.headers.get_all("Content-Length", [])
            transfers = response.headers.get_all("Transfer-Encoding", [])
            content_types = response.headers.get_all("Content-Type", [])
            if (len(content_types) != 1 or content_types[0].split(";")[0].strip().lower() != "application/json"
                    or response.getheader("Content-Encoding", "identity").lower() != "identity"
                    or len(lengths) > 1 or len(transfers) > 1 or (lengths and transfers)
                    or (transfers and transfers[0].lower() != "chunked")):
                return status, document, failure
            length = None
            if lengths:
                if not re.fullmatch(r"[0-9]{1,9}", lengths[0]) or int(lengths[0]) > _MAX_BYTES:
                    return status, document, failure
                length = int(lengths[0])
            raw = response.read(_MAX_BYTES + 1)
            if len(raw) > _MAX_BYTES or (length is not None and len(raw) != length) or monotonic() - started >= self._timeout:
                return status, document, failure
            document = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_object, parse_constant=_nonfinite)
            failure = None
        except (OSError, HTTPException, ValueError, RecursionError):
            # Never retain raw errors: URLs, bodies and messages can contain identity.
            pass
        finally:
            if watchdog is not None:
                watchdog.cancel()
                watchdog.join()
            connection.close()
        return status, document, failure

    def _call(self, method, route, *, path=None, query=None, payload=None, validate):
        body = None if payload is None else json.dumps(payload, allow_nan=False).encode("utf-8")
        if body is not None and len(body) > _MAX_BYTES:
            raise ApiError(code="invalid_request")
        target = path or route
        if query:
            target += "?" + urlencode({k: v for k, v in query.items() if v is not None})
        started = monotonic()
        status, document, failure = self._wire(method, target, body)
        if self._event_sink is not None:
            try:
                self._event_sink({"method": method, "route": route, "status": status,
                                  "latency_ms": round((monotonic() - started) * 1000, 3)})
            except Exception:
                # Diagnostics cannot turn a completed effect into a failed attempt.
                pass
        write = method == "POST"
        if failure is None and status == (201 if write else 200) and validate(document):
            return document
        if failure is None and _object(document, {"code": _text, "message": _text}):
            allowed = {503: {"downstream_unavailable"}}
            if route == "/appointments":
                allowed.update({400: {"missing_parameter", "invalid_json", "confirmation_required", "unknown_patient", "unknown_slot"},
                                409: {"slot_taken"}})
            elif route == "/handoffs":
                allowed[400] = {"missing_parameter", "invalid_parameter", "invalid_json"}
            elif route == "/patients/{patientId}/appointments":
                allowed[404] = {"patient_not_found"}
            else:
                allowed[400] = {"missing_parameter", "invalid_parameter", "unknown_patient"}
            if document["code"] in allowed.get(status, set()):
                raise ApiError(status, document["code"])
        if write:
            raise UnknownOutcome(status)
        raise ApiError(status, failure or "invalid_response")

    @staticmethod
    def _require(condition):
        if not condition:
            raise ApiError(code="invalid_request")

    def providers(self, specialty=None, location=None):
        self._require((specialty is None or _enum(_SPECIALTIES)(specialty)) and
                      (location is None or _enum(_LOCATIONS)(location)))
        def valid(doc):
            return _object(doc, {"providers": _array(lambda p: _object(p, _PROVIDER))}) and all(
                (specialty is None or p["specialty"] == specialty) and
                (location is None or location in p["locations"]) for p in doc["providers"])
        return self._call("GET", "/providers", query={"specialty": specialty, "location": location}, validate=valid)["providers"]

    def search_patients(self, phone, dob):
        self._require(_text(phone, 128) and _day(dob))
        def valid(doc):
            return _object(doc, {"matches": _array(lambda p: _object(p, _PATIENT))}) and all(
                p["phone"] == phone and p["dateOfBirth"] == dob for p in doc["matches"])
        return self._call("GET", "/patients/search", query={"phone": phone, "dob": dob}, validate=valid)["matches"]

    def availability(self, patient_id, specialty, location=None, start_date=None, end_date=None):
        self._require(_identifier(patient_id) and _enum(_SPECIALTIES)(specialty) and
                      (location is None or _enum(_LOCATIONS)(location)) and
                      (start_date is None or _day(start_date)) and (end_date is None or _day(end_date)) and
                      (start_date is None or end_date is None or start_date <= end_date))
        def valid(doc):
            return _object(doc, {"slots": _array(lambda s: _object(s, _SLOT))}) and all(
                s["specialty"] == specialty and (location is None or s["location"] == location) and
                (start_date is None or s["startTime"][:10] >= start_date) and
                (end_date is None or s["startTime"][:10] <= end_date) for s in doc["slots"])
        return self._call("GET", "/availability", query={"patientId": patient_id, "specialty": specialty,
                          "location": location, "startDate": start_date, "endDate": end_date}, validate=valid)["slots"]

    def appointments(self, patient_id):
        self._require(_identifier(patient_id))
        def valid(doc):
            return _object(doc, {"appointments": _array(lambda a: _object(a, _APPOINTMENT))}) and all(
                a["patientId"] == patient_id for a in doc["appointments"])
        return self._call("GET", "/patients/{patientId}/appointments",
                          path=f"/patients/{patient_id}/appointments", validate=valid)["appointments"]

    def book(self, patient_id, slot: dict):
        self._require(_identifier(patient_id) and _object(slot, _SLOT))
        # Snapshot before I/O so later mutation cannot change receipt matching.
        submitted = dict(slot)
        def valid(doc):
            return _object(doc, {"appointment": lambda a: _object(a, _APPOINTMENT)}) and (
                doc["appointment"]["patientId"] == patient_id and all(
                    doc["appointment"][key] == submitted[key] for key in ("providerId", "specialty", "location", "startTime")))
        return self._call("POST", "/appointments", payload={"patientId": patient_id, "slotId": submitted["slotId"],
                          "confirmed": True}, validate=valid)["appointment"]

    def handoff(self, reason, summary):
        self._require(_enum(_REASONS)(reason) and _text(summary))
        return self._call("POST", "/handoffs", payload={"reason": reason, "summary": summary},
                          validate=lambda doc: _object(doc, _HANDOFF))
