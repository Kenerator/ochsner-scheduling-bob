# Scheduling with BOB

Internal-use synthetic demonstration with public source, not a real healthcare service. BOB is AI, not
a clinician or live representative. Follow [setup](../../README.md) with an
explicit Python 3.11+ environment. Offline use needs no model account.

## Find and confirm an appointment

Start an independent patient session. Choose specialty/location, select **Find
providers**, then choose a returned provider. In **Private synthetic identity**,
enter `555-0101`, `1985-04-12`, `70112` and select **Check or correct identity**.
Select **Get current availability**, choose a numbered option and review its exact
time, provider and location. Select **Confirm appointment** separately to attempt
the mock booking. Selection alone does not book; no email is required.

## Refine or correct the search

Change specialty, location or dates and select **Apply preferences**. Review
**Active filters**, then request current availability again. Blank a date control
to clear it; choose **Any location** to remove that filter. The public request box
also accepts offline `provider 1`, `clear provider` and `clear dates`. A spelling
suggestion requires explicit acceptance; it is never silently selected.

Correct private details with **Check or correct identity**. Blank private fields
retain prior local entries; verified inputs clear from the browser. Identity
changes revoke old private results and proposals. **Decline / change my mind**
clears the pending proposal, not an earlier booking. Request fresh options and
review a new proposal before confirming after a correction or decline.
Keep names, phone, DOB and ZIP out of the public request box; use private controls.

## Look up existing appointments

Check the current synthetic identity, then select **Look up my appointments**.
Returned appointments appear in the options area. They are different from
**Outcomes**, the history of booking/handoff attempts. Correcting identity clears
the old private results before another lookup.

## Recover or request assistance

No providers/availability means refine the search or use **Help**. No identity
match means correct private details; multiple matches require ZIP without exposing
candidate records. Empty appointment lookup differs from failed lookup. For a
failed read, follow the message and retry the read when appropriate. For an
**unknown write outcome**, do not repeat the write: follow [recovery](recovery.md).
Reset retains unresolved effect protection.

**Help**, **Medical boundary** and **Unsupported request** remain reachable.
Deliberately select **Submit mock handoff** if wanted. A queued result is a
validated mock receipt, not contact with a person. See the [demo runbook](../internal/demo.md).

## Support view

Join the one-use grant in a separate local tab. The participant can remain
**joined** while the **control lease is inactive**. Takeover requires a fresh
patient acknowledgement and expires after five minutes; Return ends control,
not pairing. Support cannot fill private identity, select a booking or Confirm.
An unaccepted suggestion changes nothing. After Return the patient must choose
to accept it, then get current options and freshly select/confirm.

## Developer view and replay

Inspect sanitized diagnostics with recording OFF; an owned OFF reference opens
bounded **current sanitized diagnostics**, explicitly not a historical state,
exact recording or full replay. The reference is session-scoped, expires and does
not grant another patient access. It cannot be stepped, forked or exactly exported.
The local Developer disclosure is not production authentication.

Record only explicitly approved synthetic sessions. Start capture before the
journey, then Seal and inspect fidelity/missing evidence. Open the resulting
reference; step or Jump to a valid event index, use bookmarks, and inspect
sanitized diagnostics. A reference is a locator, not an access capability.
Complete matching recordings can show core semantic parity; browser-renderer
parity remains false. Replay/forks never perform live booking or model calls.

Typed variants are counterfactual experiments, not historical results. Review
the regression-fixture proposal and provenance manually; generated proposals
are simulation-only and are not automatically executed or adopted as tests.
Export/import accepts bounded reviewed data, never executable instructions or
live consent. Use Purge only for a disposable recording: its reference becomes
permanently expired and importing its external export does not revive it.
