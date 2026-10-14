# Session and public discovery

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

### toolbar

Actual isolated offline capture: source `bdc4585`, role patient.
Empty join field; no pairing grant; patient controls disabled

![Actual session and public discovery controls with numbered locators; toolbar.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Start independent patient` | Start a separate local patient session; does not reconnect the old patient or clear its effect history. |
| 2 | `One-use pairing grant` | Enter the patient's one-use local grant only in this private join field; never publish it. |
| 3 | `Join demo support` | Consume a current one-use grant to join read-only Support; private identity/confirmation excluded. |
| 4 | `Create support pairing grant` | Patient-only creation of a short-lived one-use local Support grant; do not capture its value. |

[Unchanged original](../../../assets/ui/walkthroughs/control-atlas/empty-toolbar.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/toolbar-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

### public filters

Actual isolated offline capture: source `bdc4585`, role patient.
Two returned providers without identity; no booking

![Actual session and public discovery controls with numbered locators; public-filters.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Specialty` | Choose the supported public specialty; a change must be applied/discovered and invalidates the prior proposal. |
| 2 | `Location` | Choose a supported public location or Any location; not clinical suitability or private identity. |
| 3 | `From date` | Set the earliest calendar date. A merged inverted range is rejected before availability I/O. |
| 4 | `Through date` | Set the latest calendar date. Review the full range; blank represents an unset filter. |
| 5 | `Apply preferences` | Apply the full visible public filters without booking; inspect Active filters afterward. |
| 6 | `Find providers` | Read current public providers using visible filters; no identity or booking is needed. |

[Unchanged original](../../../assets/ui/walkthroughs/control-atlas/patient-discovery.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/public-filters-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

### public request and provider

Actual isolated offline capture: source `bdc4585`, role patient.
Two returned providers without identity; no booking

![Actual session and public discovery controls with numbered locators; public-request-and-provider.](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Public scheduling request` | Enter public scheduling intent only. Never enter names, phone, DOB, ZIP, a grant or confirmation here. |
| 2 | `Send scheduling request` | Submit public intent; model-first launch may interpret it, while local controls keep authority. Enter also submits. |
| 3 | `Choose provider {number}` | Select a returned numbered provider as a public filter; no slot or appointment is selected. |

[Unchanged original](../../../assets/ui/walkthroughs/control-atlas/patient-discovery.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

### public spelling

Historical executed synthetic capture: source `c3e6df2`, role patient.
Historical executed synthetic state shown in the retained original, not a fresh run.

![Historical session and public discovery controls with numbered locators; public-spelling.](../../../assets/ui/walkthroughs/control-atlas/public-spelling-composite.svg)

| Number | Control / observation | What it does and important boundary |
|---|---|---|
| 1 | `Use {value}` | Explicitly accept a public canonical suggestion; never a patient fuzzy match or automatic provider selection. |

[Unchanged original](../../../assets/ui/stills/feature-completion-20261010/P23-readable-public-suggestion.jpg) · [Separate vector layer](../../../assets/ui/walkthroughs/control-atlas/public-spelling-annotation.svg).
Open the full-size figure when small labels are hard to read; numbered text remains
usable at document width. Original pixels are not edited, and no crop hides a warning.

## Complete control index

| Catalog ID | Local actor | Accessible label | Purpose |
|---|---|---|---|
| `start-independent-patient` | both | Start independent patient | Start a separate local patient session; does not reconnect the old patient or clear its effect history. |
| `public-request` | patient | Public scheduling request | Enter public scheduling intent only. Never enter names, phone, DOB, ZIP, a grant or confirmation here. |
| `send-request` | patient | Send scheduling request | Submit public intent; model-first launch may interpret it, while local controls keep authority. Enter also submits. |
| `specialty` | patient | Specialty | Choose the supported public specialty; a change must be applied/discovered and invalidates the prior proposal. |
| `location` | patient | Location | Choose a supported public location or Any location; not clinical suitability or private identity. |
| `from-date` | patient | From date | Set the earliest calendar date. A merged inverted range is rejected before availability I/O. |
| `through-date` | patient | Through date | Set the latest calendar date. Review the full range; blank represents an unset filter. |
| `apply-preferences` | patient | Apply preferences | Apply the full visible public filters without booking; inspect Active filters afterward. |
| `find-providers` | patient | Find providers | Read current public providers using visible filters; no identity or booking is needed. |
| `choose-provider` | patient | Choose provider {number} | Select a returned numbered provider as a public filter; no slot or appointment is selected. |
| `spelling-suggestion` | patient | Use {value} | Explicitly accept a public canonical suggestion; never a patient fuzzy match or automatic provider selection. |

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
