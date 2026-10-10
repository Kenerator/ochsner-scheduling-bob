# Recovery and limitations

Updated 2026-10-09. All data and appointments are synthetic. Results refer to the
supplied local mock, never a real appointment or staff contact.

- **Completed:** a matching validated receipt was returned. History is separate
  from the current attempt; a later rejection does not erase earlier success.
- **Rejected/failed:** a definite validated failure was returned. Correct the
  issue, get current options, select anew and confirm separately.
- **Unknown/attempted:** the result is not known. No automatic retry. Workflow
  Reset, reconnect, recording expiry and restart do not clear durable protection.
  Keep the private effect namespace and reconcile before any real-service retry.
- **No identity match/ambiguous:** correct local phone/DOB/ZIP. No candidates are
  disclosed. Every correction revokes the prior match, results and proposal.
- **Stale screen:** review the current screen before acting; stale submissions
  never obtain a fresh confirmation token automatically.
- **Support stale:** last acknowledged screen is not necessarily current backend
  context. Keep private information out of public drafts; failed acknowledgements
  are not evidence of freshness. Pair/lease/grants expire.

An intentionally fresh supplied mock run uses a new explicit application namespace
or CLI journal, retaining prior uncertain claims. Do not delete private state or
the shared model ledger as a reset mechanism. Stop only the processes you launched.

Limits: matching is not production authentication; the local journal is not remote
exactly-once/idempotency; recorded-only core replay is not browser-renderer parity; mock support is
not delivery. See [next steps](../product/next-steps.md) for real-use prerequisites.
