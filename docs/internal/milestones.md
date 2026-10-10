# Milestones and optional UX refinement

Updated: 2026-10-10. These are source checkpoints, not production release claims.

| Tag | Source commit | Purpose / timing | Relevant docs or demo |
| --- | --- | --- | --- |
| `poc/unfinished-baseline` | `a43fb61532a62f83b91dd862099419b385caee98` | Reviewed unfinished design/core baseline; credential guard 196 files, zero findings; remote main and tag verified. Browser, genuine model and completion evidence still pending. | [Native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md) |
| `poc/integrated-core-01` | `9625185fa799816ee7456275785348cc83567e3b` | 378-test integration with actual booking/shared-core replay and approved read-only pairing. Private main and annotated/peeled tag refs verified. Its later clean export failed on missing Git provenance; not a clean-setup completion tag. | [Retained failure and corrective evidence](../../specs/001-ochsner-scheduling-assistant/tasks.md) |
| `poc/qualified-01` | `5e7ae0c6b1ae29d198f734a0c26e2c96e525b961` | Annotated code/test milestone: fresh committed export/install, 387 tests, all eight supplied scenarios, demos and six widget checks passed. Not production, browser-wide, remote-clone or finished-video certification. | [Exact source/evidence](../../specs/001-ochsner-scheduling-assistant/tasks.md), [as built](as-built/architecture.md) |
| `RC-1` | `e2dfa7e9f471513921063d568bb3bc890eff1800` | Replay post-booking lookup and separate Support membership/control repairs. Parent 398 tests/three demos; clean committed export/install 398 tests/three demos. Annotated object `ca101e7ce6bfeb2768d7a78f6327049e850f6e22`; remote object and peeled target verified. | [Follow-on evidence](../../specs/001-ochsner-scheduling-assistant/tasks.md), [current stills](video-notes.md#feature-completion-supplement--2026-10-10) |

RC-1 is immutable and intentionally precedes the documentation/asset checkpoint
that records it. The earlier private-destination history below remains historical.
The Operator approved this exact repository becoming public on 2026-10-10;
internal-use PoC status and no-deployment/no-video-publication limits remain.

Qualified code/test source: `5e7ae0c6b1ae29d198f734a0c26e2c96e525b961`.
Fresh committed export/install, 387 tests, eight supplied scenarios, demos and
six renderer checks passed. This following documentation-only checkpoint records
that exact source binding. `poc/qualified-01` points to the qualified code/test
commit above, not to this later documentation commit; no tag is moved to include
its own record. Final authorized private remote verification is reported in the
completion chat. The milestone does not certify production/public release.

Approved private destination: `nxus-SYSTEMS/ochsner-scheduling-bob`. Preferred
SSH alias could not access that repository; the explicitly approved
`kenerator-github.com` fallback was verified and used. No force push or public
publication occurred. Active implementation after the baseline is not implied
to be included in that checkpoint.

Create **annotated, immutable tags** for useful reviewed milestones—not each tool call. Suggested names: `poc/scaffold`, `poc/planned`, `poc/mvp`, `poc/ux-01-before`, `poc/ux-01-after`, `poc/submitted`. Use `poc/budget-baseline` only when the Operator directs capture of an actual agreed work-window baseline. Names are suggestions, not mandatory gates; tags do not confer release/publication authority.[^tagging]

After committing the intended source and verifying the tag is unused:

```sh
git tag -a poc/mvp -m "Working MVP checkpoint"
git rev-parse 'poc/mvp^{commit}'
# Only with push authority to the confirmed remote:
git push origin refs/tags/poc/mvp
```

Record the tag, resolved commit and purpose here in the next documentation commit; do not move a tag to include its own record. Use a new numbered tag for a later checkpoint. Never force-update tags or push all unrelated tags. See [Git setup](git-setup.md) for remote/commit cadence.

## Optional refinement

During Spec-Kit Tasks, consider an **optional post-MVP** task for a bounded UI/UX flow/polish pass. It cannot delay a working required slice, weaken acceptance, or substitute for core correctness. Follow the Operator's scope and timing decisions; agents must not silently stop or shrink work based on estimated elapsed time.

If selected, retain the working baseline with a pre-refinement tag, make the focused changes, test affected behavior, and tag the post-refinement result. Document the user benefit/trade-off in the existing decisions/next-steps files. Comparable synthetic-data screenshots or short clips may help the review; use the same scenario/view and disclose any separately permitted later work. If not selected, put a brief deferred item in next steps—no unfinished mandatory gate.

Link relevant tags from as-built docs and video notes instead of duplicating this table. Budget compliance and permission for supplemental work remain Operator decisions; never imply all versions were built within an agreed time window.

## Optional adversarial review

Consider one near-final or explicitly deferred task to populate the [review report](reviews/adversarial-review.md). Reuse a sufficient existing independent review. Preserve the source commit reviewed; commit sanitized findings and useful synthetic regressions. A suggested immutable tag is `poc/review-01`; record its source here and push that named tag only under existing destination/privacy authority. No raw consultation transcript, new mandatory gate or extra publication grant.

[^tagging]: [Git: tagging](https://git-scm.com/book/en/v2/Git-Basics-Tagging). Reviewed 2026-10-07. Use annotated tags for meaningful source checkpoints and explicitly push selected tags. Limit: A checkpoint is not release/publication authority or a budget-compliance claim.
