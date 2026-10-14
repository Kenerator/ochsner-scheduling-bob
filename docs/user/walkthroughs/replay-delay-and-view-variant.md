# Compare timing and recorded-view differences

Purpose: See event evidence differences even when semantic state matches, while respecting the absence of a view-edit control. Role: developer or regression reviewer.

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

1. Capture private identity, Primary care/Downtown preferences and availability; do not confirm.
2. Typed API delay sample: `{"api_delay_ms":123}` at availability event index `2` in the minimal capture.
3. Automated view replacement: `Another synthetic label`; there is no allowed typed `view` key.
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

## Step 3 — Capture the approved private fixture selection
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["private-entry-composite"],"control_ids":["private-disclosure","synthetic-phone","date-of-birth","zip-discriminator","check-identity"]} -->

Expand **2 · Private synthetic identity** (`private-disclosure`), enter phone `555-0101`, DOB `1985-04-12` and ZIP `70112` in `synthetic-phone`, `date-of-birth`, `zip-discriminator`, then select **Check or correct identity** (`check-identity`) once. Expected: verified fixture and cleared browser fields; the capture uses host-approved `patient-1`, not raw identity. Recovery: correct only local private controls if necessary; unbound or missing fixture evidence is an explicit capture gap.

![Source-bound actual offline control composite; private entry composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/private-entry-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Capture preferences and one availability read
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-filters-composite","returned-options-and-confirm-composite"],"control_ids":["specialty","location","apply-preferences","get-availability"]} -->

Choose **Primary care** in **Specialty** (`specialty`), **Downtown** in **Location** (`location`) and select **Apply preferences** (`apply-preferences`). Then select **Get current availability** (`get-availability`) once. Expected: mock-returned options or a truthful read result; do not select or confirm an appointment. In this deliberately minimal sequence the identity, preference and availability events are expected at zero-based 0, 1 and 2; verify the actual event count. Recovery: if read fails, retain that outcome and do not invent an ok observation.

![Source-bound actual offline control composite; public filters composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

![Source-bound actual offline control composite; returned options and confirm composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/returned-options-and-confirm-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 5 — Seal and open the owned recorded reference
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["recording-and-diagnostics-composite","replay-basic-composite"],"control_ids":["seal-recording","interaction-reference","open-reference"]} -->

Select **Seal recording** (`seal-recording`). Review its reference, recording status, missing fields, dropped count and stored flag. Keep the returned reference in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`). Expected: an owned recorded-only simulation starting at index -1, with event_count and fidelity disclosed. `incomplete_capture` may still permit bounded semantic inspection; it never becomes full browser evidence. Recovery: if storage is unavailable or the reference is expired/not granted, preserve the report and capture a new disposable session if appropriate. OFF diagnostics cannot substitute for an exact recording.

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 6 — Fork a recorded API delay
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["replay-position-and-bookmark-composite","variant-edit-and-review-composite"],"control_ids":["replay-index","typed-variant","fork"]} -->

Enter `2` in **Replay step index (zero based)** (`replay-index`) only after confirming the intended event is at that index. Replace **Typed variant JSON** (`typed-variant`) with:

```json
{"api_delay_ms":123}
```

Select **Fork isolated simulation** (`fork`). Expected: a separate branch/reference/namespace; the recorded API delay is 123 ms; this is evidence metadata, not a deliberate live network wait, response-time target or new measured latency. Recovery: invalid JSON, wrong event kind, missing evidence, expired reference or a stale index requires review/reopening of the owned recording. Do not change serialized authority or force success. The current plate locates controls only; it is not evidence this variant succeeded.

![Source-bound actual offline control composite; replay position and bookmark composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 7 — Inspect the variant and compare with its parent
<!-- walkthrough-step: {"number":7,"interactive":true,"visual_ids":["replay-position-and-bookmark-composite","variant-edit-and-review-composite"],"control_ids":["jump","interaction-reference","compare"]} -->

Keep the intended event index and select **Jump / inspect before and after** (`jump`) to inspect the variant's actual state and missing evidence. For comparison, enter the saved original reference in **Interaction reference** (`interaction-reference`) and select **Compare with reference** (`compare`) while the variant remains the active replay; do not select Open reference, which would replace it. Expected: simulation-only differences and provenance drift, with immutable original history. Recovery: if no active variant or wrong parent is selected, reopen the owned original and create the intended variant again. Comparison output may identify an event/outcome change even when semantic state matches.

![Source-bound actual offline control composite; replay position and bookmark composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 8 — Review the automated-only recorded-view comparison
<!-- walkthrough-step: {"number":8,"interactive":false,"visual_ids":["variant-edit-and-review-composite"],"control_ids":[]} -->

There is no current UI control or typed-change field for editing recorded view. Do not paste a view key into Typed variant JSON. The exact test forks its confirm event at index 4 with api_delay_ms=123, asserts an outcomes event difference despite equal semantics, then replaces its test document's visible label with Another synthetic label through its re-signed fixture helper and asserts a view difference. Recovery: use that disposable automated fixture; do not hand-edit real exports or claim a captured failure. This current actual control plate is orientation only.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_delay_and_view_changes_are_visible_even_when_semantic_state_matches -v
```

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Only a private simulation branch and its comparison data are created. No live booking, model request, handoff, staff contact or care is produced by replay. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: Delay has a typed UI route; view editing is automated-only and absent from the closed schema. A digest recalculated in a fixture is not authenticity. W2 only located controls and did not execute this delay/view comparison. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_delay_and_view_changes_are_visible_even_when_semantic_state_matches -v
```

Not run by this document worker: setup/install/doctor, app launch, browser actions, fault injection, model calls, destructive purge, demos or the full suite. Parent owns combined verification and final integration. Structural coverage is not browser certification; no mobile, accessibility, renderer-parity or genuine new model qualification is claimed.

## Revision history

- 2026-10-14: Drafted from exact sources and supplied atlas evidence; parent final QA/integration pending. Native tasks remain the sole progress ledger.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) · [plan](../../../specs/001-ochsner-scheduling-assistant/plan.md) · [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
- [Control atlas](../controls/replay-variants-and-data.md) · [all control groups](../controls/index.md).
- [Visual manifest and evidence limitations](../../../assets/ui/walkthroughs/manifest.json) · [historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json).
- [Runtime and exact-note helper guidance](../getting-started.md) · [recovery](../recovery.md).
- [tests/test_replay_contract.py](../../../tests/test_replay_contract.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
