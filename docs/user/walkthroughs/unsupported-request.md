# Follow the supplied medical-advice scenario

Purpose: Exercise the medical boundary and an explicitly requested minimized mock handoff. Role: patient reviewer.
Scope: unsupported_request supplied scenario / US3 / FR-011–FR-012. Mode: normal model-first launch with an explicit offline
control path; the documented local controls need no model call.
Limits: synthetic fixtures only; no production authentication, real staff contact
or clinical care. The supplied scenario ID means medical advice; generic unsupported scheduling is a separate [flow](unsupported-intent.md).

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

1. Boundary control: Medical boundary; no medical details or identity entry needed.
2. Optional exact public command for this scenario: `handoff medical_advice`; no names, phone, DOB or ZIP.

Identity values belong only in private controls. Keep names, phone, DOB and ZIP
out of Public scheduling request; its examples below contain public intent only.

## Step 2 — Start a dedicated patient session
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite"],"control_ids":["start-independent-patient"]} -->

Select **Start independent patient** (`start-independent-patient`) in the toolbar of your own trial tab. Expected: a patient role and current revision, with no identity or proposal. Recovery: if creation or connection fails, resolve the launcher/connection message before entering data. Starting another session does not reconcile an earlier unknown write; do not use it to retry that write.

![Actual control locator: Empty join field and Start independent patient; no pairing grant shown.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 3 — Choose the medical boundary for this supplied scenario
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["medical-boundary"]} -->

Select **Medical boundary** (`medical-boundary`). Expected: BOB says it cannot give medical advice or triage and can prepare a medical-advice handoff request; no appointment or queue effect occurs. Recovery: Help remains available. This instruction demonstrates BOB's boundary, not a clinical answer or triage service.

![Actual control locator: Help, Medical boundary, Unsupported request, Submit mock handoff and Reset local workflow.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 4 — Explicitly submit the medical-advice mock reason
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-request-and-provider-composite"],"control_ids":["public-request","send-request"]} -->

To match the supplied scenario's reason exactly, enter `handoff medical_advice` in **Public scheduling request** (`public-request`) and select **Send scheduling request** (`send-request`). This supported local command works offline. Expected: a validated mock handoff: queued result, without identity or booking. The separate Submit mock handoff button always uses user_requested, so it does not reproduce this exact reason. Recovery: failed/rejected is not queued; unknown means do not repeat the write.

![Actual control locator: Public scheduling request, Send scheduling request and numbered Choose provider buttons.](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Completion and cleanup

Effect: Medical boundary itself has no external effect; the later explicit public command submits one minimized mock handoff with reason medical_advice. No booking is requested. No real staff or care is provided. An unknown write may have
succeeded: do not retry it, even after reset, reconnect or a new session.

Cleanup: stop only your own launch with Ctrl-C in its terminal. Do not stop another
listener, purge recordings, erase Operator state or reset accounting/effect history.
Leave any existing receipt/history and uncertainty protection intact.

## Known gaps and evidence

Recovery: Boundary wording is not a submission receipt. Distinguish this supplied medical scenario from generic unsupported intent and from the button's user_requested handoff reason.

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_supplied_http.SuppliedHttpScenarioTests.test_unsupported_request test_conversation.ConversationTests.test_help_and_medical_route_before_private_data_or_language
```

These are existing test contracts, not a report of a run by this document worker.

Source basis: widget/service/core and test sources consulted at checker candidate
`66da0c8`; W2 actual offline atlas captures bind `bdc4585`. Later changes here
are documentation only and do not extend runtime evidence. W2 help-actions actually shows a queued handoff and a separate historical booking, but does not prove this medical_advice reason was executed. The supplied method verifies the reason and that a medical interruption revokes an existing proposal.

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
- [Exact tests/test_supplied_http.py](../../../tests/test_supplied_http.py)
- [Exact tests/test_conversation.py](../../../tests/test_conversation.py)
- [Exact src/ochsner_bob/conversation.py](../../../src/ochsner_bob/conversation.py)
