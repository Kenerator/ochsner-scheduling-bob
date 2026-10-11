# Recovery and limitations

Updated 2026-10-10. All data and appointments are synthetic. Results refer to the
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
- **Invalid identity field:** correct that field; blank controls keep the other
  bounded entries privately in this session. The invalid value is not replaced
  by an older valid one. Verification stays missing until all fields are valid;
  Reset clears these entries. Do not enter identity in public chat.
- **Replay reference unavailable/not granted:** check the reference or import an
  approved recording into this current session. This does not mean pairing has
  failed; keep a valid session. A reference alone never grants access, and no
  effect is retried. True session/pairing failures retain their separate guidance.
- **Stale screen:** review the current screen before acting; stale submissions
  never obtain a fresh confirmation token automatically.
- **Support stale:** last acknowledged screen is not necessarily current backend
  context. Keep private information out of public drafts; failed acknowledgements
  are not evidence of freshness. Pair/lease/grants expire.

Support membership and control are distinct: joined/inactive is a valid state
before takeover and after Return. Do not interpret an inactive lease as failed
pairing. Current backend context and the last acknowledged patient screen can
differ; read their separate revision/freshness labels.

A selected recording Purge leaves an expired/tombstoned reference. An external
export may still exist, but importing the same reference does not restore it.
Do not rename/bypass tombstones to imply recovery. Recording retention/purge
does not remove booking uncertainty, effect-journal claims or model reservations.

An intentionally fresh supplied mock run uses a new explicit application namespace
or CLI journal, retaining prior uncertain claims. Do not delete private state or
the shared model ledger as a reset mechanism. Stop only the processes you launched.

Limits: matching is not production authentication; the local journal is not remote
exactly-once/idempotency; recorded-only core replay is not browser-renderer parity; mock support is
not delivery. See [next steps](../product/next-steps.md) for real-use prerequisites.
