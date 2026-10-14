# Handle an expired recording and replay

Purpose: Recognize the retention boundary without reviving data or erasing effect protection. Role: developer or failure/recovery reviewer.

Scope: US4 / FR-015 / tests/test_recording_store.py. Mode: recorded-simulation; deterministic expiry is automated-only. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

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

1. Default recording TTL: `86400` seconds (24 hours); inspect expires_at for the actual capture.
2. Test boundary: available at NOW+86399, expired at NOW+86400.
3. Use only an already owned expired reference; do not age Operator state or alter the machine clock.
4. Private synthetic phone: `555-0101` in **Synthetic phone** only.
5. Private DOB: `1985-04-12` in **Date of birth** only.
6. Private ZIP: `70112` in **ZIP discriminator** only. These values are optional orientation for flows that do not identify a patient.

Keep names, phone, DOB and ZIP out of the public request box. Only application-owned private identity controls receive those fixture values. Use only your own disposable local session and recording references.

## Step 2 — Start a patient and inspect the safe local controls
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite","recording-and-diagnostics-composite"],"control_ids":["start-independent-patient","developer-disclosure","inspect-diagnostics"]} -->

Use the disposable patient session already owning an expired reference, if one exists. Otherwise select **Start independent patient** (`start-independent-patient`) only for orientation; a new session does not inherit old recording access. Expand **Developer Mode** (`developer-disclosure`) and select **Inspect sanitized diagnostics** (`inspect-diagnostics`). Expected: current bounded diagnostic state; this step does not age or expire a recording. Recovery: inspect again if reconnect clears output, retaining the actual missing/expired information.

![Source-bound actual offline control composite; toolbar composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 3 — Open an owned expired reference if one already exists
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["replay-basic-composite"],"control_ids":["interaction-reference","open-reference"]} -->

If your own approved capture has actually expired, enter its reference in **Interaction reference** (`interaction-reference`) and select **Open reference** (`open-reference`). Expected: expired with no replay payload; active controls must not retain an old snapshot. If no such reference exists, proceed to the automated step instead of waiting or forcing expiry. Recovery: capture a new approved synthetic interaction separately. A foreign or unknown reference yields generic not-granted/unavailable and must not be called expired.

![Source-bound actual offline control composite; replay basic composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/replay-basic-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Check the retention boundary and active replay erasure
<!-- walkthrough-step: {"number":4,"interactive":false,"visual_ids":["recording-data-actions-composite"],"control_ids":[]} -->

Automated-only: temporary-store tests compare NOW+86399 with NOW+86400, erase expired payload and preserve the expired reference across reopen. The active-Replay test asserts its snapshot/bookmarks are erased and controls stop. Expected: expired data cannot be replayed/exported or renewed by polling/reopening. Recovery: preserve tombstone and effect protection; do not reset timestamps, reimport to revive the reference, purge extra state or change the system clock. The plate is orientation only, not a captured expired recording.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_ttl_boundary_erases_payload_and_reference_stays_expired_across_reopen -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_expiring_an_active_replay_erases_its_snapshot_and_stops_controls -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_expired_and_incomplete_imports_never_become_full_replay_or_exportable_expired_data -v
```

![Source-bound actual offline control composite; recording data actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-data-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Orientation and the cited disposable fault fixtures do not authorize real scheduling, staff contact or care. There is no live write retry. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: No expired UI fixture is supplied and no new TTL wait or expiry operation ran. Expiry differs from absence, denied ownership and OFF inspection. Unknown-write claims outlive recordings and remain blocked. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_recording_store.RecordingStoreTests.test_ttl_boundary_erases_payload_and_reference_stays_expired_across_reopen -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_expiring_an_active_replay_erases_its_snapshot_and_stops_controls -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_expired_and_incomplete_imports_never_become_full_replay_or_exportable_expired_data -v
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
- [tests/test_replay_contract.py](../../../tests/test_replay_contract.py).
- [tests/test_interaction_service.py](../../../tests/test_interaction_service.py).
- [src/ochsner_bob/recording_store.py](../../../src/ochsner_bob/recording_store.py).
- [src/ochsner_bob/replay.py](../../../src/ochsner_bob/replay.py).
- [src/ochsner_bob/interaction_service.py](../../../src/ochsner_bob/interaction_service.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
