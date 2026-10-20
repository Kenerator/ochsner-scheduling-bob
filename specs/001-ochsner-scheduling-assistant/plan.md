# Implementation Plan: Ochsner Best-of-Breed Scheduling Assistant

**Local Git**: `main` | **Date**: 2026-10-09 | **Spec**: [spec.md](spec.md)

**Input**: Reconciled feature spec, intake/RFP originals, pinned personas, project decisions, and Constitution.

**Note**: This template is filled in by the `$speckit-plan` command; its definition describes the execution workflow.

## Summary

Build one deterministic scheduling core with thin CLI, Marimo patient/support views, bounded language and supplied-HTTP adapters, standalone ZEN policy, public RapidFuzz suggestions, sanitized traces, replay/fork simulation, and truthful effect/handoff state. Identity, confirmation, effect certainty, and safety/help remain application-owned. The original mock API and copied-input bindings remain unchanged.

## Technical Context


**Language/Version**: Python 3.11+; macOS ARM first target.

**Primary Dependencies**: Marimo, RapidFuzz, standalone ZEN engine, bounded model adapter, supplied HTTP mock adapter; no nxusKit runtime.

**Storage**: Private in-memory domain state; bounded sanitized traces and explicit synthetic recordings. Separate private atomic write-ahead effect claims survive reset/reconstruction. Persistent capability bindings recover the same opaque effect namespace after restart without persisting identity. No production store.

**Testing**: `PYTHONPATH=src python3 -m unittest discover -s tests -v`, focused unit/contract/integration/UI-transition tests, owned mock process tests, CLI demos, and explicit browser checks.

**Target Platform**: macOS ARM only for required qualification; Linux/Minty deferred.

**Project Type**: Local Python library plus CLI and two-view browser PoC.

**Performance Goals**: Useful local feedback around 400 ms where feasible; expose measured latency for longer work; no unsupported SLA claim.

**Constraints**: Synthetic data only; loopback mock; API `startTime` authoritative; identity/correction revocation; reserve-before-write; no automatic retry after unknown; no real authentication, PHI, clinical advice, live handoff, application deployment or external media-publication claim. Public source/retained branding are approved only for this exact repository, not general relicensing or endorsement.

**Scale/Scope**: One local demo process, two paired synthetic sessions for isolation checks, eight supplied scenarios, B01-B18 and R01-R16 contracts, seven pinned persona constraints.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Design alignment only, not implementation proof: personas and Morgan-Rae support coverage map to stories/tests; explicit confirmation and correction revocation make interaction predictable; measured responsiveness is honest; reusable core/thin adapters keep authority deterministic; tests cover success, negative, boundary, recovery, concurrency, replay, and supplied mock integration; synthetic fixtures and approved branding provenance with explicit distribution boundaries preserve safe exploration; clean setup, reset, demos, video notes, README index, and as-built docs are planned; native `tasks.md` remains the single completion ledger.

## Project Structure

### Documentation (this feature)

```text
specs/001-ochsner-scheduling-assistant/
├── plan.md              # This file ($speckit-plan command output)
├── research.md          # Phase 0 output ($speckit-plan command)
├── data-model.md        # Phase 1 output ($speckit-plan command)
├── quickstart.md        # Phase 1 output ($speckit-plan command)
├── contracts/           # Phase 1 output ($speckit-plan command)
└── tasks.md             # Phase 2 output ($speckit-tasks command - NOT created by $speckit-plan)
```

### Source Code (repository root)

```text
src/ochsner_bob/
├── session.py          # revisioned domain authority
├── journal.py          # durable effect claims separate from traces
├── http_mock.py        # actual unchanged supplied HTTP API boundary
├── policy.py           # actual standalone ZEN graph/provenance
├── language.py         # bounded optional real language transport
├── suggestions.py      # public RapidFuzz suggestions
├── conversation.py     # shared CLI/browser orchestration
├── browser_service.py  # capability pairing, leases and projections
├── local_transport.py  # exact-origin loopback JSON transport
├── widget.py           # thin Marimo custom-widget wrapper
└── replay.py           # strict recordings and recorded-only shared-core simulation
apps/scheduling_app.py
tests/test_*.py
scripts/demo_*.py
```

**Structure Decision**: Keep reusable behavior in `src/ochsner_bob`, with effects and framework concerns at adapters. Establish the shared interaction/effect contracts before parallel story work. Existing bootstrap/template packages remain support tooling; BOB product code, tests, fixtures, UI assets, and docs stay isolated.

