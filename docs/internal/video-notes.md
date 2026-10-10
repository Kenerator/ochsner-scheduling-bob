# Video production notes

Updated: 2026-10-10. Status: source-bound feature-completion still supplement delivered;
video assembly and Operator bookends remain with the media owner.
The existing video task owns narration/assembly; this is not a finished video.

Completeness correction, 2026-10-10: RC-1/R04's historical no-gap label qualified
the narrower core projection, not retained browser receipt history. New code
captures ordered acknowledgements and labels absent required observations
incomplete; renderer parity remains false. Recording-OFF API/model diagnostics
are repaired separately. Existing images/scripts are not evidence of these new
behaviors; no new capture, upload or paid QA is part of this repair. See
[native T053–T056](../../specs/001-ochsner-scheduling-assistant/tasks.md).
Reviewed repair source: `c8463252251dd840ac443641702656fd3134eebc` / RC-2,
415 tests/all demos passed. This code checkpoint does not relabel existing stills
or require new capture/media work; their original source bindings remain intact.

Audience update 2026-10-10: the Operator approved branded synthetic assets in
this exact public-source repository. BOB remains an internal-use PoC, not a
publicly deployed application. Earlier private-only notes below describe the
historical capture grant; they do not override this later decision. External
video publication remains outside this grant.

## Feature-completion supplement — 2026-10-10

[Final manifest](../../assets/ui/stills/feature-completion-20261010/manifest.json):
87 unedited native JPEG viewports with byte hashes, dimensions, visible target
rectangles/anchors and per-entry source. No crop, pixel repair, continuous
recording, model calls or access to the Operator's active trial was used.
Default source metadata applies only to the ordinary set; never relabel all
frames as RC-1. Three isolated capture sets are disclosed in `capture_sets`:

| Set | Count / source | Actual change and evidence |
| --- | --- | --- |
| Ordinary | 64 / `c3e6df20dff2518014d763c162359ceb9de23d1d` | Backend literal changed to isolated port 28541; independent mock/private namespace. Historical incomplete post-booking replay retained. |
| Receipt loss | 6 / same `c3e6df2` | Isolated port 28543 plus capture-only launcher using existing accepted-receipt-hiding wrapper. Launcher/proof hashes included; not transport-only. |
| Repaired | 17 / `e2dfa7e9f471513921063d568bb3bc890eff1800` | Clean export/install qualified before sole backend-literal change to 28545. Actual complete core replay and separate Support status. |

