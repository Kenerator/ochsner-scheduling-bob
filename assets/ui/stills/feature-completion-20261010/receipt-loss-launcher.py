"""Approved capture-only reuse of the existing labeled receipt-loss demo fault.

No product/mock changes, model opt-in, or raw private receipts in evidence.
The observer independently reads the supplied mock before the existing wrapper
hides its accepted receipt. This is not a real network failure.
"""
import json
import os
from pathlib import Path

import serve_browser
from demo_booking import _HideAcceptedBookingReceipt

RealAdapter = serve_browser.HttpMockAdapter
PROOF = Path('.bob-local/receipt-loss-proof.jsonl')


class VerifiedAdapter:
    def __init__(self, delegate):
        self.delegate = delegate
        self.attempts = 0

    def __getattr__(self, name):
        return getattr(self.delegate, name)

    def book(self, patient_id, slot):
        self.attempts += 1
        receipt = self.delegate.book(patient_id, slot)
        # A second validated HTTP read independently checks accepted mock state.
        rows = self.delegate.appointments(patient_id)
        matching = [a for a in rows if a['patientId'] == patient_id and all(
            a[k] == slot[k] for k in ('providerId', 'specialty', 'location', 'startTime'))]
        proof = {'fault': 'accepted_booking_receipt_hidden_at_adapter_boundary',
                 'attempt': self.attempts, 'validated_accept': True,
                 'independent_lookup_matching_rows': len(matching),
                 'public_start_time': slot['startTime'], 'public_location': slot['location']}
        fd = os.open(PROOF, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600)
        with os.fdopen(fd, 'a') as stream:
            stream.write(json.dumps(proof, sort_keys=True) + '\n')
            stream.flush()
            os.fsync(stream.fileno())
        return receipt


def adapter(*args, **kwargs):
    return _HideAcceptedBookingReceipt(VerifiedAdapter(RealAdapter(*args, **kwargs)))


if __name__ == '__main__':
    serve_browser.HttpMockAdapter = adapter
    raise SystemExit(serve_browser.main(['--port', '28543', '--ui-port', '28542',
                                       '--namespace', '.bob-local/receipt-loss']))
