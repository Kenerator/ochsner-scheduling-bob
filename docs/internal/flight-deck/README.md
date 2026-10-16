# BOB project-local Flight Deck

Updated 2026-10-14. The Flight Deck is an on-demand, offline derived review view,
not application state, a second task ledger, a permission source or production
acceptance. Native [specification](../../../specs/001-ochsner-scheduling-assistant/spec.md)
and [tasks](../../../specs/001-ochsner-scheduling-assistant/tasks.md) remain canonical.

Mapping delta prepared 2026-10-16 on base `14474ac`: FR-001/014/020/027/027a
now include relevant T108–T114 follow-on tasks. Pending review/live/result tasks
must remain incomplete in the derived implementation view; offline test narratives
still cannot manufacture verification or acceptance. Shared runtime bytes and six
elements are unchanged. Exact candidate generation/status belongs in native tasks.

## Generate and inspect

From the repository root, use the installed Ruby/Git tools. No gem/npm install,
private DevOps/SDK checkout, app service or model account is needed. The local Mac
consumer qualification uses Ruby 2.6.10; current source/CI limits are in native tasks.

```sh
ruby --version
git --version
ruby --disable-gems tools/aeos-dashboard/poc-self-check
ruby --disable-gems tools/aeos-dashboard/poc-flight-deck doctor
ruby --disable-gems tools/aeos-dashboard/poc-flight-deck generate
ruby --disable-gems tools/aeos-dashboard/poc-flight-deck latest
```

Doctor checks contained public inputs, exact runtime resources and ignored output.
Generate prints the local `index.html` path; open that file, or explicitly use
`ruby --disable-gems tools/aeos-dashboard/poc-flight-deck open`. Generation does
not open a browser unless requested. It never starts BOB, retrieves a credential,
calls a model, dispatches work, reconciles SDK state or updates SDK latest pointers.

Each unique snapshot contains exactly six files in
`tmp/aeos-dashboards/ochsner-scheduling-bob/poc-.../`:

- `index.html` — standalone executive view, capability matrix and native drilldown.
- `level-1-executive-flight-deck.md` — concise six-element posture.
- `level-2-executive-matrix-board.md` — deeper requirement/capability view.
- `manager.md` — gaps, attention and next action.
- `engineering.md` — source hashes, provenance and evidence limits.
- `snapshot.yaml` — structured source-bound data and artifact integrity hashes.

`latest` is the last recognized generated snapshot, not an automatic live refresh.
Regenerate after relevant source changes; preserve earlier snapshots and their
original source/time. Do not edit generated files to improve a posture or manually
rewrite the latest pointer. Artifact edit detection is not a signature/authenticity
guarantee. Cleanup refuses unknown/modified output; do not run it automatically or
use it to remove source, accounting, claims or recordings.

## Interpret the six elements

[project.yaml](project.yaml) maps 30 native FR IDs and 12 capabilities into exactly
six elements: functional coverage, UX, safety/authority, verification,
documentation/training, repository/readiness. FR-025/025a explicitly retain
historical/superseded fixed-day scope as DEFERRED, not an active spending gate.
The other 28 are active; duplicate inclusion across elements does not duplicate
the overall unique-requirement denominator.

| Lifecycle | Actual input | What it does not establish |
|---|---|---|
| Implementation | Native task checkmarks for mapped IDs | Verification, human acceptance or permission |
| Verification | Applicable structured qualification with source/scope/artifact hashes and freshness | A pass from a narrative test count or old unrelated candidate |
| Recorded acceptance | Applicable structured human-decision reference and evidence | Independently authenticated consent or authority to advance a release gate |

Existing test/CI/model/UI narratives are linked with their original source/limits,
not converted into fabricated result records. Thus a passing local suite can coexist
with dashboard verification UNKNOWN: they are different data contracts. Missing,
unparsed, stale, contradictory and dirty evidence cannot manufacture green.
Completion estimates remain unavailable when their supported denominator/evidence
is unknown. No additional paid proof or human approval cycle is required merely to
make this dashboard look complete.

The current gap mapping retains support acknowledgement, intermittent local
connection and whole-journey execution limits. These are not repaired by this
documentation tool. Production identity/PHI/live staff and broad model reliability
remain separately deferred. The dashboard creates no new console, integration or
Operator decision request.

## Source and verification boundary

The exact managed [manifest](../../../tools/aeos-dashboard/export-manifest.json)
and [provenance notice](../../../tools/aeos-dashboard/POC-EXPORT-NOTICE.md) identify
shared source and byte closure. Only the project mapping and consumer tests are
BOB-owned; shared corrections return through their owner, never a local fork.
The [consumer tests](../../../tests/test_flight_deck_mapping.py) exercise the real
Ruby input/generator with disposable public fixtures: native IDs, six elements,
private-path rejection, immutable bundle bytes and unknown verification/acceptance.
Generated files are Git-ignored and remain local, not a deployment/publication.

## Revision history

- 2026-10-14: First six-element native mapping and local generation/desktop/narrow
  review. Exact integrated source, API-compatibility review and CI remain in native
  tasks; draft/working snapshots are not relabeled committed qualification.

## References

- [Individual walkthroughs](../../user/walkthroughs/index.md)
- [Annotated control atlas](../../user/controls/index.md)
- [As-built architecture](../as-built/architecture.md)
- [Persona/story/test crosswalk](../persona-story-test-index.md)
- [Short next steps](../../product/next-steps.md)
