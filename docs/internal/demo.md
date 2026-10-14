# BOB demonstration orientation

Updated 2026-10-14. Use one [individual walkthrough](../user/walkthroughs/index.md)
beside BOB; each supplies install/launch, synthetic inputs, actual controls,
expected result, recovery, visuals and cleanup. This page is an orientation,
not an omnibus script or second completion ledger.

## Suggested review route

1. [Provider lookup](../user/walkthroughs/provider-lookup.md) before identity, then
   [happy booking](../user/walkthroughs/happy-path-booking.md): selection is not consent.
2. [Identity no-match](../user/walkthroughs/no-patient-match.md) versus
   [ambiguity/ZIP](../user/walkthroughs/multiple-patient-matches.md), and
   [empty availability](../user/walkthroughs/no-availability.md) versus
   [read failure](../user/walkthroughs/api-failure.md).
3. [Help](../user/walkthroughs/request-help.md), [medical boundary](../user/walkthroughs/unsupported-request.md)
   and [separate mock queue](../user/walkthroughs/submit-mock-handoff.md).
4. [Read-only support join](../user/walkthroughs/pair-support.md), separately
   [control lease](../user/walkthroughs/support-take-and-return-control.md) and
   [patient adoption](../user/walkthroughs/patient-adopts-support-suggestion.md).
5. [Recording-OFF diagnostics](../user/walkthroughs/recording-off-diagnostics.md),
   then approved [synthetic capture](../user/walkthroughs/capture-and-seal.md) and
   [recorded-only Replay](../user/walkthroughs/replay-navigation-and-bookmarks.md).

Use the [annotated atlas](../user/controls/index.md) for numbered control locators.
The exact eight supplied scenarios and all additional native journeys retain their
own guides; no distinct failure is hidden in the happy path.

## What the evidence does and does not show

Latest checker checkpoint `612d4bf`: 558 combined synthetic tests, 52 portable
structural fixtures plus two BOB-only visual/inventory consumer tests; three BOB
booking demos and retained starter demos pass. Test contracts do not constitute
new browser/model qualification. New W2 captures are offline at `bdc4585`;
historical Support/spelling source provenance remains visible in the
[manifest](../../assets/ui/walkthroughs/manifest.json).

The current Support demo joined with control inactive, private identity excluded
and confirmation disabled. Acknowledgement/kernel/reconnect warnings mean reliable
screen synchronization is not established. W2 observed a mock booking/lookup/
queued handoff and bounded capture/replay navigation; desired preference-variant
success was not observed after reconnect/index reset. Export/import/purge locations
do not prove those operations were freshly executed. Fault/clock/concurrency
branches explicitly use their exact automated source, not invented UI controls.

From the repository root:

```sh
.venv/bin/python scripts/demo_booking.py --flow all
```

Demos own synthetic mock processes/temp journals and make no paid model calls:
success completes once; conflict rejects then fresh selection succeeds; labeled
lost-receipt unknown remains blocked. Never retry an unknown write, erase the
canonical journal/accounting, or start a new namespace to get another attempt.

## Cleanup and optional team exercise

Stop only your own launch with Ctrl-C. Workflow reset is not cancellation or
uncertainty erasure. A team may review a presentation-label/public typo change
against [as-built boundaries](as-built/architecture.md), then use meaningful
tests-first and affected behavior verification under a separately selected change;
this orientation does not authorize weakening identity/consent/effect guards.

## Video boundary and history

The approved project-local exception has no duration bound; short is preferred,
Operator supplies intro/wrap, minimal effects and screenshots/animated stills.
Continuous recording, a second video and external publication remain unapproved.
Existing media work remains on hold; these docs do not reactivate it. Retain
[dated video/still evidence](video-notes.md) without relabeling old frames current.

## References

- [Setup and model-first launch](../../README.md#normal-model-first-launcher)
- [Individual walkthrough collection](../user/walkthroughs/index.md)
- [Persona/story/test crosswalk](persona-story-test-index.md)
- [Native completion and open work](../../specs/001-ochsner-scheduling-assistant/tasks.md)
