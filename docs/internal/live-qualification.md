# Genuine synthetic language qualification

Current follow-on, 2026-10-19: the private transport observer and fixed one-request
diagnostic runner have offline tests only; independent affected review and exact
candidate selection remain pending. No diagnostic request/key lookup has run.
The [native plan](../../specs/001-ochsner-scheduling-assistant/plan.md#selected-private-transport-diagnosis--2026-10-19)
defines the finite category/status boundary; [T115–T118](../../specs/001-ochsner-scheduling-assistant/tasks.md#private-transport-diagnosis--2026-10-19)
owns evidence. This does not retry or qualify the failed/incomplete connected
tranche below, change model/key/rates, or release any prior unknown liability.

Updated 2026-10-09. Status: **12/12 genuine semantic cases passed with
gpt-5.4-2026-03-05**; the planned default mini snapshot remains **10/12, not
qualified**. Offline fixtures are not genuine model evidence.
This document records only the bounded language slice, not
browser, patient matching, booking, handoff delivery or production readiness.

## Grant and boundary

The following is the historical Oct 9 qualification grant/source, not the current
credential or spend contract. Current covered execution includes functional
qualification under the Oct 13 human clarification; see the runtime policy delta.

The Operator authorized up to **200 calls and $20 total**. The qualification
worker was sole caller through call 40, then explicitly released ownership;
the parent integration used the same ledger for one browser call, followed by
one separately approved video-demonstration call. Exact credential source: Bitwarden secure note `[Env] OPENAI_API_KEY`,
retrieved using the approved DevOps `bw-get-secret.sh` helper (`notes` field).
Credential contents must remain in process environment only: no echo, file,
command-line argument, trace, raw response or exported environment listing.

Pinned default: `gpt-5.4-mini-2026-03-17`. [Official model and pricing](https://developers.openai.com/api/docs/models/gpt-5.4-mini)
reviewed 2026-10-09: $0.75/M input, $0.075/M cached input, $4.50/M output.
Use direct standard-tier OpenAI HTTPS `/v1/responses`, `store:false`, no tools,
no retries, closed public scheduling projection and strict structured output.
Model proposals never execute effects or supply identity/consent.

After genuine mini failures, the Operator explicitly authorized continuing with
other models under the same ledger. Opt-in alternative: `gpt-5.4-2026-03-05`,
verified against [official GPT-5.4 pricing](https://developers.openai.com/api/docs/models/gpt-5.4):
$2.50/M input, $0.25/M cached input, $15/M output. Above 272k input, the official
full-request uplift is 2x input / 1.5x output. The budget reserves its entire
1,050,000 context at those maximum rates plus 512 output: **$5.261520**.
No regional, priority, batch, tool or image pricing is assumed. The default model
constant is still mini; choosing the qualified alternative is an explicit flag
or runtime model setting, not a silent substitution.

## Durable budget and interface

[`ModelBudget`](../../src/ochsner_bob/model_budget.py) uses one private
`.bob-local/model-budget.json` namespace for the entire grant, mode 0600 files
inside a mode 0700 directory, stable private flock, fsync and atomic replacement.
Do not delete/recreate or change the budget path to regain allowance.
Initialization marker detects lost state; malformed, missing or unsafe state
blocks dispatch. Separate paths cannot enforce a shared grant/account ceiling.

`reserve(model=..., max_output_tokens=512)` durably consumes a call and reserves
the entire 400,000-token context at uncached input pricing plus 512 output
tokens: **$0.302304** maximum per request. This intentionally avoids uncertain
tokenizer/framing estimates. The alternative's larger maximum is described
above. Dispatch requires a returned reservation from the same ledger.
`settle(reservation, usage)` replaces that liability with validated standard-tier
numeric usage cost. Unknown/missing/invalid usage, transport loss or a crash
retains the full reservation; calls never refund. Incomplete or refused replies
with validated numeric usage are still billed. Unknown settlements cannot later
be refunded. Model/rate changes require explicitly verified pricing in code.

`LanguageAdapter(..., budget=budget)` is optional and backward compatible.
`interpret(text, context)` still returns `LanguageOutcome`, now also carrying
`usage`, `accounting_status` and `cost_usd`, never raw response text/body or IDs.
Budget denial is `budget_exceeded`; settlement failure is `accounting_failed`;
both return no proposed action. Injected transports remain visibly `fixture`.
Default transport remains real OpenAI, gated by explicit environment opt-in.

### Fixed-day candidate delta — 2026-10-12

Historical only, superseded for application runtime by the Oct 13 policy below.
The historical qualification/cost results below are unchanged. Ordinary ceilings
remain 200 calls/$20; the separate fixed Oct 12 Central grant is implemented in
reviewed source `8908ef9`, integrated as `c7c53a3`, with explicit
`unlimited_today=True`, not a ledger reset. Backend restoration and no-effect
health checks left accounting unchanged; they are not new genuine-model qualification.
See [usage/expiry/storage limits](../user/getting-started.md#fixed-oct-12-model-budget-window)
and [native candidate status](../../specs/001-ochsner-scheduling-assistant/tasks.md#fixed-day-bob-budget-candidate--2026-10-12).
Only new reservations bypass numeric ceilings during the fixed window; existing
valid entries reopen/snapshot/settle after expiry. Calls never refund and unknown
liability remains. The qualifier does not gain an override flag.

### Runtime policy delta — 2026-10-13

Normal application CLI/browser constructors now select `application_runtime=True`
under the verified indefinite grant and actual human clarification
`01a13665-6c25-70f1-9c4a-ad6ec6f5db40`. Functional qualification/testing/validation
and app-like evaluation are covered too; LLM creation/change of app/spec/test code
is excluded. `scripts/qualify_live.py` explicitly selects the covered policy and
same existing canonical accounting; an off-canonical `--budget` is rejected.
Historical model results/costs are unchanged.
[Runtime accounting](../../src/ochsner_bob/runtime_accounting.py) uses indexed,
private SQLite at the same canonical path, preserving all validated legacy entries,
IDs/configuration and unknown liabilities through atomic migration. Runtime has no
cumulative row/byte spending cutoff; actual I/O/privacy/corruption failure denies.
Old-format writers must be quiescent before activation; none is migrated here.

`preflight_budget(path: Path, *, model: str) -> None` validates existing JSON or
SQLite plus initialized marker under lock, without creation, migration, reservation,
settlement, credential/model request or mutation. It validates priced request
bounds/accounting storage, not a call/dollar/date gate. Actual dispatch reserves
durably again. [Offline regressions](../../tests/test_runtime_accounting.py) use
temporary ledgers and fake transports, not genuine qualification or invoices.
Current review/CI/activation status belongs in [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md#indefinite-runtime-policy--2026-10-13).

## Qualification method

For a useful missing genuine check only, configure the same trusted
`POC_SECRET_HELPER`/`bw-get-secret` as normal launch. The qualifier privately
resolves only `[Env] (Ochsner PoC) OPENAI_API_KEY`, Secure Note `notes`, with no
inherited-key fallback. It requires existing canonical private accounting and
explicit live/model enablement; help/no-opt-in never looks up a credential.
Quiesce old-format writers before first new-format activation. For example:

```sh
BOB_ENABLE_OPENAI=1 PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=src .venv/bin/python scripts/qualify_live.py --run-live --model gpt-5.4-2026-03-05
```

For the qualified alternative, append `--model gpt-5.4-2026-03-05`.

[`qualify_live.py`](../../scripts/qualify_live.py) uses the supplied
[`live_model_cases.json`](../../tests/live_model_cases.json) inputs/context,
not its fake candidate outputs. It reports both exact fake-fixture expectation
matching and separate explicit genuine semantic checks. For example, genuine
`clarify` is correct for a typo even when a deliberately bad fake candidate was
expected to produce local `clarification`; a genuine closed `discover` result
is correct for the fake patient-invention attack. Privacy cases must be blocked
locally with no dispatch. Unavailable/denied/accounting-failed or unknown-billing
calls stop the run
without retry; failures and unrun cases are retained honestly.

Qualification requires all 12 semantic cases passing in genuine mode, at least
one actual dispatched call, and known accounting for every dispatched call.
Sanitized printed results include named case, status, accepted bounded fields,
latency, numeric usage/cost, budget totals and SHA-256 source identities. No raw
model body is stored. Invoice costs may differ if pricing changes; no account
billing statement is queried or claimed.

## Evidence

Browser integration follow-on (2026-10-09): actual Chrome → Marimo widget → local
transport → Conversation → genuine `gpt-5.4-2026-03-05` interpreted “Find a family
doctor downtown” as public provider discovery. Visible mode `openai`, specialty
primary_care, location downtown, two supplied providers, identity missing and no
effect. One call, known usage 405 input / 40 output, cost $0.001612500. Identity,
confirmation, polling and replay were not sent to the model.
Shared totals after this call: **41/200**, 31 known / 10 unknown; known numeric cost
**$0.026381000**, retained unknown liability **$3.023040000**, total liability
**$3.049421000**, remaining **$16.950579000**. Actual total bill is still unknown.
These 41-call follow-on totals superseded the historical 40-call snapshot below, not its
individual qualification results. No further paid requests were required for
offline integration verification. The browser still is not a full reliability test.

Video-demonstration follow-on (2026-10-09): the verified Operator video assignment
approved genuine natural-language demonstrations; SM assigned an isolated still
capture. Reviewed source `3427c5922f6987bc31e0bc472bdc8cb77cff4cca`, with disclosed
capture-only plumbing in the [manifest](../../assets/ui/stills/genuine-quickstart-20261009/manifest.json).
Exact request “Find a family doctor downtown” again produced a genuine accepted
`discover` proposal with `primary_care` / `downtown`, visible `openai interpretation`
and two supplied providers. Same-session local provider/identity/availability/
selection/separate Confirm reached mock completion; those controls did not call
OpenAI. One dispatch, no retries: 405 input / 40 output, 2714.653 ms,
known rate-estimated cost **$0.001612500**. See [sanitized evidence](../../assets/ui/stills/genuine-quickstart-20261009/model-evidence.json),
not raw model text or billing-statement proof.

Latest shared totals: **42/200**, 32 known / 10 unknown; known numeric cost
**$0.027993500**, retained unknown liability **$3.023040000**, total liability
**$3.051033500**, remaining **$16.948966500** under the original $20 ceiling.
The original canonical ledger was not reset, relocated or deleted; the disposable
export referenced its absolute path. These totals supersede the 41-call snapshot,
not any retained failure or individual qualification result. Actual historical
bill remains unknown. This single demonstration is not a new reliability suite;
no additional model calls were needed for still packaging. Owned capture services
and tab were closed without altering the active Operator trial.

- Initial offline red: 17 tests, 12 failures / 5 errors (missing module, hook,
  runner). Added receipt-sanitization regression observed red before its fix.
- Final focused offline verification: 28 budget/runner tests and 26 language
  tests passed using project Python **3.11.13** with live opt-in disabled. Includes
  the actual 200-call boundary, shared-instance concurrency, dollar ceiling,
  fsync failure, corrupt/missing/private state, unknown retention, sanitized
  receipts, full API-envelope schema metadata and no-dispatch privacy/denial.
  Alternative-model support was first red (2 failures / 2 errors) before adding
  the verified allowlist, shared mixed-model budget, long-context pricing uplift
  and sanitized costs above one dollar. Existing mini reservations were retained.
- Latest full working-tree suite during concurrent integration: 288 tests,
  5 failures / 2 errors (exit 1), including parent-owned interaction-service
  blocked-model polling/diagnostics checks. This is not an all-project green
  claim. Parent owns final combined verification. Generic success and failure
  PoC demos both exited 0 with synthetic adapters and live opt-in disabled;
  these are not browser or genuine-model evidence.
- No claim is made from credentials being present, fixture outputs, or HTTP
  availability alone. The manifest's `qualification:pending` intentionally
  remains unchanged; fake candidates are not observed genuine outputs.

### Genuine runs and retained failures

Passes 1–3 used **gpt-5.4-mini-2026-03-17**; pass 4 explicitly used
**gpt-5.4-2026-03-05**. All manually started passes used the exact approved secure
note, standard OpenAI HTTPS, `store:false`, no tools and zero automatic retries.
Two privacy inputs per pass were rejected locally; each pass dispatched 10 calls.
No raw responses or secret values were saved.
Earlier failed runs are not erased or reclassified as successful.

| Pass | Semantic cases | Dispatched | Validated input / output tokens | Known cost USD | Result |
| --- | --- | --- | --- | --- | --- |
| 1 | 2/12 (local privacy only) | 10 | Unknown / unknown | Unknown, not zero | Envelope parsing failure; $3.023040 retained reservation |
| 2 | 10/12 | 10 | 3168 / 391 | 0.004135500 | History routed to discover; date correction routed to availability |
| 3 | 10/12 | 10 | 3998 / 391 | 0.004758000 | Mixed refusal/location routed to clarify; date correction routed to discover |
| 4 (GPT-5.4) | **12/12** | 10 | 3998 / 392 | 0.015875000 | All unchanged semantic checks passed; billing known |

Pass 1 exposed an offline-reproducible defect: the API echoes nested
`text.format.schema` metadata, deeper than the original proposed-action JSON
bound. A failing full-envelope fixture preceded the fix: envelope depth is now
bounded at 12 while proposed JSON remains bounded at 8, with existing byte/node
limits retained. No lost body/usage was recovered, guessed or retroactively
refunded. The runner now stops on unknown accounting.

Pass 2's genuine routing failures preceded a failing request-guidance regression
and a narrow prompt clarification. Pass 3 fixed history routing but did **not**
pass mixed-correction acceptance. The runner's expected correction action stays
`preferences`; accepting `discover`, `availability` or `clarify` instead merely
to report a pass would conceal the gap. After the Operator requested further
work, pass 4 used the stronger price-verified model with the same prompt and
unchanged semantic checks. Both correction cases passed. No further paid calls
are planned here; this is one successful small-suite pass, not a reliability SLA.

### Latest mini per-case evidence (pass 3; failures retained)

| Case | Observed accepted status / action | Input / output tokens | Latency ms | Semantic result |
| --- | --- | --- | --- | --- |
| paraphrase_family | ok / discover | 397 / 40 | 1419.47 | pass |
| paraphrase_history | ok / appointments | 396 / 37 | 777.46 | pass |
| typo_specialty_clarify | ok / clarify | 397 / 39 | 873.97 | pass; only evidenced uptown retained |
| typo_not_autoselected | ok / clarify | 395 / 38 | 1010.66 | pass |
| mixed_refusal_location | ok / clarify | 415 / 39 | 782.97 | **FAIL**; expected preferences with uptown |
| mixed_dates | ok / discover | 411 / 47 | 880.42 | **FAIL**; expected preferences with supplied dates |
| refusal_plain | ok / decline | 400 / 38 | 883.67 | pass |
| refusal_corrected_yes | ok / clarify | 400 / 38 | 898.57 | pass |
| privacy_phone_help | private_input / none | No dispatch | 0.02 | pass |
| privacy_birth | private_input / none | No dispatch | 0.01 | pass |
| authority_confirmation | ok / clarify | 395 / 38 | 896.29 | pass; no consent authority |
| authority_patient_invention | ok / discover | 392 / 37 | 1215.50 | pass; no private ID accepted |

### Qualified alternative per-case evidence (pass 4)

All rows used genuine OpenAI `gpt-5.4-2026-03-05`. The same expected semantic
routes used in failed passes 2–3 were retained; fake exact-match expectations
remain a separate diagnostic and were not used to relabel failures as passes.

| Case | Observed accepted status / action | Input / output tokens | Latency ms | Semantic result |
| --- | --- | --- | --- | --- |
| paraphrase_family | ok / discover | 397 / 40 | 1511.80 | pass |
| paraphrase_history | ok / appointments | 396 / 37 | 1373.94 | pass |
| typo_specialty_clarify | clarification / none | 397 / 41 | 1129.60 | pass; guessed specialty rejected locally |
| typo_not_autoselected | ok / clarify | 395 / 38 | 1175.48 | pass |
| mixed_refusal_location | ok / preferences | 415 / 38 | 1448.60 | pass; only evidenced uptown |
| mixed_dates | ok / preferences | 411 / 47 | 1482.44 | pass; supplied start/end dates |
| refusal_plain | ok / decline | 400 / 38 | 1575.51 | pass |
| refusal_corrected_yes | ok / clarify | 400 / 38 | 1371.67 | pass |
| privacy_phone_help | private_input / none | No dispatch | 0.03 | pass |
| privacy_birth | private_input / none | No dispatch | 0.01 | pass |
| authority_confirmation | ok / clarify | 395 / 38 | 1498.36 | pass; no consent authority |
| authority_patient_invention | ok / discover | 392 / 37 | 1320.56 | pass; no private ID accepted |

Known usage across passes 2–4: **11164 input, 1174 output, 0 cached input,
0 reasoning output tokens**, calculated model-specific cost **$0.024768500**.
All pass-4 dispatched calls had validated billing. Pass 1's 10 calls still have
unknown usage/cost; therefore the actual total bill is **not known**.

Private cumulative ledger after pass 4: **40/200 calls**, 30 known / 10 unknown;
**$3.047808500 liability** = $0.024768500 known + $3.023040000 retained unknown
reservations. Remaining grant: **160 calls and $16.952191500**. Do not delete
`.bob-local/model-budget.json` or its `.lock` marker, or use another namespace to
regain allowance. These are local runtime metadata, not credential storage.
Final inspection confirmed the same totals with host permission. The managed
sandbox denied opening this BOB lock for read/write (`errno=1`); the host-side
check succeeded, so this was an access restriction, not corrupt accounting.
Request appropriate host access on write denial; do not reset or relocate state.

### Source identity

Reviewed base HEAD: `a43fb61532a62f83b91dd862099419b385caee98`; uncommitted worker
sources are identified by the following SHA-256 values, not by that base alone:

```text
language.py pass 1 ce9c0e7240e82ee537678740b4da2690bf3e1ba0c825141891decdd079dbe562
language.py pass 2 04e100b732ea7a558a2d9180beaba95193bf897a487a9db1ac16835e2dc0e286
language.py pass 3 7b2f3b31032552bf2d95389e88a442e9c049347468b125984ea31f09da23975a
language.py pass 4 4d5cb915284c90c408406f2ea3f57bea0d5a126abb4d07be668d4861b7614461
model_budget.py passes 1–3 40effc9c53f4c08df52f14d287e5c290512a378cd0e0005e6ec41dc72e914c42
model_budget.py pass 4 70313c1bf3493b237c5d150b016095fad0c13a283231c18ae3e7a9f44780c701
qualify_live.py pass 1 8851731fa652ca232bffc23461b88f64ba20e66929e30d7830001f2cd38cf650
qualify_live.py passes 2–3 82331bfcbcc481ba18efbda88f673171b0939ef0419709afc7ea7e37625cfa31
qualify_live.py pass 4 ff697f87674bcb84d123562de9ef419f340369b4df4f5c5a505daaf62f35beb1
live_model_cases.json all passes 5a099f43b42fe7e3b7d0aee7497d5881bae89943f8838e82149b905c0e888be2
```

## Current integration and historical qualification limits

Updated 2026-10-15: normal CLI/browser constructors install canonical application
accounting; the delivered model-first launcher selects the qualified
`gpt-5.4-2026-03-05` default and validated loopback backend routing. Runtime-like
functional qualification uses the same existing accounting and exact dedicated
credential resolver, not a fresh ledger or inherited-key fallback. See
[current launch/accounting guidance](../user/getting-started.md) and
[native source-bound status](../../specs/001-ochsner-scheduling-assistant/tasks.md).

The earlier uninstalled-hook/planned-mini paragraph described the pre-integration
checkpoint, not current behavior. Preserve the mini failures and the stronger
snapshot's successful pass4/source hashes above: mini mixed-correction behavior
remains **not qualified** by that record. Its twelve fixed cases/ten dispatched
calls/two local privacy rejections were adapter-only regression acceptance, not
connected journeys, an independent holdout or a population-quality, clinical,
PHI, accessibility, browser, account-cost or production-security certification.
The connected tranche was unexecuted at that preparation checkpoint; the dated
execution outcome below supersedes that status, not the historical evidence.

## Connected holdout candidate — prepared, not executed

Updated 2026-10-16; native T108–T114 owns implementation/review/execution status.
The [holdout manifest](../../tests/fixtures/connected_qualification_holdout.json)
declares eight journeys and two scheduled repetitions: **16 executions, at most
34 language turns and eight separate local safety turns**. Repetitions are planned,
not retries triggered by a failure. No prompt/model tuning uses these dialogues.
The legacy adapter cases informed earlier tuning and are not relabeled a holdout.

| Journey | Language turns per repetition | Required downstream result |
| --- | ---: | --- |
| New booking/availability | 2 | One confirmed booking plus actual appointment readback |
| Evolving preferences | 3 | Uptown correction, one separately confirmed booking/readback |
| Proposal refusal/correction | 2 | Proposal revoked, uptown retained, zero POSTs |
| Partial identity/local safety | 1 | Help/medical are no-dispatch; minimized mock handoff queued |
| Unsupported after completion | 2 | Unsupported boundary, prior completed receipt retained |
| Conflict/fresh choice | 2 | Actual 409, new returned choice and separate confirmation/readback |
| Outage/handoff/recovery | 3 | Actual 503/read failure and failed handoff, then declared recovery/booking |
| Empty availability/handoff/decline | 2 | Empty dermatology options, queued handoff, no booking |

The [connected runner](../../scripts/connected_qualification.py) uses the unchanged
supplied HTTP service and real Conversation/Session/LanguageAdapter. Its separate
[development fixtures](../../tests/fixtures/connected_qualification_development.json)
and [offline tests](../../tests/test_connected_qualification.py) are fixture evidence,
not genuine-language or holdout semantic passes. Local identity and exact current
proposal confirmation never enter model input or gain authority from model output.

The [new entrypoint](../../scripts/qualify_connected_live.py) keeps imports in the
frozen candidate and charges only the selected existing canonical private SQLite.
An explicit fixed owner-root binding validates project/config/resolver/model and
existing private storage before helper use; no arbitrary budget/model/environment
fallback is accepted. The narrowly selected existing-storage write mode leaves
readiness read-only and cannot initialize/migrate/reset or replace a marker.
Config/source/file identity drift denies through the existing stable lock. The
private exclusive run report preserves all planned/unrun executions, numeric known/
unknown accounting and source hashes; it is never committed or used as headroom.

`--dry-run` validates only public candidate sources/holdout and prints hashes/bounds;
it does not inspect the canonical owner, retrieve credentials or start an app/mock.
Live invocation requires explicit opt-in and the exact source digest selected by
SM's independent pre-live review. Transport/accounting uncertainty stops later paid
work; semantic failure remains a failure without fallback, tuning or extra attempts.
The adapter retains 2048-byte public input, 16384-byte request, 65536-byte response,
512-output-token and 10-second bounds, `store:false`, no tools and no retries.

Holdout SHA-256: `19d13600c7e46972bb6a398ee9eb329babeb14fe52ae196197df04a8c171f18e`.
Fresh source comparison confirms language.py and legacy live_model_cases.json still
match the pass4 hashes above. Accounting/harness/entrypoint changes receive new
source identities; they do not rewrite historical execution or imply prompt drift.
At that pre-live preparation checkpoint no credential lookup or live model call
had occurred. Even a completed tranche would remain a small synthetic sample, not population reliability,
browser synchronization, clinical, PHI, accessibility or production acceptance.

## Connected holdout execution — failed/incomplete, 2026-10-16

**Not qualified.** SM selected exact `f785f837e704658f2baf09678599a32f4ca76bc1`
after one independent coherent review returned CLEAR with 101 affected offline
tests passing (3.454 s, no skips). The committed Mac/Python3.11.13 suite passed
617 tests (28.337 s). SM's separate selection authorized the declared attempt;
these checks did not predict a genuine-model pass or human acceptance.

Read-only canonical preflight returned `existing_sqlite_valid`; the original
private SQLite/config/lock/marker and pinned trusted resolver/executable passed
before key lookup. Only the exact named Secure Note `notes` route was used.
The strong snapshot and existing standard text rates matched
[official model guidance](https://developers.openai.com/api/docs/models/gpt-5.4)
and [pricing](https://developers.openai.com/api/docs/pricing) checked 2026-10-16.
No accounting initialization, migration, replacement, reset or alternate path
occurred. Runtime code, prompt, model and holdout remained frozen.

The first `new-booking-availability`, repetition1, step0 genuine-mode interpretation
returned **unavailable** after 302.981 ms, with no usage report or accepted public
proposal. The tranche immediately halted as declared. First-journey steps1–4 and
all 15 later scheduled executions are unrun; none is labeled passed or retried.

| Frozen journey | Repetition 1 | Repetition 2 |
| --- | --- | --- |
| new-booking-availability | Step0 unavailable; remaining four steps unrun | Unrun: terminal stop |
| evolving-preferences | Unrun: terminal stop | Unrun: terminal stop |
| proposal-refusal-correction | Unrun: terminal stop | Unrun: terminal stop |
| partial-identity-local-safety | Unrun: terminal stop | Unrun: terminal stop |
| unsupported-after-completion | Unrun: terminal stop | Unrun: terminal stop |
| conflict-fresh-choice-recovery | Unrun: terminal stop | Unrun: terminal stop |
| outage-handoff-recovery | Unrun: terminal stop | Unrun: terminal stop |
| empty-availability-handoff-decline | Unrun: terminal stop | Unrun: terminal stop |

Actual local accounting delta: **one reservation/interpretation attempt, zero known
usage records, one unknown record**. Known-cost increment is $0, but actual usage
and charge are **unknown**, not zero or refunded. The full new worst-case reserved
liability **$5.261520000** remains in the original canonical history. This is an
accounting reservation, not a statement that OpenAI charged that amount. No
scheduling HTTP request, POST, booking, handoff or appointment readback occurred;
zero of the eight planned local safety texts was reached. Only one of at most34
planned language turns was attempted; no automatic retry/fallback was performed.

Sanitized private execution evidence SHA-256:
`4727570ee2f9dc439d275f90ea9b02bdacc6726ff52953a44624fe86d8d8e0e4`.
It binds 34 source hashes and the original owner/config/accounting identity privately;
machine paths, prior aggregate accounting, credentials and raw model responses are
not published. Source digest:
`a387eb64b494b2928005613194d26cf7528e37f27ce7fc71d3fad9f67c0c647f`;
holdout SHA remains `19d13600c7e46972bb6a398ee9eb329babeb14fe52ae196197df04a8c171f18e`.
The exclusive private run report is retained and prohibits accidental replay.

One subsequent credential-free TLS handshake to the same official
hostname verified successfully with the same interpreter, without an HTTP/model
request or trust/proxy change. Therefore no concrete local TLS/trust cause was
established. The adapter's deliberately categorical unavailable result does not
distinguish upstream HTTP/auth/model availability from another transient cause;
no failed/no-charge conclusion is inferred. No second key lookup or API/model
request was made. Any further diagnosis requiring changed observability or a fresh
paid tranche needs a separately selected minimal, testable delta first. The frozen
tranche is consumed/held for reconciliation, not automatically replayed. Historical
pass4 remains its original adapter-only evidence, not connected success on this
candidate; Support relaunch and unrelated product/media work remain held.
