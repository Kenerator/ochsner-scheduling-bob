# As-built code walkthrough

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
400/409 rejection versus 404/503 failure versus uncertain-outcome distinction.
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

## Production entry points

The [public exports](../../../src/ochsner_bob/__init__.py) are SchedulingSession,
HttpMockAdapter, ApiError and UnknownOutcome. Retained `core.py` / `adapters.py`
are the sketch, not production authority. [Historical core tests](../../../tests/test_bob_core.py)
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
   a unique actual patient match. ZIP filters returned candidates locally, without
   exposing candidate identities. Correction clears old private state first;
   failed refresh clears stale slots/appointment rows before I/O.
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

Shared interface: `Conversation(session, language=None)`,
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
slot. Validated 400/409 are rejection; validated 503 is definite failure; lost,
malformed or mismatched write responses are UnknownOutcome. Exceptions/events
never expose private response/request values; events are method/normalized route/
status/latency only.

[http_support.py](../../../tests/http_support.py) owns ephemeral unchanged supplied
servers with synchronized categorical audits. Eight exact supplied scenario IDs
run real Session + Policy + EffectJournal + HTTP. SessionContractTests' safe unit
fixture is not supplied-service acceptance evidence.

## Browser, Interaction and widget

RC-1 repair: [Support status regressions](../../../tests/test_support_status.py)
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
raw notice text, pixel state, a nonce or consent. Legacy three-field receipts remain valid.
Support suggests public preferences; patient explicitly adopts after
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
takeover lease. Sidecar URL is fixed at `http://127.0.0.1:28451` (default UI port
28450); changing launcher ports alone does not reconfigure it.

## Replay and optional language

RC-1 repair: InteractionService validates post-booking appointment rows against
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
full browser draft/focus/acknowledgement state are outside the core projection.
Variants are counterfactual simulations, not assertions of historical parity.

[RecordingStore](../../../src/ochsner_bob/recording_store.py) provides private atomic
quota-bound retention/expiry/tombstones/purge, separate from effect claims. Replay
step/jump/bookmark/fork/compare/regression proposals cannot reach HTTP/models/the
journal. References locate records, not grant access; service grants are memory-
only/session-scoped. Reviewed exports are still untrusted data. See
[replay tests](../../../tests/test_replay_contract.py), [store tests](../../../tests/test_recording_store.py)
and [fidelity limits](architecture.md#replay-fidelity-and-retention).
The [same-core tests](../../../tests/test_replay_live_core.py) prohibit network,
disk-journal construction and legacy-interpreter fallback during a supplied-HTTP
capture replay, while checking unchanged live state/journal/write count.
InteractionService's `maintain_retention()` additionally sweeps retained idle
memory/store state. The launcher schedules it through the server's poll-loop
`service_actions`, even without patient traffic; this is not a detached daemon.

[LanguageAdapter](../../../src/ochsner_bob/language.py) receives public text and
preferences/workflow only, proposes closed public actions and supplies no identity
or consent. [ModelBudget](../../../src/ochsner_bob/model_budget.py) reserves before
dispatch against the one `.bob-local/model-budget.json` used by CLI/browser/
qualifier; construction/view does not dispatch. Unknown billing keeps the
reservation. [Language](../../../tests/test_language.py) and
[budget tests](../../../tests/test_model_budget.py) are offline evidence; injected
model transports are explicitly fixtures, not genuine model qualification.
The separately scoped [genuine language record](../live-qualification.md) retains
default-model failures and the explicitly selected alternative's semantic result.

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
