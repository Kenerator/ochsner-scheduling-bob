# Data Model: Ochsner Best-of-Breed Scheduling Assistant

| Entity | Key fields and rules |
|---|---|
| Session | `session_id`, intent, preferences, identity, proposal, effect ledger, trace, support mirror, freshness; isolated from every other session. |
| FixtureIdentity | phone, DOB, ZIP provenance, match status, verified fixture identifier; never model-supplied; correction revokes dependent state. |
| Provider/Slot | Public provider and mock-returned slot with authoritative `startTime`; provider filtering is local over returned slots. |
| Proposal | Immutable id, source slot, identity/preference generation, displayed summary; cannot authorize a write. |
| Confirmation | Current proposal id, explicit user action, consumed status, effect generation; one use only. |
| EffectAttempt/Receipt | Booking or handoff attempt, provenance, result (`attempted`, `completed`, `rejected`, `unknown`, `queued`), validation, unknown latch. |
| DiagnosticEvent | Allowlisted category, transition, rule reason, API outcome, latency, certainty, sanitized references; no identity-bearing raw text. |
| InteractionReference/Variant | Source trace/step, fork changes, provenance, diff, simulation-only and review status; no authority. |
| OFF inspection grant | Bounded session-owned reference/expiry in memory; returns current sanitized diagnostics with requested/current revision, never an exact historical snapshot or recording. |
| SupportMirror | Acknowledged patient view, known/missing/uncertain facts, current/prior outcomes, freshness, takeover state, session id. |

## Invariants

1. Private reads and writes require current verified fixture identity.
2. Identity, preference, correction, refusal, invalid input, model failure, reset, and unknown effect transitions invalidate dependent authority as appropriate.
3. A booking write requires a current proposal and separately consumed confirmation.
4. Unknown effects are never retried automatically and remain distinct from rejected/completed effects.
5. Replay and variants are isolated simulation state only.
6. Support takeover cannot bypass policy, identity, confirmation, or effect certainty guards.
