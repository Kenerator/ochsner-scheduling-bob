# Correct an inverted date range without applying it

Purpose: Keep the prior valid public range when a correction would invert its endpoints. Role: patient reviewer.
Scope: US1 / FR-005 / tests/test_conversation.py. Mode: normal model-first launch with an explicit offline
control path; the documented local controls need no model call.
Limits: synthetic fixtures only; no production authentication, real staff contact
or clinical care. Dates are public filters; native date-picker formatting may differ, so verify the ISO value/Active filters rather than a screenshot's display format.

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
2. Initial From date: `2099-01-01`; Through date: `2099-01-31`.
3. Invalid replacement From date: `2099-02-01`, while Through date remains `2099-01-31`.
4. Recovery Through date: `2099-02-28`, then From date: `2099-02-01`; no identity needed.

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

## Step 4 — Apply the initial valid range
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["from-date","through-date","apply-preferences"]} -->

Set From date (`from-date`) to `2099-01-01` and Through date (`through-date`) to `2099-01-31`; select **Apply preferences** (`apply-preferences`). Expected: Active filters contains both dates; no availability request or booking is needed. Recovery: if the browser rejects entry, use its native calendar control to select the exact same dates and inspect Active filters.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 5 — Reject the inverted correction
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["from-date","through-date","apply-preferences"]} -->

Set From date (`from-date`) to `2099-02-01`, retain Through date `2099-01-31`, and select **Apply preferences** (`apply-preferences`). Expected: start-must-be-on-or-before-end notice; previous valid range remains active and no availability request occurs. The widget may restore visible fields to that retained range. Recovery: correct the end first so each applied range is valid.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 6 — Extend the end before moving the start
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["through-date","from-date","apply-preferences"]} -->

Set Through date (`through-date`) to `2099-02-28` and select **Apply preferences** (`apply-preferences`); then set From date (`from-date`) to `2099-02-01` and select Apply again. Expected: a valid February range with Primary care/Downtown retained, no proposal or booking. Recovery: if either apply is rejected/stale, inspect the retained Active filters before continuing.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Completion and cleanup

Effect: Public filter validation/updates only after one discovery read; no private read, availability request or booking/handoff write. No real staff or care is provided. An unknown write may have
succeeded: do not retry it, even after reset, reconnect or a new session.

Cleanup: stop only your own launch with Ctrl-C in its terminal. Do not stop another
listener, purge recordings, erase Operator state or reset accounting/effect history.
Leave any existing receipt/history and uncertainty protection intact.

## Known gaps and evidence

Parent partial UI attempt, 2026-10-14 at offline source `612d4bf`: a first date
edit hit connection unavailable; read-only reload recovered revision7/identity/
filters, then dates2099-01-01..2099-01-31 applied at revision8. The subsequent
start2099-02-01 edit again hit connection unavailable while both owned listeners
remained alive. Atomic UI rejection/correction is therefore not qualified here;
use the exact automated contract below. No effect was retried or model invoked.

Recovery: Repair an inverted range atomically without querying availability. The far-future dates are validation fixtures, not a claim that future appointments exist.

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_conversation.ConversationTests.test_date_correction_validates_merged_range_before_http test_session_contract.SessionContractTests.test_invalid_merged_dates_do_not_call_availability
```

These are existing test contracts, not a report of a run by this document worker.

Source basis: widget/service/core and test sources consulted at checker candidate
`66da0c8`; W2 actual offline atlas captures bind `bdc4585`. Later changes here
are documentation only and do not extend runtime evidence. The exact Conversation test uses local public dates/start/end commands with these 2099 values and proves no further HTTP. The native date controls submit the same validated preferences; this particular browser date-picker sequence remains unexecuted.

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
- [Exact tests/test_session_contract.py](../../../tests/test_session_contract.py)
- [Exact src/ochsner_bob/conversation.py](../../../src/ochsner_bob/conversation.py)