## Selected diagnostics and connected-language follow-on — 2026-10-15

Scope: existing FR-001/008–015/020/027/027a. Direct Operator selection is MLX
turn `01a14226-eaee-7be1-a9af-560d3b694c36`, human message
`01a14227-0333-7d80-8131-4193d5950828`, verified by SM and forwarded to the sole
BOB owner. The private assessment is reference material, never a public input or
artifact. No interview/vendor/private-RFP content is adopted here.

Bounded design: retain optional `handoff_reason` in the actual handoff result and
session/API diagnostic event. Validate against the existing categorical allowlist
at each observation boundary; invalid/extra-field inputs cannot leak. Booking,
policy/consent, receipt certainty, durable duplicate protection and Recording/Replay
schemas stay unchanged. Prove OFF queued/rejected/failed/unknown, privacy, ordinary
CLI/browser exposure, effect-free repeated inspection and compatibility tests.
Correct only the stale current accounting/default and fixed-widget-port statements.

Connected qualification extends the existing local qualification pattern, not a
hosted eval service. Reuse actual LanguageAdapter, Conversation/Session and the
unchanged supplied HTTP mock through owned lifecycle/free ports. Build the harness
with separate development fixtures; predeclare eight synthetic connected journeys
and two scheduled repetitions (16 executions). Freeze exact dialogue, outcome/
effect assertions, local no-dispatch turns, model-turn bounds and source/prompt/
schema/policy/case hashes before live. Identity, returned option selection and
separate current confirmation remain local deterministic controls. Never tune the
prompt/model on this tranche while retaining holdout labeling.

Planned families: new booking/availability intent; evolving preferences; negation/
refusal after a proposal; help/medical during partial identity; general unsupported
request after completion; supplied slot conflict/fresh-choice recovery; supplied
outage/help/handoff failure then recovery; no availability/help/queued handoff.
Exact dialogues/bounds live in the frozen synthetic case manifest, not copied task
status. Every failure, local safety turn, unrun step/repetition and accounting
uncertainty is reported. A transport/accounting unknown halts further dispatch;
semantic failure is retained without automatic retry, fallback or tuning.

Parent owns diagnostics/core, public docs, native artifacts, holdout manifest,
credential/accounting integration and final integration. One disjoint offline
worker may own only the new connected harness and its development tests/fixtures;
no model/vault/live ledger access or reviewer fan-out. SM owns ONE coherent final
candidate review before live, then affected evidence/status confirmation. Reuse
canonical private accounting/history/locks/unknown liabilities; never initialize
alternate headroom. SM selected A: frozen candidate code imports remain in the
owned clone; `--canonical-owner-root` is fixed to the selected OS-account checkout
`codeRepos/ochsner-scheduling-bob`, never an environment/alternate budget path.
Validate regular bounded schema1/project/adapter/exact credential/model config,
agreement with candidate config, no symlink substitution, private existing SQLite
and initialized stable lock/marker before any helper. Pin/recheck config/source
hashes and ledger/lock/root identities through the existing locking boundary.

Source inspection found `_existing_only=True` intentionally rejects reserve and
settle. SM explicitly selected the minimal compatibility extension on 2026-10-16:
`_existing_writes=True` is valid only with both application runtime and existing-only
mode and already-validated SQLite. Preserve read-only readiness/default semantics,
no initialization/migration/marker creation, and normal durable reserve/settle IDs.
Do not flip safety flags after construction or redesign global accounting/locks.
The new qualifier has no model or budget override; it selects the strong configured
snapshot, exact pinned resolver and explicit reviewed source digest. A private
exclusive-create run report retains started/unrun execution evidence and prevents
accidental replay of this tranche; it is not accounting, headroom or another task
ledger. Public summaries exclude machine paths/accounting file identities.
Full offline suite/demos, source/privacy/guard, protected CI/PR/readback follow.
No Support-sync/global-lock/scaling repair, media, platform, tags or deployment.

## Selected private transport diagnosis — 2026-10-19

Approved design: SM human message `01a14770-df0b-74b2-98c2-8a4c5ea7d6e5`,
question `call_257bf110952d47b88a4bbdd65ce3ef77`; maintenance timing hold lifted by
MLX human `01a156cd-df53-7350-a11d-681eb2d5df5d`. FR-014/027/027a, US6 only.
This is a separate one-request diagnosis, not a replay or pass of the consumed
16-execution holdout. All earlier unknown liabilities and failed/unrun outcomes stay.

