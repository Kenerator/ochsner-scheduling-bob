# Optional adversarial review

## Stage-one correction summary — 2026-10-10

This is the approved quality-correction summary, **not the separate stage-two
adversarial review**. Baseline `517a9b27d9ccc9cd863f3c8e868acd6e8f5b6710`;
runtime/test candidate `56fc4e8bc10ec4a15dc2befabb76208f2d64a807`.
The sole BOB writer integrated read-only documentation drafting; no comparator
re-audit or additional architecture/features were introduced.

The reproduced OFF-reference failure now opens bounded session-owned current
sanitized diagnostics, explicitly not historical/exact replay. Six tests cover
privacy, expiry/no renewal, foreign/invalid references, truncation, no store or
live effects and clearing an old replay target. Explicit package ESM fixes the
reproduced Node detection dependency without changing widget bytes. All eight
current widget checks passed under Node 22.14.0 with detection both enabled and
disabled. The focused documented nested `.bob-local/run-N` launch passed; its
parent-directory preparation is a prerequisite, not a newly claimed defect.

Fresh parent combined suite: 422 tests passed (24.018 s); supplied-HTTP booking
success/conflict/unknown demos and retained starter success/failure passed.
Clean committed export/install qualification passed all seven steps on Python
3.11.13/macOS ARM; profile SHA-256
`697809cdf69ba24119e380c3e78ee7a1e7bb91cfce80c997fc9c19d30d578f39`.
Browser/live-model/remote-clone coverage is not checked by that profile.
The new offline workflow uses official full-SHA actions, read-only permissions
and a standard runner. Two independent domain reviews approved the exact runtime/
engineering commit with no actionable findings. The OFF reviewer inspected all
six regressions and passed nine bounded in-memory/socket-denied probes with zero
API/model/store/record-grant/exact-replay activity; engineering reviewed ESM,
nested launch, dependency checks and workflow boundaries. Final documentation/
evidence review and actual CI remain pending; no complete-candidate approval,
green CI or merge claim is made here. Changed runtime bytes require only an
affected-delta rereview, not a duplicate broad audit.

README/task help, BOB versus inherited tooling, policy-to-spec provenance,
as-built/persona links and historical merge/video/public-source wording are
reconciled. GitHub About readback confirmed the truthful internal-use synthetic
scheduling description and six topics, with no homepage/license invented.
Native [T057–T063](../../../specs/001-ochsner-scheduling-assistant/tasks.md) owns
completion and final guard/navigation/CI/PR evidence; this summary is not a second
ledger. RC-1/RC-2 remain unchanged. No paid calls, capture, trial control,
deployment or media publication occurred. Stage-two work remains held until
stage one is complete/frozen; stage-two remediation is not authorized here.

## Historical independent review — 2026-10-09

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
