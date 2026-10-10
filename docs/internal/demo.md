# BOB demonstration runbook

Updated 2026-10-09. Short preferred; no duration bounds. Operator supplies on-camera
introduction/wrap. Only synthetic screenshots/animated stills, minimal effects;
no continuous recording or public delivery authorized. See [video notes](video-notes.md).

Use [README setup](../../README.md) and the explicit project interpreter. First run
`.venv/bin/python scripts/demo_booking.py --flow all`: success completes once;
conflict records rejection then a newly selected option succeeds; labeled unknown
hides an accepted receipt and stays blocked after Reset. Demos own isolated mock
processes and temporary journals. They do not spend model budget.

## Patient flow · Jules / Billy-June / Ellie-Rae

1. Start an independent patient in the actual Marimo app. Choose Primary care /
   Downtown, Find providers, then provider 1. Discovery needs no identity.
2. In private controls use supplied phone `555-0101`, DOB `1985-04-12`, ZIP `70112`.
   Matching is exact; `5550101` has no match and can be corrected without reset.
3. Get availability, select a numbered returned option. Show exact API timestamp,
   location, specialty and provider. Selecting is not booking.
4. Confirm separately. Show completed result/history and disabled confirmation.
   Reload is read-only. A new correction requires new selection/confirmation.

## Help and paired continuity · Amy-Lou / Nina-Jean / Morgan-Rae

After completion, use Medical boundary or Help: no clinical advice, email demand
or new booking. Submit mock handoff only deliberately; queued is a validated mock
receipt, never live staff contact. API failure/unknown paths are automated tests
and must be labeled as such unless actually shown in the browser.

Create a one-use support pairing grant; use another tab's Join demo support. Show
last acknowledged public drafts/focus/disclosures, freshness and current backend
context separately. Private fields stay blank, no usable nonce is exposed. Take
demo control, suggest Uptown without adopting it, return control, then let the
patient explicitly accept the public suggestion. Confirm remains core-guarded.

## Developer review · Sam-Rae

Open lower Developer Mode, explicitly Start synthetic recording, perform Help
and public provider discovery, Seal, then Open the returned reference. Step / play /
pause / jump, before-after, typed fork, compare and reviewed fixture proposal are
data-only simulation: no API/model writes, identity or live consent. Export/import
is strict, host-fixture-bound, private and size/TTL-limited. Replay is **not** the
same interpreter or exact renderer as live Session; missing boundaries are reported.

## Reset, cleanup and team exercise

Use workflow Reset, not deletion of private journal/budget files. Stop the two
owned terminals with Ctrl-C. Start a new explicit namespace only with a fresh
mock, retaining old uncertain claims. [Quickstart](../../specs/001-ochsner-scheduling-assistant/quickstart.md)
explains distinct ports and optional model configuration.

Team exercise: change a public presentation label or the public typo-suggestion
cutoff. Write a regression first; run affected tests and the full suite. Do not
change identity matching, exact confirmation or effect protection as a cosmetic
exercise. Review [as-built boundaries](as-built/architecture.md) first.

Working-code browser checks and automated evidence are distinguished in the
[task ledger](../../specs/001-ochsner-scheduling-assistant/tasks.md). A staged still
does not prove a whole journey, accessibility conformance or production readiness.
