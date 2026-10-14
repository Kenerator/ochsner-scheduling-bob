# Quickstart and qualification

Updated 2026-10-12. macOS ARM with explicit Python 3.11+ is the required target.
The qualified working environment used Python 3.11.13. System Python 3.9 is not
supported. Follow the exact setup and terminal commands in [README](../../README.md).

```sh
python3.11 --version
python3.11 -m venv .venv
.venv/bin/python -m pip install -e .
.venv/bin/python -m pip check
PYTHONPATH=src .venv/bin/python -m unittest discover -s tests -v
.venv/bin/python scripts/demo_booking.py --flow all
.venv/bin/python scripts/measure_local.py --samples 30
```

Node.js is needed for shipped-JavaScript boundary tests. No model account is
needed for this sequence. The fixture service and policy are local vendored
files with [hash provenance](../../vendor/reference/PROVENANCE.md), not a remote
real healthcare API. Direct dependencies are pinned; transitive resolution is
not locked. Do not install the optional bootstrap profile for normal BOB use.

Browser terminals: `scripts/serve_browser.py` owns the mock and backend at
127.0.0.1:28451; Marimo serves `apps/scheduling_app.py` at 127.0.0.1:28450.
Use the numeric URL, not an alternate hostname: backend Host/Origin checks are
intentional. The normal model-first launcher configures its selected free pair
through the validated public `BOB_TRANSPORT_URL` widget trait. Direct custom
launches must set that public variable on the viewer and matching sidecar flags.
The CLI's separately owned mock uses 4010. Never stop another project's listener
to acquire a port. Ctrl-C stops only each owned process.

Manual acceptance: follow [demo runbook](../../docs/internal/demo.md) for returned
options, separate confirmation, correction, safety/help, paired support and pure
replay. Do not substitute starter `poc-demo` output as BOB evidence. Scripted
unknown deliberately hides an accepted booking's receipt at the adapter boundary;
it is not a supplied server scenario or proof of a real network failure.

Reset clears local workflow, not uncertain effects. Restart/reconnect cannot
restore identity/consent; the same private journal/namespace retains protection.
When deliberately starting a fresh supplied mock, use an explicitly new backend
`--namespace .bob-local/run-N` or CLI `--journal .bob-local/run-N/effects.json`.
Retain prior namespaces; do not reinterpret prior unknowns. Model allowance always
uses the same root ledger, regardless of mock namespace.

The normal [model-first wrapper](../../README.md#normal-model-first-launcher)
uses the exact Ochsner Secure Note `notes` field and requires existing canonical
accounting; help/doctor/startup do not make model requests. Its explicit `--offline`
path stays key-free. Exact L4 candidate/CLI ownership status is in native tasks;
shared mechanism tests alone are not consumer or cross-platform qualification.

Direct optional genuine language requires `--openai`, the three explicit environment
settings in README and the runtime-only policy in the
[user guide](../../docs/user/getting-started.md#application-runtime-accounting).
No dated budget flag is required; functional qualification/testing/validation is
covered too, while LLM creation/change of app/spec/test code remains excluded. Never paste keys into
commands/logs/browser. No model calls on construction, view, poll, support or
replay. See [genuine qualification](../../docs/internal/live-qualification.md)
for the qualified alternative, mini failures, unknown cost and exact grant.

Source-bound clean-copy verification and final outcomes are recorded in the
[native task ledger](tasks.md), not assumed from this procedure. See
[data model](data-model.md) and [contract](contracts/interaction-contract.md).
