"""Catch unsafe destinations, unvalidated API facts, hidden retries and false receipts."""

import json
import os
import time
import unittest
from unittest.mock import patch

from ochsner_bob import http_mock
from http_support import HostileServer, supplied_server


SLOT = {"slotId": "slot_4001", "providerId": "prov_2001", "specialty": "primary_care",
        "location": "downtown", "startTime": "2026-10-16T09:00:00-05:00", "available": True}
APPOINTMENT = {"appointmentId": "appt_9002", "patientId": "pat_1001", "providerId": "prov_2001",
               "specialty": "primary_care", "location": "downtown",
               "startTime": "2026-10-16T09:00:00-05:00", "status": "scheduled"}
PATIENT = {"patientId": "pat_1001", "firstName": "Maya", "lastName": "Chen",
           "dateOfBirth": "1985-04-12", "phone": "555-0101", "zipCode": "70112", "establishedPatient": True}
PROVIDER = {"providerId": "prov_2001", "name": "Dr. Elena Brooks", "specialty": "primary_care",
            "locations": ["downtown", "uptown"], "modalities": ["in_person", "virtual"]}


class HttpAdapterTests(unittest.TestCase):
    def api(self, base_url, **kwargs):
        self.assertTrue(callable(getattr(http_mock.HttpMockAdapter, "providers", None)),
                        "unsafe sketch has no typed supplied-service API")
        return http_mock.HttpMockAdapter(base_url, **kwargs)

    def assert_safe_error(self, error):
        for value in ("pat_1001", "555-0101", "1985-04-12", "70112", "private-summary", "slot_4001"):
            self.assertNotIn(value, str(error))
            self.assertNotIn(value, repr(error))
        self.assertIsNone(error.__cause__)
        self.assertIsNone(error.__context__)

    def test_public_provider_lookup_uses_original_http_service(self):
        with supplied_server() as server:
            rows = self.api(server.base_url).providers("primary_care", "downtown")
            self.assertEqual([p["providerId"] for p in rows], ["prov_2001", "prov_2002"])
            self.assertEqual(server.wait_for_audits(1), [{"method": "GET", "route": "/providers", "status": 200}])

    def test_happy_booking_matches_exact_returned_slot_and_consumes_it(self):
        with supplied_server() as server:
            api = self.api(server.base_url)
            patient = api.search_patients("555-0101", "1985-04-12")[0]
            self.assertEqual(patient["patientId"], "pat_1001")
            slots = api.availability(patient["patientId"], "primary_care", "downtown")
            slot = next(s for s in slots if s["slotId"] == "slot_4001")
            receipt = api.book(patient["patientId"], slot)
            for key in ("providerId", "specialty", "location", "startTime"):
                self.assertEqual(receipt[key], slot[key])
            self.assertEqual(receipt["patientId"], "pat_1001")
            self.assertEqual(receipt["status"], "scheduled")
            self.assertIn(receipt, api.appointments("pat_1001"))
            self.assertNotIn(slot, api.availability("pat_1001", "primary_care", "downtown"))
            with self.assertRaises(http_mock.ApiError) as caught:
                api.book("pat_1001", slot)
            self.assertEqual((caught.exception.status, caught.exception.code), (409, "slot_taken"))
            self.assertEqual(len(server.wait_for_audits(6)), 6)

    def test_no_match_duplicate_match_no_availability_and_empty_history(self):
        with supplied_server() as server:
            api = self.api(server.base_url)
            self.assertEqual(api.search_patients("555-9999", "1990-01-01"), [])
            matches = api.search_patients("555-0130", "1978-09-22")
            self.assertEqual([p["patientId"] for p in matches], ["pat_1003", "pat_1004"])
            self.assertEqual({p["zipCode"] for p in matches}, {"70115", "70005"})
            self.assertEqual(api.availability("pat_1002", "dermatology", "lakeside"), [])
            self.assertEqual(api.appointments("pat_1005"), [])
            self.assertEqual(len(server.wait_for_audits(4)), 4)

    def test_permanent_conflict_is_rejection_without_retry(self):
        with supplied_server() as server:
            api = self.api(server.base_url)
            slot = next(s for s in api.availability("pat_1001", "primary_care") if s["slotId"] == "slot_conflict_001")
            self.assertNotIn("conflictOnBooking", slot)
            with self.assertRaises(http_mock.ApiError) as caught:
                api.book("pat_1001", slot)
            self.assertEqual((caught.exception.status, caught.exception.code), (409, "slot_taken"))
            self.assertEqual(len(server.wait_for_audits(2)), 2)

    def test_validated_400_and_404_are_distinct_from_empty(self):
        with supplied_server() as server:
            api = self.api(server.base_url)
            for call, status, code in ((lambda: api.appointments("missing"), 404, "patient_not_found"),
                                      (lambda: api.availability("missing", "primary_care"), 400, "unknown_patient"),
                                      (lambda: api.book("missing", SLOT), 400, "unknown_patient")):
                with self.assertRaises(http_mock.ApiError) as caught:
                    call()
                self.assertEqual((caught.exception.status, caught.exception.code), (status, code))
                self.assert_safe_error(caught.exception)
            self.assertEqual(len(server.wait_for_audits(3)), 3)

    def test_handoff_receipt_and_medical_scenario_use_real_service(self):
        with supplied_server() as server:
            result = self.api(server.base_url).handoff("medical_advice", "Scheduling boundary; help requested")
            self.assertEqual(set(result), {"handoffId", "status"})
            self.assertEqual(result["status"], "queued")
            self.assertEqual(server.wait_for_audits(1)[0]["route"], "/handoffs")

    def test_api_failure_scenario_is_consistent_on_all_six_methods(self):
        with supplied_server() as server:
            api = self.api(server.base_url, scenario="api_failure")
            calls = (lambda: api.providers(), lambda: api.search_patients("555-0101", "1985-04-12"),
                     lambda: api.availability("pat_1001", "primary_care"), lambda: api.appointments("pat_1001"),
                     lambda: api.book("pat_1001", SLOT), lambda: api.handoff("api_failure", "private-summary"))
            for call in calls:
                with self.assertRaises(http_mock.ApiError) as caught:
                    call()
                self.assertNotIsInstance(caught.exception, http_mock.UnknownOutcome)
                self.assertEqual((caught.exception.status, caught.exception.code), (503, "downstream_unavailable"))
                self.assert_safe_error(caught.exception)
            self.assertEqual([r["status"] for r in server.wait_for_audits(6)], [503] * 6)

    def test_calendar_dates_and_filters_are_transmitted_as_documented(self):
        with HostileServer(payload={"slots": []}) as server:
            self.api(server.base_url).availability("pat_1001", "primary_care", "uptown", "2028-02-29", "2028-03-01")
            self.assertEqual(server.wait_for_requests(1)[0]["path"],
                             "/availability?patientId=pat_1001&specialty=primary_care&location=uptown&startDate=2028-02-29&endDate=2028-03-01")

    def test_invalid_unicode_is_rejected_locally_without_private_exception(self):
        with supplied_server() as server:
            api = self.api(server.base_url)
            for call in (lambda: api.search_patients("555-0101\ud800", "1985-04-12"),
                         lambda: api.handoff("other", "private-summary\ud800")):
                with self.assertRaises(http_mock.ApiError) as caught:
                    call()
                self.assert_safe_error(caught.exception)
            self.assertEqual(server.audits, [])

    def test_invalid_timezone_offset_is_not_a_calendar_valid_slot(self):
        with HostileServer(payload={"slots": [{**SLOT, "startTime": "2026-10-16T09:00:00-05:60"}]}) as server:
            with self.assertRaises(http_mock.ApiError):
                self.api(server.base_url).availability("pat_1001", "primary_care")

    def test_request_validation_precedes_io_and_does_not_leak_values(self):
        with supplied_server() as server:
            api = self.api(server.base_url)
            calls = (lambda: api.providers("not_supported"), lambda: api.providers(location="wrong"),
                     lambda: api.search_patients("555-0101", "1985-02-30"),
                     lambda: api.search_patients("", "1985-04-12"),
                     lambda: api.availability("pat_1001", "primary_care", start_date="2026-02-30"),
                     lambda: api.availability("pat_1001", "primary_care", start_date="2026-10-20", end_date="2026-10-01"),
                     lambda: api.appointments("pat_1001/../../providers"),
                     lambda: api.book("pat_1001", {**SLOT, "available": 1}),
                     lambda: api.book("pat_1001", {**SLOT, "daysFromToday": 7}),
                     lambda: api.handoff("wrong", "private-summary"), lambda: api.handoff("other", ""),
                     lambda: api.handoff("other", "x" * 256001))
            for call in calls:
                with self.assertRaises(http_mock.ApiError) as caught:
                    call()
                self.assert_safe_error(caught.exception)
            self.assertEqual(server.audits, [])

    def test_rejects_non_owned_destinations_and_unbounded_configuration(self):
        urls = ("http://localhost:4010", "http://127.0.0.2:4010", "http://2130706433:4010",
                "https://127.0.0.1:4010", "http://user:pass@127.0.0.1:4010", "http://127.0.0.1",
                "http://127.0.0.1:0", "http://127.0.0.1:65536", "http://127.0.0.1:+4010",
                "http://127.0.0.1:4010/path", "http://127.0.0.1:4010?x=y", "http://127.0.0.1:4010#frag",
                " http://127.0.0.1:4010", "http://127.0.0.1:4010\n")
        for url in urls:
            with self.subTest(url=url), self.assertRaises(ValueError):
                self.api(url)
        for timeout in (0, -1, float("inf"), float("nan"), True, 61):
            with self.subTest(timeout=timeout), self.assertRaises(ValueError):
                self.api("http://127.0.0.1:4010", timeout=timeout)
        with self.assertRaises(ValueError):
            self.api("http://127.0.0.1:4010", scenario="api_failure\r\nInjected: yes")

    def test_proxy_environment_is_ignored(self):
        with supplied_server() as server, HostileServer(payload={"providers": []}) as proxy:
            with patch.dict(os.environ, {"http_proxy": proxy.base_url, "HTTP_PROXY": proxy.base_url,
                                         "ALL_PROXY": proxy.base_url, "NO_PROXY": "", "no_proxy": ""}):
                self.assertEqual(len(self.api(server.base_url).providers()), 3)
            self.assertEqual(len(server.wait_for_audits(1)), 1)
            self.assertEqual(proxy.requests, [])

    def test_redirects_never_forward_reads_or_writes(self):
        with HostileServer(payload={"providers": []}) as target:
            for status in (301, 302, 303, 307, 308):
                with HostileServer(status, {}, headers={"Location": target.base_url + "/providers"}) as server:
                    api = self.api(server.base_url)
                    with self.assertRaises(http_mock.ApiError):
                        api.providers()
                    with self.assertRaises(http_mock.UnknownOutcome):
                        api.handoff("other", "private-summary")
                    self.assertEqual(len(server.wait_for_requests(2)), 2)
            self.assertEqual(target.requests, [])

    def test_read_schema_rejects_missing_extra_wrong_types_and_naive_dates(self):
        cases = [("providers", {"providers": [{**PROVIDER, "name": 3}]}),
                 ("providers", {"providers": [{**PROVIDER, "locations": [1]}]}),
                 ("providers", {"providers": [{**PROVIDER, "private": "555-0101"}]}),
                 ("providers", {"providers": [], "extra": True}),
                 ("providers", {}), ("providers", {"providers": {}}),
                 ("patients", {"matches": [{**PATIENT, "establishedPatient": 1}]}),
                 ("patients", {"matches": [{**PATIENT, "dateOfBirth": "1985-02-30"}]}),
                 ("patients", {"matches": [{**PATIENT, "phone": "wrong"}]}),
                 ("slots", {"slots": [{**SLOT, "available": 1}]}),
                 ("slots", {"slots": [{**SLOT, "available": False}]}),
                 ("slots", {"slots": [{**SLOT, "startTime": "2026-10-16T09:00:00"}]}),
                 ("slots", {"slots": [{**SLOT, "startTime": "2026-02-30T09:00:00-05:00"}]}),
                 ("slots", {"slots": [{**SLOT, "conflictOnBooking": True}]}),
                 ("appointments", {"appointments": [{**APPOINTMENT, "patientId": "wrong"}]}),
                 ("appointments", {"appointments": [{**APPOINTMENT, "status": "canceled"}]})]
        for route, payload in cases:
            with self.subTest(route=route, payload=payload), HostileServer(payload=payload) as server:
                api = self.api(server.base_url)
                call = {"providers": api.providers, "patients": lambda: api.search_patients("555-0101", "1985-04-12"),
                        "slots": lambda: api.availability("pat_1001", "primary_care"),
                        "appointments": lambda: api.appointments("pat_1001")}[route]
                with self.assertRaises(http_mock.ApiError) as caught:
                    call()
                self.assert_safe_error(caught.exception)

    def test_booking_receipt_must_match_each_submitted_fact(self):
        changes = ({"patientId": "wrong"}, {"providerId": "wrong"}, {"specialty": "dermatology"},
                   {"location": "uptown"}, {"startTime": "2026-10-17T09:00:00-05:00"},
                   {"status": "queued"}, {"daysFromToday": 7}, {"appointmentId": None})
        for change in changes:
            with self.subTest(change=change), HostileServer(201, {"appointment": {**APPOINTMENT, **change}}) as server:
                with self.assertRaises(http_mock.UnknownOutcome) as caught:
                    self.api(server.base_url).book("pat_1001", SLOT)
                self.assert_safe_error(caught.exception)
                self.assertEqual(len(server.wait_for_requests(1)), 1)

    def test_post_payload_contains_only_documented_fields(self):
        with HostileServer(201, {"appointment": APPOINTMENT}) as server:
            self.api(server.base_url).book("pat_1001", SLOT)
            body = json.loads(server.wait_for_requests(1)[0]["body"])
            self.assertEqual(body, {"patientId": "pat_1001", "slotId": "slot_4001", "confirmed": True})
        with HostileServer(201, {"handoffId": "handoff_9002", "status": "queued"}) as server:
            self.api(server.base_url).handoff("other", "private-summary")
            self.assertEqual(json.loads(server.wait_for_requests(1)[0]["body"]),
                             {"reason": "other", "summary": "private-summary"})

    def test_malformed_error_and_unexpected_status_never_prove_write_failure(self):
        cases = [(400, {"code": "invalid_parameter"}), (409, {"code": "wrong", "message": "555-0101"}),
                 (503, {"code": "downstream_unavailable", "message": 3}),
                 (503, {"code": "555-0101", "message": "private-summary"}),
                 (500, {"code": "internal_error", "message": "private-summary"}),
                 (200, {"handoffId": "handoff_9002", "status": "queued"}),
                 (201, {"handoffId": "handoff_9002", "status": "delivered"}),
                 (201, {"handoffId": "handoff_9002", "status": "queued", "summary": "private-summary"})]
        for status, payload in cases:
            with self.subTest(status=status, payload=payload), HostileServer(status, payload) as server:
                with self.assertRaises(http_mock.UnknownOutcome) as caught:
                    self.api(server.base_url).handoff("other", "private-summary")
                self.assert_safe_error(caught.exception)
                self.assertEqual(len(server.wait_for_requests(1)), 1)

    def test_uncertain_write_cannot_be_caught_as_definite_api_error(self):
        with HostileServer(action="disconnect") as server:
            certainty = "completed"
            try:
                self.api(server.base_url).handoff("other", "private-summary")
            except http_mock.ApiError:
                certainty = "definite_failure"
            except http_mock.UnknownOutcome:
                certainty = "unknown"
            self.assertEqual(certainty, "unknown")

    def test_bounded_strict_json_transport_failures_are_unknown_after_write(self):
        cases = ({"raw": b"{"}, {"raw": b"\xff"}, {"raw": b"[]"},
                 {"raw": b'{"handoffId":"a","handoffId":"b","status":"queued"}'},
                 {"raw": b'{"handoffId":NaN,"status":"queued"}'},
                 {"raw": b" " * 256001}, {"action": "disconnect"}, {"action": "delay"},
                 {"action": "drip"}, {"headers": {"Content-Type": "text/html"}},
                 {"headers": {"Content-Encoding": "gzip"}},
                 {"headers": {"Content-Length": "1000"}})
        for options in cases:
            with self.subTest(options=list(options)), HostileServer(201, {"handoffId": "handoff_9002", "status": "queued"}, **options) as server:
                started = time.monotonic()
                with self.assertRaises(http_mock.UnknownOutcome) as caught:
                    self.api(server.base_url, timeout=0.08).handoff("other", "private-summary")
                self.assertLess(time.monotonic() - started, 0.5)
                self.assert_safe_error(caught.exception)
                self.assertEqual(len(server.wait_for_requests(1)), 1)

    def test_events_are_categorical_and_normalize_private_routes(self):
        events = []
        with supplied_server() as server:
            api = self.api(server.base_url, event_sink=events.append)
            api.search_patients("555-0101", "1985-04-12")
            api.appointments("pat_1001")
            api.handoff("other", "private-summary")
            self.assertEqual(len(events), 3)
            self.assertEqual(events[1]["route"], "/patients/{patientId}/appointments")
            for event in events:
                self.assertEqual(set(event), {"method", "route", "status", "latency_ms"})
                self.assertGreaterEqual(event["latency_ms"], 0)
            for private in ("pat_1001", "555-0101", "1985-04-12", "private-summary"):
                self.assertNotIn(private, json.dumps(events))

    def test_event_sink_failure_cannot_change_success_or_duplicate_write(self):
        def broken_sink(_event):
            raise RuntimeError("private-summary")
        with supplied_server() as server:
            receipt = self.api(server.base_url, event_sink=broken_sink).handoff("other", "private-summary")
            self.assertEqual(receipt["status"], "queued")
            self.assertEqual(len(server.wait_for_audits(1)), 1)


if __name__ == "__main__":
    unittest.main()
