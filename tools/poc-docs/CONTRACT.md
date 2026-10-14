# Walkthrough structural contract, version 1

The reusable Python 3.11+ standard-library checker does not import BOB, start an
application, run Git/hooks, retrieve credentials, write files or access a network.
Native tasks own implementation progress. A structural pass is not workflow,
acceptance, pixel/privacy, accessibility or production certification.

## Interface

```sh
python tools/poc-docs/check_walkthroughs.py --root . --catalog docs/user/walkthroughs/catalog.json
```

`check_catalog(root: Path, catalog: dict) -> list[str]` returns at most 256 safe
errors. `check_placement(source: dict, placement: dict) -> list[str]` validates
integer source-pixel rectangles. `main(argv=None) -> int` returns 0 only for
structural success, 2 for invalid/unavailable input. Diagnostic text never includes
raw failed JSON/argv/content values. Valid bounded catalog IDs identify rows.

The catalog has exactly `schema_version: 1`, nonempty `flows`, and `controls`.
Flow keys: `id`, `source_ids`, `document`, `status`, `mode`, `steps`, `gap_refs`,
`evidence_refs`. Steps have `number`, `anchor`, `interactive` and optional
`visual_ids`/`control_ids`. Numbers begin 0, 1 and are consecutive; documents are
unique per flow; executable flows contain at least one interactive step, rather
than only an empty setup/launch template. Each interactive section embeds its declared visual with alt
text. Source IDs resolve to native US/FR IDs, supplied scenario ID projections or
contained regular public source files. Local references/Markdown anchors resolve.
Partial/unsupported/unverified rows need a real gap reference, never `passed: true`.

Control keys: `id`, `label`, `role`, `group`, `document`, `visual_ids`.
Roles: patient/support/both/developer. Groups: session-and-public,
private-and-booking, help-and-outcomes, support, developer-recording,
replay-navigation, replay-variants-and-data. BOB's seven-group content is separate
from these reusable validation bytes. Empty mappings are pending, not completion.

Statuses: implemented/partial/unsupported/unverified. Modes:
model/offline/recorded-simulation/not-executable. These describe availability and
document scope, not copied task completion or accepted workflow execution.

## Visual manifest

`assets/ui/walkthroughs/manifest.json` has exactly `schema_version: 1`, `visuals`.
Each visual has all and only these keys:

```json
{
  "id": "example",
  "kind": "screenshot",
  "path": "assets/ui/walkthroughs/example/clean.jpg",
  "sha256": "64 lowercase hexadecimal characters",
  "source_revision": "40 lowercase hexadecimal characters",
  "working_tree_state": "clean",
  "scenario": "example-flow",
  "action": "What the user actually did",
  "result": "What was actually visible",
  "role": "patient",
  "viewport": {"width": 1280, "height": 720},
  "width": 1280,
  "height": 720,
  "source_visual_id": null,
  "placements": [],
  "limitations": []
}
```

The illustrative hash/revision strings above are not a valid manifest. Kinds are
screenshot/schematic/annotation/composite. Clean screenshots are PNG or JPEG;
schematics are explicitly labeled SVG drawings. Hashes match actual bytes and
declared dimensions match bounded PNG/JPEG headers or SVG dimensions. Header
validation does not decode every pixel or establish that a raster was captured
from the UI. Manual provenance/privacy inspection remains required.

Annotation/composite rows name exactly a clean screenshot source, match its
dimensions, viewport, revision, working-tree state, scenario and role, and declare
nonempty `placements` of exactly `{x, y, width, height}`. Coordinates are
nonnegative integers, dimensions positive integers, rectangles fully inside the
source. No source cycles or drawing masquerading as captured UI. Number-to-control
mapping and crop bounds belong in action/result/limitations and the atlas text;
rectangles do not by themselves certify target correspondence. Keep clean originals
and SVG layers separate. A composite SVG may embed only its declared local clean
source, never an external/data URL, other asset or annotation chain. Active SVG
content/external references are rejected. No image is transformed by the checker.

Local Git HEAD/loose/packed metadata is read best-effort without launching Git.
Different source revisions require an explicit `historical` limitation; unknown or
dirty source state needs limitations. This is declared source identity, not a fresh
execution claim or runtime-byte equivalence check. Exact source/action/result/crop
review remains separate. Existing approved historical captures may be reused only
with truthful lineage/limitations, never relabeled newly executed.

## Bounds and public paths

JSON/Markdown input is at most 1 MiB per file; visual bytes at most 16 MiB.
Catalog rows/visuals at most 512, steps/placements at most 128. IDs are bounded
lowercase technical slugs. Duplicate JSON fields, nonfinite values, unsupported
fields/types and unavailable files fail safely. Root-relative paths and resolved
Markdown references must stay contained regular files, without symlink ancestors.
Known private roots (.git, .bob-local, .env*, .venv, .superpowers, tmp, intake,
original RFP source) cannot be referenced as public content. This is not a generic
secret scanner; the existing whole-index guard and manual image review still apply.
External ordinary links are not fetched or certified; remote images are rejected.

## Verification

Run `python -m unittest discover -s tests -p test_walkthrough_contract.py -v`.
Fixtures are temporary, synthetic and no-call; real collection checks may fail
until its actual documents/assets exist. SM owns the exact Template export and
generic generation guidance. Consumers must pin the reviewed checker/test contract
without BOB-specific scenarios, private RFP data or a private DevOps dependency.
