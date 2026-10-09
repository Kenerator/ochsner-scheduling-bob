# Tooling and export map

Navigation, not a task ledger. Application as-built docs are populated near the
end of implementation, not as a prerequisite to coding.

| Inspect/change | Entry point | Behavior tests |
| --- | --- | --- |
| Manifest/CLI | `launch_spec.py`, `__main__.py` | `test_launch_spec.py`, `test_bootstrap_cli.py` |
| Offline scaffold/input/persona pins | `bootstrap.py:preview_bootstrap`, `create_scaffold` | bootstrap, user-story and traceability tests |
| Native stages/recovery | `bootstrap_workflow.py`, `speckit_adapter.py` | `test_bootstrap_workflow.py` |
| Executable/version binding | `runtime_selection.py` | runtime-selection and workflow tests |
| Operation diagnostics | `doctor.py:inspect_project` | `test_doctor.py` |
| Source-bound coverage | `qualification.py:qualify_project` | `test_qualification.py` |
| Staged credential guard | `secret_scan.py` | `test_secret_scan.py` |

Modules live under `src/poc_template/`; tests under `tests/`.

## Before simplifying an export

Inventory first; no automatic stripping. Keep application source/tests, native
specs/tasks, setup and relevant product/user/internal docs. Template CLI/persona
tooling and optional profiles are development tools, not necessarily application
runtime dependencies. `.specify` and assistant integrations serve native stages.
Environments, workflow runs and local intake may contain private/generated state;
inspect ignore rules and authority before delivery. `maintainer/` is deliberately
excluded from bootstrap exports; never copy private preparation by default.

See [operations](operations.md), [traceability](persona-story-test-index.md) and
[optional CI](../../reference/bootstrap/ci-python.yml). That example is inert and
supplies no successful-CI or branch-protection claim.
