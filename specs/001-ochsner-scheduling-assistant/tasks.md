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

- [x] T001 Create BOB product package layout in `src/ochsner_bob/`, `apps/`, `tests/`, and `scripts/` per `specs/001-ochsner-scheduling-assistant/plan.md`.
- [x] T002 [P] Create the project-local Python 3.11+ environment and pin direct runtime/UI dependencies in `pyproject.toml`.
- [x] T003 [P] Add synthetic fixture provenance and owned mock lifecycle instructions in `vendor/reference/` and `scripts/mock_lifecycle.py`.
- [x] T004 [P] Add README contents/document index links and reconcile `docs/product/backlog.md`, `roadmap.md`, and `sprint-planning.md` with explicit deferred items.

## Phase 2: Foundational

- [x] T005 Write failing domain invariant tests for identity provenance, proposal generations, confirmation consumption, unknown latches, and session isolation in `tests/test_session_contract.py and tests/test_transition_acceptance.py`.
- [x] T006 [P] Implement immutable domain records and session state in `src/ochsner_bob/session.py` using constraints from `data-model.md`.
- [x] T007 [P] Implement deterministic state transitions and safe reset/reconnect behavior in `src/ochsner_bob/session.py`.
- [x] T008 [P] Implement sanitized allowlisted diagnostic events and effect-free projections in `src/ochsner_bob/session.py`.
- [x] T009 [P] Implement actual supplied HTTP mock adapter with bounded transport, response validation, consistent scenario injection, and no unknown-write retry in `src/ochsner_bob/http_mock.py`; qualify against unchanged supplied server.
- [x] T010 [P] Implement bounded language adapter schema excluding identity, patient IDs, slots, consent, and tool authority in `src/ochsner_bob/language.py`.
- [x] T011 [P] Implement actual standalone ZEN engine policy with closed categorical facts, stable rules/reasons, provenance, and fail-closed engine errors in `src/ochsner_bob/policy.py` and `policies/bob.json`; guard actual core operations and test real engine decisions.
- [x] T012 [P] Implement public-only RapidFuzz suggestion adapter in `src/ochsner_bob/suggestions.py`.
- [x] T013 Add red contract tests for shared CLI/browser commands and projections in `tests/test_conversation.py`.

## Phase 3: User Story 1 - Find and explicitly confirm (P1) 🎯 MVP

**Independent test**: Public discovery → local identity → returned slot → immutable proposal → current confirmation → one validated receipt; correction, decline, invalid input, conflict, concurrency, and unknown paths stay safe.

- [x] T014 [P] [US1] Add failing journey tests for B01/B02/B04/B07/B08 and R03/R05/R07/R09 in `tests/test_session_contract.py and tests/test_transition_acceptance.py`.
- [x] T015 [P] [US1] Implement public discovery, date/provider filters, and returned-slot selection in `src/ochsner_bob/session.py`.
- [x] T016 [US1] Implement proposal creation, immutable summaries, explicit confirmation consumption, and booking effect certainty in `src/ochsner_bob/session.py`.
- [x] T017 [US1] Implement shared multi-turn CLI with local identity controls and current confirmation in `src/ochsner_bob/__main__.py` and `src/ochsner_bob/conversation.py`.
- [x] T018 [US1] Add the thin Marimo patient view and correction/confirmation controls in `apps/scheduling_app.py`.
- [x] T019 [US1] Add success and unknown demos in `scripts/demo_booking.py`.

## Phase 4: User Story 2 - Correct identity and lookup (P1)

**Independent test**: Zero/multiple/unique identity, ZIP correction, invalid ZIP, appointment empty/404/outage; no candidate disclosure and no stale private authority.

- [x] T020 [P] [US2] Add failing identity regression tests for B03 and R01/R02 in `tests/test_session_contract.py and tests/test_transition_acceptance.py`.
- [x] T021 [US2] Implement local identity entry, ZIP resolution, and generation revocation in `src/ochsner_bob/session.py`.
- [x] T022 [US2] Implement current-identity appointment lookup and stale-result clearing in `src/ochsner_bob/session.py`.
- [x] T023 [US2] Add identity correction and appointment lookup controls to `apps/scheduling_app.py` and `src/ochsner_bob/conversation.py`.

## Phase 5: User Story 3 - Safety and help (P1)

