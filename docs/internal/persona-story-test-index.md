# Persona → story → executable acceptance

Updated 2026-10-12: current constraint crosswalk first; dated execution evidence
follows the reproduction instructions and limits. This is not a second task
ledger: [native stories](../../specs/001-ochsner-scheduling-assistant/spec.md) own
acceptance detail and [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md)
own completion. Persona hypotheses do not grant permissions or prove user research.

## Exact pins and material adoption

Every pin below has catalog prefix `poc-template-seed-v1:`. Names link to the
[canonical pinned cards](../product/personas.md); cards/ancestry remain there,
not duplicated as proof. Six actors are human; Sam-Rae is an agent and has no
booking authority. None of these hypotheses grants permissions. Every row has
an executable journey in [test_persona_acceptance.py](../../tests/test_persona_acceptance.py),
class `PersonaAcceptanceTests` (method names below).

| Pin / native stories | Constraint adopted into behavior and code | Executable journey / evidence boundary |
| --- | --- | --- |
| [Jules](../product/personas.md#jules--jules-find-and-explicitly-confirm-a-mock-appointment), `56e6af21-d1e4-4698-8485-83a341d77031@1`; US1, US2 | Busy, few interactions: public discovery before private entry; exact returned appointment is inspectable; choice/render is not consent; later bound confirmation submits once. [Conversation.enter_identity/confirm](../../src/ochsner_bob/conversation.py) and [SchedulingSession.command/_effect](../../src/ochsner_bob/session.py) keep identity, proposal and writes application-owned. | `test_jules_reviews_exact_returned_option_before_one_explicit_booking`: supplied HTTP GETs only before confirmation; receipt matches displayed provider/specialty/location/time; old confirmation cannot submit again. Proves command journey, not a measured few-interaction usability target or clinical suitability. |
| [Billy-June](../product/personas.md#billy-june--billy-june-coordinate-convenient-continuity-of-appointments), `0de53f87-1856-40ac-84fe-ec4d890e3770@1`; US1, US2 | Limited travel/windows: location, date and returned-provider filters remain visible/effective; inverted one-sided date edits retain valid range; correction revokes proposal; clearing provider preserves dates/location/verified identity. [Conversation._local](../../src/ochsner_bob/conversation.py), [SchedulingSession._preferences/availability](../../src/ochsner_bob/session.py), [HttpMockAdapter.availability](../../src/ochsner_bob/http_mock.py). | `test_billy_june_corrects_travel_and_date_window_without_reusing_proposal`: real returned time constrains a one-day window; only selected provider appears; invalid correction creates no HTTP request; old proposals stay stale. [SuppliedHttpScenarioTests.test_no_availability](../../tests/test_supplied_http.py) covers truthful no-match/help. No clinical continuity policy is inferred; unsupported hours/time-of-day filtering and comparative usability are not established by this journey. |
| [Amy-Lou](../product/personas.md#amy-lou--amy-lou-complete-a-scheduling-journey-with-help-when-needed), `aae4b004-4bbf-4ac5-b532-2d7af776e168@1`; US3, US5 | Low confidence/no email or smartphone: Help remains reachable during incomplete identity and private text; email is not required; browser/basic-phone and real-staff limits are explicit. [Conversation.interpret](../../src/ochsner_bob/conversation.py) routes Help before model/privacy; [SchedulingSession help/handoff](../../src/ochsner_bob/session.py) separates assistance from delivery. | `test_amy_lou_gets_no_email_assistance_without_smartphone_or_identity`: no patient search is required; actual mock queue receipt follows explicit handoff; minimized summary omits pasted phone and names missing identity. This is truthful browser-demo assistance, not a working basic-phone/telephony channel or research-validated plain language. |
| [Ellie-Rae](../product/personas.md#ellie-rae--ellie-rae-select-and-confirm-with-minimal-input), `cb706720-85fb-42ef-9318-2bcec4c2b621@1`; US1, US3 | Limited reach/one-handed situation: short numbered selections; invalid choice preserves valid identity, options and preferences while revoking stale consent. [Conversation._local](../../src/ochsner_bob/conversation.py) accepts a number; [SchedulingSession select](../../src/ochsner_bob/session.py) requires a separately confirmed proposal. | `test_ellie_rae_recovers_numbered_choice_without_reentering_valid_context`: `99` → useful number correction → `1` creates a fresh exact proposal with no POST. This does not prove actual keyboard focus, tab order, scrolling/target usability, screen-reader support, or assumptions about age/diagnosis/handedness. |
| [Nina-Jean](../product/personas.md#nina-jean--nina-jean-understand-choices-and-correct-preferences), `5d4d7083-1479-4637-90cd-5e841bfe080d@1`; US3, US1 | Unfamiliar terminology/ambiguous request: one bounded plain specialty choice, explicit typo suggestions rather than clinical guessing, visible location correction and revoked proposal. [SchedulingSession availability/_preferences](../../src/ochsner_bob/session.py), actual [RapidFuzz suggest](../../src/ochsner_bob/suggestions.py), [Conversation safety routing](../../src/ochsner_bob/conversation.py). | `test_nina_jean_gets_plain_choice_and_explicit_typo_correction_not_clinical_guess`: missing specialty names Primary care/Dermatology; typo does not choose automatically; explicit correction updates canonical preferences; medical interruption gives no advice or booking. Natural-language ambiguity/classification needs separate [genuine qualification](live-qualification.md); this deterministic journey does not prove it. |
| [Morgan-Rae](../product/personas.md#morgan-rae--morgan-rae-understand-request-and-unresolved-work-without-repetition), `657aedfe-4a4a-4ec4-83c0-52614111f07c@1`; US5, US3 | Incomplete support context: distinguish known/missing facts, current versus last acknowledged screen, freshness, booking outcome and queue/demo participation; no consent nonce in either mirror; another session stays isolated. [BrowserService.read/ack/command](../../src/ochsner_bob/browser_service.py), [SchedulingSession.support_view/handoff](../../src/ochsner_bob/session.py). | `test_morgan_rae_observes_acknowledged_screen_and_truthful_paired_handoff`: unseen public progress does not advance observation; verified proposal is acknowledged without nonce; support cannot confirm; takeover revokes it; return and real mock handoff are distinct from joining staff. [SessionContractTests.test_decline_preserves_historical_success](../../tests/test_session_contract.py) and [SuppliedHttpScenarioTests.test_slot_conflict](../../tests/test_supplied_http.py) cover prior/current outcome distinctions. Server semantic evidence, not pixel fidelity or real representative delivery. |
| [Sam-Rae](../product/personas.md#sam-rae--sam-rae-expose-unsafe-confirmations-and-recovery), `98e1dcd5-8ee9-4b2b-b7fe-2045d389b9b4@1`; US4, US6, US1 | Adversarial/replayed/uncertain outcomes: inspect → fork → compare → reviewed fixture proposal stays isolated; reference is not access; unknown write survives reset/re-identification and blocks retry. [InteractionService capture/replay](../../src/ochsner_bob/interaction_service.py), [Replay](../../src/ochsner_bob/replay.py), [SchedulingSession._effect](../../src/ochsner_bob/session.py), [EffectJournal](../../src/ochsner_bob/journal.py). | `test_sam_rae_reviews_and_forks_recording_without_live_authority_or_hidden_parity` runs real public HTTP capture, isolated replay/fork/compare and review-gated proposal with no new HTTP or live state change; another capability cannot open it. `test_sam_rae_unknown_wire_result_survives_reset_and_fresh_identity_without_retry` loses the HTTP response deliberately, keeps unknown explicit, and forbids a second POST after reset/fresh identity. Replay explicitly reports `core_renderer_parity=false`; neither pin nor fixture is consent. |

Support/Admin coverage is Morgan-Rae's truthful context/read-only mirror plus
Sam-Rae's reproducible diagnostics/review; it does not invent an admin console,
accounts, authenticated production support, delivery capability or authority.
US2's complete identity correction/history contract remains in
[SuppliedHttpScenarioTests.test_multiple_patient_matches](../../tests/test_supplied_http.py)
and [ConversationTests.test_private_chat_never_becomes_identity_or_reaches_language](../../tests/test_conversation.py),
not inferred from persona traits. US6 operational coverage also links
[CliAndOwnedMockTests](../../tests/test_conversation.py) and
[browser launcher tests](../../tests/test_browser_launch.py); these do not by themselves
prove clean-copy installation or actual browser usability.

## US6 budget-candidate evidence — 2026-10-12

Sam-Rae's pinned adversarial/uncertain-outcome needs above also motivate inspectable
model accounting; persona selection supplies no spending permission. FR-025/025a
come from separate Operator direction. [ModelBudget](../../src/ochsner_bob/model_budget.py)
preserves unknown liability and late settlement after fixed-day expiry.
[Window](../../tests/test_budget_window.py), [launch](../../tests/test_budget_window_launch.py)
and [readiness](../../tests/test_budget_preflight.py) regressions test default denial,
explicit opt-in, expiry, storage headroom and no readiness mutation. Source baseline
`d925f326dd604b3eba07d844914810e2f2574705`; exact candidate/review status stays in
[native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md#fixed-day-bob-budget-candidate--2026-10-12).
No patient/support authority, console, paid model or actual UI evidence is added.

## Reproduction and limits

Reproduce offline with explicit project Python 3.11+:

```sh
BOB_ENABLE_OPENAI=0 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -p test_persona_acceptance.py -v
```

The eight tests use real SchedulingSession, Conversation, BrowserService,
InteractionService, standalone ZEN, RapidFuzz, private temporary journals and
the unchanged supplied synthetic HTTP handler/store. Only the unknown-result
case substitutes a disconnecting external HTTP wire. No live model, patient,
secret, production service or new budget reservation is involved.

Not established by these eight tests alone: full browser/assistive-technology
usability across these persona journeys, unsupported-hour explanations,
comparative/low-confidence user testing or clean-copy setup. The historical final parent
section below supplies separate bounded operational/browser evidence.
Actual channel availability, language and research validation remain unknown
for all seven pins. Basic-phone access, real staff delivery, clinical suitability,
production authentication and mobile/screen-reader/platform certification are
not supplied capabilities. The persona index must not turn these into passes.

## Historical source-bound evidence

The dated counts and pending/candidate wording below belong to their original
checkpoints, not a fresh verification or current integration-status claim.

Reviewed 2026-10-09 against base `a43fb61532a62f83b91dd862099419b385caee98`
plus dirty integration on that date. This is a constraint/evidence crosswalk,
not a second task ledger. [Native US1–6 and acceptance criteria](../../specs/001-ochsner-scheduling-assistant/spec.md)
own story detail; [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md)
own completion. Story wording is inferred from accepted requirements and pinned
needs, not evidence of research validation. See [design](../../specs/001-ochsner-scheduling-assistant/plan.md),
accepted B17/R01–R16 and interaction contracts from private local intake
`002.md`/`003.md`, reconciled in the native spec. Originals are intentionally
excluded from Git/clean exports; they are reference data, not additional authority.

## Adversarial recovery evidence — 2026-10-10

Runtime/test source `f7f852c613e306123041866b379a093255582543`; exact persona pins
below are unchanged. US2 Jules/Billy-June's recoverable-correction requirement maps
to [private draft recovery tests](../../tests/test_identity_draft_recovery.py):
correct only the invalid field, never reuse prior verified authority, no private
draft mirroring/model/persistence. US4 Sam-Rae maps to
[empty Replay regressions](../../tests/test_replay_empty.py), including unchanged
historical imports with explicit gaps and no live effects. US4/US5 Morgan-Rae's
truthful Support context maps to [HTTP recovery tests](../../tests/test_local_transport.py)
and [shipped-widget checks](../../tests/test_widget_projection.py): unavailable
references do not imply failed pairing, and the same fixed notice is mirrored.
US6 maintainer reliability maps to [owned acquisition tests](../../tests/test_mock_acquisition.py).
Integrated affected suite: 105 passed; offline service/renderer/lifecycle evidence,
not new browser, accessibility, user-research or model qualification. Final
qualification/review progress remains solely in [native T064–T069](../../specs/001-ochsner-scheduling-assistant/tasks.md).

## Stage-one quality evidence — 2026-10-10

Runtime/test source `56fc4e8bc10ec4a15dc2befabb76208f2d64a807` (candidate).
US4 Sam-Rae's inspectability constraint maps to
[`InteractionService._open_off_inspection`](../../src/ochsner_bob/interaction_service.py)
and [six OFF-reference contracts](../../tests/test_off_reference.py): owned,
bounded current sanitized diagnostics, fixed expiry, no historical state or live
effects, no recording store and no inherited fork/export target. US5 Morgan-Rae's
paired-session privacy boundary is retained; another patient's reference is denied.
US6 reviewer/maintainer setup maps to explicit widget ESM classification,
[Node regressions](../../tests/test_widget_projection.py), the
[nested namespace launch check](../../tests/test_browser_launch.py) and adapted
[qualification profile](qualification.json). Fresh combined 422 tests and all
profile steps passed locally, including a clean committed export/install on
Python 3.11.13/macOS ARM. Node 22.14.0 checks passed with syntax detection both
enabled and disabled. This is offline contract/setup evidence, not new browser,
live-model, accessibility or user-research validation. Actual CI/review status
belongs only in [native T057–T063](../../specs/001-ochsner-scheduling-assistant/tasks.md).
The exact persona pins and historical journeys below are unchanged.

## Completeness repair evidence — 2026-10-10

US4/US6 Sam-Rae and US5 Morgan-Rae: [ordered receipt tests](../../tests/test_view_receipt_capture.py)
bind actual acknowledgement API observations to delivered revisions, distinguish
missing/partial evidence from full replay and reject imported authority.
[Recording-OFF diagnostic tests](../../tests/test_live_diagnostics.py) exercise
actual browser/CLI constructors, isolated/restored sessions, final API certainty,
public model context/field categories/timing and nonmutating inspection. These
are offline service/renderer contracts, not new actual-browser or paid-model
qualification. Reviewed code/test source `c8463252251dd840ac443641702656fd3134eebc`
/ RC-2: 415 tests/all demos passed; independent repair-delta review clear.
Repair base `00ed37d`; native T056 holds the PR/results/limits.
The exact persona pins and historical source-bound journeys below are unchanged.

## Current follow-on evidence — 2026-10-10

Source `e2dfa7e9f471513921063d568bb3bc890eff1800` / immutable RC-1.
US2/US4 continuity and developer evidence: [post-booking replay regressions](../../tests/test_post_booking_replay.py)
bind validated dynamic appointments without private row persistence and retain
fail-closed malformed/foreign/ambiguous evidence. US5 Support/Admin and US4
Developer: [Support status regressions](../../tests/test_support_status.py),
[shipped-widget tests](../../tests/test_widget_projection.py) and actual S30–32
captures distinguish joined membership from the control lease, including before
first observation. No support identity/select/confirm permission is added.
US1/US3/US6 uncertainty/safety: actual F08–F10 captures retain blocking through
Reset/reverification/new selection, with a separately disclosed receipt-loss
fault. [Feature notes](video-notes.md#feature-completion-supplement--2026-10-10)
and manifest bind each original to its real source/mode.

Combined 398 tests and all three demos passed in the parent and clean committed
export/install. These are bounded regressions/actual selected browser journeys,
not user research or all-persona/assistive-technology acceptance. Pinned persona
needs and unresolved/deferred channel capabilities below are unchanged.
Earlier review dates/source/counts remain historical; the native ledger owns
completion, not this crosswalk.

## Evidence and remaining checks

Tests were written and executed before this index was expanded. Initial run:
eight tests, seven passed/one test-helper error (support responses nest the
patient revision). Correcting that helper produced **8/8 passed** with the
existing production code unchanged. This is new acceptance evidence over
implemented behavior, **not** a claimed historical production red/green cycle.
No source-text/card-presence assertions count as persona adoption proof.
The combined offline unittest suite then passed **360 tests in 18.600 seconds**
with project Python **3.11.13**. A test-only negative control that substituted
current state for the acknowledged support snapshot caused Morgan-Rae's real
observation assertion to fail, as intended. The substitution was scoped to that
test process; no production source was changed and it is not product red/green.

Parent-reported browser observations (2026-10-09), not rerun by this slice:
actual Chrome booking, pairing/takeover/return and format correction; later
offline capture → Help → discover → seal → open → step passed, displaying
`core_renderer_parity=false`. Parent also reported one additional genuine public
model call (41 cumulative calls); this index neither re-qualifies it nor revises
the private budget. See [framework evidence](marimo-feasibility.md) and
[genuine language evidence](live-qualification.md) for their own sources/limits.
No card, API journey, injected fixture or parent-reported observation is labeled
an independently completed browser acceptance suite here.

## Final parent integration evidence — 2026-10-09

Reviewed code/test revision `5e7ae0c6b1ae29d198f734a0c26e2c96e525b961`: parent 387 combined tests passed
(21.155 s), then a fresh clean committed export passed the same 387 tests
(19.282 s), all eight supplied scenarios, demos and six renderer checks. Earlier
360-test snapshots above are historical. Clean-copy setup is now qualified on
this Mac/Python target, not inferred from a persona card or starter tests.

Actual Chrome evidence remains bounded to the described journeys: returned-slot
booking/separate confirmation, keyboard numbered selection, read-only reload,
shared-core booking capture/replay and isolated unknown fork; final specifically
approved read-only paired tab showed fresh revision 5/completed and empty/disabled
private fields. Final takeover was outside that narrow grant and not rerun;
earlier actual takeover/suggestion/return evidence remains separate. Source/mode
boundaries and still hashes are in [video notes](video-notes.md).
Full seven-persona browser/assistive-technology usability, unsupported-hour
explanations and comparative/user-research hypotheses remain unproven. No
production, real-staff, basic-phone or mobile capability is invented.
