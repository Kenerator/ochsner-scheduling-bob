# As-built code walkthrough

Updated: 2026-10-09 · Reviewed source revision: working tree, pre-commit.

The implemented slice is `src/ochsner_bob/core.py` (synthetic identity, discovery, proposal/confirmation, booking certainty, help, handoff, and sanitized events), `src/ochsner_bob/replay.py` (effect-free variants), `src/ochsner_bob/adapters.py` (bounded language/policy), and `apps/scheduling_app.py` (thin optional Marimo entry point).

`tests/test_bob_core.py` covers explicit confirmation, identity correction, unknown booking, truthful handoff, authority exclusion, policy denial, and effect-free replay. Remaining task-ledger work is intentionally not presented as completed.