1. In `language.py`, add optional `transport_observer=None` to LanguageAdapter
   and `_http_transport`. Preserve the actual transport identity and injected
   fixture protocol. Emit one fresh dictionary of category and HTTP status only:
   success/http_error/protocol_error/invalid_response/timeout/tls_error/url_error/
   network_error/other; status is an exact int 100..599 or null. Never read non-200
   bodies, stringify exceptions, retain headers or parse provider error fields.
   Ordinary observer exceptions are swallowed without retry; process-control
   exceptions retain cancellation semantics. Test HTTP400/401/403/404/429/5xx,
   redirects, timeout/TLS/URL/network/unknown errors, malformed length/body/input,
   observer failure, no message leakage, unchanged outcomes and unknown accounting.
2. Add `scripts/diagnose_language_transport.py`: one fixed synthetic public input/
   context directly through actual LanguageAdapter, no Session command, owned mock
   or scheduling action. Reuse `qualify_connected_live` canonical binding, exact
   named-notes resolver and private report writer; include the new script in the
   existing source hash closure. Keep prompt/model/rates unchanged. Dry-run is
   owner/key/network/app-free. Live opt-in requires the reviewed exact source digest
   and BOB_ENABLE_OPENAI=1, existing canonical SQLite/config/root/ledger/lock/marker
   identities, and one exclusive private result file before helper access.
   Fixed run ID `transport-diagnostic-20261019`; fixed ignored report under existing
   `tmp/connected-qualification/`. No CLI run/model/key/report/accounting overrides.
   Preserve started/incomplete evidence on failure; do not overwrite old run.json.
   Bounds: one request, 512 output tokens, 10 seconds, 2048 input bytes, 16384
   request bytes, 65536 response bytes, tools none/retries zero. Retain only safe
   numeric usage/cost/accounting, finite transport observation and source binding;
   no public action/preferences/raw data and no semantic-qualification claim.
3. Tests first for each deliverable, then full offline suite and success/failure
   demos, staged credential guard and one frozen affected-code review. Native tasks
   are the only completion record; dependent work stays sequential under one writer.
   SM selects the reviewed candidate before ANY key access or single live request.
   This implementation handoff stops before that selection. No Support relaunch,
   global accounting/locking redesign, provider/key/model switch, TLS weakening,
   fallback, media, new task/monitor, cloud or external publication/deployment.

Review focus: observer receives only two sanitized primitives; constructor/read/
close failures emit once without masking; interrupted result cannot be replayed;
source/config/ledger drift denies before helper/reserve; a 4xx still retains unknown
accounting, never assumed zero charge. Offline tests exercise these boundaries with
synthetic connection fixtures and disposable existing-SQLite bindings only.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
BOB video-duration amendment directly approved and applied 2026-10-09; see Constitution addendum. The patient and support views are one local PoC surface over one shared core, not separate products.

## Corrective integration and early framework checkpoint

Updated 2026-10-09; this design is not completion evidence. Standard Marimo
forms expose submitted values only. A throwaway real-browser probe demonstrated
that the supported AnyWidget bridge acknowledges an unsent public draft and focus
while retaining the input. An unrelated browser session starts independently.
Continue with that bridge, not an unproven framework fallback.

Keep one canonical service outside reactive kernels and reuse one patient renderer
read-only for support. Semantic acknowledgements carry revision, drafts, focus,
scroll and disclosures; private identity must not enter diagnostics. Display
observation age/freshness without pixel-fidelity claims. Poll/reconnect/replay
never submit domain commands or invoke models. Prove actual pairing and preserved
draft/focus/disclosures before substantial UI; trace references never authenticate.

Earlier core/fake-adapter sketches must not remain public authority or real
integration evidence. Genuine-model qualification remains required for full
completion; surface its exact credential/model/cost decision if no applicable
grant exists. Preserve a reviewed baseline/private milestone early, excluding
raw intake, credentials, environments and private native state.

## Approved launch, training and Flight Deck delta — 2026-10-12

Scope: FR-021–FR-024, principally US6 with US1–US5 flow/control coverage.
The approved plan baseline is DevOps `7da4364fdfb3822681026ae444e90c40d576921d`;
human confirmation is MLX turn `01a13245-6a8c-76c2-b626-c6cebcafe2cc`,
message `01a13245-8239-77d3-8adb-03fab212d260`. This records plan selection,
not a new credential, spend, media-publication or product-repair grant.

