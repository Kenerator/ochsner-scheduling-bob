# Reject malformed model output safely

Purpose: Keep invalid model shapes, fields and JSON from becoming preferences, identity or booking authority. Role: developer or failure/recovery reviewer.

Scope: US1 / FR-001 / tests/test_language.py. Mode: offline orientation plus automated-only fault contract; normal model-first launch remains distinct. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

## Step 0 — Install and set up

From the repository root, verify Python 3.11+ and install into the project environment:

```sh
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip check
.venv/bin/python tools/poc-runtime/launch.py --doctor
```

If `python3.11` is absent, use an explicit compatible executable, for example `/opt/homebrew/bin/python3.12`: verify its `--version` is 3.11+ and use that same executable for `-m venv .venv`. Do not assume `python3` is compatible. Follow [getting started](../getting-started.md) for the trusted exact-note helper and current application runtime policy. Doctor retrieves no key, starts no service and makes no model call.

## Step 1 — Launch

Normal model-first launch:

```sh
.venv/bin/python tools/poc-runtime/launch.py
```

Open the printed local URL. Startup/readiness does not qualify model behavior. A port conflict is an error, not permission to stop another process. Ctrl-C owns only this launch and its children.

For an explicit no-call walkthrough, use the following only if **both ports are free**:

```sh
.venv/bin/python tools/poc-runtime/launch.py --offline --ui-port 29580 --transport-port 29581
```

Do not reuse or stop an existing process on those ports. All supplied W2 capture evidence is offline or dated historical synthetic evidence; it is not genuine new model qualification.

## Arrange the workspace

Keep this rendered Markdown on the left and BOB on the right. In Chrome, open a tab's context menu and use **New split view**, then **Add tab** to select the other tab; use **Swap sides** if needed. See [official Chrome Split View guidance](https://support.google.com/chrome/answer/16971124?hl=en). If unavailable, use side-by-side windows; no extension or experimental flags are needed.

## Synthetic sample data

1. Exact public adapter text: `Find providers`.
2. Test malformed output: `{}` or `{"action":"discover"}` (missing fields). These are response fixtures, not public request instructions.
3. Test duplicate-key output: `{"action":"discover","action":"help","preferences":{}}`; do not paste it into the UI as if it controls a model response.
4. Private synthetic phone: `555-0101` in **Synthetic phone** only.
5. Private DOB: `1985-04-12` in **Date of birth** only.
6. Private ZIP: `70112` in **ZIP discriminator** only. These values are optional orientation for flows that do not identify a patient.

Keep names, phone, DOB and ZIP out of the public request box. Only application-owned private identity controls receive those fixture values. Use only your own disposable local session and recording references.

## Step 2 — Start a patient and inspect the safe local controls
<!-- walkthrough-step: {"number":2,"interactive":true,"visual_ids":["toolbar-composite","recording-and-diagnostics-composite"],"control_ids":["start-independent-patient","developer-disclosure","inspect-diagnostics"]} -->

Select **Start independent patient** (`start-independent-patient`), expand **Developer Mode** (`developer-disclosure`) below the flow and select **Inspect sanitized diagnostics** (`inspect-diagnostics`). Expected: a current session, declared interpretation mode and bounded sanitized state. This is interactive orientation only, not reproduction of a model or recording fault. Recovery: reconnect may clear output; inspect again and retain the real mode/missing information rather than manufacturing failure.

![Source-bound actual offline control composite; toolbar composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/toolbar-composite.svg)

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 3 — Inspect a genuine invalid-output notice only if it occurs
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help"]} -->

If the current app independently reports invalid_output, read the sanitized notice, review current preferences/proposal state and select **Help** (`help`) if wanted. Expected: invalid response is not applied as successful scheduling intent and cannot confirm a booking. If none occurs, Help is orientation only. Recovery: correct public intent or use the structured controls after current-state review; private identity remains in private controls. There is no model-response editor in this UI.

![Source-bound actual offline control composite; help actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Reproduce malformed response rejection in the test harness
<!-- walkthrough-step: {"number":4,"interactive":false,"visual_ids":["recording-and-diagnostics-composite"],"control_ids":[]} -->

Automated-only fake responses exercise missing fields, wrong shapes/types/date values, duplicate keys, NaN, trailing content, fenced JSON and unauthorized fields/actions. The Conversation mistyped-outcome test asserts invalid_output and empty providers. Expected: bounded invalid_output, no raw exception disclosure or authority reuse. Recovery: fail closed and request supported correction/help; do not make the malformed result acceptable by dropping schema checks or pasting serialized authority. Current diagnostics controls are orientation only, not a captured malformed response.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_wrong_shapes_types_values_and_dates_are_rejected -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_duplicate_keys_nonfinite_trailing_and_code_fenced_json_are_rejected -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_authority_and_unknown_fields_are_rejected_at_both_levels -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_mistyped_language_outcome_fails_closed_without_raw_exception -v
```

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Orientation and the cited disposable fault fixtures do not authorize real scheduling, staff contact or care. There is no live write retry. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: Malformed model response injection is automated-only. Invalid JSON in Typed variant JSON is a different client/replay-input validation case; it does not reproduce a malformed model. W2 offline captures provide no new model-output evidence. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_wrong_shapes_types_values_and_dates_are_rejected -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_duplicate_keys_nonfinite_trailing_and_code_fenced_json_are_rejected -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_authority_and_unknown_fields_are_rejected_at_both_levels -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_mistyped_language_outcome_fails_closed_without_raw_exception -v
```

Not run by this document worker: setup/install/doctor, app launch, browser actions, fault injection, model calls, destructive purge, demos or the full suite. Parent owns combined verification and final integration. Structural coverage is not browser certification; no mobile, accessibility, renderer-parity or genuine new model qualification is claimed.

## Revision history

- 2026-10-14: Drafted from exact sources and supplied atlas evidence; parent final QA/integration pending. Native tasks remain the sole progress ledger.

## References

- [Native specification](../../../specs/001-ochsner-scheduling-assistant/spec.md) · [plan](../../../specs/001-ochsner-scheduling-assistant/plan.md) · [native tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md).
- [Control atlas](../controls/developer-recording.md) · [all control groups](../controls/index.md).
- [Visual manifest and evidence limitations](../../../assets/ui/walkthroughs/manifest.json) · [historical still provenance](../../../assets/ui/stills/feature-completion-20261010/manifest.json).
- [Runtime and exact-note helper guidance](../getting-started.md) · [recovery](../recovery.md).
- [tests/test_language.py](../../../tests/test_language.py).
- [tests/test_conversation.py](../../../tests/test_conversation.py).
- [src/ochsner_bob/language.py](../../../src/ochsner_bob/language.py).
- [src/ochsner_bob/conversation.py](../../../src/ochsner_bob/conversation.py).
- [src/ochsner_bob/widget.js](../../../src/ochsner_bob/widget.js).
