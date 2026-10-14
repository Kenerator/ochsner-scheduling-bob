# BOB walkthrough inventory

Updated 2026-10-13. Current runtime baseline: `e615d9894666909708fbf9810efcdafadc173a1a`.
This is an input-traced inventory, not the completed walkthrough collection.
Native progress remains in [tasks.md](../../../specs/001-ochsner-scheduling-assistant/tasks.md).

## Pending documents and visuals

All 67 catalog entries are documentation-unverified. Their individual documents,
final launch instructions, interactive steps and source-bound visuals remain W2/W3
work. The catalog deliberately fails the structural checker until those artifacts
exist; empty Step 0/1 declarations are not a completion claim. The seven control
atlas documents and all control visual mappings also remain pending. No old
schematic is represented as an actual executed screenshot.

The reviewed model-first launcher is now delivered with the exact dedicated Ochsner
Secure Note and qualified default model. Use
[current getting started](../getting-started.md) for the delivered interface.
FR-027/027a cover runtime and functional qualification; code-generation and unrelated
research/media remain excluded. This inventory does not require a paid probe.

## Source reconciliation

The eight supplied IDs come from the public-safe
[ID projection](../../../tests/fixtures/supplied_scenarios.json), not raw intake.
Other cases derive from native [stories/requirements](../../../specs/001-ochsner-scheduling-assistant/spec.md),
[actual controls](../../../src/ochsner_bob/widget.js) and existing tests/demos.
Source origin and documentation status are separate: an explicit input remains
explicit even when its current UI execution is unverified.

The supplied `unsupported_request` is a medical-advice case. It keeps its own
required document; `medical-boundary` documents the direct safe route, and the
additional `unsupported-intent` documents the distinct generic unsupported
control. These are separate entry paths, not silently collapsed aliases.
Unknown-write injection is a test/demo fault, not an invented mock scenario or UI
button. Reset/reconnect recovery does not imply wiping unresolved effect claims.

### Supplied scenarios

| Planned document slug | Native story | Origin |
|---|---|---|
| `happy-path-booking` | US1 | Supplied scenario |
| `provider-lookup` | US1 | Supplied scenario |
| `no-patient-match` | US2 | Supplied scenario |
| `multiple-patient-matches` | US2 | Supplied scenario |
| `slot-conflict` | US1 | Supplied scenario |
| `no-availability` | US1 | Supplied scenario |
| `api-failure` | US3 | Supplied scenario |
| `unsupported-request` | US3 | Supplied scenario |

### Identity and preferences

| Planned document slug | Native story | Origin |
|---|---|---|
| `correct-private-identity` | US2 | Existing story/control/test-derived flow |
| `lookup-appointments` | US2 | Existing story/control/test-derived flow |
| `empty-appointment-lookup` | US2 | Existing story/control/test-derived flow |
| `change-preferences` | US1 | Existing story/control/test-derived flow |
| `decline-and-reselect` | US1 | Existing story/control/test-derived flow |
| `accept-spelling-suggestion` | US1 | Existing story/control/test-derived flow |

### Safety and recovery

| Planned document slug | Native story | Origin |
|---|---|---|
| `request-help` | US3 | Existing story/control/test-derived flow |
| `medical-boundary` | US3 | Existing story/control/test-derived flow |
| `unsupported-intent` | US3 | Existing story/control/test-derived flow |
| `submit-mock-handoff` | US3 | Existing story/control/test-derived flow |
| `unknown-booking-outcome` | US1 | Existing story/control/test-derived flow |
| `reset-and-reconnect` | US3 | Existing story/control/test-derived flow |

### Paired continuity

| Planned document slug | Native story | Origin |
|---|---|---|
| `pair-support` | US5 | Existing story/control/test-derived flow |
| `support-take-and-return-control` | US5 | Existing story/control/test-derived flow |
| `patient-adopts-support-suggestion` | US5 | Existing story/control/test-derived flow |

### Developer and Replay

| Planned document slug | Native story | Origin |
|---|---|---|
| `recording-off-diagnostics` | US4 | Existing story/control/test-derived flow |
| `capture-and-seal` | US4 | Existing story/control/test-derived flow |
| `replay-navigation-and-bookmarks` | US4 | Existing story/control/test-derived flow |
| `replay-typed-variant-comparison` | US4 | Existing story/control/test-derived flow |
| `review-regression-proposal` | US4 | Existing story/control/test-derived flow |
| `export-and-import-recording` | US4 | Existing story/control/test-derived flow |
| `purge-disposable-recording` | US4 | Existing story/control/test-derived flow |
| `unavailable-replay-reference` | US4 | Existing story/control/test-derived flow |

### Additional distinct native acceptance and recovery cases

