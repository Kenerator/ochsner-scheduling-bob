# BOB control inventory

Updated 2026-10-12 against `d925f326dd604b3eba07d844914810e2f2574705`
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

The grouped annotated atlas pages and visuals are pending W2. This source inventory
was reconciled with earlier patient/paired runtime observations, but the below-fold
Developer collection has not been newly exercised on the current candidate.

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

## References

- [Walkthrough inventory](../walkthroughs/index.md)
- [Source-bound native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
