# Tasks: Ochsner Best-of-Breed Scheduling Assistant

**Input**: Design documents from `specs/001-ochsner-scheduling-assistant/`
**Prerequisites**: `plan.md`, `spec.md`, `research.md`, `data-model.md`, `contracts/`, `quickstart.md`
**Tests**: Required by the feature specification; write meaningful red tests before implementation.

**Corrective audit 2026-10-09**: prior checked markers were unsupported and restored
to pending. The previous 15-test result was 5 BOB sketch tests plus 10 template
tests. It did not prove supplied HTTP, actual ZEN, concurrency, restart, browser,
paired support, or genuine model behavior. Tests/code had been written together;
no historical tests-first claim is retained. See the
[retained Analyze report](analysis-20261009.md). Corrective regressions must be
observed failing before implementation. Small flat modules replace the earlier
unimplemented package hierarchy. The narrow Constitution video amendment was directly approved in this BOB chat
and applied 2026-10-09 after the earlier automatic-review rejections.

## Phase 1: Setup

- [ ] T001 Create BOB product package layout in `src/ochsner_bob/`, `apps/`, `tests/`, and `scripts/` per `specs/001-ochsner-scheduling-assistant/plan.md`.
- [x] T002 [P] Create the project-local Python 3.11+ environment and pin direct runtime/UI dependencies in `pyproject.toml`.
- [ ] T003 [P] Add synthetic fixture provenance and owned mock lifecycle instructions in `tests/fixtures/` and `scripts/mock_lifecycle.py`.
- [ ] T004 [P] Add README contents/document index links and reconcile `docs/product/backlog.md`, `roadmap.md`, and `sprint-planning.md` with explicit deferred items.

## Phase 2: Foundational

- [ ] T005 Write failing domain invariant tests for identity provenance, proposal generations, confirmation consumption, unknown latches, and session isolation in `tests/test_bob_core.py`.
- [ ] T006 [P] Implement immutable domain records and session state in `src/ochsner_bob/session.py` using constraints from `data-model.md`.
- [ ] T007 [P] Implement deterministic state transitions and safe reset/reconnect behavior in `src/ochsner_bob/session.py`.
- [ ] T008 [P] Implement sanitized allowlisted diagnostic events and effect-free projections in `src/ochsner_bob/session.py`.
- [x] T009 [P] Implement actual supplied HTTP mock adapter with bounded transport, response validation, consistent scenario injection, and no unknown-write retry in `src/ochsner_bob/http_mock.py`; qualify against unchanged supplied server.
- [ ] T010 [P] Implement bounded language adapter schema excluding identity, patient IDs, slots, consent, and tool authority in `src/ochsner_bob/language.py`.
- [x] T011 [P] Implement actual standalone ZEN engine policy with closed categorical facts, stable rules/reasons, provenance, and fail-closed engine errors in `src/ochsner_bob/policy.py` and `policies/bob.json`; guard actual core operations and test real engine decisions.
- [ ] T012 [P] Implement public-only RapidFuzz suggestion adapter in `src/ochsner_bob/suggestions.py`.
- [ ] T013 Add red contract tests for shared CLI/browser commands and projections in `tests/contract/test_interaction_contract.py`.

## Phase 3: User Story 1 - Find and explicitly confirm (P1) 🎯 MVP

**Independent test**: Public discovery → local identity → returned slot → immutable proposal → current confirmation → one validated receipt; correction, decline, invalid input, conflict, concurrency, and unknown paths stay safe.

- [ ] T014 [P] [US1] Add failing journey tests for B01/B02/B04/B07/B08 and R03/R05/R07/R09 in `tests/test_bob_core.py`.
- [ ] T015 [P] [US1] Implement public discovery, date/provider filters, and returned-slot selection in `src/ochsner_bob/session.py`.
- [ ] T016 [US1] Implement proposal creation, immutable summaries, explicit confirmation consumption, and booking effect certainty in `src/ochsner_bob/session.py`.
- [ ] T017 [US1] Implement shared multi-turn CLI with local identity controls and current confirmation in `src/ochsner_bob/__main__.py` and `src/ochsner_bob/conversation.py`.
- [ ] T018 [US1] Add the thin Marimo patient view and correction/confirmation controls in `apps/scheduling_app.py`.
- [ ] T019 [US1] Add success and unknown demos in `scripts/demo_booking.py`.

## Phase 4: User Story 2 - Correct identity and lookup (P1)

**Independent test**: Zero/multiple/unique identity, ZIP correction, invalid ZIP, appointment empty/404/outage; no candidate disclosure and no stale private authority.

