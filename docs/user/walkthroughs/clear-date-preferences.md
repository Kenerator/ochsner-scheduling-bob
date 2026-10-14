# Clear date filters while retaining specialty and location

Purpose: Remove a date range without resetting other public preferences. Role: patient reviewer.
Scope: US1 / FR-005 / tests/test_conversation.py. Mode: normal model-first launch with an explicit offline
control path; the documented local controls need no model call.
Limits: synthetic fixtures only; no production authentication, real staff contact
or clinical care. Clearing public dates differs from blank private identity fields, which preserve their local draft.

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

1. Public Specialty: Primary care (`primary_care`); Location: Downtown (`downtown`).
2. Public From date: `2099-01-01`; Through date: `2099-01-31`.
3. Exact public local command: `clear dates`; no private fields needed.

Identity values belong only in private controls. Keep names, phone, DOB and ZIP
out of Public scheduling request; its examples below contain public intent only.

## Step 2 — Start a dedicated patient session
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite"],"control_ids":["start-independent-patient"]} -->

Select **Start independent patient** (`start-independent-patient`) in the toolbar of your own trial tab. Expected: a patient role and current revision, with no identity or proposal. Recovery: if creation or connection fails, resolve the launcher/connection message before entering data. Starting another session does not reconcile an earlier unknown write; do not use it to retry that write.

![Actual control locator: Empty join field and Start independent patient; no pairing grant shown.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 3 — Find current public providers
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["specialty","location","from-date","through-date","find-providers"]} -->

Choose (1) **Primary care** in Specialty (`specialty`) and (2) **Downtown** in Location (`location`); leave From date and Through date blank. Select **Find providers** (`find-providers`). Expected: the two returned public providers and matching Active filters, without private lookup or booking. Recovery: if no providers or an API error appears, review filters or use Help; do not fabricate a provider.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 4 — Apply a bounded public date range
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["from-date","through-date","apply-preferences"]} -->

Set From date (`from-date`) to `2099-01-01` and Through date (`through-date`) to `2099-01-31`, then select **Apply preferences** (`apply-preferences`). Expected: both dates plus Primary care/Downtown in Active filters; no current proposal. Recovery: resolve date validation or stale state before clearing so the initial state is known.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 5 — Clear both dates through the supported public command
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["public-request-and-provider-composite"],"control_ids":["public-request","send-request"]} -->

Enter `clear dates` in **Public scheduling request** (`public-request`) and select **Send scheduling request** (`send-request`). Expected: date filters disappear, date boxes become blank on synchronization, and Primary care/Downtown remain. This explicit local command works offline without a model. Recovery: if fields remain unsent/dirty, review Active filters; clear both native date controls and Apply preferences as the direct-control alternative, not Reset.

![Actual control locator: Public scheduling request, Send scheduling request and numbered Choose provider buttons.](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 6 — Verify the retained public filters
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["specialty","location","from-date","through-date","apply-preferences"]} -->

Review Specialty (`specialty`), Location (`location`), From date (`from-date`) and Through date (`through-date`); if using the direct-control alternative, blank both dates and select **Apply preferences** (`apply-preferences`). Expected: Primary care/Downtown remain, dates unset, and no proposal or booking. Recovery: correct only unintended filters; request fresh availability after identity verification if continuing.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Completion and cleanup

Effect: Public filter changes only after discovery; no booking, handoff or private read. Clearing dates invalidates any old proposal rather than authorizing it. No real staff or care is provided. An unknown write may have
succeeded: do not retry it, even after reset, reconnect or a new session.

Cleanup: stop only your own launch with Ctrl-C in its terminal. Do not stop another
listener, purge recordings, erase Operator state or reset accounting/effect history.
Leave any existing receipt/history and uncertainty protection intact.

## Known gaps and evidence

Recovery: Use clear dates or blank both date controls and Apply. Do not Reset the entire workflow just to remove dates, and do not apply public-field clearing semantics to private identity drafts.

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_conversation.ConversationTests.test_date_correction_validates_merged_range_before_http
```

These are existing test contracts, not a report of a run by this document worker.

Source basis: widget/service/core and test sources consulted at checker candidate
`66da0c8`; W2 actual offline atlas captures bind `bdc4585`. Later changes here
are documentation only and do not extend runtime evidence. The exact Conversation method asserts clear dates leaves only specialty/location and does not add HTTP reads. The widget alternative maps blank public dates to null preferences; W2 filters are locators, not a newly executed clear-date journey.

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
- [Exact tests/test_conversation.py](../../../tests/test_conversation.py)
- [Exact src/ochsner_bob/conversation.py](../../../src/ochsner_bob/conversation.py)
