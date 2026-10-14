# Prevent stale selection after a failed availability refresh

Purpose: Invalidate earlier returned slots and their proposal when a new read fails. Role: patient reviewer.
Scope: US1 / FR-005 / tests/test_transition_acceptance.py. Mode: normal model-first launch with an explicit offline
control path; proposal setup is interactive; the failed-refresh injection is automated-only.
Limits: synthetic fixtures only; no production authentication, real staff contact
or clinical care. No current UI outage switch exists; a second ordinary availability click does not guarantee a failure.

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

1. Private Synthetic phone: `555-0101`.
2. Private Date of birth: `1985-04-12`.
3. Private ZIP discriminator: `70112`.
4. Public Specialty: Primary care (`primary_care`); Location: Downtown (`downtown`); dates blank.
5. Automated refresh scenario: `api_failure`, after a valid proposal; expected HTTP `503`.

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

## Step 4 — Check the private synthetic identity
<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["private-entry-composite"],"control_ids":["private-disclosure","synthetic-phone","date-of-birth","zip-discriminator","check-identity"]} -->

Expand **2 · Private synthetic identity** (`private-disclosure`). Enter (1) **Synthetic phone** `555-0101` (`synthetic-phone`), (2) **Date of birth** `1985-04-12` (`date-of-birth`), and (3) **ZIP discriminator** `70112` (`zip-discriminator`). Select **Check or correct identity** (`check-identity`). Expected: Identity: verified and cleared browser input boxes; fixture matching is not production authentication. Blank boxes on later submissions preserve the service’s local draft, not new consent. Recovery: if missing or ambiguous, correct only the private controls and check again; do not request private results until verified.

![Actual control locator: Private disclosure, Synthetic phone, Date of birth, ZIP discriminator and Check or correct identity.](../../../assets/ui/walkthroughs/control-atlas/private-entry-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 5 — Select a returned option and review its proposal
<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["returned-options-and-confirm-composite"],"control_ids":["get-availability","select-option"]} -->

Select **Get current availability** (`get-availability`), then **Select option 1** (`select-option`) only if that currently returned row is the desired appointment. Review card 4's exact API time, provider and location. Expected: a proposal and separate **Confirm appointment** control, with no booking yet. The atlas time is historical; use the returned time, which is materialized from the mock's current-date fixtures. Recovery: if empty, stale, or failed, request fresh options after correcting the cause; never choose from an old figure.

![Actual control locator: Get current availability, Look up my appointments, numbered Select option, separate Confirm and Decline.](../../../assets/ui/walkthroughs/control-atlas/returned-options-and-confirm-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Locator only: the pictured state is not proof that this step was newly executed.

## Step 6 — Check that a failed refresh revokes stale slots
<!-- walkthrough-step: {"number":6,"interactive":false,"visual_ids":["returned-options-and-confirm-composite"],"control_ids":[]} -->

Automated-only: no current widget control or normal-launch scenario selector produces this fault. Run this exact isolated contract from the repository root:

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_transition_acceptance.TransitionAcceptanceTests.test_failed_availability_refresh_cannot_reselect_stale_slots
```

These are existing test contracts, not a report of a run by this document worker.

Expected: the test prepares a valid proposal, swaps its adapter to api_failure, and refreshes availability. State outage, slots empty and proposal absent; selecting old option 1 cannot create a proposal and old confirmation adds no history. Recovery: once the read cause resolves, fetch current options and freshly select/review. Do not retry an unknown write or use the old screenshot as a slot list.

![Actual control orientation only: Get current availability, Look up my appointments, numbered Select option, separate Confirm and Decline.](../../../assets/ui/walkthroughs/control-atlas/returned-options-and-confirm-composite.svg)

Actual offline screenshot with a separate numbered annotation, source `bdc4585`. Orientation only: this figure does not capture the fault or prove the test outcome.

## Completion and cleanup

Effect: UI orientation stops at an unconfirmed proposal; the isolated test makes reads and blocks stale booking. No mock appointment is written. No real staff or care is provided. An unknown write may have
succeeded: do not retry it, even after reset, reconnect or a new session.

Cleanup: stop only your own launch with Ctrl-C in its terminal. Do not stop another
listener, purge recordings, erase Operator state or reset accounting/effect history.
Leave any existing receipt/history and uncertainty protection intact.

## Known gaps and evidence

Recovery: A refresh failure must clear both options and proposal. The user can refresh a read after recovery, but cannot retain an earlier choice as current authority.

From the repository root, the exact automated contract command is:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest -v test_transition_acceptance.TransitionAcceptanceTests.test_failed_availability_refresh_cannot_reselect_stale_slots
```

These are existing test contracts, not a report of a run by this document worker.

Source basis: widget/service/core and test sources consulted at checker candidate
`66da0c8`; W2 actual offline atlas captures bind `bdc4585`. Later changes here
are documentation only and do not extend runtime evidence. The exact real-HTTP test asserts all three state fields and no history after stale selection/confirm. W2 shows a successful proposal for orientation only; it is not a captured failed refresh or browser reproduction.

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
- [Exact src/ochsner_bob/http_mock.py](../../../src/ochsner_bob/http_mock.py)
