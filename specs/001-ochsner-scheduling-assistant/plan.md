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
