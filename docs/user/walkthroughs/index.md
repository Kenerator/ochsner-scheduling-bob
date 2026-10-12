# BOB walkthrough inventory

Updated 2026-10-12. Inventory baseline: `d925f326dd604b3eba07d844914810e2f2574705`.
This is an input-traced inventory, not the completed walkthrough collection.
Native progress remains in [tasks.md](../../../specs/001-ochsner-scheduling-assistant/tasks.md).

## Pending documents and visuals

All 31 catalog entries are documentation-unverified. Their individual documents,
final launch instructions, interactive steps and source-bound visuals remain W2/W3
work. The catalog deliberately fails the structural checker until those artifacts
exist; empty Step 0/1 declarations are not a completion claim. The seven control
atlas documents and all control visual mappings also remain pending. No old
schematic is represented as an actual executed screenshot.

The approved model-first launch will use the dedicated Ochsner vault item and
qualified model, but the reviewed launcher bundle is not installed yet. Use
[current getting started](../getting-started.md) for the delivered interface.
No new paid qualification is authorized by this inventory.

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

## Interrupted IAB walkthrough — 2026-10-12

Source baseline above, synthetic fixtures only, recording OFF. Public provider
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

## References

- [Native implementation plan](../../../specs/001-ochsner-scheduling-assistant/plan.md)
- [Existing supplied HTTP tests](../../../tests/test_supplied_http.py)
- [Existing demo orientation](../../internal/demo.md)
