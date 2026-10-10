# Interaction Contract

The CLI and browser views consume the same core projections and commands.

## Commands

- Public discovery/refinement: specialty, location, date range, provider selection, clear/correct.
- Private identity: local phone, DOB, ZIP; resolve, correct, or stop.
- Appointment: lookup, choose returned slot, view proposal, explicitly confirm.
- Recovery: help, medical boundary, unsupported request, public-intent switch, handoff.
- Developer/support: inspect events, copy/open reference, replay, fork variant, takeover/return.

## Projection rules

Every projection labels current state, certainty, freshness, and next action. Private identity and raw model text are excluded from diagnostics. Handoff receipt status and local simulated support status are separate. A proposal projection is read-only and cannot invoke a write.

An owned recording-OFF reference opens bounded current sanitized diagnostics,
with requested/current revisions and no historical-state claim. Session-scoped
in-memory grants expire without polling renewal; foreign/unknown references do
not grant access. This path creates no RecordingStore or exact replay and cannot
be stepped, forked, purged as a recording or exactly exported. Explicit synthetic
capture/import remains separate and preserves all replay/effect guards.

## External boundaries

The HTTP adapter sends only the supplied API contract and validates response shape/status. The mock is owned by the demo lifecycle and remains unmodified. ZEN receives closed categorical facts and returns a reasoned decision. The model adapter interprets bounded language but cannot return identity, patient IDs, slots, consent, or tool authority.
