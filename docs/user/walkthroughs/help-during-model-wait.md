# Keep Help responsive while language interpretation waits

Purpose: keep help responsive while language interpretation waits. Role: patient/reviewer; automated checks use isolated synthetic state.
Scope: US3 / FR-011. Mode: model-first launch available; documented deterministic controls and tests use explicit offline mode.
Limits: fixture matching is not production authentication; mock effects are not care or live staff contact.

## Step 0 — Install and set up

From the repository root, verify an explicit Python 3.11+ interpreter and install:

```sh
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip check
.venv/bin/python tools/poc-runtime/launch.py --doctor
```

If python3.11 is unavailable, use another explicitly verified compatible executable
for both version check and venv creation. Use synthetic fixtures only. Doctor starts
nothing and reads no key. Follow [getting started](../getting-started.md) for the
trusted dedicated-note helper and current runtime/qualification policy; never paste
or save an API key in this document or the app.

## Step 1 — Launch

The normal model-first entrypoint is:

```sh
.venv/bin/python tools/poc-runtime/launch.py
```

Use its printed local app URL. For this document's deterministic no-call control/
test path, explicitly choose the offline alternative instead:

```sh
.venv/bin/python tools/poc-runtime/launch.py --offline --ui-port 29580 --transport-port 29581
```

Use those ports only when free; a conflict is not permission to stop another
process. Ctrl-C stops only this launch's owned children. Test commands below create
their own disposable state and do not require a real model/key or the running UI.

## Arrange the workspace

Put this rendered Markdown on the left and BOB on the right. In Chrome use the
tab menu's New split view/Add tab controls, then Swap sides if needed. If Split
View is unavailable, use side-by-side windows, without extensions or experimental
flags. See [official Chrome guidance](https://support.google.com/chrome/answer/16971124?hl=en).

## Synthetic sample data

1. Public synthetic request in controlled fixture: `Find primary care providers`.
2. Recovery action: Help; no identity is needed and no real slow-model request is required.

## Step 2 — Start an independent patient

<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite"],"control_ids":["start-independent-patient"]} -->

In BOB's toolbar select Start independent patient once and wait for the current
patient view. Expected: Patient role with an initial revision and enabled
scheduling controls; no verified identity, current proposal, booking or handoff.
This creates local synthetic workflow state, not a transaction or Support join.
Recovery: if the page stays uninitialized or reports a connection error, stop
before the next step and check your own launch. Do not reuse another patient's
capability, copy a pairing grant, or restart an Operator session.

![Source-bound actual toolbar locator; selecting Start independent patient is a prerequisite, not newly executed whole-journey evidence.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

## Step 3 — Locate Help and diagnostics

<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite","recording-and-diagnostics-composite"],"control_ids":["help","developer-disclosure","inspect-diagnostics"]} -->

Use Help, and optionally open Developer Mode/Inspect sanitized diagnostics to locate the pending/status fields. Do not create a paid request just to induce a delay. Help has no booking/handoff effect.

![Source-bound actual offline/historical control locator for help-during-model-wait; help-actions-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

![Source-bound actual offline/historical control locator for help-during-model-wait; recording-and-diagnostics-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

## Step 4 — Run the event-controlled wait test

<!-- walkthrough-step: {"number":4,"interactive":false,"visual_ids":[],"control_ids":[]} -->

Run the exact test below. A bounded synthetic language transport waits on an Event while Help, another independent patient's read, paired polling and diagnostics are checked. Each probe must finish within that test's 400ms bound; release occurs in finally. The late language result is stale, preferences stay unchanged and no API writes occur. If capture was enabled by the test, its stale result is explicitly incomplete—not upgraded to full replay.

## Completion and cleanup

Effect: Help remains effect-free; a late stale interpretation cannot overwrite the newer workflow or authorize an effect.

Cleanup: stop only your own launch with Ctrl-C when finished. Leave Operator trials,
canonical accounting, locks and effect namespaces untouched. Reset local workflow
is not erasure of an unresolved write and recording cleanup is not effect recovery.

## Known gaps and evidence

Recovery: inspect the latest response/outcome before another action; obtain fresh
returned options/proposal after invalidation. Never retry an unknown write or
interpret a stale screen as confirmation authority. The 400ms assertion is a controlled service-test bound, not a browser latency SLA or fresh real-provider benchmark. Current IAB reconnect/kernel issues remain separate observed gaps.

Exact automated path from the repository root:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_interaction_service.InteractionServiceTests.test_blocked_model_does_not_block_help_other_patient_or_paired_polling -v
```

The runtime source is unchanged from the W2 capture candidate `bdc4585`; checker/
document checkpoints `66da0c8` and `46ddcff` do not add product behavior. Parent's
558-test suite is synthetic service/contract evidence, not proof of this complete
browser journey. Images retain source/hash/mode/unknown-tree/historical limitations
in the [visual manifest](../../../assets/ui/walkthroughs/manifest.json). The visible
2026-10-13 offline booking used returned API time, not a fixed date from a screenshot.
Current support acknowledgement/kernel/reconnect warnings are not hidden.

## Revision history

- 2026-10-14: Corrected the independent-session prerequisite after source-bound
  review; new interactive metadata/toolbar locator do not claim a new browser run.

- 2026-10-14: Drafted from current controls and exact test source; whole-collection
  navigation, independent review and protected integration remain in native tasks.

## References

- [Collection](index.md)
- [Control atlas](../controls/index.md)
- [Native requirements](../../../specs/001-ochsner-scheduling-assistant/spec.md)
- [Exact automated source](../../../tests/test_interaction_service.py)
- [Native completion ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