**Independent test**: Safety/help routes from every relevant partial, duplicate, proposal, success, rejection, unknown, and terminal state; no clinical advice or unauthorized effect.

- [x] T024 [P] [US3] Add failing all-state safety tests for B09 and R04/R08/R11/R12/R13 in `tests/test_transition_acceptance.py`.
- [x] T025 [US3] Implement help, medical-boundary, unsupported, and public-intent transitions in `src/ochsner_bob/session.py`.
- [x] T026 [US3] Implement truthful assistance/handoff preparation without email demand in `src/ochsner_bob/session.py`.
- [x] T027 [US3] Add safe next-action rendering and keyboard-first numbered choices in `apps/scheduling_app.py`.

## Phase 6: User Story 4 - Diagnostics, replay, and variants (P2)

**Independent test**: Reference/open/step/compare/fork/promote never performs a booking or handoff and preserves provenance.

- [ ] T028 [P] [US4] Add failing replay/privacy/variant tests for B12-B15 and R14-R16 in `tests/test_replay_contract.py and tests/test_interaction_service.py`.
- [ ] T029 [US4] Implement sanitized trace references, replay controls, isolated forks, typed fault/time/order changes, and diffs in `src/ochsner_bob/replay.py`.
- [x] T030 [US4] Implement reviewed minimal regression fixture promotion in `src/ochsner_bob/replay.py`.
- [x] T031 [US4] Add the lower Developer Mode panel and effect-free inspect/replay controls in `apps/scheduling_app.py`.

## Phase 7: User Story 5 - Paired support continuity (P2)

**Independent test**: Two isolated sessions, freshness, acknowledged screen, known/missing/uncertain context, takeover/return, and queued/rejected/unknown handoff are truthful.

- [x] T032 [P] [US5] Add failing paired-view and handoff tests for B10/B16 and R08/R10 in `tests/test_browser_service.py and tests/test_supplied_http.py`.
- [x] T033 [US5] Implement support mirror, freshness, isolation, and explicit takeover/return in `src/ochsner_bob/browser_service.py`.
- [x] T034 [US5] Implement mock handoff receipt validation and separate local demo-support state in `src/ochsner_bob/session.py`.
- [x] T035 [US5] Add paired support view, outcome history, and support controls in `apps/scheduling_app.py`.

## Phase 8: User Story 6 - Operate and demonstrate (P2)

**Independent test**: Clean Mac setup, owned mock/reset, tests, success/failure demos, UI/CLI parity, and source-bound docs work without source edits.

- [x] T036 [P] [US6] Add persona-linked acceptance tests for Jules, Billy-June, Amy-Lou, Ellie-Rae, Nina-Jean, Morgan-Rae, and Sam-Rae in `tests/test_persona_acceptance.py`.
- [ ] T037 [P] [US6] Add clean setup, CLI, reset, and demo smoke tests in `tests/test_browser_launch.py and tests/test_cli_restart.py`.
- [x] T038 [US6] Populate `docs/internal/persona-story-test-index.md` with pinned constraints, native stories, code paths, and test evidence.
- [x] T039 [US6] Adopt approved Ochsner assets into `assets/ui/` and update `docs/internal/ui-assets.md` with provenance/private audience limits.
- [ ] T040 [US6] Update `docs/internal/video-notes.md` with source-bound narrative/still manifest, tested states, modes, and limitations.

## Phase 9: Polish and completion evidence

