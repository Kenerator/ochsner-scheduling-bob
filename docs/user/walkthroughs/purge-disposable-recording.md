# Purge only a selected disposable recording

Purpose: Understand selected-recording removal while preserving effect protection and unrelated Operator state. Role: developer or synthetic-session reviewer.

Scope: US4. Mode: recorded-simulation; capture uses the explicitly chosen launch mode. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

## Step 0 — Install and set up

From the repository root, verify Python 3.11+ and install into the project environment:

```sh
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip check
.venv/bin/python tools/poc-runtime/launch.py --doctor
```

If `python3.11` is absent, use an explicit compatible executable, for example `/opt/homebrew/bin/python3.12`: verify its `--version` is 3.11+ and use that same executable for `-m venv .venv`. Do not assume `python3` is compatible. Follow [getting started](../getting-started.md) for the trusted exact-note helper and current application runtime policy. Doctor retrieves no key, starts no service and makes no model call.

## Step 1 — Launch

Normal model-first launch:

```sh
.venv/bin/python tools/poc-runtime/launch.py
```

Open the printed local URL. Startup/readiness does not qualify model behavior. A port conflict is an error, not permission to stop another process. Ctrl-C owns only this launch and its children.

For an explicit no-call walkthrough, use the following only if **both ports are free**:

```sh
.venv/bin/python tools/poc-runtime/launch.py --offline --ui-port 29580 --transport-port 29581
```

Do not reuse or stop an existing process on those ports. All supplied W2 capture evidence is offline or dated historical synthetic evidence; it is not genuine new model qualification.

## Arrange the workspace

Keep this rendered Markdown on the left and BOB on the right. In Chrome, open a tab's context menu and use **New split view**, then **Add tab** to select the other tab; use **Swap sides** if needed. See [official Chrome Split View guidance](https://support.google.com/chrome/answer/16971124?hl=en). If unavailable, use side-by-side windows; no extension or experimental flags are needed.

## Synthetic sample data

1. Create a new disposable recording of **Help**, then **Medical boundary**.
2. Selection must be your exact disposable original reference, not an Operator recording or a fork left selected.
3. Purge has no undo; do not rely on reimport of an export to revive its tombstone.
4. Private synthetic phone: `555-0101` in **Synthetic phone** only.
5. Private DOB: `1985-04-12` in **Date of birth** only.
6. Private ZIP: `70112` in **ZIP discriminator** only. These values are optional orientation for flows that do not identify a patient.

Keep names, phone, DOB and ZIP out of the public request box. Only application-owned private identity controls receive those fixture values. Use only your own disposable local session and recording references.

## Step 2 — Start a disposable patient and opt into capture
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite","recording-and-diagnostics-composite"],"control_ids":["start-independent-patient","developer-disclosure","start-recording"]} -->

Select **Start independent patient** (`start-independent-patient`), scroll below the main flow and expand **Developer Mode · local PoC diagnostics and replay** (`developer-disclosure`). Select **Start synthetic recording** (`start-recording`) before the sample actions. Expected: explicit synthetic capture is active with a local reference. This disclosure is not authentication. Recovery: if disabled or denied, check patient role, pending work and takeover; do not use a Support role or an Operator session to force capture.

