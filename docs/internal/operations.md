# PoC operations — launch, recover, deliver

Reviewed: 2026-10-09. A short operating checklist, not another workflow engine or approval gate.

## Launch

1. Select a verified Python 3.11+ interpreter, the exact candidate directory and preserved intake. Preview bootstrap, then create once. Local Git starts on `main`; make a scoped baseline commit once meaningful content exists.
2. Run the read-only doctor from the Template/tool environment. Resolve errors relevant to the work; optional-tool warnings do not block offline work. It does not test account/model access, alter settings or delete locks.

```sh
PYTHONPATH=src python3 -m poc_template doctor --project ../my-poc
PYTHONPATH=src .venv-speckit/bin/python -m poc_template doctor --project ../my-poc --operation automatic-stage
# Explicitly test only the current caller's ability to write the destination parent:
PYTHONPATH=src python3 -m poc_template doctor probe-write --parent /absolute/project/parent
```

3. Use the chosen cumulative native stages or generated copy/paste handoffs. Stage 0 invokes none; Stage 4 attempts Specify → Clarify → Plan → Tasks. Claude and Codex may be selected independently for manual stages. Native stages own their questions and normal operation.
4. Start the mandatory working slice as soon as critical requirements/API restrictions are understood. Advisory market/reuse research runs alongside it. Keep independent writers in separate files/repos; preserve ordered stages on each feature.

## Answer or recover

Doctor reports `ready`, `blocked` or `not_checked` for each required/optional
capability. `--operation qualification` checks the local source context;
`--operation delivery` deliberately leaves GitHub capability unverified for the
authorized private broker. A free port is advisory until bind, not a lease.
Doctor neither removes locks nor installs tools. A Manager's escalated write
probe does not establish the receiver's effective permissions; run the explicit
probe from the receiver before its first write when permissions are uncertain.

Use the [bootstrap guide](bootstrap.md) for exact-run status/resume commands. Surface actual questions in chat; retain answers and completed prefixes. After resolving a recorded failure, use explicit `--retry-failed`.

Known **not-launched** failures can resume without recreating the project. An intent without a final outcome is different: inspect its owner/process and reconcile before retry. Doctor never repairs this ambiguity automatically. Do not rehash controls or copy a bound run into another root.

Optional Git-extension failures use the bounded, local [Git recovery procedure](git-setup.md); no force reinstall, repeated blind launch or global update. Manual/offline work remains available. Ordinary authorized commits need no per-stage approval.

## Deliver

1. Update the actual README/setup, native task list and near-final as-built/video notes. Keep one completion source; link supporting documents.
2. Adapt `docs/internal/qualification.json` to the **actual** install, tests and core/failure commands, review it and commit it with the candidate. Its default checks exercise the generic starter, not an application-specific scheduling journey.
3. Preview or execute the qualification helper:

```sh
PYTHONPATH=src python3 -m poc_template qualify --project ../my-poc
PYTHONPATH=src python3 -m poc_template qualify --project ../my-poc --execute
```

The helper exports the exact committed local revision into an owned disposable directory, creates its own virtual environment and runs the trusted profile's argv without a shell. Setup may install declared dependencies using the configured package index/cache. The helper itself requests no global-tool or source-checkout changes; executed project code must still be trusted. Uncommitted changes are excluded; commit repairs before qualifying them. Scratch files are removed after execution.

Profile v1 remains supported, without inferred coverage categories. V2 checks declare `kind`, `scenarios` (IDs), `mode` and boolean `required`. Kinds are `starter`, `product`, `service-integration`, `ui-static`, `browser`, `live-model`, `remote-clone`; optional `required_kinds` lists categories that must be present and pass. Reports bind the exact profile digest, Git commit and host/Python. A passing starter check never proves product/browser readiness; unexecuted categories remain `not_checked`.

Live-model and remote-clone checks are skipped unless separately selected with `--execute-kind live-model` or `--execute-kind remote-clone` alongside `--execute`. Required skipped/missing checks produce `incomplete`, not green. Selection is not credentials, spending or external-effect authority. Categories describe trusted developer declarations, not an OS sandbox or independent semantic verification; review all argv before execution. Ordinary fixtures must not be mislabeled to evade external-effect boundaries.

Use the [persona/story/test index](persona-story-test-index.md) and [transition suggestions](../../reference/testing/transition-scenarios.md) to expose actual adoption and missing scenario coverage without adding another progress ledger.

Profiles execute project code: they are reviewed developer configuration, **not safe untrusted intake**. A zero exit records command success, not semantic acceptance, clinical readiness, secret-free history or real API compatibility. A local export is not proof of GitHub/reviewer access. Qualify proposed submissions from their private remote on supported platforms as well.

4. Use coherent scoped commits and immutable milestone tags; push only under the current destination/privacy grant. Check [staged credential hygiene](security.md), preserving existing hooks. Perform one final review, then affected-only rereviews after fixes. The [optional adversarial report](reviews/adversarial-review.md) may reuse that review or be deferred to an Operator-selected follow-on; it is not another MVP gate. Prefer read-only Claude in observable tmux, Codex fallback, with sanitized findings/regressions and a named immutable review tag when performed. Do not repeat full setup at every commit; repeat when runtime/dependencies/setup or relevant flows change.

The human owns external effort-budget compliance and trade-offs. Agents report timing without silently stopping, shrinking requirements or replanning by elapsed time. Explicit pauses and operational tool timeouts still apply.
