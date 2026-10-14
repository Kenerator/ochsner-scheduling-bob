# Developer Mode and recording

Use the numbered actual screenshots to locate controls; the text below is the
readable equivalent. Actions remain guarded by the application, not these figures.
New captures are isolated **offline**, at source `bdc4585` (2026-10-13), not genuine
model qualification. Historical figures retain their original 2026-10-10 source
and are labeled explicitly. [Manifest](../../../assets/ui/walkthroughs/manifest.json)
contains exact original/layer hashes, dimensions, source and placement rectangles.

## Role, prerequisites and effects

See the [shared disabled-state matrix](index.md#disabled-conditions-and-effect-scope)
and [role/state inventory](index.md#accessible-roles-and-required-atlas-states).
A visible or focused button is not permission. Patient confirmation, private drafts,
unknown-effect protection and replay isolation remain application-owned.

## Numbered figures

### recording and diagnostics

Actual isolated offline capture: source `bdc4585`, role developer.
Developer controls visible with blank output after reconnect; OFF response was observed separately

![Actual developer mode and recording controls with numbered locators; recording-and-diagnostics.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Developer Mode · local PoC diagnostics and replay` | Expand lower local diagnostics/replay. This disclosure is not authentication. |
| 2 | `Interaction reference` | Enter an owned synthetic diagnostic/recording reference, not a bearer capability or booking token. |
| 3 | `Start synthetic recording` | Explicitly opt into bounded synthetic capture before relevant actions; only approved fixture references. |
| 4 | `Seal recording` | Stop and seal current capture; incomplete fields stay missing, full_replay is not renderer certification. |
| 5 | `Inspect sanitized diagnostics` | Read sanitized decisions/timing/certainty with recording OFF or ON; no exact private transcript. |

[Unchanged original](../../../assets/ui/walkthroughs/control-atlas/developer-recording-off.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

## Complete control index

| Catalog ID | Local actor | Accessible label | Purpose |
|---|---|---|---|
| `developer-disclosure` | both | Developer Mode · local PoC diagnostics and replay | Expand lower local diagnostics/replay. This disclosure is not authentication. |
| `interaction-reference` | both | Interaction reference | Enter an owned synthetic diagnostic/recording reference, not a bearer capability or booking token. |
| `start-recording` | patient | Start synthetic recording | Explicitly opt into bounded synthetic capture before relevant actions; only approved fixture references. |
| `seal-recording` | both | Seal recording | Stop and seal current capture; incomplete fields stay missing, full_replay is not renderer certification. |
| `inspect-diagnostics` | both | Inspect sanitized diagnostics | Read sanitized decisions/timing/certainty with recording OFF or ON; no exact private transcript. |

## Known gaps and recovery

- Acknowledgement-unavailable and transient kernel/reconnect warnings occurred.
  Joined role does not prove synchronized screens; compare the acknowledged revision
  with current context. Do not retry an unknown write.
- Reconnect can clear displayed diagnostics or reset the replay index. Review the
  actual state and re-enter a bounded index/reference; do not infer that a queued
  action or intended preference change succeeded.
- Historical Support screenshots explain unchanged controls/lease labels, not a
  fresh takeover or Support-sync test. Current captures did not take control, purge
  a recording or call a model. The data-controls plate shows locations, not proof
  every export/import action was executed.
- OFF controls are visible even if reconnect cleared the output. Inspect again
  for current sanitized diagnostics; never replace them with a saved exact transcript.
- These desktop figures are not mobile, screen-reader or production certification.

## Revision history

- 2026-10-13: Source-bound clean originals, separate vector layers/composites and
  numbered text equivalents prepared; independent final review/integration remain
  in [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).

## References

- [Control inventory](index.md)
- [Walkthrough collection](../walkthroughs/index.md)
- [Native requirements](../../../specs/001-ochsner-scheduling-assistant/spec.md)
- [Historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json)
