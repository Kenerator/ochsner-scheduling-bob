# Video production notes

Updated: 2026-10-09. Status: implementation in progress; not a finished video.

Keep this file current as Specify, Plan and Implement establish the actual product. Record confirmed behavior, not aspirations; link to canonical specs/tests instead of copying them. Use synthetic data and keep credentials and personal data out of recordings.

## Audience and personas

<!-- Bootstrap: selected personas -->
Selected personas; evidence labels and full constraints remain in the [persona cards](../product/personas.md). Validate relevant needs in the actual application.

- **Jules** (poc-template-seed-v1:56e6af21-d1e4-4698-8485-83a341d77031@1): Jules: Find and explicitly confirm a mock appointment
  Acceptance requirements: Show exact proposal without booking until explicit confirmation
- **Billy-June** (poc-template-seed-v1:0de53f87-1856-40ac-84fe-ec4d890e3770@1): Billy-June: Coordinate convenient continuity of appointments
  Acceptance requirements: Honor supported constraints or explain no match; invalidate old proposal
- **Amy-Lou** (poc-template-seed-v1:aae4b004-4bbf-4ac5-b532-2d7af776e168@1): Amy-Lou: Complete a scheduling journey with help when needed
  Acceptance requirements: Do not demand email; explain limitation and prepare truthful assistance
- **Ellie-Rae** (poc-template-seed-v1:cb706720-85fb-42ef-9318-2bcec4c2b621@1): Ellie-Rae: Select and confirm with minimal input
  Acceptance requirements: Select one with a number; invalid input preserves context; keyboard flow works
- **Nina-Jean** (poc-template-seed-v1:5d4d7083-1479-4637-90cd-5e841bfe080d@1): Nina-Jean: Understand choices and correct preferences
  Acceptance requirements: Ask one useful scheduling question; visibly update and invalidate old proposal
- **Morgan-Rae** (poc-template-seed-v1:657aedfe-4a4a-4ec4-83c0-52614111f07c@1): Morgan-Rae: Understand request and unresolved work without repetition
  Acceptance requirements: Separate known facts, missing information and booking outcome; no false delivery
- **Sam-Rae** (poc-template-seed-v1:98e1dcd5-8ee9-4b2b-b7fe-2045d389b9b4@1): Sam-Rae: Expose unsafe confirmations and recovery
  Acceptance requirements: Do not create a booking or unsafe retry; show truthful state
<!-- Bootstrap: end selected personas -->

## What to demonstrate (no duration bounds; short preferred)

Use the [persona/story/test index](persona-story-test-index.md) to distinguish actual persona-driven changes from selected cards. Record each demonstrated mode and source revision; a fixture/UI still is not live-model proof. Preserve original assets and separately label derivatives with format, provenance and scenario coverage before handoff. Do not initiate new capture without its current authorization.

- Purpose and user pain: Not yet recorded.
- Demonstrated User Story and corresponding Persona (including a useful Support/Admin case), supplied vs inferred origin: Not yet recorded. Link [stories](../product/user-stories.md) and native specs; do not present a draft or deferred story as working behavior.
- Core flow and visible outcome: Not yet recorded.
- Failure/recovery or handoff flow, including what really happens: Not yet recorded.
- Exact launch/scenario/reset commands and prerequisites: Not yet recorded.
- Technical walkthrough: architecture and core/adapter boundaries; stack; key decisions and trade-offs: Not yet recorded.
- Methodologies actually used: Spec-Kit stages, meaningful tests/TDD, reviews and persona-driven acceptance: Not yet recorded.
- Limitations, mock vs real integrations, measured vs unmeasured performance, and next steps: Not yet recorded.
- Small live-review modification to invite team discussion: Not yet recorded.

Use the [demo runbook](demo.md) for timing and reproducibility, [decisions](../product/decisions.md) for rationale and [next steps](../product/next-steps.md) for unfinished work. Update the date and replace placeholders as work completes; the video Agent should ask about unresolved facts rather than inventing them.

Link the [code walkthrough](as-built/code-walkthrough.md) and [as-built architecture](as-built/architecture.md) when populated. If multiple candidates will be submitted, explain the distinct hypotheses/trade-offs and why retaining alternatives helps reviewers choose; identify the recommended starting point. Do not imply every candidate is complete or demonstrate unverified behavior.

Record the demonstrated [milestone tags](milestones.md) and permitted [UI assets/conventions](ui-assets.md). If a bounded post-MVP refinement actually occurred, note pre/post tags, comparable redacted views and the user benefit/trade-off. Distinguish separately permitted later work from the original baseline. For the ending/review discussion, include any unresolved sponsor/platform UI-conventions question and whether refinement was performed or deferred; use the Operator-approved project-local video addendum.

Operator-approved direction: on-camera introduction and wrap-up supplied by the Operator, minimal effects, screenshots/animated stills. No continuous screen recording authorized. Native source and exact final still manifest remain pending integration; no finished-video claim.
