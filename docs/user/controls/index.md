# BOB control inventory

Updated 2026-10-14 against integrated runtime `e615d9894666909708fbf9810efcdafadc173a1a`
[widget.js](../../../src/ochsner_bob/widget.js). These 57 control families
include dynamic numbered provider/slot choices and spelling suggestions. Labels
are accessible text; no new UI IDs were added for documentation. `both` means a
control can be present in either local role, not that its server action is authorized.
Developer disclosure is not authentication. Outputs/status/history are observations,
not controls and not proof of effect authority.

## Disabled conditions and effect scope

- Patient request/filter/identity/choice controls require a current patient state,
  no pending work and no active support takeover. Reset remains available during
  takeover. Dynamic provider/slot/spelling buttons follow the same role guard.
- Confirm additionally requires a current verified exact proposal, matching revision,
  no unsent correction and no blocked/unknown effect. Support never confirms.
- Help/medical/unsupported need a current state and remain reachable during waits.
  They do not book. Handoff is a separate minimized mock write, not employee contact.
- Pair creation is patient-only. Take control requires fresh Support; Return and
  Suggest require active takeover. Patient adoption requires a pending suggestion
  and returned control. Pairing alone grants no booking/identity authority.
- Private disclosure and Developer disclosure can be expanded without granting
  authority. Private drafts are never mirrored. Support public fields are a read-only
  acknowledgement projection, not independent transaction inputs.
- Developer/replay inputs and many buttons are not visually disabled by role in
  the renderer. Server capability/reference/schema guards remain authoritative;
  visibility is not permission. Start recording is patient-gated; Seal/Inspect and
  Replay controls must report truthful server denials. Replay never books live care.
- Purge is intentionally destructive to the selected recording, not effect claims;
  it requires the applicable confirmation before an actual UI demonstration.

## Inventory

The local grouped atlas is complete: 18 unchanged actual originals, 17 separate
vector layers and 17 self-contained composites, bound in the
[52-record manifest](../../../assets/ui/walkthroughs/manifest.json). New captures
are offline at `bdc4585`; historical Support/spelling originals retain their source
and limits. Actual control locations do not prove every displayed action was run.

- [Session and public search](session-and-public.md)
- [Private identity and booking](private-and-booking.md)
- [Help and outcomes](help-and-outcomes.md)
- [Paired support](support.md)
- [Developer recording/diagnostics](developer-recording.md)
- [Replay navigation/bookmarks](replay-navigation.md)
- [Replay variants and data](replay-variants-and-data.md)

Each group has numbered figures, readable text equivalents, prerequisites/effects
and original/layer links. All 57 control IDs map to an actual composite. Final
independent collection review/integration remains in native tasks.

### Accessible roles and required atlas states

Native input type/accessible role is distinct from the local actor role in the
inventory below. Public request, phone, ZIP, pairing grant, interaction reference
and bookmark name are text fields; Typed variant JSON and Reviewed recording JSON
are multiline text fields. DOB/From/Through are native date fields, Replay step
index is a numeric spinbutton, Specialty/Location/Suggested public location are
comboboxes. Other actions are buttons; Private identity/Developer summaries are
disclosure buttons. Dynamic provider, option and `Use {value}` controls are buttons.
Browser-native date-picker subcontrols are framework/browser affordances, not new
BOB actions. Their exact rendering is verified in the corresponding actual capture.

| Purpose group | Distinct role/state coverage required in W2 | Authority/disabled boundary |
|---|---|---|
| session-and-public | Fresh/no session; patient filters/dates; returned providers; explicit public typo suggestions; support mirror | Starting an independent patient is separate from joining; patient actions disabled with no state, wait or takeover; support is read-only |
| private-and-booking | Expanded patient identity; missing/ambiguous/verified/corrected; returned slots and current proposal; support expanded private region | Private inputs never mirrored; selection is not confirmation; dirty/stale/unknown/Support cannot confirm |
| help-and-outcomes | Help/medical/unsupported from normal and waiting/error/terminal states; handoff queued/failed/unknown; current versus historical result | Safety actions remain reachable while waiting; separate handoff write does not mean employee contact |
| support | Empty join toolbar; patient pair action with grant excluded from assets; joined/inactive, active lease, returned/expired lease, pending suggestion/adoption, stale/missing observation | Read-only pairing does not grant takeover, private identity or confirmation; suggestion is not adoption |
| developer-recording | Disclosure closed/open; recording OFF diagnostics/reference; explicit capture active/sealed; Support denied operations | Visible Developer controls are not authorization; private fields/capabilities excluded from diagnostics |
| replay-navigation | Owned opened reference; previous/step/play/pause; zero-based jump/before-after; named bookmark; unavailable/expired reference | Simulation only; missing observations/provenance limits remain explicit; no live effect |
| replay-variants-and-data | Typed API/preference/fixture/clock/model/order/view variants; comparison; reviewed proposal; bounded export/import; rejected import; disposable purge | No historical identity/consent revival; promotion is data, not executable code; purge never removes effect protection |

