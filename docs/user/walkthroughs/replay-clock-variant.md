# Inspect a forward-clock counterfactual

Purpose: Change simulation time without changing the machine clock or predicting browser observations. Role: developer or regression reviewer.

Scope: US4 / FR-015 / tests/test_replay_contract.py. Mode: recorded-simulation; no live effects in forks. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

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

1. Capture exactly one **Help** event; intended event index is `0`.
2. Exact test clock: `1791543600`; test change is `{"clock":1791543612}` (12 seconds later).
3. For a fresh UI capture, read its own events[0].clock and use that finite numeric value plus `12`, not the historical test timestamp.
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

## Step 3 — Capture one Help action
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help"]} -->

Select **Help** (`help`) once and wait for its displayed result. Expected: one captured local help event with no model, booking or handoff. Recovery: if acknowledgement is unavailable, preserve the incomplete report; no renderer observation may be invented.

![Source-bound actual offline control composite; help actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Seal and open the owned recorded reference
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["recording-and-diagnostics-composite","replay-basic-composite"],"control_ids":["seal-recording","interaction-reference","open-reference"]} -->

Select **Seal recording** (`seal-recording`). Review its reference, recording status, missing fields, dropped count and stored flag. Keep the returned reference in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`). Expected: an owned recorded-only simulation starting at index -1, with event_count and fidelity disclosed. `incomplete_capture` may still permit bounded semantic inspection; it never becomes full browser evidence. Recovery: if storage is unavailable or the reference is expired/not granted, preserve the report and capture a new disposable session if appropriate. OFF diagnostics cannot substitute for an exact recording.

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 5 — Read the selected event's actual clock
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["recording-data-actions-composite"],"control_ids":["export-recording","recording-json"]} -->

After reviewing your disposable synthetic capture, select **Export reviewed synthetic recording** (`export-recording`) and inspect **Reviewed recording JSON / import** (`recording-json`). Read events[0].clock and compute that number plus 12. Expected: an exact captured timestamp, not wall-clock authorization. Recovery: if expired, unexportable or missing a valid event clock, use the automated contract below; do not alter the system clock or an Operator recording.

![Source-bound actual offline control composite; recording data actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-data-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 6 — Fork a finite forward clock value
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["replay-position-and-bookmark-composite","variant-edit-and-review-composite"],"control_ids":["replay-index","typed-variant","fork","jump"]} -->

Set **Replay step index** (`replay-index`) to `0`. In **Typed variant JSON** (`typed-variant`) enter an object with only clock and the numeric value you computed, for example `{"clock":1791543612}` only for the exact test recording clock 1791543600. Paste a real number, not a formula or placeholder. Select **Fork isolated simulation** (`fork`), then **Jump / inspect before and after** (`jump`). Expected contract: the help core still recomputes, original view receipts are removed and the counterfactual is incomplete rather than original parity. Recovery: review the current index and bounds; never make the operating-system clock match the example.

![Source-bound actual offline control composite; replay position and bookmark composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 7 — Inspect the variant and compare with its parent
<!-- walkthrough-step: {"number":7,"interactive":true,"visual_ids":["replay-position-and-bookmark-composite","variant-edit-and-review-composite"],"control_ids":["jump","interaction-reference","compare"]} -->

Keep the intended event index and select **Jump / inspect before and after** (`jump`) to inspect the variant's actual state and missing evidence. For comparison, enter the saved original reference in **Interaction reference** (`interaction-reference`) and select **Compare with reference** (`compare`) while the variant remains the active replay; do not select Open reference, which would replace it. Expected: simulation-only differences and provenance drift, with immutable original history. Recovery: if no active variant or wrong parent is selected, reopen the owned original and create the intended variant again. Comparison output may identify an event/outcome change even when semantic state matches.

![Source-bound actual offline control composite; replay position and bookmark composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 8 — Verify the exact plus-twelve contract in automation
<!-- walkthrough-step: {"number":8,"interactive":false,"visual_ids":["variant-edit-and-review-composite"],"control_ids":[]} -->

Automated-only exact example advances the captured event clock by 12, asserts empty observed_views and incomplete_capture, and recomputes Help without writes. Recovery: retain the new missing browser evidence; changed time cannot transplant original acknowledgements or renew retention.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_view_receipt_capture.ViewReceiptCaptureTests.test_forward_clock_variant_keeps_core_but_does_not_predict_browser_observation -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_typed_preference_identity_clock_model_and_order_variants -v
```

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Only a private simulation branch and its comparison data are created. No live booking, model request, handoff, staff contact or care is produced by replay. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: A clock variant is not recording TTL renewal, a new browser observation or a live expiry test. W2 did not execute this complete counterfactual; original browser receipts are explicitly unavailable after clock/order changes. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_view_receipt_capture.ViewReceiptCaptureTests.test_forward_clock_variant_keeps_core_but_does_not_predict_browser_observation -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_typed_preference_identity_clock_model_and_order_variants -v
```

Not run by this document worker: setup/install/doctor, app launch, browser actions, fault injection, model calls, destructive purge, demos or the full suite. Parent owns combined verification and final integration. Structural coverage is not browser certification; no mobile, accessibility, renderer-parity or genuine new model qualification is claimed.

## Revision history

- 2026-10-14: Drafted from exact sources and supplied atlas evidence; parent final QA/integration pending. Native tasks remain the sole progress ledger.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) · [plan](../../../specs/001-ochsner-scheduling-assistant/plan.md) · [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
- [Control atlas](../controls/replay-variants-and-data.md) · [all control groups](../controls/index.md).
- [Visual manifest and evidence limitations](../../../assets/ui/walkthroughs/manifest.json) · [historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json).
- [Runtime and exact-note helper guidance](../getting-started.md) · [recovery](../recovery.md).
- [tests/test_view_receipt_capture.py](../../../tests/test_view_receipt_capture.py).
- [tests/test_replay_contract.py](../../../tests/test_replay_contract.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
