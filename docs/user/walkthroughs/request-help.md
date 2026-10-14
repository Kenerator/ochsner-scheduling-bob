# Ask for scheduling help without making a write

Purpose: Reach assistance from the patient workflow without identity or email prerequisites. Role: patient reviewer.
Scope: US3 / FR-011. Mode: normal model-first launch with an explicit offline
control path; the documented local controls need no model call.
Limits: synthetic fixtures only; no production authentication, real staff contact
or clinical care. Help prepares a path; it does not submit a queue entry, connect an employee or provide basic-phone delivery.

## Step 0 — Install and set up

From the repository root in your dedicated local checkout:

```sh
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip check
.venv/bin/python tools/poc-runtime/launch.py --doctor
```

Verify Python 3.11+ before creating the environment. If `python3.11` is absent,
use `python3.12 --version` and `python3.12 -m venv .venv` after verifying that
explicit executable is compatible; the remaining commands stay the same.
The doctor reads no key, starts no service and makes no model request. Use
[getting started](../getting-started.md) for the trusted exact-note helper and
current application runtime policy; do not paste a key into BOB or these notes.
Resolve a failed install, dependency check or doctor before proceeding.

## Step 1 — Launch

Normal model-first launch:

```sh
.venv/bin/python tools/poc-runtime/launch.py
```

Open the printed local URL. Startup/readiness is not model qualification.
For an explicit no-call walkthrough alternative, use the following ONLY IF both
ports are free:

```sh
.venv/bin/python tools/poc-runtime/launch.py --offline --ui-port 29580 --transport-port 29581
```

A port conflict is not permission to stop another process. Do not reuse an
existing process for this trial; arrange another free pair or defer launch.
Ctrl-C in your launch terminal stops only this launch's owned children. All
supplied W2 capture evidence is offline or explicitly historical, with no new
genuine model qualification.

## Arrange the workspace

Keep this rendered Markdown on the left and BOB on the right. In Chrome, open
the tab context menu and choose **New split view**, then **Add tab** for the
other page; use **Swap sides** if needed. Follow the
[official Chrome Split View instructions](https://support.google.com/chrome/answer/16971124?hl=en).
If unavailable, arrange two windows side by side; no extension or experimental
flags are required. Open figures full size if labels are small; each action
below also has a text equivalent.

## Synthetic sample data

1. Control: Help; no private identity or email is required.
2. Optional public-only equivalent: `help`; use the button in this walkthrough.

Identity values belong only in private controls. Keep names, phone, DOB and ZIP
out of Public scheduling request; its examples below contain public intent only.

## Step 2 — Start a dedicated patient session
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite"],"control_ids":["start-independent-patient"]} -->

Select **Start independent patient** (`start-independent-patient`) in the toolbar of your own trial tab. Expected: a patient role and current revision, with no identity or proposal. Recovery: if creation or connection fails, resolve the launcher/connection message before entering data. Starting another session does not reconcile an earlier unknown write; do not use it to retry that write.

![Actual control locator: Empty join field and Start independent patient; no pairing grant shown.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 3 — Request plain scheduling assistance
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help"]} -->

Select **Help** (`help`). Expected: BOB offers a mock handoff, says no email is required, and discloses no real staff contact or basic-phone access. No new queued result appears just from Help. Recovery: if disconnected, restore the local connection and inspect Current attempt before any separate write.

![Actual control locator: Help, Medical boundary, Unsupported request, Submit mock handoff and Reset local workflow.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Completion and cleanup

Effect: Local assistance only; no booking or handoff POST. Any earlier receipt/unknown protection remains. No real staff or care is provided. An unknown write may have
succeeded: do not retry it, even after reset, reconnect or a new session.

Cleanup: stop only your own launch with Ctrl-C in its terminal. Do not stop another
listener, purge recordings, erase Operator state or reset accounting/effect history.
Leave any existing receipt/history and uncertainty protection intact.

## Known gaps and evidence

Recovery: Submit mock handoff is separate and deliberate. Help remains reachable during waits; do not treat a historical queued receipt in the atlas as a new submission.

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_transition_acceptance.TransitionAcceptanceTests.test_all_reachable_state_safety_and_public_interruptions_are_effect_free test_interaction_service.InteractionServiceTests.test_blocked_model_does_not_block_help_other_patient_or_paired_polling test_widget_projection.WidgetProjectionTests.test_local_help_is_not_swallowed_during_pending_text
```

These are existing test contracts, not a report of a run by this document worker.

Source basis: widget/service/core and test sources consulted at checker candidate
`66da0c8`; W2 actual offline atlas captures bind `bdc4585`. Later changes here
are documentation only and do not extend runtime evidence. State-transition, blocked-language-service and shipped-widget harness tests check reachable help without unauthorized writes. W2 Help figures show controls with an already queued handoff; that pictured effect was not caused by the reader's Help action.

The atlas supplies actual app observations for its labeled state only. Its
acknowledgement/kernel/reconnect warnings remain gaps; synchronized screens are
not established by a visible role. This entire journey remains unverified on this
document revision. This worker did not launch BOB, run a browser, invoke a model,
capture new visuals, run the listed tests or repeat the parent’s combined suite.
Structural coverage is not browser certification. Parent final QA/integration is pending.

## Revision history

- 2026-10-14: Drafted from exact native, test, widget/service and source-bound atlas
  sources; parent final QA/integration pending.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md)
- [Native plan](../../../specs/001-ochsner-scheduling-assistant/plan.md)
- [Native progress and existing evidence](../../../specs/001-ochsner-scheduling-assistant/tasks.md)
- [Public discovery atlas](../controls/session-and-public.md)
- [Private identity and booking atlas](../controls/private-and-booking.md)
- [Help and outcomes atlas](../controls/help-and-outcomes.md)
- [Visual provenance manifest](../../../assets/ui/walkthroughs/manifest.json)
- [Widget controls](../../../src/ochsner_bob/widget.js)
- [Scheduling authority](../../../src/ochsner_bob/session.py)
- [Browser service](../../../src/ochsner_bob/browser_service.py)
- [Exact tests/test_transition_acceptance.py](../../../tests/test_transition_acceptance.py)
- [Exact tests/test_interaction_service.py](../../../tests/test_interaction_service.py)
- [Exact tests/test_widget_projection.py](../../../tests/test_widget_projection.py)
