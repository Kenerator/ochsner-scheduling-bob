# Feature Specification: Ochsner Best-of-Breed Scheduling Assistant

**Feature Branch**: `001-ochsner-scheduling-assistant`
**Created**: 2026-10-09
**Status**: Draft
**Input**: Reconciled docs/product/intake/001.md through 013.md, docs/product/RFP/README.md, docs/product/user-stories.md, and docs/product/personas.md.

## User Scenarios & Testing *(mandatory)*

This is one synthetic-data PoC, not a merger, clinical assistant, production authentication system, contact center, rescheduling/cancellation service, or nxusKit integration. The seven pinned personas are hypotheses and design/test constraints, not permissions.

Story wording is inferred from explicitly accepted B01–B18 requirements and pinned
persona needs. Origin is distinct from scope acceptance. The exact catalog pins
and ancestry in [persona cards](../../docs/product/personas.md) bind each named
persona in these native stories. B01–B18/R01–R16 in
private local intake `002.md` and the effect/replay/support contracts in `003.md`
refine these stories. Originals are intentionally excluded from Git/clean exports;
the reconciled requirements below are the exported execution contract.
The eight required scenario IDs are `happy_path_booking`, `provider_lookup`,
`no_patient_match`, `multiple_patient_matches`, `slot_conflict`, `no_availability`,
`api_failure`, and `unsupported_request` (the supplied medical-advice scenario).

### User Story 1 - Find and explicitly confirm an appointment (Priority: P1)

As Jules, Billy-June, or Ellie-Rae, I want concise, correctable scheduling choices so I can see exactly what would be booked and explicitly confirm it.

**Why this priority**: A correct, inspectable scheduling journey is the core value.

**Independent Test**: With synthetic fixtures and the supplied mock, discover providers, enter identity locally, select a returned slot, inspect an immutable proposal, and confirm one booking.

**Acceptance Scenarios**:

1. **Given** a clear specialty/location/date request, **When** providers and returned slots are selected, **Then** active filters and the exact proposal are visible.
2. **Given** a proposal, **When** a preference changes, the user declines, input is invalid, or the model is unavailable, **Then** prior proposal authority is invalidated and a new proposal is required.
3. **Given** a current verified synthetic identity and exact proposal, **When** the user explicitly confirms, **Then** one validated mock booking is attempted and completed, rejected, or unknown is reported truthfully.
4. **Given** double-click, second tab, reconnect, delayed event, or reset, **When** a booking is in flight or completed, **Then** no duplicate or revived write occurs.

### User Story 2 - Correct private identity and appointment history safely (Priority: P1)

As a patient with limited time or access, I want local phone, date-of-birth, and ZIP entry with clear correction behavior so private results are never guessed or carried across an identity change.

**Independent Test**: Exercise zero, multiple, unique, correction, invalid ZIP, empty appointment, 404, and outage responses; verify no candidates are disclosed and every correction revokes dependent state.

**Acceptance Scenarios**:

1. **Given** no locally entered identity, **When** language suggests a patient or appointment, **Then** local identity entry is requested and no private read/write occurs.
2. **Given** duplicate phone/date-of-birth matches, **When** ZIP A is replaced by ZIP B or invalid ZIP, **Then** old identity, private results, and proposal authority are revoked before dependent work.
3. **Given** a unique current verified identity, **When** existing appointments are requested, **Then** only that synthetic identity's appointments are shown and empty, 404, and outage remain distinct.

### User Story 3 - Stay safe and get help in every state (Priority: P1)

As Nina-Jean or Amy-Lou, I want plain-language correction, help, medical-boundary, and unsupported-request paths to remain reachable without clinical advice or an email prerequisite.

**Independent Test**: From partial identity, duplicate, proposal, success, rejection, unknown, and terminal states, trigger help, medical, unsupported, and public-intent paths; verify safe routing and zero unauthorized booking.

**Acceptance Scenarios**:

1. **Given** any reachable state, **When** the user asks for help, **Then** a supported help path is available without booking.
2. **Given** medical or unsupported language, **When** the assistant responds, **Then** it explains the boundary and next safe step without diagnosis, triage, or invented completion.
3. **Given** email or smartphone is unavailable, **When** contact information is discussed, **Then** email is not demanded and truthful assistance is offered.

### User Story 4 - Review diagnostics, replay, and safe variants (Priority: P2)

As Sam-Rae or a developer, I want sanitized decisions and safe replay/forking so failures and regressions are reproducible without repeating effects.

**Independent Test**: Copy a step reference, reopen it in Developer Mode, inspect state/rules, fork typed input/fault/time/order changes, and verify no live write or consent is inherited.

**Acceptance Scenarios**:

