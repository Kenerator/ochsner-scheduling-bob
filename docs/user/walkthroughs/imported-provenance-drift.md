# Review provenance drift in imported recording data

Purpose: Treat differing source/dependency/policy/prompt/schema/fixture provenance as comparison rather than identical replay. Role: developer or failure/recovery reviewer.

Scope: US4 / FR-015 / tests/test_replay_contract.py. Mode: recorded-simulation; exact drift fixture is automated-only. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

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

1. Exact test drift: expected prompt digest is 64 `b` characters, differing from the recording's prompt hash.
2. Provenance fields: source_revision, dependencies, policy, prompt, schema, fixtures.
3. Import payload must be an existing reviewed approved synthetic JSON export; do not fabricate a hash or recording.
4. Private synthetic phone: `555-0101` in **Synthetic phone** only.
5. Private DOB: `1985-04-12` in **Date of birth** only.
6. Private ZIP: `70112` in **ZIP discriminator** only. These values are optional orientation for flows that do not identify a patient.

Keep names, phone, DOB and ZIP out of the public request box. Only application-owned private identity controls receive those fixture values. Use only your own disposable local session and recording references.

## Step 2 — Start a patient and inspect the safe local controls
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite","recording-and-diagnostics-composite"],"control_ids":["start-independent-patient","developer-disclosure","inspect-diagnostics"]} -->

Select **Start independent patient** (`start-independent-patient`), expand **Developer Mode** (`developer-disclosure`) below the flow and select **Inspect sanitized diagnostics** (`inspect-diagnostics`). Expected: a current session, declared interpretation mode and bounded sanitized state. This is interactive orientation only, not reproduction of a model or recording fault. Recovery: reconnect may clear output; inspect again and retain the real mode/missing information rather than manufacturing failure.

![Source-bound actual offline control composite; toolbar composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 3 — Review provenance on an approved import
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["recording-data-actions-composite"],"control_ids":["recording-json","import-recording"]} -->

If you already have an approved synthetic export from a different recorded provenance, review it, place it in **Reviewed recording JSON / import** (`recording-json`) and select **Import bounded synthetic recording** (`import-recording`). Expected: host validation, comparison mode for drift and explicit compatibility.drift; an accepted digest does not authenticate its author. If no suitable payload exists, skip import and use the automated step. Recovery: expired, invalid or unapproved fixture data must not be forced through. This current control plate shows locations, not executed import/drift.

![Source-bound actual offline control composite; recording data actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-data-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Check exact prompt drift in automation
<!-- walkthrough-step: {"number":4,"interactive":false,"visual_ids":["variant-edit-and-review-composite"],"control_ids":[]} -->

Automated-only: import the prepared synthetic recording with a differing expected prompt hash, assert mode=comparison and compatibility.drift=[prompt], and inspect its historical completed outcome. Expected: a completed recorded observation stays historical; it is not an identical-replay claim or a live receipt. Recovery: retain provenance mismatch and review comparisons; do not overwrite provenance merely to remove the warning. No UI control changes the host's expected provenance.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_provenance_drift_is_comparison_not_claimed_identical_replay -v
```

![Source-bound actual offline control composite; variant edit and review composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/variant-edit-and-review-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Orientation and the cited disposable fault fixtures do not authorize real scheduling, staff contact or care. There is no live write retry. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: A reviewed drifted payload is an optional prerequisite, not provided by the atlas. Exact drift reproduction is automated-only. Even later docs-only source revisions can change reported source provenance; neither a matching digest nor historical success proves authenticity, current parity or live authority. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_replay_contract.ReplayContractTests.test_provenance_drift_is_comparison_not_claimed_identical_replay -v
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
