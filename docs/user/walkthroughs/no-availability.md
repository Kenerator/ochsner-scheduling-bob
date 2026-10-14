# Recognize a successful search with no available slots

Purpose: Handle an empty availability result without inventing an appointment. Role: patient reviewer.
Scope: no_availability / US1 / FR-005. Mode: normal model-first launch with an explicit offline
control path; the documented local controls need no model call.
Limits: synthetic fixtures only; no production authentication, real staff contact
or clinical care. An empty successful read is distinct from an outage; an optional handoff remains a separate write.

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

1. Private Synthetic phone: `555-0102`.
2. Private Date of birth: `1992-06-03`; ZIP discriminator: `70118`.
3. Public Specialty: Dermatology (`dermatology`); Location: Lakeside (`lakeside`); dates blank.

Identity values belong only in private controls. Keep names, phone, DOB and ZIP
out of Public scheduling request; its examples below contain public intent only.

## Step 2 — Start a dedicated patient session
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite"],"control_ids":["start-independent-patient"]} -->

Select **Start independent patient** (`start-independent-patient`) in the toolbar of your own trial tab. Expected: a patient role and current revision, with no identity or proposal. Recovery: if creation or connection fails, resolve the launcher/connection message before entering data. Starting another session does not reconcile an earlier unknown write; do not use it to retry that write.

![Actual control locator: Empty join field and Start independent patient; no pairing grant shown.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 3 — Check the private synthetic identity
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["private-entry-composite"],"control_ids":["private-disclosure","synthetic-phone","date-of-birth","zip-discriminator","check-identity"]} -->

Expand **2 · Private synthetic identity** (`private-disclosure`). Enter (1) **Synthetic phone** `555-0102` (`synthetic-phone`), (2) **Date of birth** `1992-06-03` (`date-of-birth`), and (3) **ZIP discriminator** `70118` (`zip-discriminator`). Select **Check or correct identity** (`check-identity`). Expected: Identity: verified and cleared browser input boxes; fixture matching is not production authentication. Blank boxes on later submissions preserve the service’s local draft, not new consent. Recovery: if missing or ambiguous, correct only the private controls and check again; do not request private results until verified.

![Actual control locator: Private disclosure, Synthetic phone, Date of birth, ZIP discriminator and Check or correct identity.](../../../assets/ui/walkthroughs/control-atlas/private-entry-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 4 — Apply the no-availability preferences
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["specialty","location","from-date","through-date","apply-preferences"]} -->

Choose **Dermatology** in Specialty (`specialty`) and **Lakeside** in Location (`location`), with blank dates; select **Apply preferences** (`apply-preferences`). Expected: Active filters reflects Dermatology/Lakeside; no proposal. Recovery: review filters before the read, and remove any unintended prior provider/date constraint.

![Actual control locator: Specialty, Location, From date, Through date, Apply preferences and Find providers.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 5 — Read and recognize the empty options result
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["returned-options-and-confirm-composite"],"control_ids":["get-availability"]} -->

Select **Get current availability** (`get-availability`). Expected: no returned options and a no-appointments-matched message; no Select option choice or current proposal authorizes booking. Recovery: change public preferences and request current availability again, or select **Help** (`help`) for assistance. Do not describe this successful empty result as a failed API.

![Actual control locator: Get current availability, Look up my appointments, numbered Select option, separate Confirm and Decline.](../../../assets/ui/walkthroughs/control-atlas/returned-options-and-confirm-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 6 — Ask for help without assuming a handoff
<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help"]} -->

Select **Help** (`help`). Expected: scheduling assistance and a separately available mock handoff path, without a booking or queued receipt. Recovery: only deliberately choose Submit mock handoff if you intend that separate mock effect; see [handoff walkthrough](submit-mock-handoff.md).

![Actual control locator: Help, Medical boundary, Unsupported request, Submit mock handoff and Reset local workflow.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Completion and cleanup

Effect: Private identity and availability reads plus local Help; no booking or handoff write in these steps. No real staff or care is provided. An unknown write may have
succeeded: do not retry it, even after reset, reconnect or a new session.

Cleanup: stop only your own launch with Ctrl-C in its terminal. Do not stop another
listener, purge recordings, erase Operator state or reset accounting/effect history.
Leave any existing receipt/history and uncertainty protection intact.

## Known gaps and evidence

Parent partial UI execution, 2026-10-14 at launch source `612d4bf` with docs-only
working edits: the documented 555-0102 fixture verified, Dermatology/Lakeside
returned no options/proposal, then Help left No current attempt. Explicit offline
owned instance; no key/model/recording/write. This verifies that subset, not a fresh
install, model path or whole-journey certification. Later unrelated date edits
encountered intermittent connection failures; retain that shared UI limitation.

Recovery: For an empty successful result, refine preferences. For an API failure, resolve the read failure before retrying. A queue receipt never guarantees appointment availability.

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_supplied_http.SuppliedHttpScenarioTests.test_no_availability
```

These are existing test contracts, not a report of a run by this document worker.

Source basis: widget/service/core and test sources consulted at checker candidate
`66da0c8`; W2 actual offline atlas captures bind `bdc4585`. Later changes here
are documentation only and do not extend runtime evidence. The supplied HTTP test verifies empty slots and no fabricated proposal, then explicitly queues a no_availability handoff. The reader steps stop at Help; W2 options/help figures locate controls and are not a new capture of this empty state.

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
- [Exact vendor/reference/data/slots.json](../../../vendor/reference/data/slots.json)