These 36 additions reconcile the native edge/acceptance cases beyond the initial
31-entry preparation. Origins are inferred walkthrough decompositions of accepted
requirements and existing executable tests, not new product scope. Rows name a
distinct observable journey; individual malformed-value permutations within the same
journey are sample values, not duplicated documents. Fault/clock/concurrency cases
without a current UI trigger must say so in their own document and link the exact
automated/CLI path. A test file reference is evidence of a contract, not proof that
its whole journey ran in IAB. No BOB unit-security invariant is silently promoted
into a newly requested UI feature.

| Planned document slug | Native basis | Distinct flow and executable source |
|---|---|---|
| `correct-duplicate-zip` | US2 / FR-004 | [Existing test source](../../../tests/test_transition_acceptance.py) — Correct a resolved duplicate from ZIP A to ZIP B; revoke prior proposal/private results. |
| `invalid-private-identity` | US2 / FR-004 | [Existing test source](../../../tests/test_transition_acceptance.py) — Reject invalid ZIP/date/phone without candidate disclosure or private progress. |
| `recover-partial-identity` | US2 / FR-004 | [Existing test source](../../../tests/test_identity_draft_recovery.py) — Correct one invalid discriminator without re-entering the valid local drafts. |
| `appointment-not-found` | US2 / FR-007 | [Existing test source](../../../tests/test_transition_acceptance.py) — Distinguish a 404 refresh from empty appointments and clear old rows. |
| `appointment-outage` | US2 / FR-007 | [Existing test source](../../../tests/test_transition_acceptance.py) — Distinguish a failed refresh from empty results; preserve safe recovery. |
| `malformed-appointment-response` | US2 / FR-007 | [Existing test source](../../../tests/test_transition_acceptance.py) — Reject malformed/transport read outcomes without retaining stale appointments. |
| `failed-availability-refresh` | US1 / FR-005 | [Existing test source](../../../tests/test_transition_acceptance.py) — Clear stale slots/proposal after a failed refresh; do not reselect old data. |
| `correct-invalid-date-range` | US1 / FR-005 | [Existing test source](../../../tests/test_conversation.py) — Reject an inverted merged range atomically, then correct it. |
| `clear-date-preferences` | US1 / FR-005 | [Existing test source](../../../tests/test_conversation.py) — Clear only dates while retaining specialty/location. |
| `select-and-clear-provider` | US1 / FR-005 | [Existing test source](../../../tests/test_conversation.py) — Select returned provider, correct it, then clear only that filter. |
| `accept-provider-name-suggestion` | US1 / FR-006 | [Existing test source](../../../tests/test_transition_acceptance.py) — Review a public provider-name suggestion without auto-selecting a provider. |
| `text-does-not-confirm` | US1 / FR-008 | [Existing test source](../../../tests/test_conversation.py) — Textual consent cannot replace the separate current Confirm action. |
| `duplicate-confirmation` | US1 / FR-009 | [Existing test source](../../../tests/test_session_contract.py) — Double or concurrent confirmation consumes one effect authority only. |
| `stale-submission` | US1 / FR-008 | [Existing test source](../../../tests/test_browser_service.py) — Reject delayed old-revision commands without a new model call or effect. |
| `unknown-after-restart` | US1 / FR-010a | [Existing test source](../../../tests/test_effect_journal.py) — Restore unresolved write protection after restart without identity/consent. |
| `success-then-conflict` | US1 / FR-010 | [Existing test source](../../../tests/test_transition_acceptance.py) — Retain the prior successful receipt separately from a later rejection. |
| `handoff-failure` | US3 / FR-012 | [Existing test source](../../../tests/test_supplied_http.py) — Report rejected/failed handoff rather than queued or live staff contact. |
| `unknown-handoff-outcome` | US3 / FR-010 | [Existing test source](../../../tests/test_live_diagnostics.py) — Keep lost/malformed handoff receipt unknown and block automatic retry. |
| `help-during-model-wait` | US3 / FR-011 | [Existing test source](../../../tests/test_interaction_service.py) — Use safety/help while language waits; ignore its later stale result. |
| `model-unavailable-no-fallback` | US6 / FR-001 | [Existing test source](../../../tests/test_language.py) — Disclose unavailable model interpretation without silently switching modes. |
| `malformed-model-response` | US1 / FR-001 | [Existing test source](../../../tests/test_language.py) — Reject invalid/contradictory model output and retain application authority. |
| `pairing-expiry-and-rejoin` | US5 / FR-017 | [Existing test source](../../../tests/test_browser_service.py) — An expired/consumed grant cannot be reused; create a new local pair. |
| `independent-session-isolation` | US5 / FR-017 | [Existing test source](../../../tests/test_browser_service.py) — A separately started patient remains isolated from the paired session. |
| `support-stale-observation` | US5 / FR-017 | [Existing test source](../../../tests/test_browser_service.py) — Distinguish current backend context from the last acknowledged patient screen. |
| `support-lease-expiry` | US5 / FR-017 | [Existing test source](../../../tests/test_support_status.py) — Lease expiry returns control without ending local support membership. |
| `replay-preference-variant` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Fork only public preferences in recorded simulation; original remains immutable. |
| `replay-identity-variant` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Use an approved fixture reference, never live identity/consent, in a variant. |
| `replay-clock-variant` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Change a bounded simulation clock with explicit provenance. |
| `replay-model-timeout-variant` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Simulate model timeout from recorded inputs without calling a model. |
| `replay-order-variant` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Reorder typed simulation events without importing confirmation authority. |
| `replay-delay-and-view-variant` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Compare delayed presentation changes even if semantic state matches. |
| `incomplete-capture` | US4 / FR-015 | [Existing test source](../../../tests/test_view_receipt_capture.py) — Missing observations stay incomplete; do not invent full renderer replay. |
| `imported-provenance-drift` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Report version/source drift as comparison rather than identical replay. |
| `expired-recording` | US4 / FR-015 | [Existing test source](../../../tests/test_recording_store.py) — Expired recording cannot be replayed or revived by import. |
| `rejected-recording-import` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — Reject invalid/authority-bearing recording data without raw-value errors. |
| `recording-limit` | US4 / FR-015 | [Existing test source](../../../tests/test_replay_contract.py) — A bounded capture overflow remains explicitly incomplete and retains earlier evidence. |