Use P50→P51 for fresh mismatch/correction (not original P25's session), and
P52→P53 for pending typo→explicit Downtown acceptance (P23 is a later repetition,
not P22's precursor). D30/D31 show actual sanitized diagnostics/provenance;
P54/P55 show medical boundary and a validated **mock** handoff, not staff contact.
R06/R07 pair readable reviewed fixture-proposal flags/provenance with control
context; this is simulation-only and not an executed/adopted test. R14/R17 include
step-index input, Jump and bookmarks. R11 is typed-invalid valid JSON, not a
malformed-JSON parser demonstration.

R01 shows actual appointment rows after booking, distinct from completed history.
R02 seals complete evidence but does not yet evaluate parity; R04 shows eight
events, no gaps, core semantic parity true and renderer parity false. The later
unknown API variant changes the final **lookup**, not the completed booking.
S30→S31→S32 shows joined/inactive → joined/active → joined/inactive; zero lease
when inactive. Historical `not_joined` labels meant inactive takeover, not failed
pairing. Private identity and confirmation authority remain excluded.

F08/F09 show Reset retaining uncertainty; F10 shows a new verified selection
still unable to Confirm. The [proof](../../assets/ui/stills/feature-completion-20261010/receipt-loss-proof.jsonl)
records one validated accepted booking and an independent matching appointments
read. Its receipt was deliberately hidden at the adapter boundary. No second
Confirm action occurred; one proof entry remains. This is not a packet audit or
actual outage. Rejected grant-bearing/framing frames remain scratch-only and are
listed in the manifest, never adopted.

R17 shows the selected disposable recording expired after Purge. An external
export is retained, but the same tombstoned reference **cannot** be revived by
re-import. Do not narrate restoration or removal of effect protection.
IAB kernel/acknowledgement failures and Chrome fallback are retained, not hidden.
The repaired capture launch also reported denied writes to Marimo's host recent-
file/server registry; actual isolated UI flows and originals were observed, but
successful capture is not evidence that those host metadata writes succeeded.
Native Chrome viewport sizes vary; per-entry JPEG dimensions govern placement.
Minimal effects, short preferred/no duration cap and Operator intro/wrap remain
the approved video approach. Stills delivery is not a finished-video claim.

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

### User-quickstart still supplement — 2026-10-09

The Operator-assigned SM requested missing native synthetic stills for the new
BOB user quickstart, prioritizing the proposal **before** separate Confirm and
the completed outcome/history. Thirteen visually checked Chrome JPEG originals
are in [quickstart stills](../../assets/ui/stills/quickstart-20261009/), with exact
captions, states, dimensions, SHA-256, source and limitations in the
[machine-readable manifest](../../assets/ui/stills/quickstart-20261009/manifest.json).

Recommended sequence: `31` offline start/disclosure → `32` public providers →
`20` private synthetic fixture → `21` numbered availability → `22` proposal before
Confirm → `23` cleared/disabled confirmation → `24` completed current/history →
`25` Help controls / `27` actual medical response → `28` truthful mock queued
handoff → optional `29` capture/seal / `30` isolated replay initial state.
`26` is an alternate medical-control view, not the response. These are actual
1700×543 **scrolled viewports**, not full pages, even though the screenshot API
accepted a full-page option. No edits, crops, animation or screen recording.

Source export: `4a21cafb803dac5a50c8f03dac83c923698435fa`. Only the disposable
widget's backend literal changed from port 28451 to 28541; its original/capture
hashes are in the manifest. Marimo ran at 28540, allowed origin matched it, and
the owned supplied mock used its own ephemeral port/private namespace. The
product repository's source stayed unchanged; this is a transport-modified
capture export, not an unmodified clean-tag execution. Python 3.11.13; six
widget checks passed in that copy. Actual journey ended booking: completed,
then a deliberate handoff: queued, never real staff contact. Sealed ten-event
replay opened with semantic parity true, renderer parity false, no gaps/drift;
still `30` shows initial simulation state, not all fidelity fields.

IAB was tried first but showed kernel-not-found/acknowledgement warnings; initial
sandboxed Marimo state writes were denied. Host-permitted restart did not remove
the IAB issue. Exploratory/rejected frames (including an initial helper bound to
the IAB tab) remain scratch-only and are not adopted. Final Chrome originals
were captured with an explicit tab binding and checked visually. The Operator's
active trial ports/tab were not controlled, reset or stopped. No model calls,
new support access or takeover. Reuse the earlier approved read-only support
original with its historical boundary. There is no new takeover-sequence still;
use an explicitly explanatory control card backed by the runbook/source, not
an implied live demonstration.

Launch verification found a fresh export needs its `.bob-local` parent created
before a nested namespace. The README now makes that preparation explicit;
existing trial state/budget/journals were not altered. No fresh install/full-suite
or production qualification is claimed by this content-only run.

### Genuine-AI quickstart supplement — 2026-10-09

Under the Operator's verified video assignment, SM requested a genuine
natural-language journey. Ten visually checked native Chrome JPEG originals
are indexed in the [genuine still manifest](../../assets/ui/stills/genuine-quickstart-20261009/manifest.json),
with [sanitized model and state evidence](../../assets/ui/stills/genuine-quickstart-20261009/model-evidence.json).
Reviewed source revision: `3427c5922f6987bc31e0bc472bdc8cb77cff4cca`.

Sequence: `01` configured start → `02` exact public request **Find a family doctor
downtown** → `03` genuine response / visible `openai interpretation` → `04` two
supplied public providers → `05` explicit provider selection → `06` private
synthetic identity → `07` actual numbered availability → `08` proposal before
separate Confirm → `09` confirmation cleared/disabled → `10` completed current
attempt and retained **outcome history**. Still `10` contains a current-attempt
paragraph and a separate history-list item; it is not an appointment-lookup
table. No same-session “Look up my appointments” still exists. Narration must
preserve that distinction.

One real `gpt-5.4-2026-03-05` request proposed `discover`, `primary_care`,
`downtown`; 405 input / 40 output tokens, 2714.653 ms, known rate-estimated cost
$0.001612500. The visible “Choose a provider or refine your search.” is core
presentation after a validated structured proposal, not raw model prose.
The initial mode is offline; after the real response it is openai; later local
controls truthfully show offline. Identity, consent and booking remain local
guarded actions, not additional model calls. The same synthetic session reached
revision 8, mock booking completed, with eight core events and no takeover.
Capture was sealed without gaps; replay was not executed in this run.

The disposable `git archive` export used UI 28540/backend 28541, its own mock
and private namespace. Capture-only changes were the widget port, an absolute
reference to the original canonical budget, and a secure-launch/sanitized-outcome
wrapper; hashes are in the manifest. Language and budget implementation bytes
were unchanged. This is not an unmodified clean-tag execution. All ten originals
are 1700×543 scrolled viewports, not full pages; no crop/edit/animation or
continuous recording. Chrome fallback follows the preceding documented IAB
failure. Six widget checks passed in the copy; no full-suite or fresh-install
qualification is claimed here.

Shared ledger advanced only from 41 to 42 of 200 calls, under the same $20
ceiling: known numeric cost $0.027993500 plus retained unknown liability
$3.023040000 = total liability $3.051033500; remaining $16.948966500.
Actual historical bill remains unknown. No correction branch, retry, new support
pairing, real PHI/staff contact or publication occurred. Owned capture services
and tab were closed; the active Operator trial was not controlled or reset.
Video assembly/bookend filming remain with the video owner; still delivery is
not a finished-video claim.
