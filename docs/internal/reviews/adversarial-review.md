# Optional adversarial review

Updated 2026-10-09. Status: **one independent review performed; three reproduced
findings corrected and bounded delta rechecked**. Method: native read-only Codex
reviewer (available fallback), not an external Claude/tmux consultation. Reviewed
baseline `a43fb61532a62f83b91dd862099419b385caee98` plus explicitly uncommitted BOB
integration, not an immutable final release. Final source binding belongs in
[milestones](../milestones.md); this report is not a security certification.

Schedule once near completion or as an Operator-selected follow-on; this is not an implementation/MVP gate. Reuse an adequate existing independent review rather than creating another mandatory cycle.

Prefer a read-only Claude consultation in observable tmux under the environment's current permissions; Codex is an acceptable fallback. Share the attach command. Review supplied sanitized evidence only; do not grant new live access or copy raw transcripts into Git.

Focus on exact confirmation/replay, ambiguous outcomes, malicious API text, constrained-persona accessibility, clean setup and misleading UI or claims. Document limits: synthetic evidence is not real-service, clinical, security or compliance acceptance.

| Finding / source location | Impact | Disposition or next step |
| --- | --- | --- |
| P1: CLI generated a new session ID on reopening the same journal (`__main__.py`) | Repeated submission could bypass an unknown claim; reproduced writes 1 → 2, not proof of downstream duplicate booking. | Fixed by private atomic `cli_namespace.py`, lifetime lock, immutable binding checks and refusal of legacy/foreign/lost state. Original two-launch diagnostic now one attempt/one unknown; 18 restart tests passed. |
| P2: expired recording status did not remove idle stored payloads (`interaction_service.py`, launcher) | TTL was not enforced without recording activity. | `maintain_retention()` purges expired memory first, tombstones stored payloads, reports errors categorically; launcher `service_actions` schedules it without traffic. Original TTL reproduction and callback tests pass; journals/budget excluded. |
| P2: fresh support omitted the patient's visible stale warning (`widget.js`, acknowledgement schema) | Backend snapshot alone overstated semantic screen fidelity. | Closed notice/pending/dirty acknowledgements, strict browser/core validation, shared notice projection and actual shipped-renderer regression. Delta reproduction showed matching warning and `pending:false`. |

Initial review ran 125 focused offline tests plus reproductions. Bounded fix
validation ran 28 focused tests; no concrete remaining regression found in that
delta. No edits, credentials, model calls or external network were used by the
reviewer. Browser validation in this review used local doubles and real-service
acknowledgements, not independent Chrome/Marimo execution.

Not independently requalified by this review: supplied HTTP integration, actual
browser, genuine language, clean setup, real services/PHI, accessibility, clinical
or compliance acceptance. Parent verification is separately source-bound in the
[task ledger](../../../specs/001-ochsner-scheduling-assistant/tasks.md). A later final
contract reconciliation identified live-core replay fidelity as remaining work;
the three-fix review does not certify that later implementation.

Include only sanitized findings and useful synthetic regressions. Commit the report and fixes, record an immutable named review tag in [milestones](../milestones.md), then push the named commit/tag only to an already-authorized destination with its required privacy. No new publication authority is implied. If deferred, record it in [next steps](../../product/next-steps.md).
