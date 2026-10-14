# Replay navigation and bookmarks

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

### replay basic

Actual isolated offline capture: source `bdc4585`, role developer.
Recorded-only replay, no executable authority; semantic parity true/renderer parity false observed separately

![Actual replay navigation and bookmarks controls with numbered locators; replay-basic.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Open reference` | Open an owned available recording for recorded-only simulation; unavailable is not a new pairing grant. |
| 2 | `Previous` | Move to the previous recorded step; never replay a live effect. |
| 3 | `Step` | Advance one recorded simulation step; inspect its actual index/state. |
| 4 | `Pause` | Stop playback; does not cancel or authorize a live booking. |
| 5 | `Play recorded steps` | Advance through recorded steps only; no live API/model writes. |

[Unchanged original](../../../assets/ui/walkthroughs/control-atlas/replay-navigation.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/replay-basic-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

### replay position and bookmark

Actual isolated offline capture: source `bdc4585`, role developer.
Recorded-only replay, no executable authority; semantic parity true/renderer parity false observed separately

![Actual replay navigation and bookmarks controls with numbered locators; replay-position-and-bookmark.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Replay step index (zero based)` | Zero-based selected replay index, not a patient revision. Re-enter after a reconnect if reset. |
| 2 | `Jump / inspect before and after` | Jump to bounded index and inspect before/after; review actual index/result rather than assuming navigation. |
| 3 | `Bookmark name` | Name a local replay bookmark, e.g. review-point; no identity or credentials. |
| 4 | `Bookmark current step` | Save the current replay index under that bounded name. |
| 5 | `Go to bookmark` | Return to the named existing bookmark; never change live patient state. |

[Unchanged original](../../../assets/ui/walkthroughs/control-atlas/replay-navigation.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

## Complete control index

| Catalog ID | Local actor | Accessible label | Purpose |
|---|---|---|---|
| `open-reference` | both | Open reference | Open an owned available recording for recorded-only simulation; unavailable is not a new pairing grant. |
| `previous` | both | Previous | Move to the previous recorded step; never replay a live effect. |
| `step` | both | Step | Advance one recorded simulation step; inspect its actual index/state. |
| `pause` | both | Pause | Stop playback; does not cancel or authorize a live booking. |
| `play` | both | Play recorded steps | Advance through recorded steps only; no live API/model writes. |
| `replay-index` | both | Replay step index (zero based) | Zero-based selected replay index, not a patient revision. Re-enter after a reconnect if reset. |
| `jump` | both | Jump / inspect before and after | Jump to bounded index and inspect before/after; review actual index/result rather than assuming navigation. |
| `bookmark-name` | both | Bookmark name | Name a local replay bookmark, e.g. review-point; no identity or credentials. |
| `bookmark` | both | Bookmark current step | Save the current replay index under that bounded name. |
| `go-bookmark` | both | Go to bookmark | Return to the named existing bookmark; never change live patient state. |

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
- At document width, replay-basic badges sit above the middle controls and overlap
  a small amount of non-target diagnostic JSON. Button labels remain readable;
  use the unchanged original and text equivalent for unobstructed context.

## Revision history

- 2026-10-13: Source-bound clean originals, separate vector layers/composites and
  numbered text equivalents prepared; independent final review/integration remain
  in [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).

## References

- [Control inventory](index.md)
- [Walkthrough collection](../walkthroughs/index.md)
- [Native requirements](../../../specs/001-ochsner-scheduling-assistant/spec.md)
- [Historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json)