![Source-bound actual offline control composite; toolbar composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 3 — Capture two safe local actions
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help","medical-boundary"]} -->

Select **Help** (`help`), wait for its visible result, then select **Medical boundary** (`medical-boundary`) and wait again. Expected: help followed by the local medical boundary without advice or a handoff write. Recording begins before both actions; browser acknowledgement failures remain missing evidence. Recovery: inspect the actual message after reconnect and do not infer that an unobserved action occurred. Never select Submit mock handoff as part of this sample.

![Source-bound actual offline control composite; help actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Seal and open the owned recorded reference
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["recording-and-diagnostics-composite","replay-basic-composite"],"control_ids":["seal-recording","interaction-reference","open-reference"]} -->

Select **Seal recording** (`seal-recording`). Review its reference, recording status, missing fields, dropped count and stored flag. Keep the returned reference in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`). Expected: an owned recorded-only simulation starting at index -1, with event_count and fidelity disclosed. `incomplete_capture` may still permit bounded semantic inspection; it never becomes full browser evidence. Recovery: if storage is unavailable or the reference is expired/not granted, preserve the report and capture a new disposable session if appropriate. OFF diagnostics cannot substitute for an exact recording.

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 5 — Pause and positively identify the disposable selection
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["replay-basic-composite","recording-and-diagnostics-composite"],"control_ids":["pause","interaction-reference","open-reference"]} -->

Select **Pause** (`pause`). Re-enter the exact original disposable reference in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`); inspect the returned reference. Expected: the intended recording is current. Recovery: do not proceed if ownership or selection is uncertain. The renderer prefers its current replayReference for purge, so editing the text field alone does not select the purge target.

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 6 — Purge only after the user selects this disposable target
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["recording-data-actions-composite"],"control_ids":["purge-recording"]} -->

This is the final destructive action and requires the user's deliberate selection of this disposable recording. Only then select **Purge selected recording only** (`purge-recording`) once. The current UI sends the action directly; do not expect an extra confirmation dialog. Expected: its reference is permanently expired and retained replay copies are disabled, while effect claims, capabilities and unrelated recordings remain. Recovery: there is no undo and an exported copy cannot revive the tombstone. If this is merely a read-through or the target is unconfirmed, stop before pressing the button.

![Source-bound actual offline control composite; recording data actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-data-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 7 — Check protection boundaries using disposable automated fixtures
<!-- walkthrough-step: {"number":7,"interactive":false,"visual_ids":["recording-data-actions-composite"],"control_ids":[]} -->

Automated-only isolation evidence uses temporary stores/journals, never Operator state. Expected: purge/expiry disable open replays but preserve unknown-write protection and unrelated files. Recovery: retain the expired reference as the honest result; create a separate new capture if needed. The current W2 plate is orientation only and does not show an executed purge.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_expiry_and_purge_disable_open_replays_without_erasing_unknown_protection -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_purge_and_expiry_never_touch_effect_journal_capabilities_or_unknown_files -v
```

![Source-bound actual offline control composite; recording data actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-data-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: If the user deliberately performs the final action, only the selected disposable recording is tombstoned; this is destructive and not undoable. No booking, staff contact or care occurs. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Pause playback and close only your own tabs. Stop only your own launch with Ctrl-C. Do not purge any additional recording or erase Operator state, accounting, capabilities or the effect journal.

## Known gaps and evidence

Recovery: No purge was executed during W2 or drafting. Selection, ownership and user intent must be checked at the final action. Purge affects recording data only, never an unknown booking/handoff liability. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_expiry_and_purge_disable_open_replays_without_erasing_unknown_protection -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_purge_and_expiry_never_touch_effect_journal_capabilities_or_unknown_files -v
```

Not run by this document worker: setup/install/doctor, app launch, browser actions, fault injection, model calls, destructive purge, demos or the full suite. Parent owns combined verification and final integration. Structural coverage is not browser certification; no mobile, accessibility, renderer-parity or genuine new model qualification is claimed.

## Revision history

- 2026-10-14: Drafted from exact sources and supplied atlas evidence; parent final QA/integration pending. Native tasks remain the sole progress ledger.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) · [plan](../../../specs/001-ochsner-scheduling-assistant/plan.md) · [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
- [Control atlas](../controls/replay-variants-and-data.md) · [all control groups](../controls/index.md).
- [Visual manifest and evidence limitations](../../../assets/ui/walkthroughs/manifest.json) · [historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json).
- [Runtime and exact-note helper guidance](../getting-started.md) · [recovery](../recovery.md).
- [tests/test_interaction_service.py](../../../tests/test_interaction_service.py).
- [tests/test_recording_store.py](../../../tests/test_recording_store.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