- [ ] T041 [P] Add final CLI/browser transition coverage and run the full unittest suite in `tests/`.
- [ ] T042 [P] Populate `docs/internal/as-built/code-walkthrough.md` from actual code/tests with navigation links and reviewed source revision.
- [ ] T043 [P] Populate `docs/internal/as-built/architecture.md` from actual components/tests with Mermaid diagrams, boundary explanation, and disclosed rendering verification.
- [ ] T044 Verify README links, docs navigation, UI asset provenance, security guard instructions, and product planning handoff documents.
- [ ] T045 Run `quickstart.md`, success/failure demos, explicit Mac interpreter check, mock cleanup, and final delta review; record any incomplete genuine-model qualification honestly in `tasks.md`.
- [x] T046 [P] Add all eight exact scenario IDs from `docs/product/RFP/source/scenarios.yaml` to `tests/test_supplied_http.py`; select additional transitions from `reference/testing/transition-scenarios.md`.
- [x] T047 [P] Add measured local feedback/latency evidence for SC-007 and the 400 ms target in `tests/test_latency_evidence.py` and `docs/internal/performance-notes.md`.
- [ ] T048 Run the staged credential guard with the explicit compatible interpreter and inspect `docs/internal/security.md` before any commit; record incomplete scans without excluding tests/docs.
- [x] T049 Persist minimal atomic write-ahead effect claims before I/O in `src/ochsner_bob/journal.py`; restored in-flight claims become unknown and corrupt restoration fails closed. Test restart/reset/trace-expiry in `tests/test_effect_journal.py`.
- [x] T050 Prove early Marimo two-view isolation, acknowledgements/freshness, drafts/focus/disclosures, zero-effect reconnect/replay and safe stale submissions in `docs/internal/marimo-feasibility.md` before substantial UI work; use authorized fallback only on a concrete recorded blocker.
- [x] T051 Qualify genuine bounded synthetic language for R15 using `tests/live_model_cases.json` and `docs/internal/live-qualification.md`; surface exact credential/model/cost decision if no applicable grant. Required for full completion; pending while unrun.
- [x] T052 Review baseline staged content, commit with credential guard, verify/create approved private destination, configure approved SSH origin, and non-force push meaningful annotated milestones per `docs/internal/git-setup.md` and `docs/internal/milestones.md`.

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

## Integrated evidence update — 2026-10-09

The paragraphs above retain historical corrective checkpoints, not current
status. The private repository and annotated unfinished baseline were subsequently
created/pushed/verified; see milestones. Raw intake, credentials, environments and
private state remain excluded. No public deployment/publication occurred.

Parent combined run: **360 tests passed, 18.396 s**, explicit Python 3.11.13,
Darwin arm64, before the latest faithful-replay correction. It includes retained
starter/sketch tests, not 360 independent product journeys. Added actual HTTP,
Session, Conversation/CLI, ZEN, journal, browser, transport, language/budget,
recording/store/replay, transition and eight persona journeys are distinguished
in their files and the persona crosswalk. Source/test invariants were red before
corrective changes; persona additions are acceptance evidence over existing code,
not retrospective TDD. A support test-helper error was fixed without production
changes. Source revisions/digests and limits are in the as-built and model notes.

Actual Chrome/Marimo: public discovery, local synthetic identity correction,
returned option, exact summary, separate confirmation, one completed outcome,
disabled confirmation and read-only reload passed. Final offline keyboard `1` +
Enter selection passed. Earlier paired actual tabs passed last acknowledged
screen/private-field exclusion, takeover/suggestion/return and patient acceptance.
A final new-recipient pairing retest was tool-blocked pending specific human
approval; it is not claimed as run. Current warning/pending/enabled-state receipt
extensions have separate strict service/shipped-renderer tests.

Actual version-1 Developer Mode passed capture/help/discover/seal/open/step,
play/pause/bookmark/jump/before-after/fork/compare/reviewed proposal and 2,024-byte
export/reimport. Live state stayed unchanged/no effect. This is explicitly typed
semantic simulation, NOT faithful live-core replay. **T028/T029 remain open**:
final reconciliation of the accepted architecture contract requires same-version
core outcomes/semantic projections, and a same-core recorded-only adapter is in
progress. No scope downgrade or full-completion claim is made.

Genuine qualification T051: GPT-5.4 alternative 12/12 semantic checks, mini 10/12
not qualified; one actual browser public-language request also passed. Shared
budget 41/200 calls, total liability $3.049421 including $3.023040 unknown
reservations; actual historical total bill unknown. No additional paid calls are
planned. See live-qualification.md for exact sources/case outcomes.

Success/conflict/unknown supplied-HTTP demos reran successfully; unknown is the
explicitly labeled accepted-receipt-hidden fault, not a server scenario. Starter
success/failure demos also pass but do not establish BOB behavior. pip check has
no broken requirements. Thirty sequential actual loopback requests measured
p50 .931 ms/p95 2.163 ms/max 2.358 ms, no effects/model calls, not browser paint/SLA.

One independent read-only review reproduced three defects (CLI namespace restart,
idle retention, missing acknowledged stale warning); all three original diagnostics
were rechecked after fixes, 28 focused tests passed. New faithful-core replay is
outside that bounded review. Final setup/source-bound docs, credential guard,
fresh combined verification and integration checkpoint remain open below.
