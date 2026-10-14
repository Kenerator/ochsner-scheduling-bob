# Handle unavailable model interpretation without fallback

Purpose: Distinguish disabled, unavailable and timeout model outcomes and preserve proposal revocation. Role: developer or failure/recovery reviewer.

Scope: US6 / FR-001 / tests/test_language.py. Mode: offline orientation plus automated-only fault contract; normal model-first launch remains distinct. Limits: synthetic local PoC only; no production authentication, live representative or clinical service. The full journey remains unverified on this documentation candidate.

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

1. Exact adapter test public text: `Find providers`.
2. Conversation test public text: `Find a family doctor`.
3. Faults are injected by fake transport in tests: TimeoutError maps to timeout; OSError/RuntimeError map to unavailable. No credential sample is needed.
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

## Step 3 — Read the live failure path without inducing an outage
<!-- walkthrough-step: {"number":3,"interactive":true,"visual_ids":["help-actions-composite"],"control_ids":["help"]} -->

If the real model-first runtime independently reports unavailable/timeout, read its sanitized message and use **Help** (`help`) for a local supported next step. If no outage is present, selecting Help only demonstrates safe help and must not be reported as model-failure reproduction. Expected: no implicit fixture/offline answer presented as model success; an earlier proposal is not reusable. Recovery: resolve the actual configuration/connection through the trusted setup guide; use offline only by explicit separate launch choice. Do not remove credentials, stop a service or induce a paid request to create this fault.

![Source-bound actual offline control composite; help actions composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/help-actions-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Step 4 — Reproduce no-fallback and transport failure in automation
<!-- walkthrough-step: {"number":4,"interactive":false,"visual_ids":["recording-and-diagnostics-composite"],"control_ids":[]} -->

Automated-only: disabled LanguageAdapter configuration revokes the conversation's previous proposal and the old confirmation produces no history. A separate failure callback gives unavailable without echoing private exception text. The bounded adapter test injects timeout/unavailable exceptions, asserts one transport call and no retry. Expected: categorical noncompletion with no fallback. Recovery: use local structured controls/help after review, with fresh proposal/confirmation for any later booking. The actual plate locates diagnostics; it is not a captured model outage.

Executable test contract (not run for this document):

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_timeouts_and_transport_errors_are_sanitized_without_retry -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_disabled_real_language_has_no_fallback_and_revokes_proposal -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_language_failure_never_echoes_exception_or_reuses_confirmation -v
```

![Source-bound actual offline control composite; recording and diagnostics composite; orientation only, not execution of this step.](../../../assets/ui/walkthroughs/control-atlas/recording-and-diagnostics-composite.svg)

The figure is an existing atlas locator with separate numbered annotations over actual pixels; the action and expected result above are its text equivalent. It is not a newly executed result or a captured failure.

## Completion and cleanup

Effect: Orientation and the cited disposable fault fixtures do not authorize real scheduling, staff contact or care. There is no live write retry. Replay and comparison confer no live consent or authority. If any earlier live write has unknown outcome, do not retry it; reconcile separately.

Cleanup: Close only your own demonstration tabs. If replay is playing, select Pause before leaving. Stop only your own launch with Ctrl-C; never stop an existing Operator process, purge an Operator recording, or erase capability, accounting or effect state.

## Known gaps and evidence

Recovery: No current UI model-outage injection exists. Exact missing helper/key at normal startup is a launch failure, not a running-model timeout, and explicit offline mode is not silent fallback or outage evidence. Fault reproduction is automated-only; no genuine new model qualification was performed. If reconnect clears diagnostics or resets the replay index, inspect current state, reopen your owned reference if available and re-enter a valid bounded index. A queued action or click is not proof that the intended transition happened.

Source basis: application/atlas source `bdc4585` and parent checker checkpoint `66da0c8`, with later docs-only changes. Support originals retain `c3e6df2` / `e2dfa7e` where used: their unchanged control constructors are applicable, but the older membership label is not evidence of repaired status. Current IAB joined/inactive and acknowledgement-unavailable observations are not fresh successful synchronization.

The W2 atlas supplies historical/offline actual control observations only; this document adds no browser execution evidence. Test methods below describe existing automated contracts, not newly run tests:

```sh
PYTHONPATH=src:tests .venv/bin/python -m unittest test_language.LanguageTests.test_timeouts_and_transport_errors_are_sanitized_without_retry -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_disabled_real_language_has_no_fallback_and_revokes_proposal -v
PYTHONPATH=src:tests .venv/bin/python -m unittest test_conversation.ConversationTests.test_language_failure_never_echoes_exception_or_reuses_confirmation -v
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