### Aliases and scope boundary

Public provider discovery without identity is the existing `provider-lookup` flow,
not a separate duplicate document. Generic unsupported intent is distinct from the
supplied medical scenario. The existing `replay-typed-variant-comparison` documents
API-status mutation; preference/identity/clock/model/order/delay variants each retain
their own document. Help, medical and public interruption steps link their relevant
state setup rather than multiplying one document per transient state. Low-level
schema, file-permission and storage corruption checks remain test evidence unless
they define a distinct user recovery journey above. No aliases erase supplied IDs.

## Interrupted IAB walkthrough — 2026-10-12

Historical source `d925f326`, synthetic fixtures only, recording OFF. Public provider
lookup used genuine model interpretation; the remaining observations used direct
core-guarded controls. This is partial actual browser evidence, not a full pass.

| Case | Observed result | Limit |
|---|---|---|
| Provider lookup | Two returned downtown primary-care providers; no identity needed | One genuine public-language request, not fresh broad qualification |
| Happy booking | Private fixture verified; separate selection/Confirm; completed mock receipt and appointment history | No real appointment |
| No patient match | Missing identity; no candidates/results; separate mock handoff queued | One availability action reported local connection unavailable; exact identity-unclear handoff reason not proven |
| Multiple matches | Ambiguous with blank ZIP; ZIP 70115 resolved and private controls cleared; truthful empty lookup | Alternate ZIP/correction invalidation not re-executed in this IAB run |
| Slot conflict | Exact conflicting option selected; separate Confirm rejected; proposal cleared and repeat Confirm disabled | Fresh recovery booking not executed |
| Support join | One-use grant joined once; fresh public mirror; private inputs blank/disabled, booking controls disabled | No takeover/suggestion/adoption; no real staff contact |
| No availability | Incomplete | No browser outcome claimed |
| API failure | Incomplete | Approved isolated fault harness was not launched |
| Supplied unsupported/medical | Incomplete | No browser outcome claimed |

Transient Marimo kernel/reconnect notices and repeated support acknowledgement
warnings occurred even while fresh revisions mirrored. Preserve these as usability
warnings, not clean-pass evidence. Later interruption left both ports absent;
UI restoration succeeded, but the dedicated vault item was missing and the backend
was not restored. Session/effects namespace and canonical budget were not reset;
no restoration readiness model call was made.

## Control atlas inventory

[Control inventory](../controls/index.md) records all 57 static/dynamic
interactive control families across seven groups, including below-fold Replay.
Source inventory is not proof that every runtime state has been visually checked.

## Revision history

- 2026-10-12: Initial W1 inventory; W2/W3, reviewed launcher integration and final
  independent review remain open. No product behavior changed.
- 2026-10-13: Reconciled current runtime/launcher and 67 distinct planned flows.
  Fresh Operator-requested Support pairing showed joined/inactive/read-only role;
  acknowledgement-unavailable and transient kernel warnings remain. No full
  synchronization, takeover, booking or model-call evidence is inferred. Its raw
  still is not a public asset and no prior capture is relabeled current.

## References

- [Native implementation plan](../../../specs/001-ochsner-scheduling-assistant/plan.md)
- [Existing supplied HTTP tests](../../../tests/test_supplied_http.py)
- [Existing demo orientation](../../internal/demo.md)
