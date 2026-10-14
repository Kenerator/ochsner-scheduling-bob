# Preserve unknown-write protection across reconstruction

Purpose: preserve unknown-write protection across reconstruction. Role: patient/reviewer; automated checks use isolated synthetic state.
Scope: US1 / FR-010a. Mode: model-first launch available; documented deterministic controls and tests use explicit offline mode.
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

1. Automated opaque synthetic effect key: `opaque-synthetic-action-a`.
2. No identity values, old proposal token or confirmation authority are restored.

## Step 2 — Read diagnostics without starting recording

<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["recording-and-diagnostics-composite"],"control_ids":["developer-disclosure","inspect-diagnostics"]} -->

Open Developer Mode and Inspect sanitized diagnostics without selecting Start synthetic recording. Read the recording-OFF status and any categorical effect outcome. This orientation does not create an unknown write or authorize restarting an Operator session.

![Source-bound actual offline/historical control locator for unknown-after-restart; recording-and-diagnostics-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

## Step 3 — Run isolated durable reconstruction checks

<!-- walkthrough-step: {"number":3,"interactive":false,"visual_ids":[],"control_ids":[]} -->

Run the exact journal test below, and `PYTHONPATH=src:tests .venv/bin/python -m unittest test_browser_service.BrowserServiceTests.test_restart_recovers_effect_namespace_but_not_identity_or_consent -v`. The journal test creates an in-flight claim in a temporary directory, reopens it as unknown and verifies a second claim is blocked without erasing bytes. Browser reconstruction keeps the effect namespace but restores neither identity nor a proposal. Do not delete, replace or move the live ledger/lock/namespace to make this pass.

## Completion and cleanup

Effect: The automated test preserves a protected unresolved claim; no second booking, real model request or browser restart.

Cleanup: stop only your own launch with Ctrl-C when finished. Leave Operator trials,
canonical accounting, locks and effect namespaces untouched. Reset local workflow
is not erasure of an unresolved write and recording cleanup is not effect recovery.

## Known gaps and evidence

Recovery: inspect the latest response/outcome before another action; obtain fresh
returned options/proposal after invalidation. Never retry an unknown write or
interpret a stale screen as confirmation authority. This is an isolated file/service reconstruction contract, not a newly executed production/browser restart. A preserved unknown cannot be downgraded to failed because its receipt is absent.

Exact automated path from the repository root:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_effect_journal.EffectJournalTests.test_reopened_attempt_is_unknown_without_erasing_the_claim -v
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
- [Exact automated source](../../../tests/test_effect_journal.py)
- [Additional reconstruction source](../../../tests/test_browser_service.py)
- [Native completion ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
