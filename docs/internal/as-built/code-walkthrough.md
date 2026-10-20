# As-built code walkthrough

Pending-review transport delta (2026-10-19): see the
[private diagnostic path](#private-transport-diagnostic-path) and native
[T115–T118](../../../specs/001-ochsner-scheduling-assistant/tasks.md#private-transport-diagnosis--2026-10-19).

Current scoped source: reviewed `f785f83` (2026-10-16); the connected run stopped
failed/incomplete, not semantically qualified. Exact source/checks and next steps
are in [native T108–T114](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
and the [execution record](../live-qualification.md#connected-holdout-execution--failedincomplete-2026-10-16).

Updated 2026-10-14 against reviewed runtime source
`79aeafd6269dd1e54f9429a3cdf49b30070b153c`, integrated as
`d3c3a044575c5666c220ab89dcb680b8a456fcbb` with the identical selected tree.
Native T087–T098 records review/qualification/CI/integration and its historical
activation handoff; later Operator-requested support restoration retained existing
accounting/effects. Follow the actual local synthetic
workflow from entry points to authority/effect boundaries, then inspection and
optional language. This is a source map, not a second completion ledger or a
production-readiness claim. Earlier repairs integrated through
[PR #6](https://github.com/Kenerator/ochsner-scheduling-bob/pull/6); budget/L3 through
[PR #8](https://github.com/Kenerator/ochsner-scheduling-bob/pull/8).
Training/Flight Deck source reviewed at `4a7a5cf`, integrated through
[PR #11](https://github.com/Kenerator/ochsner-scheduling-bob/pull/11) as `7494bb0`;
runtime source above was unchanged at that training delivery. `f785f83` adds the
existing-storage option described below; native tasks retain actual evidence/gaps.

Navigation: [entry points](#entry-points) → [booking](#follow-a-booking) →
[boundaries](#boundary-modules) → [browser/Support](#browser-interaction-and-widget) →
[diagnostics/Replay](#diagnostics-recording-and-replay) → [language](#optional-language).
[Architecture A–D](architecture.md#components-and-authority) supplies matching
zoom-ins; [spec](../../../specs/001-ochsner-scheduling-assistant/spec.md),
[plan](../../../specs/001-ochsner-scheduling-assistant/plan.md),
[decisions](../../product/decisions.md) and [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
retain requirements/design/completion. [Dated evidence](#history-and-evidence)
is kept at the bottom and never relabeled as new execution.

<a id="production-entry-points"></a>

## Entry points

The [managed launcher](../../../tools/poc-runtime/launch.py) loads
[public BOB config](../../../poc-launch.json), validates request/readiness, resolves
only the exact named Secure Note field in model mode, constructs role-scoped
process specs and supervises owned children. Its [manifest](../../../tools/poc-runtime/export-manifest.json)
pins shared-source bytes; consumer [tests](../../../tests/test_runtime_launcher.py)
exercise actual BOB boundaries. Explicit direct entrypoints below remain available.

The [public exports](../../../src/ochsner_bob/__init__.py) are SchedulingSession,
HttpMockAdapter, ApiError and UnknownOutcome. Retained `core.py` / `adapters.py`
are the sketch, not the active scheduling implementation. [Historical core tests](../../../tests/test_bob_core.py)
and [authority regressions](../../../tests/test_authority_regressions.py) explicitly
import that sketch; passing them does not establish supplied-service acceptance.

| Entry | Actual role | Evidence |
| --- | --- | --- |
| [__main__.py](../../../src/ochsner_bob/__main__.py) | Multi-turn CLI using shared Conversation; offline default, `--api-url`, supplied `--scenario`, `--journal`, explicit `--openai` | [Conversation/CLI tests](../../../tests/test_conversation.py) |
| [serve_browser.py](../../../scripts/serve_browser.py) | Owned mock process plus InteractionService and loopback transport outside Marimo kernels | [Launcher tests](../../../tests/test_browser_launch.py), [transport tests](../../../tests/test_local_transport.py) |
| [scheduling_app.py](../../../apps/scheduling_app.py), [widget.py](../../../src/ochsner_bob/widget.py), [widget.js](../../../src/ochsner_bob/widget.js) | Marimo AnyWidget rendering/submission, not independent scheduling authority | [Widget tests](../../../tests/test_widget_projection.py), [early browser probe](../marimo-feasibility.md) |
| [demo_booking.py](../../../scripts/demo_booking.py), [mock_lifecycle.py](../../../scripts/mock_lifecycle.py) | Real supplied HTTP success/conflict; separately labeled adapter-boundary unknown fault | [Owned lifecycle/demo tests](../../../tests/test_conversation.py) |

OwnedMock imports the unchanged vendored Store/Handler, binds its own ephemeral
or explicit numeric loopback port and runs Popen with raw output suppressed.
L3 delta, updated 2026-10-12, reviewed at `8908ef9` and integrated as `c7c53a3`: its child now
receives only PATH/locale/TZ/temp/SYSTEMROOT plus forced bytecode suppression,
not the parent model/vault/token/import environment. The actual child/vendor
readiness and cleanup boundary is tested with private Boolean-only
[canary reports](../../../tests/test_mock_child_environment.py). Exact CI and
restoration evidence are in [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md#l3-secret-free-mock-child-prerequisite--2026-10-12).
Cleanup terminates only its child, never an unrelated listener. See
[vendor provenance](../../../vendor/reference/PROVENANCE.md) for source/fixture hashes.

[cli_namespace.py](../../../src/ochsner_bob/cli_namespace.py) now restores one opaque
effect namespace for the same CLI journal, under an exclusive lifetime lock. It
persists no identity/consent, checks the immutable binding before every turn and
rejects missing/corrupt/unsafe/legacy state or foreign journal claims. An explicit
new `--journal` path is required for a genuinely new synthetic mock run; changing
API/scenario flags does not replenish uncertainty. See
[CLI restart regressions](../../../tests/test_cli_restart.py).

## Follow a booking

1. [Conversation](../../../src/ochsner_bob/conversation.py) routes Help, medical
   boundary and unsupported input before privacy/model handling. Deterministic
   commands need no model; identity uses dedicated local controls, never chat.
2. [SchedulingSession.command](../../../src/ochsner_bob/session.py) checks actor
   and exact revision under its lock. Accepted turns increment revision and revoke
   the old proposal. Stale submissions have no effect.
3. Public providers require no identity. Private availability/appointments require
   a unique returned synthetic patient match. ZIP filters returned candidates locally, without
   exposing candidate identities. Correction clears old private state first;
   failed refresh clears stale slots/appointment rows before I/O. `_identity` retains
   a bounded private invalid candidate so fixing one field can recover, but never
   retains prior verified authority or sends drafts to recording/model/Support.
   Omitted fields reuse only that candidate; unsupported keys or non-text values
   clear it and reject. Reset clears the candidate as well as workflow state,
   but does not erase unresolved effect protection.
4. Selecting an actual returned slot creates a proposal, not consent. Provider,
   date, identity or ordinary-text corrections revoke the prior proposal.
5. Dedicated confirmation supplies the displayed proposal ID, nonce and revision.
   Real ZEN permission is necessary but cannot bypass structural identity/consent.
6. The journal durably claims before POST. Validated success/rejection/failure and
   unknown are distinct. Unknown cannot be retried through reset.
7. Views separate latest attempted result from copied prior receipt history.
   Starting another proposal does not itself clear that result; reset clears
   workflow/private state, not uncertainty or history. A handoff is mock queued,
   not real staff contact.

Shared interface: `Conversation(session, language=None, *, diagnostic_sink=None)`,
`interpret(text, expected_revision)`,
`enter_identity(phone, dob, zip_code=None, *, expected_revision)`,
`confirm(proposal_id, nonce, *, expected_revision)`, `view()`.
Interpretation adds categorical mode/status. Text invalidates consent before a
model wait; delayed output cannot overwrite a later revision. Plain “yes” is not
the dedicated confirmation control.

## Boundary modules

| Source | Enforced boundary | Tests |
| --- | --- | --- |
| [session.py](../../../src/ochsner_bob/session.py) | Revision/actor checks, matching/corrections, private-read clearing, current/prior certainty, categorical trace | [Unit contract](../../../tests/test_session_contract.py), [transition acceptance](../../../tests/test_transition_acceptance.py) |
| [http_mock.py](../../../src/ochsner_bob/http_mock.py) | Actual supplied HTTP, strict fields/types/calendar/offset-aware times, exact booking receipt match | [Hostile transport](../../../tests/test_http_adapter.py), [eight supplied scenarios](../../../tests/test_supplied_http.py) |
| [policy.py](../../../src/ochsner_bob/policy.py), [bob.json](../../../policies/bob.json) | Actual zen-engine graph, five closed categorical facts, loaded-byte digest, fail-closed errors | [ZEN tests](../../../tests/test_zen_policy.py), including 240 fact combinations |
| [journal.py](../../../src/ochsner_bob/journal.py) | Stable flock/thread lock, private atomic/fsynced durable claims; persisted attempted becomes unknown; corrupt/missing storage denies | [Journal tests](../../../tests/test_effect_journal.py) |
| [suggestions.py](../../../src/ochsner_bob/suggestions.py) | RapidFuzz public vocabularies/current public providers only; no patient search, auto-selection or implicit adoption | [Transition tests](../../../tests/test_transition_acceptance.py) |

`HttpMockAdapter(base_url, scenario=None, timeout=2, *, event_sink=None)` exposes
providers, search_patients, availability, appointments, book and handoff. It
permits HTTP numeric `127.0.0.1` with explicit port only, direct connections/no
proxies, no redirects/retries, bounded finite timeout and 256,000-byte body.
Booking checks patient/provider/specialty/location/startTime against the submitted
slot. Recognized schema/code-matching 400/409 writes are rejection; recognized 503
is definite failure. Raw POST 404 is unrecognized and remains unknown, unlike
an injected Session ApiError(404) classified as failed. Lost,
malformed or mismatched write responses are UnknownOutcome. Exceptions/events
never expose private response/request values; events are method/normalized route/
status/latency only.

[http_support.py](../../../tests/http_support.py) owns ephemeral unchanged supplied
servers with synchronized categorical audits. Eight exact supplied scenario IDs
run real Session + Policy + EffectJournal + HTTP. SessionContractTests' safe unit
fixture is not supplied-service acceptance evidence.

## Browser, Interaction and widget

[Support status regressions](../../../tests/test_support_status.py)
pin the paired role independently from takeover. BrowserService resolves joined;
SchedulingSession reports only control status and unknown membership. The widget
renders joined/inactive with zero lease both before and after takeover, including
before a first observation; [renderer tests](../../../tests/test_widget_projection.py)
exercise the shipped JavaScript. Return does not remove the role binding.

[BrowserService](../../../src/ochsner_bob/browser_service.py) owns role-bound opaque
capabilities, pairing, exact delivered/acknowledged views and takeover leases.
Support's `observed_patient` is the last accepted patient renderer receipt, not
current server state relabeled as seen. Both support snapshots remove proposal
nonces. Bounded revision/renderer/visible/public-draft/focus/scroll/disclosure
receipts must acknowledge an actually delivered response. Age/staleness remains
visible. Optional strictly typed `presentation: {notice, pending, dirty, can_confirm}`
carries categorical warning/pending/unsent-edit and observed enabled-state, not
raw notice text, pixel state, a nonce or consent. Legacy three-field presentation objects (not whole receipts) remain valid for
live acknowledgement; missing can_confirm makes exact capture incomplete.
Fresh requires the current revision and acknowledgement age under five seconds;
the independent takeover lease is 300 seconds. BrowserService rejects Support
identity/availability/appointments/select/confirm/handoff commands. Support
suggestions require active control and current revision; patient explicitly adopts after
return, then freshly selects/confirms. [Browser tests](../../../tests/test_browser_service.py)
cover isolation, role/freshness checks and restart bindings.

[InteractionService](../../../src/ochsner_bob/interaction_service.py) adds shared
Conversation and actual-boundary capture. Language waits do not hold the global
lock: polling, other sessions and local safety controls continue. Outcomes are
turn/revision-bound. Delivered snapshots include final categorical notices for
truthful acknowledgement. Its `live` label means the real local core path, not
proof of a paid model call. See [interaction tests](../../../tests/test_interaction_service.py).
[local_transport.py](../../../src/ochsner_bob/local_transport.py) checks exact
Host/Origin, bearer capability and bounded closed JSON schemas; raw logs are off.

The shipped widget uses textContent for untrusted strings, the same read-only
patient renderer for support observation, and separate current-context labeling.
Per-tab sessionStorage holds capabilities/public drafts/disclosures, not private
identity drafts. Dirty unsent changes disable confirmation, which submits the
shown snapshot. Poll/ack does not schedule or invoke models; reads may expire a
takeover lease. Default sidecar/UI remain 28451/28450. The L4 candidate adds a
synced, validated public `backend_url` trait from `BOB_TRANSPORT_URL`; it permits
only numeric IPv4 loopback HTTP and JavaScript uses that trait. Direct custom
pairs set it explicitly; the managed launcher sets it on the key-free viewer.
[Consumer tests](../../../tests/test_runtime_launcher.py) exercise actual model
constructors, role-scoped child environments, no-call readiness, configured
renderer routing and real owned offline HTTP cleanup. This is not live-model
qualification; [native L4 status](../../../specs/001-ochsner-scheduling-assistant/tasks.md#l4-model-first-consumer--2026-10-12)
records the adopted CLI correction and completed review/CI/protected integration.

## Diagnostics, recording and Replay

InteractionService validates post-booking appointment rows against
the current approved fixture identity and a unique approved public-slot projection.
It records fixture bindings, not private rows or receipt IDs. The recorded-only
port reconstructs simulation placeholders; missing/extra/foreign/ambiguous data
remain gaps. [Post-booking replay regressions](../../../tests/test_post_booking_replay.py)
cover Confirm → appointments → seal/open/export/import with semantic parity,
privacy checks and fail-closed invalid bindings. Live booking/effect behavior is
unchanged. Same-reference re-import cannot revive a purged store tombstone.

[replay.py](../../../src/ochsner_bob/replay.py) drives actual SchedulingSession
through fixed recorded-only fixtures and private memory claims. Actual capture
replaces private values with approved host fixture bindings. Each replay starts
with a fresh isolated namespace and recomputes authority; imported records supply
no live identity, proposal nonce, consent, callbacks, endpoints or journal path.
Per-command comparison with the original sanitized core projection detects gaps
and mismatches. Matching complete captures report `core_semantic_parity=true`;
legacy recordings without core evidence remain explicitly incomplete.
`core_renderer_parity=false` remains truthful: private records, receipt IDs and
browser execution is outside the core projection. Ordered original browser
receipts are separately retained as `observed_views` when captured; missing required receipts remain
incomplete, not silently regenerated by core parity.
Variants are counterfactual simulations, not assertions of historical parity.

[RecordingStore](../../../src/ochsner_bob/recording_store.py) provides private atomic
quota-bound retention/expiry/tombstones/purge, separate from effect claims. Replay
step/jump/bookmark/fork/compare/regression proposals cannot reach live HTTP/models/the
durable effect journal. References locate records, not grant access; service grants are memory-
only/session-scoped. Reviewed exports are still untrusted data. See
[replay tests](../../../tests/test_replay_contract.py), [store tests](../../../tests/test_recording_store.py)
and [fidelity limits](architecture.md#replay-fidelity-and-retention).
The [same-core tests](../../../tests/test_replay_live_core.py) prohibit network,
disk-journal construction and legacy-interpreter fallback during a supplied-HTTP
capture replay, while checking unchanged live state/journal/write count.
InteractionService's `maintain_retention()` additionally sweeps expired recording/capture/open-Replay
memory/store state, not all session identity/diagnostics or effect/budget state. The launcher schedules it through the server's poll-loop
`service_actions`, even without patient traffic; this is not a detached daemon.


[diagnostics.py](../../../src/ochsner_bob/diagnostics.py) separates `ObservedAPI`
(validated outcomes/timing) from bounded `Diagnostics` metadata. CLI constructs
that observer directly; `InteractionService._attach` wires capture observation
and its per-session diagnostics. `Conversation` publishes public model context,
accepted/rejected fields, application status and latency. Raw identity/text,
receipts and exception payloads are withheld; metadata is not an exact transcript.
`diagnostics()` and CLI `/diagnostics` inspect without scheduling/model effects.
`SchedulingSession.command` validates an allowlisted handoff reason, `_effect`
attaches it only to that claimed attempt, and `_event` retains the selected
category. `ObservedAPI` passes a fifth handoff-only category argument;
`InteractionService._api_observation` forwards it only to ordinary diagnostics,
not capture observations. `render` adds the categorical CLI label. See
[OFF diagnostics tests](../../../tests/test_handoff_diagnostics.py) for queued,
rejected, failed, unknown, invalid/private input, duplicate and replay compatibility.

`InteractionService._summary` registers bounded OFF references;
`_open_off_inspection` checks ownership/expiry and opens current sanitized
diagnostics with separate requested/current revisions and
`historical_state_available=false`, without API/model calls. It clears any prior Replay
target: OFF inspection is not a RecordingStore/replay/fork/export fallback.
`ReferenceUnavailable` maps to the same generic transport 403 for unknown,
foreign or ungranted references. The shipped widget recognizes only the closed
Replay category, preserves a valid capability and mirrors a fixed `reference`
notice; join/true-capability failures retain separate guidance. See
[OFF contracts](../../../tests/test_off_reference.py),
[HTTP notice contracts](../../../tests/test_local_transport.py) and
[widget harness](../../../tests/widget_harness.mjs).

`Recording.require_view/acknowledge` retains bounded ordered receipts bound to
delivered core-step revisions. `Replay.fork` clears both empty-result lists;
`_RecordedPort._result` defensively returns no rows, and `Recording.missing`
discloses contradictory historical imports without rewriting their bytes/digest.
[Empty-read tests](../../../tests/test_replay_empty.py) cover discovery,
availability and appointments; [receipt tests](../../../tests/test_view_receipt_capture.py)
cover captured observations, gaps and non-authoritative imported presentation.

## Optional language

[LanguageAdapter](../../../src/ochsner_bob/language.py) receives public text and
preferences/workflow only, proposes closed public actions and supplies no identity
or consent. [ModelBudget](../../../src/ochsner_bob/model_budget.py) reserves before
dispatch against `.bob-local/model-budget.json`, the CLI/browser path and
qualifier default. The qualifier accepts `--budget` only when it is the canonical
path, never a fresh-history override; construction/view does not dispatch.
Actual application and functional qualification constructors select uncapped
covered-execution accounting. The qualifier privately resolves the exact Ochsner
Secure Note `notes` through the pinned helper, not an inherited key. Explicit live
opt-in remains; LLM generation of app/spec/test code is outside this authorization.
[RuntimeLedger](../../../src/ochsner_bob/runtime_accounting.py) stores indexed
transactions at the same canonical path, migrates validated JSON atomically with
all history/IDs/configuration, and retains private locking/marker and fail-safe
storage validation. Readiness is read-only and activation requires old writers
quiescent. See [runtime boundary](architecture.md#indefinite-runtime-accounting--2026-10-13).
Unknown
billing keeps the reservation. [Language](../../../tests/test_language.py) and
[budget tests](../../../tests/test_model_budget.py) are offline evidence; injected
model transports are explicitly fixtures, not genuine model qualification.
The separately scoped [genuine language record](../live-qualification.md) retains
default-model failures and the explicitly selected alternative's semantic result.

[connected_qualification.py](../../../scripts/connected_qualification.py) validates
bounded synthetic manifests, runs real Conversation/Session against OwnedMock and
records categorical HTTP/language/effect evidence. Local confirmation consumes the
immediately returned proposal only; a completed booking gets an actual appointments
readback. Fresh effect journals are per journey; model accounting is supplied once
by the caller, never replenished. [Development tests](../../../tests/test_connected_qualification.py)
use injected fixture transports and deny real HTTPS.
[qualify_connected_live.py](../../../scripts/qualify_connected_live.py) schedules
the declared 8×2 holdout with terminal-stop/unrun retention, binds the fixed owner
and exact existing SQLite, selects the pinned notes resolver/strong snapshot and
requires a reviewed source digest before live opt-in. `--dry-run` is public-source
only; `--preflight` is existing-state-only. Explicit `_existing_writes=True` adds
only existing-SQLite reserve/settle to the otherwise read-only mode; default
readiness semantics remain. [Policy tests](../../../tests/test_connected_qualification_policy.py)
use disposable owners/ledgers, not the Operator's state. An exclusive private run
report prevents accidental second-tranche replay; it is evidence, not a new budget
ledger or qualification claim. No legacy qualifier/prompt/case bytes are changed.

## Training contract and source-bound visuals

[check_catalog/check_placement](../../../tools/poc-docs/check_walkthroughs.py)
provide standard-library, read-only structural checking outside the app. Exact
local checker checkpoint `612d4bf` has 52 portable regression fixtures; BOB-only
[inventory/layer tests](../../../tests/test_bob_walkthrough_inventory.py) retain
seven groups/57 controls and validate current originals/layers. Composite raster
data must decode to the declared unchanged source; inert SVG/no-namespace geometry
is permitted, SMIL/CSS/foreign/linked active forms are denied. The checker does not
render or execute a workflow. [67 guides](../../user/walkthroughs/index.md) keep
their own install/launch/input/actions/results/recovery/effects/cleanup and link
exact automated-only paths where the current UI has no fault/clock trigger.
Their annotations are locator evidence, not newly captured failure outcomes.
The one independent collection review and affected correction are clear at
`4a7a5cf`, delivered through PR #11. BOB-only
[prerequisite tests](../../../tests/test_walkthrough_prerequisites.py) consume ordered
guide metadata against real service/session boundaries; they are not complete
browser journeys or human-prose qualification. Native tasks retain CI/merge/gaps.

The [Flight Deck entrypoint](../../../tools/aeos-dashboard/poc-flight-deck) loads
only the frozen PoC runtime. `PocCLI` verifies its manifest/resources, `PocInput`
resolves the native [mapping](../flight-deck/project.yaml), and
`PocSnapshotBuilder` keeps implementation/verification/acceptance distinct before
`Generator` renders six ignored artifacts. [BOB consumer tests](../../../tests/test_flight_deck_mapping.py)
run the actual input/generator with fixed public temporary fixtures. None of this
starts the app, reads a key, calls a model or invokes SDK reconciliation. The
[usage guide](../flight-deck/README.md) explains UNKNOWN narrative evidence and
snapshot/latest integrity; source-bound test/CI status stays in native tasks.

## History and evidence

These are historical source-bound checkpoints, not current execution claims.
Pending/candidate wording and numeric results below retain their original scope.
The revision at the top identifies the code inspected for this reorganization;
no new runtime/browser/model qualification is implied.

### Diagnostics/connected candidate checkpoint — 2026-10-16

Prepared on base `14474ac`: allowlisted OFF handoff diagnostics and the connected
qualification entrypoint/binding below were the new candidate delta. This dated
notice was moved from the top to keep current navigation concise. Independent
pre-live review cleared `f785f83`; the subsequent selected tranche stopped on its
first unavailable interpretation with unknown usage and no scheduling effects.
All 15 later executions remain unrun. No prompt/model change or retry followed.
Historical reviewed sources below remain unchanged in scope; the current
[execution record](../live-qualification.md#connected-holdout-execution--failedincomplete-2026-10-16)
and native tasks hold actual results and remaining delivery status.

## Adversarial repair delta — 2026-10-10

Updated against runtime/test source `f7f852c613e306123041866b379a093255582543`;
review/integration status belongs in [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
In [replay.py](../../../src/ochsner_bob/replay.py), `Replay.fork` canonicalizes
empty results, `_RecordedPort._result` defensively returns an empty list, and
`Recording.missing` identifies contradictory historical empty observations without
rewriting imports. [Tests](../../../tests/test_replay_empty.py) cover discovery,
availability, appointments, export/import and effect-free suffix recomputation.
In [session.py](../../../src/ochsner_bob/session.py), `_identity` keeps a private
candidate bounded to valid field maximum plus one, retaining invalidity until
correction while revoking authority first.
[Recovery tests](../../../tests/test_identity_draft_recovery.py) cover all three
discriminators, oversized/non-text/unsupported input, reset and privacy.

[OwnedMock.__enter__](../../../scripts/mock_lifecycle.py) closes its child on
unexpected startup exits before re-raising; [fake-child acquisition tests](../../../tests/test_mock_acquisition.py)
exercise select/read interruption, descriptor cleanup and terminate/kill fallback.
`ReferenceUnavailable` is mapped by [local_transport.py](../../../src/ochsner_bob/local_transport.py)
to the closed `reference_unavailable` response. [widget.js](../../../src/ochsner_bob/widget.js)
recognizes it only for Replay 403; join/invalid-capability failures retain their
own guidance. Session, BrowserService and Recording accept the same closed
`reference` notice category. [HTTP tests](../../../tests/test_local_transport.py)
and the [actual-widget harness](../../../tests/widget_harness.mjs) verify denial
indistinguishability, valid-capability retention and Support/recorded mirroring.
No component or diagram topology changed; see [architecture](architecture.md#adversarial-repair-delta--2026-10-10).

## Stage-one quality delta — 2026-10-10

Updated/reviewed runtime/test source:
`56fc4e8bc10ec4a15dc2befabb76208f2d64a807` (candidate, not an integrated RC).
In [InteractionService](../../../src/ochsner_bob/interaction_service.py), `_summary`
registers bounded OFF references with fixed TTL; `_open_off_inspection` exposes
only current sanitized diagnostics after session authorization. Requested/current
revision and `historical_state_available=false` prevent an exact-history claim.
No RecordingStore/API/model or domain mutation occurs; previous replay targets
are cleared so fork/export cannot silently address an older recording.
[Six OFF-reference regressions](../../../tests/test_off_reference.py) cover the
access/expiry/privacy/bounds/no-effect boundaries; existing replay/store tests
retain exact-recording guards.

[package.json](../../../src/ochsner_bob/package.json) explicitly classifies the
shipped widget as ESM; [widget tests](../../../tests/test_widget_projection.py)
exercise actual imports with syntax detection disabled. Node 22.14.0 is a
verification prerequisite, not application runtime.
The [workflow](../../../.github/workflows/bob-offline.yml) runs retained
`poc_template.qualification.qualify_project` against the [BOB profile](../qualification.json).
Inherited tools remain useful, not scheduling authority or an invented local
maintainer-test suite. The component diagram is unchanged; see the
[current boundary note](architecture.md#stage-one-quality-delta--2026-10-10).

## Completeness delta — 2026-10-10

Updated/reviewed 2026-10-10. Code/test source
`c8463252251dd840ac443641702656fd3134eebc` / immutable RC-2; repair base `00ed37d`.
415 tests/all demos passed; independent repair-delta review clear. Native T056
records the [protected PR](https://github.com/Kenerator/ochsner-scheduling-bob/pull/3)
handoff and limitations. This later documentation records that source; it does
not move the tag to include itself.
[diagnostics.py](../../../src/ochsner_bob/diagnostics.py) owns bounded final
API/model metadata; [Conversation](../../../src/ochsner_bob/conversation.py)
publishes public context, accepted/rejected categories, stale/application status
and model-port latency. [CLI](../../../src/ochsner_bob/__main__.py) exposes
inspection without interpreting it. [InteractionService](../../../src/ochsner_bob/interaction_service.py)
keeps this live evidence separate from capture observers and hooks actual
delivered views/acknowledgements into [Recording](../../../src/ochsner_bob/replay.py).
Replay exposes ordered original observations separately from recomputed core.
Imported drafts reuse the live privacy gate. Clock/order variants omit original
browser observations, and required-receipt markers obey both byte ceilings.
Model decoration and metadata share the service freshness lock; older diagnostic
revisions cannot overwrite newer ones. Write diagnostics retain the core's
400/409 rejection versus injected ApiError(404)/recognized 503 failure versus
uncertain outcomes. Raw HTTP POST 404 is unrecognized and stays unknown; this
source-accuracy clarification does not change historical test execution.
See [new constructor tests](../../../tests/test_live_diagnostics.py) and
[receipt tests](../../../tests/test_view_receipt_capture.py). The unchanged
diagram topology is in [architecture](architecture.md#completeness-delta--2026-10-10).
Historical RC-1 source/digests/counts below retain their original scope.

Historical checkpoint reviewed 2026-10-10: code/test source `e2dfa7e9f471513921063d568bb3bc890eff1800` (RC-1).
Documentation finalized after that tested source checkpoint. See the
[architecture snapshot](architecture.md#reviewed-source-and-verification) for
code digests and verification limits.

Navigation: [architecture](architecture.md), [spec](../../../specs/001-ochsner-scheduling-assistant/spec.md),
[plan](../../../specs/001-ochsner-scheduling-assistant/plan.md),
[native task ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md),
[decisions](../../product/decisions.md). This is a source map, not a completion ledger.

### Replay and optional language

Compatibility anchor retained after splitting the current walkthrough into
[diagnostics/recording/Replay](#diagnostics-recording-and-replay) and
[optional language](#optional-language).

## Evidence limits

[Architecture verification](architecture.md#reviewed-source-and-verification)
records the fresh suite/demos, navigation checks and Mermaid method. Node widget
tests use a minimal DOM/fetch harness, not actual-browser/accessibility evidence.
The genuine early Marimo probe predates the full UI and does not qualify final
renderer/reconnect fidelity. Subsequently, on 2026-10-09 the parent reported a
passed actual final-UI journey: capture → Help → discover → seal → open → step.
This is parent-observed browser evidence, not a rerun by this documentation
worker; it establishes that specific journey, not complete paired-renderer,
reconnect, accessibility or replay/core parity. The native ledger owns remaining
acceptance. CLI restart protection is tested at actual main reentry; this does
not claim remote idempotency or persistent restoration of the private workflow.

Source/export boundary: build_provenance uses only this exact Git root or fixed
bounded regular archive revision metadata, never an ancestor repository or an
environment-supplied revision. Archive state stays unknown/conservatively dirty;
actual source bytes are independently hashed. See
[8 provenance regressions](../../../tests/test_source_provenance.py).
The earlier qualified clean committed export passed 387 combined tests plus supplied-HTTP,
demo and shipped-renderer checks; the earlier Git-free startup failure is retained
in native tasks. A Git-free archive is supported, not a standalone wheel.
The RC-1 clean export/install subsequently passed 398 tests (19.696 s), pip
dependency checks and all three demos on Python 3.11.13/macOS ARM. Its capture
copy later changed only the widget backend port, explicitly disclosed in the
[current still manifest](../../../assets/ui/stills/feature-completion-20261010/manifest.json).

## Private transport diagnostic path

Updated 2026-10-19 against working source based on `c6102e5`; affected review pending.
In [language.py](../../../src/ochsner_bob/language.py), `_observe_transport` constructs
two sanitized primitives and ignores ordinary observer failures. `_http_transport`
observes constructor/connect/read/close outcomes once; the ordinary adapter still
validates output and settles usage exactly as before. No observation is added to
`LanguageOutcome` or ordinary UI/recording schemas. See
[transport tests](../../../tests/test_transport_diagnostics.py).
[diagnose_language_transport.py](../../../scripts/diagnose_language_transport.py)
binds one fixed input and source digest, checks explicit live opt-in, uses the
existing qualifier's canonical storage/resolver checks, then exclusive-creates a
private result before key access. It invokes only LanguageAdapter, never a Session
command or mock. [Runner tests](../../../tests/test_transport_diagnostic_runner.py)
exercise no-call dry-run, one reservation/unknown, prior report preservation,
exclusive replay refusal, source/config drift and private output boundaries.
Native tasks retain actual checks and the held review/live step, not this source map.
