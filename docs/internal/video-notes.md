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

- Purpose: concise scheduling choices with recoverable corrections, exact separate confirmation, truthful uncertainty and support continuity. Synthetic personas are hypotheses, not user research.
- Stories: native US1/US2 for Jules/Billy-June/Ellie-Rae; US3 Amy-Lou/Nina-Jean; US4 Sam-Rae; US5 Morgan-Rae; US6 reviewer setup. Wording is inferred from explicitly accepted requirements and pinned needs; use the [story index](../product/user-stories.md), not duplicated acceptance detail.
- Core actually shown in Chrome/Marimo: public Primary care/Downtown discovery, provider 1, supplied local fixture identity, returned API slot, numbered selection with Enter, exact timestamp/provider/location summary, separate Confirm, completed history and disabled confirmation; reload retained completion without revived consent. A format error (`5550101`) was corrected to the exact supplied `555-0101` without reset.
- Recovery actually shown: Help/Medical remain available after completion; no clinical advice. Scripted supplied conflict rejects then freshly completes; the separately labeled adapter fault hides an accepted booking receipt and preserves unknown/no-retry after reset. Those scripted faults are not claimed as browser captures or real-service behavior.
- Support shown before final receipt delta: paired local tab, private fields blank, acknowledged result/freshness versus current revision, guarded takeover, nonadopted Uptown suggestion, return and explicit patient acceptance. After specific human approval, final read-only pairing also passed: fresh acknowledged revision 5/completed, observed `can_confirm=false`, and all three private identity inputs empty/disabled. That approval did not include takeover; its attempted retest was rejected and not bypassed. The second test tab was closed. Keep earlier takeover and later read-only evidence distinct.
- Genuine browser language: one public request “Find a family doctor downtown” used explicitly selected GPT-5.4 and returned two supplied public providers with visible `openai` mode; no private lookup/effect. The 12-case qualification and retained unknown-cost liability are separate [evidence](live-qualification.md).
- Setup/reset: exact commands/prerequisites in [README](../../README.md) and [runbook](demo.md). Python 3.11.13 on Darwin arm64; disposable environment, owned supplied mock, numeric loopback URLs. Reset never deletes journal or shared model budget.
- Architecture: one SchedulingSession authority, shared Conversation, strict supplied HTTP, real ZEN plus structural guards, public RapidFuzz, separate journal/recording/budget paths and thin AnyWidget. [Walkthrough](as-built/code-walkthrough.md) links actual symbols/tests.
- Methods: cumulative native Spec-Kit through Implement; original sketch written with tests is not retrospective TDD. Corrective red/green regressions, real component tests, disjoint parallel ownership and one independent review with three reproduced fixes. Eight persona journeys are acceptance additions, not historical implementation-red claims.
- Replay correction actually shown later: explicit capture before preferences/identity/availability/select/confirm, seal five events, open and jump to original completed revision 5 with no missing evidence and `core_semantic_parity=true`; typed unknown-API fork recomputed unknown/blocking in the isolated actual core while the patient retained completed. Reopening the original restored completed simulation, not a live write.
- Limits: no real PHI/authentication/staff/API/deployment, branding private-only, small model sample, unknown historical cost, transitive dependencies not locked. [Performance](performance-notes.md) measures local HTTP completion, not frame timing or SLA. Version-1 stills do not prove the later same-core correction. Even the corrected replay does not claim full browser draft/focus/acknowledgement or private receipt parity.
- Team change: modify one public label or typo-suggestion cutoff, first add a regression and then rerun affected/full tests; preserve identity/consent/effect boundaries. No automatic generated-test execution from replay import.

Use the [demo runbook](demo.md) for timing and reproducibility, [decisions](../product/decisions.md) for rationale and [next steps](../product/next-steps.md) for unfinished work. Update the date and replace placeholders as work completes; the video Agent should ask about unresolved facts rather than inventing them.

Link the [code walkthrough](as-built/code-walkthrough.md) and [as-built architecture](as-built/architecture.md) when populated. If multiple candidates will be submitted, explain the distinct hypotheses/trade-offs and why retaining alternatives helps reviewers choose; identify the recommended starting point. Do not imply every candidate is complete or demonstrate unverified behavior.

