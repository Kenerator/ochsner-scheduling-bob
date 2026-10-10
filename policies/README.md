# Rules, decision tables and scenarios

BOB adopts one executable standalone ZEN policy (`zen-engine==2.1.2`), not the
optional engine-neutral starter. Reviewed 2026-10-10; source/test progress is in
[native tasks](../specs/001-ochsner-scheduling-assistant/tasks.md).

- [rules/](rules/README.md): executable rule sources, such as CLIPS `.clp` files.
- [tables/](tables/README.md): decision models, such as ZEN JSON graphs/tables.
- [scenarios/](scenarios/README.md): synthetic inputs and expected decisions.

Supplied requirements/policies remain authoritative. Keep confidential originals
in the ignored `docs/product/RFP/source/`, not here. Record each adopted policy's
stable ID, source section, specified/inferred origin, purpose and owning module in
this index. Link native feature stories/tasks rather than duplicating status.

Keep engine adapters and transaction effects in application source; test their
behavior in `tests/` using these scenarios. An engine's decision is not consent
or proof of a completed external action. Do not implement the same policy twice
in separate engines unless deliberately comparing alternatives.

When adopting an engine, pin its dependency and qualify clean reviewer setup.
Test allow/deny/missing input, conflicting or malformed data, changed context,
and state isolation where relevant. Record expected output and no-effect cases;
bound rule execution when loops are possible. Rules and embedded functions are
code: do not execute unreviewed intake merely because it was copied here.

## Adopted policy index

| Model / owner | Contract and origin | Executable evidence |
| --- | --- | --- |
| [bob.json](bob.json) / [Policy](../src/ochsner_bob/policy.py) | Specified B11 / native FR-013: five closed categorical facts (`action`, `identity`, `proposal`, `confirmation`, `effect`) → boolean allow, stable rule/reason, engine and exact loaded-graph digest. Ordered first-match table; default deny. | [test_zen_policy.py](../tests/test_zen_policy.py): real engine compile/evaluation, all 240 combinations, malformed/missing facts, graph drift and engine failure. |

[SchedulingSession._guard](../src/ochsner_bob/session.py) evaluates the actual
graph and independently enforces current identity, proposal, confirmation and
durable effect claims. A ZEN allow is never consent or a successful API receipt.
Invalid facts / unavailable or malformed engine results deny; no raw exception
or private fact enters the rule explanation. The graph is source-relative and
qualified for editable/source-export setup, not a standalone-wheel claim.
Historical scaffold checkpoints are retained in Git, not current guidance.
