# Future production design (not implemented)

Reviewed 2026-10-10 against the accepted BOB scope and current loopback source.
These notes satisfy the design-only follow-on in the approved requirements;
they authorize no production data, accounts, deployment, integration or spend.

- Costs and latency: retain per-request reservations, bounded input/output,
  measured model/API latency and explicit timeout/cancellation status. Estimate
  real workload and pricing before selecting limits; do not infer reliability
  or capacity from the [small model sample](../internal/live-qualification.md)
  or [loopback measurements](../internal/performance-notes.md). Unknown billable
  usage keeps its liability. No silent model fallback or write retry.
- Monitoring: instrument categorical rule decisions, API/model outcomes,
  uncertain effects, diagnostic drops, queue failures and retention failures.
  Separate operational alerts from opt-in exact recordings. Use authenticated
  least-privilege access, minimized retention and reviewed redaction; never
  export identity, nonces, prompts or raw exceptions to general logs.
- Rollout/rollback: first qualify a versioned read-only/synthetic canary, then
  a reviewed limited cohort with server-side flags and explicit stop criteria.
  Version policy/schema/adapter contracts together. Rollback presentation or
  model/policy versions without deleting unresolved effect claims, restoring
  old consent or relabeling unknown writes. Durable-state/schema migration and
  upstream reconciliation require a separate design and rehearsed recovery.
- Reschedule/cancel: the supplied API has neither endpoint. A future contract
  must define ownership, eligibility, exact changed appointment summary, fresh
  separate confirmation, concurrent edits, idempotency and authoritative receipt
  reconciliation. Until then, explain unsupported behavior; never implement
  cancellation as local reset or rewrite history.
- Authenticated support/replay: replace loopback demo capabilities with verified
  identities, server-side role/tenant/session authorization on every HTTP and
  WebSocket path, consent/minimization, audit and revocation. Replay references
  remain identifiers, not credentials. Imported evidence cannot restore live
  identity, consent or effects; use isolated recorded-only adapters. Demo
  Developer Mode and takeover are not production authorization.

These boundaries complement [decisions](decisions.md), [as-built architecture](../internal/as-built/architecture.md)
and [next steps](next-steps.md); detailed implementation status stays in
[native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md).
