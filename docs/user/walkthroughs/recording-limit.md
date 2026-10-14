# Recognize capture and storage limits honestly

Purpose: Keep earlier capture intact and report overflow without altering the live workflow result. Role: developer or failure/recovery reviewer.

Scope: US4 / FR-015 / tests/test_replay_contract.py. Mode: recorded-simulation; lowered-limit faults are automated-only. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

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

1. Normal sample capture: **Help**, then **Medical boundary**.
2. Exact overflow fixture: max_events=`1`, append Help then Medical; prior Help event survives and the second append is dropped.
3. Default bounds: 2000 events, 4096-character strings, depth 12, 10 MiB recording, 1 MiB import; the store has separate session/aggregate bounds.
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

## Step 5 — Read dropped, missing and storage information
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["recording-and-diagnostics-composite"],"control_ids":["inspect-diagnostics"]} -->

Select **Inspect sanitized diagnostics** (`inspect-diagnostics`) and inspect the seal/open report. Expected: within normal limits this two-action capture need not overflow. If a real overflow or storage error exists, dropped/missing/stored must disclose it while the patient Help/Medical outcome remains truthful. Recovery: do not treat an incomplete recording as a failed clinical action or retry a write; preserve earlier evidence and report its limit.

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 6 — Reproduce bounded overflow without filling real storage
<!-- walkthrough-step: {"number":6,"interactive":false,"visual_ids":["recording-and-diagnostics-composite"],"control_ids":[]} -->

Automated-only: set max_events=1 in a disposable fixture, append Help then Medical, preserve the first event and report incomplete_capture. The byte-overflow test uses max_record_bytes=1500 and a 4096-character language input; it preserves earlier capture and reports dropped=1. The interaction-service fixture verifies the live Medical result survives capture overflow/storage failure. Expected: explicit gaps with no truncation of earlier history. Recovery: use a new small approved capture after reviewing the cause; never mass-click, lower production limits or fill/purge Operator storage to demonstrate failure. No UI limit-setting control exists.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_overflow_does_not_mutate_prior_events_or_hide_incomplete_capture -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_recording_byte_overflow_drops_without_losing_earlier_capture -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_overflow_and_storage_failure_are_visible_without_changing_live_result -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_aggregate_overflow_preserves_existing_recording_and_is_visible -v
```

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Orientation and the cited disposable fault fixtures do not authorize real scheduling, staff contact or care. There is no live write retry. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: The ordinary small UI capture is orientation, not overflow reproduction. Recording size/event limits, import size, receipt-history bounds and aggregate store capacity are distinct contracts. Exact reduced-limit and storage-failure triggers are automated-only; no new limit failure was observed in W2. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_overflow_does_not_mutate_prior_events_or_hide_incomplete_capture -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_recording_byte_overflow_drops_without_losing_earlier_capture -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_overflow_and_storage_failure_are_visible_without_changing_live_result -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_aggregate_overflow_preserves_existing_recording_and_is_visible -v
```

Not run by this document worker: setup/install/doctor, app launch, browser actions, fault injection, model calls, destructive purge, demos or the full suite. Parent owns combined verification and final integration. Structural coverage is not browser certification; no mobile, accessibility, renderer-parity or genuine new model qualification is claimed.

## Revision history

- 2026-10-14: Drafted from exact sources and supplied atlas evidence; parent final QA/integration pending. Native tasks remain the sole progress ledger.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) · [plan](../../../specs/001-ochsner-scheduling-assistant/plan.md) · [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
- [Control atlas](../controls/developer-recording.md) · [all control groups](../controls/index.md).
- [Visual manifest and evidence limitations](../../../assets/ui/walkthroughs/manifest.json) · [historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json).
- [Runtime and exact-note helper guidance](../getting-started.md) · [recovery](../recovery.md).
- [tests/test_replay_contract.py](../../../tests/test_replay_contract.py).
- [tests/test_interaction_service.py](../../../tests/test_interaction_service.py).
- [tests/test_recording_store.py](../../../tests/test_recording_store.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/recording_store.py](../../../src/ochsner_bob/recording_store.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
