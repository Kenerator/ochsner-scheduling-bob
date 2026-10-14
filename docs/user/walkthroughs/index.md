# BOB individual walkthroughs

Updated 2026-10-14. Start with one guide below: every guide contains its own
Python 3.11+ install/doctor, normal model-first launch, explicit offline alternative,
enumerated synthetic inputs, exact controls/results/recovery, visuals and cleanup.
Keep the rendered guide beside BOB. [Quick setup/map](../getting-started.md) and the
[seven-group annotated control atlas](../controls/index.md) provide orientation.

The collection covers **67 distinct input/native journeys**, not 67 newly passed
browser tests. The [catalog](catalog.json) retains all flows as documentation-
unverified for whole-journey execution. Every guide makes current UI actions,
automated-only faults, historical/offline figures and unexecuted gaps explicit.
The structural checker passes 414 declared steps (248 interactive), but cannot
certify prose accuracy, screenshot correspondence, model reliability or UI fidelity.
Native progress remains only in [tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).

## Choose a walkthrough

### Supplied assignment scenarios

| Guide | Native/source basis | Documented mode |
|---|---|---|
| [happy-path-booking](happy-path-booking.md) | `happy_path_booking`, `US1` | offline |
| [provider-lookup](provider-lookup.md) | `provider_lookup`, `US1` | offline |
| [no-patient-match](no-patient-match.md) | `no_patient_match`, `US2` | offline |
| [multiple-patient-matches](multiple-patient-matches.md) | `multiple_patient_matches`, `US2` | offline |
| [slot-conflict](slot-conflict.md) | `slot_conflict`, `US1` | offline |
| [no-availability](no-availability.md) | `no_availability`, `US1` | offline |
| [api-failure](api-failure.md) | `api_failure`, `US3` | offline |
| [unsupported-request](unsupported-request.md) | `unsupported_request`, `US3` | offline |

### Identity, preferences and recovery

| Guide | Native/source basis | Documented mode |
|---|---|---|
| [correct-private-identity](correct-private-identity.md) | `US2` | offline |
| [lookup-appointments](lookup-appointments.md) | `US2` | offline |
| [empty-appointment-lookup](empty-appointment-lookup.md) | `US2` | offline |
| [change-preferences](change-preferences.md) | `US1` | offline |
| [decline-and-reselect](decline-and-reselect.md) | `US1` | offline |
| [accept-spelling-suggestion](accept-spelling-suggestion.md) | `US1` | offline |
| [request-help](request-help.md) | `US3` | offline |
| [medical-boundary](medical-boundary.md) | `US3` | offline |
| [unsupported-intent](unsupported-intent.md) | `US3` | offline |
| [submit-mock-handoff](submit-mock-handoff.md) | `US3` | offline |
| [unknown-booking-outcome](unknown-booking-outcome.md) | `US1` | offline |
| [reset-and-reconnect](reset-and-reconnect.md) | `US3` | offline |

### Paired support

| Guide | Native/source basis | Documented mode |
|---|---|---|
| [pair-support](pair-support.md) | `US5` | offline |
| [support-take-and-return-control](support-take-and-return-control.md) | `US5` | offline |
| [patient-adopts-support-suggestion](patient-adopts-support-suggestion.md) | `US5` | offline |

### Developer recording and replay

| Guide | Native/source basis | Documented mode |
|---|---|---|
| [recording-off-diagnostics](recording-off-diagnostics.md) | `US4` | offline |
| [capture-and-seal](capture-and-seal.md) | `US4` | offline |
| [replay-navigation-and-bookmarks](replay-navigation-and-bookmarks.md) | `US4` | recorded-simulation |
| [replay-typed-variant-comparison](replay-typed-variant-comparison.md) | `US4` | recorded-simulation |
| [review-regression-proposal](review-regression-proposal.md) | `US4` | recorded-simulation |
| [export-and-import-recording](export-and-import-recording.md) | `US4` | recorded-simulation |
| [purge-disposable-recording](purge-disposable-recording.md) | `US4` | recorded-simulation |
| [unavailable-replay-reference](unavailable-replay-reference.md) | `US4` | recorded-simulation |

### Additional native acceptance and recovery journeys

