# Keep a lost handoff receipt unknown and block automatic retry

Purpose: keep a lost handoff receipt unknown and block automatic retry. Role: patient/reviewer; automated checks use isolated synthetic state.
Scope: US3 / FR-010. Mode: model-first launch available; documented deterministic controls and tests use explicit offline mode.
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

1. Controlled CLI test command: `handoff user_requested`.
2. Unknown means delivery cannot be established; it is neither queued nor failed.

## Step 2 — Read the handoff outcome boundary

<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help"]} -->

Select Help without submitting another mock handoff. Read Outcomes separately from generic recovery text. A previously unknown handoff must not be retried by Help or Reset. The atlas figure's queued example is control orientation only, not the unknown case.

![Source-bound actual offline/historical control locator for unknown-handoff-outcome; help-actions-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

## Step 3 — Run the lost-receipt reentry contract

<!-- walkthrough-step: {"number":3,"interactive":false,"visual_ids":[],"control_ids":[]} -->

Run the exact CLI test below. Its explicit LostReceiptPort records one handoff write then raises UnknownOutcome; a second CLI entry using the same disposable journal runs Help/Reset/handoff and must retain unknown with exactly one write. No supplied eight-scenario mode or UI toggle emits this boundary fault. Never substitute the canonical journal or a fresh namespace to get another attempt.

## Completion and cleanup

Effect: One controlled synthetic attempted handoff remains unknown; reentry/help/reset do not dispatch another.

Cleanup: stop only your own launch with Ctrl-C when finished. Leave Operator trials,
canonical accounting, locks and effect namespaces untouched. Reset local workflow
is not erasure of an unresolved write and recording cleanup is not effect recovery.

## Known gaps and evidence

Recovery: inspect the latest response/outcome before another action; obtain fresh
returned options/proposal after invalidation. Never retry an unknown write or
interpret a stale screen as confirmation authority. This journey is grounded in the explicit CLI unit boundary, not a newly observed IAB lost receipt. The existing diagnostics classification test covers booking outcomes and is not by itself handoff-reentry evidence.

Exact automated path from the repository root:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_cli_restart.CliRestartTests.test_unknown_handoff_reentry_keeps_help_without_second_write -v
```

The runtime source is unchanged from the W2 capture candidate `bdc4585`; checker/
document checkpoints `66da0c8` and `46ddcff` do not add product behavior. Parent's
558-test suite is synthetic service/contract evidence, not proof of this complete
browser journey. Images retain source/hash/mode/unknown-tree/historical limitations
in the [visual manifest](../../../assets/ui/walkthroughs/manifest.json). The visible
2026-10-13 offline booking used returned API time, not a fixed date from a screenshot.
Current support acknowledgement/kernel/reconnect warnings are not hidden.

## Revision history

- 2026-10-14: Drafted from current controls and exact test source; whole-collection
  navigation, independent review and protected integration remain in native tasks.

## References

- [Collection](index.md)
- [Control atlas](../controls/index.md)
- [Native requirements](../../../specs/001-ochsner-scheduling-assistant/spec.md)
- [Exact automated source](../../../tests/test_cli_restart.py)
- [Native completion ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