Source review confirms the 57 BOB control families cover these static/dynamic
construction paths. The grouped figures locate controls across representative
states; they do not certify every listed transition. Current IAB pairing showed
acknowledgement warnings, so synchronization remains a visible gap.

### session-and-public

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `start-independent-patient` | Start independent patient | both |
| `public-request` | Public scheduling request | patient |
| `send-request` | Send scheduling request | patient |
| `specialty` | Specialty | patient |
| `location` | Location | patient |
| `from-date` | From date | patient |
| `through-date` | Through date | patient |
| `apply-preferences` | Apply preferences | patient |
| `find-providers` | Find providers | patient |
| `choose-provider` | Choose provider {number} | patient |
| `spelling-suggestion` | Use {value} | patient |

### private-and-booking

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `private-disclosure` | 2 · Private synthetic identity | both |
| `synthetic-phone` | Synthetic phone | patient |
| `date-of-birth` | Date of birth | patient |
| `zip-discriminator` | ZIP discriminator | patient |
| `check-identity` | Check or correct identity | patient |
| `get-availability` | Get current availability | patient |
| `lookup-appointments` | Look up my appointments | patient |
| `select-option` | Select option {number} | patient |
| `confirm-appointment` | Confirm appointment | patient |
| `decline` | Decline / change my mind | patient |

### help-and-outcomes

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `help` | Help | both |
| `medical-boundary` | Medical boundary | both |
| `unsupported-request` | Unsupported request | both |
| `submit-handoff` | Submit mock handoff | patient |
| `reset-workflow` | Reset local workflow | patient |

### support

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `pairing-grant` | One-use pairing grant | both |
| `join-support` | Join demo support | both |
| `create-pairing` | Create support pairing grant | patient |
| `take-control` | Take demo control | support |
| `return-control` | Return patient control | support |
| `suggested-location` | Suggested public location | support |
| `suggest-preference` | Suggest preference — not adoption | support |
| `accept-suggestion` | Accept reviewed support suggestion | patient |

### developer-recording

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `developer-disclosure` | Developer Mode · local PoC diagnostics and replay | both |
| `interaction-reference` | Interaction reference | both |
| `start-recording` | Start synthetic recording | patient |
| `seal-recording` | Seal recording | both |
| `inspect-diagnostics` | Inspect sanitized diagnostics | both |

### replay-navigation

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `open-reference` | Open reference | both |
| `previous` | Previous | both |
| `step` | Step | both |
| `pause` | Pause | both |
| `play` | Play recorded steps | both |
| `replay-index` | Replay step index (zero based) | both |
| `jump` | Jump / inspect before and after | both |
| `bookmark-name` | Bookmark name | both |
| `bookmark` | Bookmark current step | both |
| `go-bookmark` | Go to bookmark | both |

### replay-variants-and-data

| Catalog ID | Accessible label/pattern | Local role |
|---|---|---|
| `typed-variant` | Typed variant JSON | both |
| `fork` | Fork isolated simulation | both |
| `compare` | Compare with reference | both |
| `propose-regression` | Propose reviewed regression fixture | both |
| `export-recording` | Export reviewed synthetic recording | both |
| `recording-json` | Reviewed recording JSON / import | both |
| `import-recording` | Import bounded synthetic recording | both |
| `purge-recording` | Purge selected recording only | both |

## Revision history

- 2026-10-12: W1 inventory only; no grouped actual screenshot certification.
- 2026-10-13: Reconciled current renderer and explicit accessible-role/state matrix;
  W2 actual clean/annotated captures and privacy review remain open.

## References

- [Walkthrough inventory](../walkthroughs/index.md)
- [Source-bound native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