1. **Given** a recorded synthetic interaction, **When** its reference is opened, **Then** the timeline can be stepped, played, paused, jumped, and compared without sensitive diagnostics.
2. **Given** a replay step, **When** a variant is forked, **Then** provenance/diff is visible and effects remain simulation-only.
3. **Given** a reviewed minimal variant, **When** it is promoted, **Then** it becomes a regression fixture only and never replays a booking.

### User Story 5 - Support truthful paired continuity (Priority: P2)

As Morgan-Rae, I want a support view that mirrors the patient's last acknowledged screen while distinguishing known, missing, current, prior, attempted, completed, and unknown outcomes.

**Independent Test**: Run paired views with two sessions, stale/fresh updates, simulated takeover/return, and mock handoff success, failure, and unknown responses.

**Acceptance Scenarios**:

1. **Given** a current synthetic session, **When** support opens the pair, **Then** screen fidelity, freshness, known/missing facts, uncertainty, and outcome history are distinct.
2. **Given** explicit takeover or return, **When** selected, **Then** the transition is visible, isolation holds, and policy/consent guards remain active.
3. **Given** a mock handoff attempt, **When** queued, rejected, failed, or unknown, **Then** API receipt and local demo participation are reported separately.

### User Story 6 - Operate and demonstrate the PoC (Priority: P2)

As a reviewer or maintainer, I want a clean supported Mac setup, deterministic CLI path, actual browser views, owned mock lifecycle, and source-bound documentation.

**Independent Test**: From a clean equivalent macOS ARM checkout with an explicit Python 3.11+ interpreter, install the disposable environment, start/reset the mock and application, run success/failure demos, and follow the document index.

**Acceptance Scenarios**:

1. **Given** a clean checkout, **When** setup, tests, success, failure/handoff, reset, and UI/CLI entry points run, **Then** the documented behavior is reproducible without source edits.
2. **Given** the model adapter is unavailable, **When** the PoC runs, **Then** fixture and genuine model modes remain visibly distinct with no silent fallback.
3. **Given** source-bound video stills or notes, **When** reviewed, **Then** mode, revision, synthetic boundary, and limitations are identified without production/certification/public-delivery claims.

### Edge Cases

- Malformed, contradictory, missing, or timed-out model output fails closed where needed and offers correction/help.
- Public typo suggestions never auto-select and never operate on patient identity.
- Inverted date corrections are rejected atomically before availability I/O.
- Failed provider reselection keeps visible/effective filters aligned and clear preserves unrelated preferences.
- Mock 409, 404, 500, timeout, truncated/invalid success, and `api_failure` on `/handoffs` never upgrade certainty.
- A later rejected proposal cannot overwrite a prior successful receipt or make it appear unsubmitted.
- Replay, forged events, stale UI, reconnect, concurrency, reset, and takeover cannot create/revive effects.
- Help, medical, unsupported, and public-intent routes stay reachable from partial, duplicate, error, success, and terminal states.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide bounded multi-turn assistance through a shared domain behavior used by CLI and browser views, with fixture and genuine model modes visibly distinct.
- **FR-002**: The system MUST support public provider discovery/refinement by specialty and location without identity or private reads, using only returned providers and truthful empty/unsupported results.
- **FR-003**: The system MUST collect phone, date of birth, and ZIP through application-owned controls; model output MUST NOT supply identity, patient identifiers, or booking authority.
- **FR-004**: The system MUST handle zero, multiple, and unique matches without displaying candidates; every discriminator correction MUST revoke prior match, private results, and proposal authority.
- **FR-005**: The system MUST validate merged date ranges before I/O, expose active filters and correction/clear controls, and locally filter selected providers from returned slots.
- **FR-006**: The system MUST provide public-only typo suggestions over specialties, locations, and returned provider names with explicit selection; it MUST never fuzzy-match patients.
- **FR-007**: The system MUST provide existing-appointment lookup only for the current verified synthetic identity and distinguish empty, not-found, and outage outcomes.
- **FR-008**: The system MUST show an immutable exact proposal and require a later current explicit confirmation; selection, prior confirmation, model output, rendering, and replay MUST NOT authorize a write.
- **FR-009**: The system MUST reserve/consume effect authority before booking or handoff writes, serialize concurrent attempts, and separate current attempts from historical receipts.
- **FR-010**: The system MUST distinguish completed, rejected, attempted, and unknown outcomes; unknown writes MUST stop automatic retry and MUST not be reset into assumed success/failure.
- **FR-010a**: Minimal durable claims MUST precede write I/O; restart restores unresolved claims as unknown, corruption fails closed, and recording expiry/purge MUST NOT delete effect protection. An owned mock reset begins a new namespace without relabeling prior uncertainty.
- **FR-011**: The system MUST keep help, medical-boundary, unsupported, and public-intent switching reachable from relevant states without requiring booking or clinical information.
- **FR-012**: The system MUST submit minimized context to the unmodified mock, validate queued handoff receipts, and distinguish API state from local simulated support.
- **FR-013**: The system MUST use one standalone ZEN policy with closed categorical facts, stable reasons, and provenance; invalid/unknown facts or engine failure MUST fail closed where safety requires, and allow MUST NOT bypass structural guards.
- **FR-014**: CLI and browser constructors MUST attach a sanitized event sink exposing intent/workflow, rule decisions, API outcome/error, escalation, latency, and certainty without sensitive identity data; inspection/render/export MUST be effect-free.
- **FR-015**: The system MUST provide references, replay, before/after inspection, comparison, isolated typed variants, provenance/diff, and reviewed fixture promotion without history rewriting or live effect replay. As required by the accepted architecture intake, same-version recorded replay MUST use the shared domain core to reproduce deterministic outcomes and semantic view projections through recorded-only simulation adapters. Missing inputs/outcomes/clock/acknowledgements MUST be disclosed as capture gaps, not silently replaced with invented history or a full-replay claim. Historical credentials, identity and consent confer no live authority.
- **FR-016**: Developer Mode MUST be visible below the patient flow and show sanitized timeline/state/rules/model projection, timing, certainty, replay, and fork controls; its PoC toggle MUST NOT be production authorization.
- **FR-017**: The system MUST provide paired patient/support views with acknowledged-screen fidelity, freshness, session isolation, known/missing/uncertain context, and explicit simulated takeover/return while preserving guards.
- **FR-018**: The system MUST adopt all seven pinned persona hypotheses before implementation and map material constraints to stories, design, and tests, including keyboard-first choices, plain labels, recoverable corrections, no email demand, and Morgan-Rae support coverage without inventing a console or delivery permission.
- **FR-019**: The system MUST preserve supplied mock/API/scenario/data provenance and approved Ochsner branding provenance for private/internal review; it MUST use synthetic data only and make no certification, endorsement, public redistribution, or production-readiness claim.
- **FR-020**: The system MUST provide a clean macOS ARM path with explicit Python 3.11+, pinned disposable dependencies, owned loopback mock lifecycle, reset, CLI/UI parity, demos, source-bound video notes/stills, README index, product planning docs, and as-built walkthrough/architecture from actual code/tests.

