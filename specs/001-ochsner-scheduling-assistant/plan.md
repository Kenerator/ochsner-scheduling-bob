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

**Constraints**: Synthetic data only; loopback mock; API `startTime` authoritative; identity/correction revocation; reserve-before-write; no automatic retry after unknown; no real authentication, PHI, clinical advice, live handoff, or public delivery claim.

**Scale/Scope**: One local demo process, two paired synthetic sessions for isolation checks, eight supplied scenarios, B01-B18 and R01-R16 contracts, seven pinned persona constraints.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

Design alignment only, not implementation proof: personas and Morgan-Rae support coverage map to stories/tests; explicit confirmation and correction revocation make interaction predictable; measured responsiveness is honest; reusable core/thin adapters keep authority deterministic; tests cover success, negative, boundary, recovery, concurrency, replay, and supplied mock integration; synthetic fixtures and private branding provenance preserve safe exploration; clean setup, reset, demos, video notes, README index, and as-built docs are planned; native `tasks.md` remains the single completion ledger.

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