| Guide | Native/source basis | Documented mode |
|---|---|---|
| [correct-duplicate-zip](correct-duplicate-zip.md) | `US2`, `FR-004` | offline |
| [invalid-private-identity](invalid-private-identity.md) | `US2`, `FR-004` | offline |
| [recover-partial-identity](recover-partial-identity.md) | `US2`, `FR-004` | offline |
| [appointment-not-found](appointment-not-found.md) | `US2`, `FR-007` | offline |
| [appointment-outage](appointment-outage.md) | `US2`, `FR-007` | offline |
| [malformed-appointment-response](malformed-appointment-response.md) | `US2`, `FR-007` | offline |
| [failed-availability-refresh](failed-availability-refresh.md) | `US1`, `FR-005` | offline |
| [correct-invalid-date-range](correct-invalid-date-range.md) | `US1`, `FR-005` | offline |
| [clear-date-preferences](clear-date-preferences.md) | `US1`, `FR-005` | offline |
| [select-and-clear-provider](select-and-clear-provider.md) | `US1`, `FR-005` | offline |
| [accept-provider-name-suggestion](accept-provider-name-suggestion.md) | `US1`, `FR-006` | offline |
| [text-does-not-confirm](text-does-not-confirm.md) | `US1`, `FR-008` | offline |
| [duplicate-confirmation](duplicate-confirmation.md) | `US1`, `FR-009` | offline |
| [stale-submission](stale-submission.md) | `US1`, `FR-008` | offline |
| [unknown-after-restart](unknown-after-restart.md) | `US1`, `FR-010a` | offline |
| [success-then-conflict](success-then-conflict.md) | `US1`, `FR-010` | offline |
| [handoff-failure](handoff-failure.md) | `US3`, `FR-012` | offline |
| [unknown-handoff-outcome](unknown-handoff-outcome.md) | `US3`, `FR-010` | offline |
| [help-during-model-wait](help-during-model-wait.md) | `US3`, `FR-011` | offline |
| [model-unavailable-no-fallback](model-unavailable-no-fallback.md) | `US6`, `FR-001` | offline |
| [malformed-model-response](malformed-model-response.md) | `US1`, `FR-001` | offline |
| [pairing-expiry-and-rejoin](pairing-expiry-and-rejoin.md) | `US5`, `FR-017` | offline |
| [independent-session-isolation](independent-session-isolation.md) | `US5`, `FR-017` | offline |
| [support-stale-observation](support-stale-observation.md) | `US5`, `FR-017` | offline |
| [support-lease-expiry](support-lease-expiry.md) | `US5`, `FR-017` | offline |
| [replay-preference-variant](replay-preference-variant.md) | `US4`, `FR-015` | recorded-simulation |
| [replay-identity-variant](replay-identity-variant.md) | `US4`, `FR-015` | recorded-simulation |
| [replay-clock-variant](replay-clock-variant.md) | `US4`, `FR-015` | recorded-simulation |
| [replay-model-timeout-variant](replay-model-timeout-variant.md) | `US4`, `FR-015` | recorded-simulation |
| [replay-order-variant](replay-order-variant.md) | `US4`, `FR-015` | recorded-simulation |
| [replay-delay-and-view-variant](replay-delay-and-view-variant.md) | `US4`, `FR-015` | recorded-simulation |
| [incomplete-capture](incomplete-capture.md) | `US4`, `FR-015` | recorded-simulation |
| [imported-provenance-drift](imported-provenance-drift.md) | `US4`, `FR-015` | recorded-simulation |
| [expired-recording](expired-recording.md) | `US4`, `FR-015` | recorded-simulation |
| [rejected-recording-import](rejected-recording-import.md) | `US4`, `FR-015` | recorded-simulation |
| [recording-limit](recording-limit.md) | `US4`, `FR-015` | recorded-simulation |

## Evidence and safety boundaries

- Use synthetic identity only in the private controls. Public text, support mirrors
  and captures exclude private identity and live pairing credentials.
- Selecting an option is not a booking. Confirm separately for the exact current
  proposal. Conflict/rejection is distinct from unknown write; unknown means no retry,
  even after reset, reconnect, restart or recording expiry.
- Joined support is not active control, fresh acknowledgement, live staff or patient
  adoption. The current support demo joined read-only, with private/confirmation
  authority excluded; acknowledgement-unavailable/kernel warnings remain a gap.
- Recording OFF is sanitized current inspection, not historical replay. Recorded-only
  simulations/variants/comparison cannot make live API/model writes or revive consent.
  Import is bounded data, not source authenticity or full renderer parity.
- Some fault/clock/concurrency branches exist only in exact automated contracts.
  Each has its own guide; there is no invented UI fault selector or hidden combined
  failure journey. Purge is not performed without its applicable action-time approval.
- Normal launch requests model mode through the trusted exact-note helper. Doctor,
  offline control paths and structural tests make no real model request. Runtime/
  functional qualification policy does not authorize LLM code creation or media work.

