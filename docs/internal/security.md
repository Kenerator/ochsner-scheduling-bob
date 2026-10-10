# Basic credential hygiene

## BOB public-source settings readback — 2026-10-10

Current exact repository: [Kenerator/ochsner-scheduling-bob](https://github.com/Kenerator/ochsner-scheduling-bob).
Operator-approved public visibility was applied after source/docs/content checks;
the application remains internal-use with no public deployment or external video
publication. Raw intake, runtime credentials, journals, capabilities and the model
ledger remain excluded. No root license was selected or third-party ownership changed.

The Operator's later ownership correction on 2026-10-10 transferred this same
repository from `nxus-SYSTEMS` to `Kenerator`: ID `1412468983`, node
`R_kgDOVDCQ9w`, public visibility and all 11 advertised refs were preserved.
Main at transfer was `ac78af3bb2e39ae6ba02995f666dc89f63bfbb4e`; RC-1 and all
older tag objects/peeled targets, plus PR #1's head/merge state, matched the
pre-transfer snapshot. The old web URL returns HTTP 301 to the current URL.
Local origin uses the verified existing `kenerator-github.com` SSH alias and
canonical Kenerator owner. No repository was copied, recreated or deleted.

The broker PAT's first transfer request returned HTTP 403 despite metadata
showing administration. After an explicitly reviewed credential-path decision,
the already-configured Kenerator keyring login was verified as user ID `95498894`
with `repo` scope and exact-source administration; its one normal transfer
request succeeded. No raw token was printed, manually retrieved, exported or replaced; no
authentication switch, login, Bitwarden mutation or global configuration change
occurred. This resolved a server-token capability mismatch, not a safety denial;
the broker credential itself was not repaired.

Transfer readback found secret scanning and push protection disabled. Only those
two previously enabled fields were restored, then the full baseline below passed
readback at the new owner with the same ruleset IDs and no bypass. PR #1 remained
merged at its original commit. Existing history/owner facts below describe their
original checkpoints, while current canonical links use Kenerator. Application
source, tests, media files and immutable tags were not changed for this correction.

Fresh authenticated REST readback verified:

- Public repository, default `main`, Pages off, auto-merge off, merged-topic-branch deletion on; existing merge methods retained.
- Active `main-integrity` ruleset **24834842**: deletion and non-fast-forward restrictions on `refs/heads/main`.
- Active `main-pull-request` **24834844**: PR plus resolved conversations, zero mandatory approvals, no code-owner/last-pusher requirement and no invented required CI contexts.
- Active `all-tags-integrity` **24834848**: update/deletion restrictions for all tags; tag creation remains allowed. All three rulesets have empty bypass lists. Future main updates use normal PRs, not direct pushes or administrative bypass.
- Secret scanning and repository push protection enabled; Dependabot alerts enabled (successful alerts-status endpoint), security updates enabled/not paused.
- Actions enablement retained, GitHub-authored actions only, full-SHA pinning required, read-only workflow tokens, workflow PR approval disabled and approval required for all external fork contributors.

The external-fork endpoint initially returned HTTP 422 because GitHub disallows
this policy on private repositories. After the approved public transition, its
normal configuration/readback succeeded; no alternate credential or safeguard
bypass was used. Visibility/settings work preserved main and every annotated tag
object/peeled target, including RC-1 (`ca101e7ce6bfeb2768d7a78f6327049e850f6e22`
→ `e2dfa7e9f471513921063d568bb3bc890eff1800`). Main at that readback was the
reviewed docs/assets checkpoint `980b882c936dcc23e43c2b11d7ede297ac0a9ca1`;
this later readback record follows the required PR workflow.

Scope/limits: settings verified by REST, not destructive force-push/tag-deletion
experiments. No original-four-PoC settings/source, collaborators, global auth,
plan subscription, application workflow or deployment changed. Administrators
can still edit rules; tags are not cryptographically immutable. Whole-index and
historical-tree pattern scans are documented in [native tasks](../../specs/001-ochsner-scheduling-assistant/tasks.md),
not secret-free/history/PHI/vulnerability-free certification. The prior guard
documentation below remains its exact implementation/limitations contract.

Reviewed: **2026-10-07**. No added dependency, global Git setting or online scan.

BOB project override reviewed 2026-10-09: `.gitignore` excludes the entire
`docs/product/intake/` tree plus the RFP source/manifest and `.bob-local/`.
The generic template paragraph below describes tracked-capable intake defaults,
not this BOB's stricter rule. Derived native specs/docs and approved synthetic
vendor assets still require review and whole-index scanning before commit.

Fresh Git-enabled scaffolds install a local pre-commit guard. It checks the **whole staged index**, including intake/docs and existing tracked files—not just changed lines or the working copy. Partial staging and Git's temporary commit index are respected. Recognizable tokens, private-key headers, likely literal credential assignments and force-added credential files block the commit. Findings report **path, line and rule only**, never suspected values.

```sh
# Run with a verified Python 3.11+ interpreter:
PYTHONPATH=src python3 -m poc_template secrets scan --project .
# For a generated project or clone with the bundled scanner (hooks aren't cloned):
PYTHONPATH=src python3 -m poc_template secrets install --project .
```

Exit **0** means no unresolved match in the checked index; **1** means findings; **2** means incomplete/error. The hook prefers `POC_PYTHON`, then `.venv/bin/python`, then a compatible Python on PATH. For a tool interpreter outside PATH, use `POC_PYTHON=/absolute/path/to/python git commit ...`; do not replace system Python. Installation is idempotent for this exact guard. An existing hook, symlinked hook directory or `core.hooksPath` is preserved; bootstrap warns and continues, while explicit install reports the conflict. Integrate the scan into your existing hook or run it explicitly—do not overwrite another safeguard.

`.gitignore` keeps common environments, credential files, keys and private-local folders out of ordinary staging; it does **not** protect already-tracked or force-added files.[^ignore] `.gitattributes` normalizes text and scripts to predictable line endings. Keep confidential intake/notes outside Git or in the ignored `docs/product/intake/private/` and `docs/internal/private/` folders. These are manual private-local locations, not automatic routing of `--input`: normal intake is copied into tracked-capable product documents. Do not pass private data to bootstrap expecting it to be anonymized. Private GitHub visibility is not protection against later publication of its history.

## False positives

Prefer environment references or obvious placeholders in examples. For a **reviewed nonsecret fixture**, add a narrow entry to `.poc-secret-allowlist.json` and stage it alongside that exact file:

```json
{"allow": [{"path": "tests/fixture.txt", "rule": "github-token", "sha256": "REPLACE_WITH_64_CHARACTER_SHA256_OF_EXACT_STAGED_BLOB", "reason": "Synthetic nonworking scanner fixture"}]}
```

Compute the digest without printing the content, using the staged blob, not its working copy:

```sh
git show :tests/fixture.txt | python3 -c 'import hashlib,sys; print(hashlib.sha256(sys.stdin.buffer.read()).hexdigest())'
```

Exact path + rule + blob digest + explanation are required; any byte change invalidates the exception. Unstaged exceptions have no effect. No wildcard directory exclusions or automatic waiver creation. Never allow a real credential; remove it from staging and revoke/rotate it if already exposed.

## Limits and optional stronger tooling

This is a small pattern guard, **not** a secret-free/history/PHI/confidentiality certification. It can miss arbitrary opaque passwords, computed/encoded values and unsupported formats. It scans bounded binary bytes for recognizable text too, but does not decode archives/images; symlink targets and submodule contents are not followed and their counts are reported. Blobs over 16 MiB or unresolved merges produce an explicit incomplete result. Hooks can be bypassed; review staged changes and public-sharing rights independently. Existing Git history and external logs need separate attention when sharing.

For a larger project, optionally qualify [Gitleaks](https://github.com/gitleaks/gitleaks) for local history/CI scanning with redacted reports. Pin a reviewed version and keep CI scopes/permissions appropriate; it is not installed or required here. Review current maintenance/tool alternatives when adopting. GitHub push protection is an additional repository setting, not an assumed safeguard on every private repo.[^push]

[^ignore]: [Git: gitignore](https://git-scm.com/docs/gitignore). Reviewed 2026-10-07; ignore rules do not affect already-tracked files.
[^push]: [GitHub: push protection](https://docs.github.com/en/code-security/concepts/secret-security/push-protection). Reviewed 2026-10-07; repository coverage/configuration must be verified.
