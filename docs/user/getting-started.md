# Scheduling with BOB

Internal-use synthetic demonstration with public source, not a real healthcare service. BOB is AI, not
a clinician or live representative. Follow [setup](../../README.md) with an
explicit Python 3.11+ environment. Offline use needs no model account. Choose an [individual walkthrough](walkthroughs/index.md)
for complete install/launch/sample/action/recovery instructions for one scenario.

## Launch mode and setup

The [normal launcher](../../README.md#normal-model-first-launcher) requests model
mode with the configured BOB snapshot; its exact Ochsner Secure Note `notes` field
is resolved privately through the existing trusted helper. `--offline` is explicit
and no-call. `--help`/`--doctor` retrieve no credentials or model output; readiness
is not qualification. No inherited-key fallback is used. See the README for
first-use accounting versus preservation of existing private ledger/unknown usage.

Custom free `--ui-port`/`--transport-port` pairs configure the public widget URL;
no source edit is needed. Keep the matching exact UI Origin. Invalid/missing
configuration, occupied ports or unavailable accounting/storage stop visibly; do
not stop another listener or reset accounting. Ctrl-C cleans only owned children.
L4 candidate review/CLI ownership status is in [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md#l4-model-first-consumer--2026-10-12).

## Find the controls

The [annotated control atlas](controls/index.md) groups 57 real control families
into seven purposes, with actual source-bound screenshots, numbered locators,
disabled/effect boundaries and text equivalents. New figures are explicit offline
captures; dated Support/spelling figures retain their original source limitations.

Header/status → session toolbar → cards 1–4, with Outcomes/Help/Support alongside
on desktop and Developer Mode below. Private identity and Developer disclosures
start collapsed. Open full-size figures when labels are small; the atlas does not
certify mobile or assistive-technology behavior. Earlier
[widget schematic](../../assets/ui/guide/widget-map.svg) remains an explicitly
schematic overview, not an executed screenshot.

## Find and confirm an appointment

Follow [happy-path booking](walkthroughs/happy-path-booking.md) or
[public provider lookup](walkthroughs/provider-lookup.md). Discovery needs no identity.
Private fixture values belong in card 2, not chat. Select a currently returned
option, review its exact API time/location/provider, then Confirm separately.
Selection or textual agreement is not consent.

## Refine or correct the search

Use [change preferences](walkthroughs/change-preferences.md),
[provider correction/clear](walkthroughs/select-and-clear-provider.md),
[date correction](walkthroughs/correct-invalid-date-range.md), or
[private identity correction](walkthroughs/correct-private-identity.md).
Corrections revoke old proposals/private results. [Decline/reselect](walkthroughs/decline-and-reselect.md)
does not cancel a prior booking; a new attempt needs fresh returned options and
separate exact confirmation.

## Look up existing appointments

Follow [appointment lookup](walkthroughs/lookup-appointments.md) or
[empty lookup](walkthroughs/empty-appointment-lookup.md). Appointments are returned
private records, not Outcomes attempt history. Empty successful reads differ from
[404](walkthroughs/appointment-not-found.md),
[outage](walkthroughs/appointment-outage.md) and malformed responses.

## Recover or request assistance

Use [Help](walkthroughs/request-help.md), [medical boundary](walkthroughs/medical-boundary.md)
or [unsupported intent](walkthroughs/unsupported-intent.md). A
[mock handoff](walkthroughs/submit-mock-handoff.md) is a separate deliberate write;
a queue receipt is not live staff contact. [Conflict](walkthroughs/slot-conflict.md)
permits fresh selection after definite rejection; [unknown write](walkthroughs/unknown-booking-outcome.md)
does not permit retry. [Reset/reconnect](walkthroughs/reset-and-reconnect.md)
retains unresolved-effect protection. See [recovery and irreversible purge](recovery.md).

## Support view

Follow [pair support](walkthroughs/pair-support.md), then separately
[take/return control](walkthroughs/support-take-and-return-control.md) and
[patient adoption](walkthroughs/patient-adopts-support-suggestion.md).
One-use joining is not takeover, freshness or consent. Support has no private
identity/availability/lookup/booking/confirmation authority. A suggestion changes
nothing until the patient reviews and accepts it after return. Current local
read-only join was observed, but acknowledgement/kernel/reconnect warnings mean
reliable synchronized screens remain unverified.

## Developer view and replay

Begin with [recording-OFF diagnostics](walkthroughs/recording-off-diagnostics.md).
Owned OFF references provide current sanitized inspection, not an exact historical
recording. Explicit approved synthetic capture is separate:
[capture/seal](walkthroughs/capture-and-seal.md) →
[navigate/bookmark](walkthroughs/replay-navigation-and-bookmarks.md) →
[typed variant/compare](walkthroughs/replay-typed-variant-comparison.md) →
[review a regression proposal](walkthroughs/review-regression-proposal.md).
[Export/import](walkthroughs/export-and-import-recording.md) is bounded private data,
not source authenticity; [purge](walkthroughs/purge-disposable-recording.md) requires
its applicable final-action approval and never removes effect protection.
Complete matching capture may establish semantic core parity, not full renderer
parity or live consent. Reference ownership/TTL and missing evidence remain explicit.

## Application runtime accounting

Updated 2026-10-14 for reviewed runtime `79aeafd`, integrated as `d3c3a04`. The
integration's historical safe activation handoff is
in [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md#indefinite-runtime-policy--2026-10-13).
The Operator authorized Ochsner-key usage involved in **running BOB** without
application call, dollar or time-window limits until further notice. No special
budget flag is needed. The human clarification includes functional qualification,
testing, validation and app-like evaluation. Excluded is LLM work that creates or
changes app/spec/test code; unrelated research/media permissions do not expand.

Normal browser/CLI and functional qualification constructors select runtime accounting. Exact model/key
selection, bounded input/output/context/HTTP timeouts, no tools/retries, privacy,
identity, confirmation and effect guards remain. Every dispatch requires a durable
reservation; known usage settles once and unknown usage retains its full liability.
No account-wide billing/invoice reconciliation is claimed.

Readiness/doctor validates existing private JSON or SQLite and its initialized
lock/marker without writes, migration, reservations or model requests. It is
accounting/storage readiness, not a spend gate or a promise that later I/O works.
The first actual new-runtime construction atomically migrates validated JSON to
private transactional SQLite at the **same** `.bob-local/model-budget.json` path.
All history, reservation IDs/configuration and late settlement are retained, with
no arbitrary cumulative-record limit. Storage exhaustion, malformed state, unsafe
permissions or unexpected SQLite companions fail safely; nothing silently resets.

**Activation:** first verify all old model writers are quiescent, then start the
reviewed/integrated runtime using the existing canonical path and effects namespace.
Old processes cannot share this format migration and old code cannot read the new
format. Do not restore an old build against migrated accounting or reset/change
the ledger to make it work. A later Operator-requested support demo restored the identified canonical runtime
with its existing SQLite/accounting/effects namespace preserved. That availability/
read-only pairing observation is not a new paid model qualification or permission
to restart another trial.

For deliberate genuine qualification only, `scripts/qualify_live.py --run-live`
requires explicit `BOB_ENABLE_OPENAI=1`, a supported priced model, the same existing
canonical ledger and exact Ochsner Secure Note `notes` helper. It ignores an inherited
generic key and rejects an alternate `--budget` path. Help/offline/unit tests never
retrieve a key. Run only useful missing checks, not duplicate paid proof; see the
[source-bound qualification method](../internal/live-qualification.md#qualification-method).

## Fixed Oct 12 model-budget window

Updated 2026-10-12: reviewed head `8908ef9` integrated through protected PR #8
as `c7c53a3`; the local backend was restored with explicit opt-in. Exact CI,
expiry and unchanged-accounting evidence are in [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md#fixed-day-bob-budget-candidate--2026-10-12).
This does not activate other already-running services or prove a model request.

Historical: the Oct 12 opt-in applied only through `2026-10-13T05:00:00Z` exclusive.
It is superseded for application runtime by the policy below; the old flag is no
longer accepted by application launchers. Historical counts/CI remain unchanged.

## References

- [All 67 individual journeys](walkthroughs/index.md)
- [Seven-group actual annotated atlas](controls/index.md)
- [Native evidence and open work](../../specs/001-ochsner-scheduling-assistant/tasks.md)
