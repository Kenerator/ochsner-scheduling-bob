# BOB and inherited tooling map

Navigation, not a task ledger. Application as-built docs are populated near the
end of implementation, not as a prerequisite to coding.

## BOB product and verification

| Task | Entry point / local evidence |
| --- | --- |
| Browser / CLI launch | [serve_browser.py](../../scripts/serve_browser.py), [Marimo app](../../apps/scheduling_app.py), [CLI](../../src/ochsner_bob/__main__.py); [launch tests](../../tests/test_browser_launch.py) |
| Scheduling, lookup and recovery | [SchedulingSession](../../src/ochsner_bob/session.py); [transition tests](../../tests/test_transition_acceptance.py) |
| Actual supplied service | [HTTP tests](../../tests/test_supplied_http.py), [booking demos](../../scripts/demo_booking.py) |
| Committed export / offline CI | [BOB profile](qualification.json), [workflow](../../.github/workflows/bob-offline.yml), retained `qualification.qualify_project` |
| Browser / model evidence | [video notes](video-notes.md), [model qualification](live-qualification.md), not JS-only test results |
| Credential hygiene | [security](security.md), retained `secret_scan.scan` |

## Inherited bootstrap and maintainer tooling

| Retained module under `src/poc_template/` | Purpose |
| --- | --- |
| `launch_spec.py`, `__main__.py` | Manifest and tool CLI |
| `bootstrap.py` | Separate-project scaffolding/input/persona pins |
| `bootstrap_workflow.py`, `speckit_adapter.py` | Native-stage orchestration/recovery |
| `runtime_selection.py` | Executable/version binding |
| `doctor.py` | Read-only operation diagnostics |
| `qualification.py` | Source-export/profile execution, used by BOB |
| `secret_scan.py` | Whole-index credential guard, used by BOB |

These useful modules remain inherited tooling, not BOB scheduling authority.
Their full Template-maintainer test suites are **not exported here**. The local
BOB `tests/` include product contracts and retained starter tests; upstream test
filenames must not be presented as local coverage.

## Before simplifying an export

Inventory first; no automatic stripping. Keep application source/tests, native
specs/tasks, setup and relevant product/user/internal docs. Template CLI/persona
tooling and optional profiles are development tools, not necessarily application
runtime dependencies. `.specify` and assistant integrations serve native stages.
Environments, workflow runs and local intake may contain private/generated state;
inspect ignore rules and authority before delivery. `maintainer/` is deliberately
excluded from bootstrap exports; never copy private preparation by default.

See [operations](operations.md), [traceability](persona-story-test-index.md) and
[inherited CI example](../../reference/bootstrap/ci-python.yml). That example is
inert; BOB's actual workflow/profile are linked above. Neither adds a successful-CI
or branch-protection claim without actual run evidence and explicit selection.
