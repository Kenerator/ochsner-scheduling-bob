# Select, correct and clear a public provider filter

Purpose: select, correct and clear a public provider filter. Role: patient/reviewer; automated checks use isolated synthetic state.
Scope: US1 / FR-005. Mode: model-first launch available; documented deterministic controls and tests use explicit offline mode.
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

1. Specialty: Primary care; location: Downtown.
2. Public deterministic commands: `provider 2`, `provider 99`, `clear provider`.

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

## Step 3 — Find returned providers

<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["public-filters-composite","public-request-and-provider-composite"],"control_ids":["specialty","location","find-providers","choose-provider"]} -->

In card 1 choose Primary care and Downtown, then Find providers. Review returned provider names and select Choose provider 2 only if that row is actually returned. Expected: the active provider filter changes; no identity or booking is created. If the list differs, select a currently returned row rather than copying a stale number.

![Source-bound actual offline/historical control locator for select-and-clear-provider; public-filters-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

![Source-bound actual offline/historical control locator for select-and-clear-provider; public-request-and-provider-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-composite.svg)

## Step 4 — Correct and clear only that filter

<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-request-and-provider-composite"],"control_ids":["public-request","send-request"]} -->

For deterministic no-call interpretation, enter `provider 2` in Public scheduling request and Send scheduling request. An out-of-range `provider 99` is rejected without substituting a provider. Enter `clear provider` and send again. Expected: provider_id is removed while Primary care/Downtown remain. The public command is not a patient name and does not enter private identity. In model-first mode these recognized commands still route locally. Recovery: reread active filters after each response; do not send rapid old-revision commands.

![Source-bound actual offline/historical control locator for select-and-clear-provider; public-request-and-provider-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-composite.svg)

## Completion and cleanup

Effect: Public preference/read changes only; no booking or handoff.

Cleanup: stop only your own launch with Ctrl-C when finished. Leave Operator trials,
canonical accounting, locks and effect namespaces untouched. Reset local workflow
is not erasure of an unresolved write and recording cleanup is not effect recovery.

## Known gaps and evidence

Parent partial UI execution, 2026-10-14 at explicit offline source `612d4bf`:
the current two-provider list was read, Choose provider2 set prov_2002, clear
provider removed only that filter and provider99 was rejected. The public
text-provider2 branch and subsequent availability were not run. Later date
commands hit intermittent local connection failure; no whole-journey pass inferred.

Recovery: inspect the latest response/outcome before another action; obtain fresh
returned options/proposal after invalidation. Never retry an unknown write or
interpret a stale screen as confirmation authority. The exact select/correct/clear sequence is covered by the no-model supplied-HTTP conversation test. W2's actual offline discovery plate is a locator, not proof that every command in this document was run in IAB.

Exact automated path from the repository root:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_provider_selection_correction_and_clear_preserve_other_filters -v
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
- [Exact automated source](../../../tests/test_conversation.py)
- [Native completion ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
