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

## External boundaries

The HTTP adapter sends only the supplied API contract and validates response shape/status. The mock is owned by the demo lifecycle and remains unmodified. ZEN receives closed categorical facts and returns a reasoned decision. The model adapter interprets bounded language but cannot return identity, patient IDs, slots, consent, or tool authority.