- [ ] T020 [P] [US2] Add failing identity regression tests for B03 and R01/R02 in `tests/test_bob_core.py`.
- [ ] T021 [US2] Implement local identity entry, ZIP resolution, and generation revocation in `src/ochsner_bob/session.py`.
- [ ] T022 [US2] Implement current-identity appointment lookup and stale-result clearing in `src/ochsner_bob/session.py`.
- [ ] T023 [US2] Add identity correction and appointment lookup controls to `apps/scheduling_app.py` and `src/ochsner_bob/conversation.py`.

## Phase 5: User Story 3 - Safety and help (P1)

**Independent test**: Safety/help routes from every relevant partial, duplicate, proposal, success, rejection, unknown, and terminal state; no clinical advice or unauthorized effect.

- [ ] T024 [P] [US3] Add failing all-state safety tests for B09 and R04/R08/R11/R12/R13 in `tests/transitions/test_safety_routes.py`.
- [ ] T025 [US3] Implement help, medical-boundary, unsupported, and public-intent transitions in `src/ochsner_bob/session.py`.
- [ ] T026 [US3] Implement truthful assistance/handoff preparation without email demand in `src/ochsner_bob/session.py`.
- [ ] T027 [US3] Add safe next-action rendering and keyboard-first numbered choices in `apps/scheduling_app.py`.

## Phase 6: User Story 4 - Diagnostics, replay, and variants (P2)

**Independent test**: Reference/open/step/compare/fork/promote never performs a booking or handoff and preserves provenance.

- [ ] T028 [P] [US4] Add failing replay/privacy/variant tests for B12-B15 and R14-R16 in `tests/integration/test_replay.py`.
- [ ] T029 [US4] Implement sanitized trace references, replay controls, isolated forks, typed fault/time/order changes, and diffs in `src/ochsner_bob/replay.py`.
- [ ] T030 [US4] Implement reviewed minimal regression fixture promotion in `src/ochsner_bob/replay.py`.
- [ ] T031 [US4] Add the lower Developer Mode panel and effect-free inspect/replay controls in `apps/scheduling_app.py`.

## Phase 7: User Story 5 - Paired support continuity (P2)

**Independent test**: Two isolated sessions, freshness, acknowledged screen, known/missing/uncertain context, takeover/return, and queued/rejected/unknown handoff are truthful.

- [ ] T032 [P] [US5] Add failing paired-view and handoff tests for B10/B16 and R08/R10 in `tests/integration/test_support.py`.
- [ ] T033 [US5] Implement support mirror, freshness, isolation, and explicit takeover/return in `src/ochsner_bob/browser_service.py`.
- [ ] T034 [US5] Implement mock handoff receipt validation and separate local demo-support state in `src/ochsner_bob/session.py`.
- [ ] T035 [US5] Add paired support view, outcome history, and support controls in `apps/scheduling_app.py`.

## Phase 8: User Story 6 - Operate and demonstrate (P2)

**Independent test**: Clean Mac setup, owned mock/reset, tests, success/failure demos, UI/CLI parity, and source-bound docs work without source edits.

- [ ] T036 [P] [US6] Add persona-linked acceptance tests for Jules, Billy-June, Amy-Lou, Ellie-Rae, Nina-Jean, Morgan-Rae, and Sam-Rae in `tests/integration/test_persona_acceptance.py`.
- [ ] T037 [P] [US6] Add clean setup, CLI, reset, and demo smoke tests in `tests/contract/test_quickstart.py`.
- [ ] T038 [US6] Populate `docs/internal/persona-story-test-index.md` with pinned constraints, native stories, code paths, and test evidence.
- [ ] T039 [US6] Adopt approved Ochsner assets into `assets/ui/` and update `docs/internal/ui-assets.md` with provenance/private audience limits.
- [ ] T040 [US6] Update `docs/internal/video-notes.md` with source-bound narrative/still manifest, tested states, modes, and limitations.

## Phase 9: Polish and completion evidence

