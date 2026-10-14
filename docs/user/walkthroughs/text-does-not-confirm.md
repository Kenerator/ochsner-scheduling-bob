# Keep textual agreement separate from exact appointment confirmation

Purpose: keep textual agreement separate from exact appointment confirmation. Role: patient/reviewer; automated checks use isolated synthetic state.
Scope: US1 / FR-008. Mode: model-first launch available; documented deterministic controls and tests use explicit offline mode.
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

1. Private controls only: phone `555-0101`, DOB `1985-04-12`, ZIP `70112`.
2. Public consent-like samples: `yes`, `confirm`, `/confirm please`, `yes but uptown instead`. Do not confuse CLI `/confirm` with public text.
3. Public filters: Specialty `Primary care`, Location `Downtown`; commit them with Apply preferences.

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

## Step 3 — Verify synthetic identity

<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["private-entry-composite"],"control_ids":["private-disclosure","synthetic-phone","date-of-birth","zip-discriminator","check-identity"]} -->

Expand private card 2, enter phone 555-0101, date of birth 1985-04-12 and ZIP 70112 in its private controls, then select Check or correct identity. Expected: verified synthetic identity and cleared private inputs, not authentication or a booking. If missing or ambiguous, correct the private fixture values before continuing; keep them out of Public scheduling request.

![Source-bound actual offline/historical control locator for text-does-not-confirm; private-entry-composite, not a newly executed journey capture.](../../../assets/ui/walkthroughs/control-atlas/private-entry-composite.svg)

## Step 4 — Apply public preferences

<!-- walkthrough-step: {"number":4,"interactive":true,"visual_ids":["public-filters-composite"],"control_ids":["specialty","location","apply-preferences"]} -->

In card 1 choose Specialty Primary care and Location Downtown, then select Apply preferences. Wait for the response and read Active filters: specialty primary_care and location downtown must be committed before the next step. Choosing dropdown values alone is not applying them. This changes public preferences only; it neither fetches slots nor books. Recovery: if Active filters are absent/different or the response is unavailable, stop and reapply the intended values before requesting availability.

![Source-bound actual offline/historical control locator for text-does-not-confirm; public-filters-composite, not a newly executed journey capture.](../../../assets/ui/walkthroughs/control-atlas/public-filters-composite.svg)

## Step 5 — Prepare but do not confirm an exact proposal

<!-- walkthrough-step: {"number":5,"interactive":true,"visual_ids":["returned-options-and-confirm-composite"],"control_ids":["get-availability","select-option"]} -->

Get current availability, then Select option for one actual returned slot. Review its exact provider/location/API time in card 4. Selection alone has no write effect. Do not confirm yet; the next step tests public agreement text. Stop if no current proposal is shown. If availability is empty or unavailable, stop and follow the response; do not invent an option.

![Source-bound actual offline/historical control locator for text-does-not-confirm; returned-options-and-confirm-composite, not a newly executed journey capture.](../../../assets/ui/walkthroughs/control-atlas/returned-options-and-confirm-composite.svg)

## Step 6 — Send agreement as public text

<!-- walkthrough-step: {"number":6,"interactive":true,"visual_ids":["public-request-and-provider-composite","returned-options-and-confirm-composite"],"control_ids":["public-request","send-request","confirm-appointment"]} -->

In explicit offline mode send `yes` through Public scheduling request. Expected: no booking, no inferred consent; the old proposal is revoked. A stale stored confirmation snapshot cannot be reused. Repeat other sample strings only after preparing a fresh proposal when running the automated test, not as a batch of browser clicks. To book later, obtain a fresh current proposal and use the separate Confirm appointment button for exactly that proposal.

![Source-bound actual offline/historical control locator for text-does-not-confirm; public-request-and-provider-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/public-request-and-provider-composite.svg)

![Source-bound actual offline/historical control locator for text-does-not-confirm; returned-options-and-confirm-composite, not a newly executed failure capture.](../../../assets/ui/walkthroughs/control-atlas/returned-options-and-confirm-composite.svg)

## Completion and cleanup

Effect: No booking from textual agreement. A future separate patient Confirm would be a new explicit mock effect.

Cleanup: stop only your own launch with Ctrl-C when finished. Leave Operator trials,
canonical accounting, locks and effect namespaces untouched. Reset local workflow
is not erasure of an unresolved write and recording cleanup is not effect recovery.

## Known gaps and evidence

Recovery: inspect the latest response/outcome before another action; obtain fresh
returned options/proposal after invalidation. Never retry an unknown write or
interpret a stale screen as confirmation authority. The exact consent-like strings are proven by a synthetic conversation contract, not a fresh whole-journey browser run. Public `/confirm` text is deliberately not the dedicated CLI confirmation control.

Exact automated path from the repository root:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_yes_and_textual_confirm_revoke_without_consent -v
```

The runtime source is unchanged from the W2 capture candidate `bdc4585`; checker/
document checkpoints `66da0c8` and `46ddcff` do not add product behavior. Parent's
558-test suite is synthetic service/contract evidence, not proof of this complete
browser journey. Images retain source/hash/mode/unknown-tree/historical limitations
in the [visual manifest](../../../assets/ui/walkthroughs/manifest.json). The visible
2026-10-13 offline booking used returned API time, not a fixed date from a screenshot.
Current support acknowledgement/kernel/reconnect warnings are not hidden.

## Revision history

- 2026-10-14: Separated identity, applied filters and proposal review; the ordered
  prerequisite test exercises the real session without a model or booking write.

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