W1 is independent: inventory native scenarios/control labels; implement a standard-
library read-only structural checker with temporary-file tests. The checker consumes
`docs/user/walkthroughs/catalog.json` and `assets/ui/walkthroughs/manifest.json`;
it resolves native story/requirement IDs and the public-safe supplied scenario ID
projection without importing app code or making network requests. W1's draft
catalog may fail while W2/W3 artifacts remain missing; no empty template passes
as a completed collection. Share reviewed reusable checker bytes with SM for
Template integration, never write the Template/shared source from BOB.

F6 waits for SM's reviewed Flight Deck export/manifest, then pins identical shared
bytes plus BOB's thin `docs/internal/flight-deck/project.yaml`. L4 is now integrated
at `e615d98`; reuse T087–T098 evidence rather than replaying that implementation.
Neither bundle is invented locally. Keep canonical `.bob-local/model-budget.json`
and existing effect namespaces; no paid startup probe. FR-027/027a supersede the
old budget/window prose for runtime and functional qualification, not code creation.

F6 mapping, 2026-10-14 (reviewed shared export `ea7cfea` adopted locally;
final BOB review/integration pending): six elements reuse native FR/task IDs rather than copied completion
percentages. The consumer test will resolve every mapped ID/public path, use a
temporary invalid-ID/private-path fixture for RED, and assert absent verification
stays unknown through the actual exported consumer, not a local substitute engine.

| Element | Native requirement basis | Implementation/task and evidence boundary |
|---|---|---|
| Functional coverage | FR-001/002/004/005/006/007/011/012/015/017 | Native shared workflow, identity/lookup, safety, Replay and Support tasks; source-bound supplied HTTP/persona tests, not all browser journeys |
| User experience | FR-005/006/011/016/018/021 | Active filters, explicit suggestions, reachable help, Developer disclosure, pinned personas and individual guides; no measured accessibility/user-research claim |
| Safety and authority | FR-003/004/008/009/010/010a/013/015/017/019/024/027a | Application-owned identity/consent, durable unknown claims, ZEN structural guards, isolated Replay, exact-key/accounting privacy; no permission from a model/persona/dashboard |
| Verification | FR-020/021/022/024/026/027/027a | Existing qualification/demos/CI/native evidence with original source/date/limits; narrative references are unparsed/unknown, not manufactured green records |
| Documentation and training | FR-018/020/021/024 | Native T073/T077/T078/T079/T099–T104 plus existing as-built/persona/assets work; structural coverage is separate from actual UI evidence |
| Repository and readiness | FR-019/020/022/023/024/026/027/027a | Existing protected integration, exact reviewed bundles, owned launch, accounting and F6 native T075; no release/publication authority or SDK-latest mutation |

FR-025/025a retain explicit historical/superseded fixed-day scope, not an active
runtime spend gate; any DEFERRED mapping states that basis instead of silently
dropping them. Public evidence references use existing native/docs files and keep
unavailable/contradictory/stale evidence independent of checked task implementation.
No qualification or human-decision JSON receipt is invented to improve a rollup.

W2/W3 final captures and launch instructions follow stable BOB/L4 routing. Use
isolated synthetic states/free ports, only materially needed stills and separate
annotation layers. Preserve actual acknowledgement/reconnect warnings and product
gaps; no UI repair or new video under the documentation grant. Reconcile public
source rights/privacy before staging assets. Finish with one independent integrated
BOB diff review, affected-delta repairs, full tests/demos and candidate-bound CI/
normal protected integration; immutable RCs remain unchanged.

Ruling: use this native `tasks.md` for task progress and decisions, not an additional
SDD progress ledger, because the project/approved assignment requires one native
completion ledger. Isolate work in an ignored local BOB clone while the Operator
checkout stays untouched; sequential execution protects the single-owner native
files and shared source remains SM-owned. Independent SM bundle work can proceed
in parallel with W1.