The [52-record visual manifest](../../../assets/ui/walkthroughs/manifest.json)
binds 18 unchanged clean originals plus 17 separate vector layers and 17 exact-source
raster composites to hashes/source/action/result/role/placement/limitations. All
57 control families have actual annotated locators and text equivalents. These
desktop assets do not claim mobile/screen-reader conformance. New W2 captures use
offline runtime source `bdc4585`; support/spelling reuse retains original `c3e6df2`/
`e2dfa7e` provenance. No old frame becomes new execution evidence.

## Current partial offline UI checks — 2026-10-14

Exact launch source `612d4bff51bc79ba172b03f325420db3f0240bab`, with documentation
edits in the working tree; runtime components are unchanged from `bdc4585`.
The earlier owned review listeners were absent and its old tab had an expired
kernel. A fresh explicitly offline owned launch on free 29580/29581 preserved all
earlier files and left Operator 28450/28451 services/state untouched. No key,
model call, recording or booking/handoff write was used in these checks.

| Documented case | Actual observed subset | Remaining boundary |
|---|---|---|
| No availability | 555-0102 private fixture verified; Dermatology/Lakeside; no matched options/proposal; Help with no current attempt | Fresh install/model path not repeated; screenshot is private QA evidence, not another adopted atlas asset |
| No patient match | 555-9999/1990-01-01 returned missing identity, no candidates and disabled Confirm | No handoff submitted; retained-draft ZIP does not establish a new empty-draft test |
| Multiple matches / empty lookup | Fresh patient; 555-0130/1978-09-22 with blank ZIP ambiguous; ZIP70115 verified/cleared inputs; successful empty appointment lookup | No alternate-ZIP correction/booking in this run |
| Provider selection/clear | Returned two Downtown primary-care providers; Choose provider2 set filter; clear provider removed only it; provider99 rejected | Text-provider2 branch and later availability not replayed |
| Date edit/reconnect | A connection failure left old display; read-only reload recovered revision7/identity/filters; valid future date range applied at revision8 | The subsequent inverted one-sided edit hit connection unavailable again; atomic UI rejection is not qualified |

Both owned listeners remained alive during the intermittent connection failures.
Bounded browser logs showed WebSocket close/error warnings, not a proven root cause.
This is an observed UI gap, not a product fix or a blanket execution pass. All
whole journeys remain unverified in the catalog; exact automated contracts and
applicable historical source-bound evidence retain their separate scope.

## Source reconciliation

Eight supplied IDs resolve through the public-safe
[ID projection](../../../tests/fixtures/supplied_scenarios.json), not raw intake.
The other 59 journeys decompose accepted native requirements and actual controls/
tests, with origin distinct from scope acceptance. Native
[specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) owns story/
acceptance detail; source IDs and each guide's references preserve its basis.

The supplied `unsupported_request` is medical advice, distinct from the generic
unsupported-intent control. Public discovery is provider-lookup, not a duplicate.
API-status replay comparison is separate from preference/identity/clock/model/order/
delay variants. Low-level schema/value permutations stay test cases unless they
form one of the distinct recovery journeys listed above. Support/Admin coverage
does not imply a console, production authentication or real service delivery.

## Verification

From the repository root, using the explicit compatible environment:

```sh
.venv/bin/python tools/poc-docs/check_walkthroughs.py --root . --catalog docs/user/walkthroughs/catalog.json
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/demo_booking.py --flow all
```

The portable checker has 52 positive/negative fixtures; BOB-only consumers retain
seven groups/57 controls, source layers, ordered session/filter prerequisites and
the real Flight Deck mapping. The prerequisite tests execute declared guide
metadata against the real service/session with disposable synthetic fixtures;
they are not complete browser journeys or verification of human prose.

Historical checkpoint: 558 tests passed in 28.151 s at checker `612d4bf`, with
three synthetic booking demos and retained starter demos. The later Flight Deck
candidate `5e8fa85` passed 564 tests in 27.342 s on the committed source, separately
from its earlier working-tree runs. These retain their original execution identity;
no new browser/model results are manufactured. The affected repair, tests,
Flight Deck and actual CI/protected delivery evidence are in
the [native completion ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md).

## Historical interrupted IAB walkthrough — 2026-10-12

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


## Revision history

- 2026-10-12: Initial 31-flow source inventory and interrupted browser observations.
- 2026-10-13: Reconciled 67 native journeys; actual source-bound atlas capture/reuse.
- 2026-10-14: Individual guides, annotated atlas and strict portable checker assembled;
  known execution gaps retained. Final independent review/integration remain open.

## References

- [Native plan](../../../specs/001-ochsner-scheduling-assistant/plan.md)
- [Control atlas](../controls/index.md)
- [Demo orientation](../../internal/demo.md)
- [Persona/story/test crosswalk](../../internal/persona-story-test-index.md)
- [As-built authority boundaries](../../internal/as-built/architecture.md)
