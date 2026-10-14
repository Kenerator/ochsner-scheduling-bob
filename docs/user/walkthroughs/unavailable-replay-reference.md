# Handle an unavailable replay reference

Purpose: Receive a safe reference denial without gaining access or inventing a historical result. Role: developer or synthetic-session reviewer.

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

1. Syntactically shaped unknown test reference: `BOB-bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb/step/1/branch/original`.
2. Malformed contrast: `not-a-reference` is invalid syntax, not proof that an actual recording expired.
3. Do not substitute a real foreign patient's reference.
4. Private synthetic phone: `555-0101` in **Synthetic phone** only.
5. Private DOB: `1985-04-12` in **Date of birth** only.
6. Private ZIP: `70112` in **ZIP discriminator** only. These values are optional orientation for flows that do not identify a patient.

Keep names, phone, DOB and ZIP out of the public request box. Only application-owned private identity controls receive those fixture values. Use only your own disposable local session and recording references.

## Step 2 — Start your own patient and open Developer Mode
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite","recording-and-diagnostics-composite"],"control_ids":["start-independent-patient","developer-disclosure"]} -->

Select **Start independent patient** (`start-independent-patient`) and expand **Developer Mode** (`developer-disclosure`). Expected: a current caller session; the disclosure does not grant access to recordings. Recovery: restore local connectivity before attempting a reference; never use a copied capability.

![Source-bound actual offline control composite; toolbar composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 3 — Request the shaped unknown reference
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["replay-basic-composite"],"control_ids":["interaction-reference","open-reference"]} -->

Enter the numbered unknown sample in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`). Expected: unavailable/not-granted notice without revealing whether a foreign recording exists; no simulation success or effect retry. Recovery: use an actual owned sealed reference, or import approved bounded recording data into this session. Do not repeatedly probe foreign references. This actual navigation plate is orientation only, not a captured denial.

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Distinguish absence, expiry and OFF inspection
<!-- walkthrough-step: {"number":4,"interactive":false,"visual_ids":["recording-and-diagnostics-composite"],"control_ids":[]} -->

Automated-only branches check unknown/missing store steps and foreign/invalid/expired OFF references. Owned expired data reports expired; a malformed reference is a validation error. A valid owned OFF reference opens current sanitized diagnostics, never exact history. Recovery: collect current owned diagnostics or make a new explicit synthetic capture; do not treat OFF as a failed exact recording to be repaired by fabricated data.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_unknown_and_missing_steps_are_unavailable_not_filesystem_paths -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_off_reference.OffReferenceTests.test_unknown_foreign_invalid_and_expired_off_references_never_gain_access -v
```

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Capture and review change only private bounded diagnostic/recording state; sample Help/Medical actions do not book or contact staff. No real care or delivery. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: No fresh unknown-reference UI failure was captured. Access denial is deliberately generic; it does not certify the existence, authenticity or expiry of someone else's recording. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_unknown_and_missing_steps_are_unavailable_not_filesystem_paths -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_off_reference.OffReferenceTests.test_unknown_foreign_invalid_and_expired_off_references_never_gain_access -v
```

Not run by this document worker: setup/install/doctor, app launch, browser actions, fault injection, model calls, destructive purge, demos or the full suite. Parent owns combined verification and final integration. Structural coverage is not browser certification; no mobile, accessibility, renderer-parity or genuine new model qualification is claimed.

## Revision history

- 2026-10-14: Drafted from exact sources and supplied atlas evidence; parent final QA/integration pending. Native tasks remain the sole progress ledger.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) · [plan](../../../specs/001-ochsner-scheduling-assistant/plan.md) · [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
- [Control atlas](../controls/replay-navigation.md) · [all control groups](../controls/index.md).
- [Visual manifest and evidence limitations](../../../assets/ui/walkthroughs/manifest.json) · [historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json).
- [Runtime and exact-note helper guidance](../getting-started.md) · [recovery](../recovery.md).
- [tests/test_recording_store.py](../../../tests/test_recording_store.py).
- [tests/test_off_reference.py](../../../tests/test_off_reference.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