Resumption 2026-10-13: reconcile preparation `68d92a8` with integrated `e615d98`.
The 31-flow baseline is not an exhaustive inventory: include distinct invalid-date,
identity-correction, lookup-error, handoff-certainty, isolation/stale-role and
typed-variant cases from native scenarios/tests. Reuse one document only for truly
identical flows; record source bases and explicit unavailable UI paths. Extend the
checker tests before implementation for strict visual provenance/hash/header,
layer/source/placement and contained public reference contracts. Every manifest row
uses the approved exact fields; safe errors never echo arbitrary input. Structural
checks cannot certify pixels or freshness beyond declared Git ancestry/limitations.
SM owns Template distribution after the stable checker handoff. Existing fresh
Operator demo tabs are retained; later captures use separately owned state/ports.
The verified conditional interruption grant permits only necessary identified BOB
stop/restart with accounting/effects preservation, not broad service control.

W3's reusable document-shape fixtures require workspace arrangement, enumerated
synthetic sample data, completion/cleanup, known gaps/evidence and references in
each flow, alongside Step 0/1 and interactive visuals. Completion explicitly labels
Effect/Cleanup, gaps label Recovery, and revision history stays before references.
These checks enforce visible instruction structure, not factual/perceptual truth.

## Fixed-day BOB budget delta — 2026-10-12

Historical plan, superseded for application runtime by FR-027 below; original
source-bound evidence remains in tasks.

FR-025/025a extend US6 in the existing budget boundary, not the Session/effects
architecture. Keep ordinary stored configuration at 200 calls/$20. Explicit
constructor/launcher opt-in uses a fixed UTC half-open interval for Oct 12 Central;
never persist or infer a renewable override. Move numeric ceiling enforcement to
new-reservation preparation, retaining structural validation on every read so valid
window entries remain readable/settleable after expiry.

Reuse the canonical ledger/private flock/atomic writes and priced worst-case
reservation. Preserve the existing byte limit and check space for every reserved
call's largest valid late usage before accepting new work. Snapshot ordinary
headroom honestly, even negative. Do not change journal namespaces or reset state.

Expose `preflight_budget(path: Path, *, model: str, unlimited_today: bool=False)
-> None` as existing-state-only readiness. Require the initialized marker and
private ledger, reuse locked reservation preparation in memory, and forbid any
creation/write/settlement. The actual model host must reserve again. Existing CLI
and browser flags pass opt-in explicitly and reject offline use; SM owns shared
launch integration. Offline tests precede code; full suite/demos/guard and one
independent review precede selected protected integration. No live activation,
credential lookup or paid readiness call is part of this candidate.

## L4 consumer integration — 2026-10-12

Consume only selected `tools/poc-runtime/{adapters,credentials,launch,processes}.py`
and its hash manifest from the authoritative Template, with public BOB config.
No local fork/regeneration of managed bytes. Central field resolution pins `notes`;
do not repeat vault proof. Test actual browser/CLI constructors with synthetic
transport credentials and isolated private ledgers before implementation claims.
The thin widget accepts a validated public `BOB_TRANSPORT_URL` trait; JavaScript
uses that trait, while the service keeps exact UI Origin/Host checks.

Preserve running Operator services, sessions and ledger. Use only disposable owned
ports/state for no-call smoke and cleanup. Keep W1 separate. Full project tests,
deterministic demos, affected docs/navigation, staged guard and one final SM diff
review precede normal protected integration. Shared tests are not consumer/live
model or cross-platform qualification.

## Indefinite runtime accounting delta — 2026-10-13

FR-027/027a supersede application spending/dated-window gating only. Actual CLI
and browser plus functional qualification constructors select `application_runtime=True`;
excluded code-generation/build-agent configuration stays unchanged. ModelBudget delegates runtime storage to stdlib SQLite
at the existing canonical path, with the stable private lock/marker. Atomic
validated JSON migration preserves all IDs/configuration/history and liabilities;
indexed transactional inserts/updates remove the cumulative-record cutoff without
dropping unknown or pending calls. SQLite DELETE journal privacy, memory temporary
storage, strict schema/row validation, full sync and no silent recovery/reset
preserve fail-safe accounting. Readiness opens old/new formats read-only, never
migrates, and exposes the compatible noflag `preflight_budget(path, model=model)`.

Activate only after all old-format model writers are quiescent; this candidate
does not migrate/restart the live app. SM's reviewed five-file source `17d4157`
is adopted without forking. Tests-first temporary/fake-transport regressions,
combined product qualification, source-bound docs/navigation/guard and one SM
consumer diff review precede normal CI/protected integration. Native tasks remain
the sole implementation ledger; no paid proof or media production is included.