Record the demonstrated [milestone tags](milestones.md) and permitted [UI assets/conventions](ui-assets.md). If a bounded post-MVP refinement actually occurred, note pre/post tags, comparable redacted views and the user benefit/trade-off. Distinguish separately permitted later work from the original baseline. For the ending/review discussion, include any unresolved sponsor/platform UI-conventions question and whether refinement was performed or deferred; use the Operator-approved project-local video addendum.

## Adopted original still manifest

These JPEG originals are synthetic actual UI captures, not rendered mockups or
proof of the entire journey. Approved private/internal audience only; no continuous
recording, PHI or credentials. No crop/animation derivative has been produced.

| Original | Actual state / source boundary | SHA-256 |
| --- | --- | --- |
| [Completed booking](../../assets/ui/stills/booked-final-20261009.jpg) | Offline current-core booking outcome, separate confirmation and reload verified; integration based on `a43fb61532a62f83b91dd862099419b385caee98`, dirty working tree. | `ee449286bbf5cb2a02ade9a98a820f3c84c730714690393e971df9ba766b0912` |
| [Genuine language](../../assets/ui/stills/genuine-language-20261009.jpg) | Visible synthetic/AI disclosure and `openai` provider-discovery mode. Historical working integration before final acknowledgement/retention deltas; not final-tag UI proof. | `c656db9bf12f7ce40e08341f80b72fbc7d9d8fd1e942d9be944cf63baec15eaa` |
| [Version-1 replay](../../assets/ui/stills/semantic-replay-v1-20261009.jpg) | Actual lower replay panel, simulation-only/non-parity. Not evidence of the later faithful-core correction. | `f5603b7ba37cb8c57fae69a8f1c52c40f9177e30f3702e75935cb53a138a4e70` |

Booking/replay capture source included backend digest
`42b77c520fe05d7524bf52e832d7e1f1f8fa81f7156b886c265670b22a1a2d0f`
(native capture module manifest) and widget SHA-256
`12bacdba860c9d29e64f23d0918255d39090e92a30c6fb80b0ef8b0e7de870a8`.
Neither equals the final source revision after subsequent changes. Preserve this
historical labeling; final reviewed source belongs in [milestones](milestones.md).

Operator-approved direction remains on-camera intro/wrap supplied by the Operator,
minimal effects and screenshots/animated stills, short preferred with no duration
bounds. Final assembly is not performed and no finished-video/publication claim is made.

### Corrected shared-core captures

| Original | Actual visible state | SHA-256 |
| --- | --- | --- |
| [Patient completed](../../assets/ui/stills/bob-booked-core-20261009.jpg) | Actual final offline patient revision 5 and completed outcome, private controls collapsed. | `9867323440509596d2efe37f0d5acb0f076ab2e85291b2f96df034a935c2fb2f` |
| [Core replay fidelity](../../assets/ui/stills/bob-core-replay-20261009.jpg) | Original recording's actual replay panel: semantic core parity true, renderer parity false, source compatible, explicit limitations. | `33fe92de2dd3fa706cb65745ccf851a502e00ecd2df95363b4bd62d201b75f44` |
| [Read-only paired support](../../assets/ui/stills/bob-support-readonly-20261009.jpg) | Specifically approved second local test tab, fresh observed completed screen, read-only controls; no private drafts or new confirmation authority. | `4f96b4961c493df38f307d327f5f4505701fe3751f3b8730dfadea8dc1ecc168` |

These unchanged JPEG captures used native backend code digest
`f8d33ea5430de7ccc78893ee01fcb29fc299c4ce4b91973249fcc4b02c129a28`
and widget SHA-256 `9639b413ae48de0a1b615b0d2563e730efa1d50b9133a65f4ef6f9f9641e83b7`.
At capture the baseline HEAD plus dirty integration was still in use, not a clean
tag. The subsequent reviewed checkpoint binds these code bytes; it does not
retroactively make the screenshots clean-tag executions. No extra paid call occurred.