### Key Entities

- **Session**: Isolated synthetic interaction with intent, verified identity, preferences, proposal, effect state, trace, support mirror, and reset state.
- **Public provider and slot**: Authoritative mock-returned values; API `startTime` is authoritative.
- **Verified fixture identity**: Application-owned result of local synthetic discriminators; not production authentication and never model-supplied.
- **Proposal and confirmation**: Immutable instance-scoped option plus separate current user confirmation.
- **Effect attempt and receipt**: Booking/handoff attempt with certainty, response provenance, history, and unknown latch.
- **Diagnostic event and interaction reference**: Sanitized evidence for inspection/replay without access or transaction authority.
- **Support mirror and regression fixture**: Freshness-labeled paired projection and reviewed minimal simulation variant.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% of tested booking attempts require current explicit confirmation and no scenario creates a second booking through retry, replay, reset, reconnect, or concurrency.
- **SC-002**: All eight supplied scenarios and B01-B18/R01-R16 have executable acceptance coverage with truthful failure/unknown next steps.
- **SC-003**: A clean supported Mac setup reaches success, failure/handoff, reset, diagnostics, and UI/CLI parity using documented commands without source edits.
- **SC-004**: 100% of identity corrections invalidate dependent private results and proposal authority before a new dependent operation; no candidate is displayed.
- **SC-005**: Paired tests keep two synthetic sessions isolated, expose freshness, and preserve policy/consent boundaries through takeover/return.
- **SC-006**: Replay/variant tests create no live writes and preserve provenance; promoted variants are identifiable reviewed fixtures.
- **SC-007**: Useful interaction feedback targets around 400 ms where feasible; longer operations expose progress and measured latency rather than an unsupported SLA.
- **SC-008**: Final handoff links native artifacts, decisions, persona/story/test index, security, video notes, UI assets, walkthrough, architecture, planning docs, and next steps with reviewed source revision.

## Assumptions

- Supplied HTTP mock, OpenAPI, policies, fixtures, scenarios, and RFP manifest are authoritative and remain unmodified; original PoCs remain unchanged.
- macOS ARM is the only required qualification target. Linux/Minty, mobile, screen-reader, production authentication, durable distributed idempotency, live model credentials, and public delivery are deferred unless separately authorized.
- Marimo is initial; a dedicated frontend is permitted only after a concrete documented interaction/handoff blocker, without weakening this contract.
- Synthetic identity matching demonstrates workflow behavior, not authentication or authorization; no real PHI, credentials, live human routing, or clinical decision support is in scope.
- Approved Ochsner branding is private/internal review only with provenance in the UI asset index; broader rights remain a delivery limitation.
- Genuine-model qualification is required for full completion after offline behavior; credentials, spend, and model choice require an applicable grant.