- [ ] T041 [P] Add final CLI/browser transition coverage and run the full unittest suite in `tests/`.
- [ ] T042 [P] Populate `docs/internal/as-built/code-walkthrough.md` from actual code/tests with navigation links and reviewed source revision.
- [ ] T043 [P] Populate `docs/internal/as-built/architecture.md` from actual components/tests with Mermaid diagrams, boundary explanation, and disclosed rendering verification.
- [ ] T044 Verify README links, docs navigation, UI asset provenance, security guard instructions, and product planning handoff documents.
- [ ] T045 Run `quickstart.md`, success/failure demos, explicit Mac interpreter check, mock cleanup, and final delta review; record any incomplete genuine-model qualification honestly in `tasks.md`.
- [ ] T046 [P] Add all eight exact scenario IDs from `docs/product/RFP/source/scenarios.yaml` to `tests/test_supplied_http.py`; select additional transitions from `reference/testing/transition-scenarios.md`.
- [ ] T047 [P] Add measured local feedback/latency evidence for SC-007 and the 400 ms target in `tests/integration/test_latency_evidence.py` and `docs/internal/performance-notes.md`.
- [ ] T048 Run the staged credential guard with the explicit compatible interpreter and inspect `docs/internal/security.md` before any commit; record incomplete scans without excluding tests/docs.
- [x] T049 Persist minimal atomic write-ahead effect claims before I/O in `src/ochsner_bob/journal.py`; restored in-flight claims become unknown and corrupt restoration fails closed. Test restart/reset/trace-expiry in `tests/test_effect_journal.py`.
- [ ] T050 Prove early Marimo two-view isolation, acknowledgements/freshness, drafts/focus/disclosures, zero-effect reconnect/replay and safe stale submissions in `docs/internal/marimo-feasibility.md` before substantial UI work; use authorized fallback only on a concrete recorded blocker.
- [ ] T051 Qualify genuine bounded synthetic language for R15 using `tests/live_model_cases.json` and `docs/internal/live-qualification.md`; surface exact credential/model/cost decision if no applicable grant. Required for full completion; pending while unrun.
- [ ] T052 Review baseline staged content, commit with credential guard, verify/create approved private destination, configure approved SSH origin, and non-force push meaningful annotated milestones per `docs/internal/git-setup.md` and `docs/internal/milestones.md`.

## Dependencies & Execution Order

Setup → Foundational → shared interaction/effect contracts → US1/US2/US3 in parallel, then US4/US5/US6 after trace/support contracts settle → Polish. US1 is the MVP. Tests are written first within each story. T042/T043 depend on stable implemented code but do not block starting implementation.

## Parallel Opportunities

T002-T004, T006-T012, T014, T020, T024, T028, T032, T036-T037, and T041-T043 are parallelizable where their file ownership is disjoint. Native stages remain sequential; implementation workers must not edit shared contracts or `tasks.md` concurrently.

## Implementation Strategy

Deliver US1 first as the MVP, validate it independently, then add identity/lookup and all-state safety. Add replay/support and reviewer/setup evidence incrementally. Keep `tasks.md` as the sole completion ledger and record genuine-model qualification, browser evidence, and deferred platform/public-delivery limits explicitly.

## Corrective implementation evidence — 2026-10-09

- T002: explicit project Python 3.11.13, Darwin arm64; pinned Marimo 0.25.1,
  AnyWidget 0.11.0, ZEN 2.1.2 and RapidFuzz 3.14.6 import; pip check has no
  broken requirements (cache permission warning disclosed, not an import failure).
- T009: parent reran 22 adapter tests against the unmodified supplied service,
  including receipt matching, bounded hostile transport, six-method scenario
  injection and unknown-versus-definite classification. Passed; source hashes
  asserted by tests. Not browser or genuine-model evidence.
- T011: parent reran 15 actual-ZEN tests, including all 240 categorical fact
  combinations, direct engine execution, compile/runtime errors, graph digest
  and editable loading. Session guards invoke this policy and retain independent
  structural identity/proposal/confirmation checks.
- T049: parent reran 19 journal tests: atomic fsync, private files, corrupt/missing
  state, process/thread concurrency, restart unknown and reset/recording expiry.
  Passed. Local safety only; no remote exactly-once claim.
- Session, browser-service and transport contracts were observed red before their
  implementations. Subsequent targeted runs passed 14 session, 7 service and
  2 transport tests. Full story/UI/replay acceptance remains pending.
- Early real Marimo probe: native form withheld an unsent draft; supported custom
  bridge acknowledged the unsent public draft and focus while retaining the
  input. A second browser session started empty. Actual paired mirror/reconnect
  feasibility is still pending; no framework fallback selected.
- Earlier five sketch tests now query returned options rather than inventing
  slots. Their passes remain sketch-only evidence, not supplied-HTTP acceptance.
- Private destination list was accessible and had no matching BOB repository.
  Organization-membership read timed out during TLS handshake; this is not
  absence or authorization failure evidence. No repository creation/push yet.
