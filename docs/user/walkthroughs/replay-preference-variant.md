# Compare a public preference variant

Purpose: Try an alternate public location without rewriting history or changing the patient session. Role: developer or regression reviewer.

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

1. Original applied preferences: Primary care (`primary_care`), Downtown (`downtown`).
2. Typed change: `{"preferences":{"location":"uptown"}}`.
3. Minimal preference/help recording: preference at zero-based `0`; use actual event evidence.
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

## Step 3 — Capture a public preference followed by Help
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["public-filters-composite","help-actions-composite"],"control_ids":["specialty","location","apply-preferences","help"]} -->

Choose **Specialty** (`specialty`) = **Primary care** and **Location** (`location`) = **Downtown**, then select **Apply preferences** (`apply-preferences`) once. Wait for Active filters to match, then select **Help** (`help`). Expected: a preference event followed by help, no private identity or write. Recovery: if stale or reconnected, inspect the actual event count and state before choosing an index; do not assume an event was captured.

![Source-bound actual offline control composite; public filters composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

![Source-bound actual offline control composite; help actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Seal and open the owned recorded reference
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["recording-and-diagnostics-composite","replay-basic-composite"],"control_ids":["seal-recording","interaction-reference","open-reference"]} -->

Select **Seal recording** (`seal-recording`). Review its reference, recording status, missing fields, dropped count and stored flag. Keep the returned reference in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`). Expected: an owned recorded-only simulation starting at index -1, with event_count and fidelity disclosed. `incomplete_capture` may still permit bounded semantic inspection; it never becomes full browser evidence. Recovery: if storage is unavailable or the reference is expired/not granted, preserve the report and capture a new disposable session if appropriate. OFF diagnostics cannot substitute for an exact recording.

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 5 — Fork the preference input
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["replay-position-and-bookmark-composite","variant-edit-and-review-composite"],"control_ids":["replay-index","typed-variant","fork"]} -->

Enter `0` in **Replay step index (zero based)** (`replay-index`) only after confirming the intended event is at that index. Replace **Typed variant JSON** (`typed-variant`) with:

```json
{"preferences":{"location":"uptown"}}
```

Select **Fork isolated simulation** (`fork`). Expected: a separate branch/reference/namespace; the simulated preference is uptown once that step is computed; live patient filters and original recording stay downtown. Recovery: invalid JSON, wrong event kind, missing evidence, expired reference or a stale index requires review/reopening of the owned recording. Do not change serialized authority or force success. The current plate locates controls only; it is not evidence this variant succeeded.

![Source-bound actual offline control composite; replay position and bookmark composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 6 — Inspect the variant and compare with its parent
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["replay-position-and-bookmark-composite","variant-edit-and-review-composite"],"control_ids":["jump","interaction-reference","compare"]} -->

Keep the intended event index and select **Jump / inspect before and after** (`jump`) to inspect the variant's actual state and missing evidence. For comparison, enter the saved original reference in **Interaction reference** (`interaction-reference`) and select **Compare with reference** (`compare`) while the variant remains the active replay; do not select Open reference, which would replace it. Expected: simulation-only differences and provenance drift, with immutable original history. Recovery: if no active variant or wrong parent is selected, reopen the owned original and create the intended variant again. Comparison output may identify an event/outcome change even when semantic state matches.

![Source-bound actual offline control composite; replay position and bookmark composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-position-and-bookmark-composite.svg)

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Only a private simulation branch and its comparison data are created. No live booking, model request, handoff, staff contact or care is produced by replay. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: W2's intended preferred-location variant was not observed succeeding. Reconnect/index reset may have changed the selected index; no adoption or successful variant is claimed. A preference variant cannot predict different server results from original recorded-only fixtures. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_typed_preference_identity_clock_model_and_order_variants -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_all_replay_controls_are_pure_and_review_is_explicit -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_live_core.LiveCoreReplayTests.test_variant_recomputes_actual_guards_instead_of_success_observation -v
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
- [tests/test_interaction_service.py](../../../tests/test_interaction_service.py).
- [tests/test_replay_live_core.py](../../../tests/test_replay_live_core.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
