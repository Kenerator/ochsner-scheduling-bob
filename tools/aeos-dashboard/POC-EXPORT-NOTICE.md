# PoC Flight Deck export provenance and limits

This bundle derives from the nxus.SYSTEMS DevOps AEOS dashboard mechanism.
`export-manifest.json` records the original repository commit, whether the
selected source files were dirty, and SHA-256 digests of the actual copied bytes.
The manifest is a deterministic closure check, not a signature, license grant,
human approval, qualification result, release acceptance or publication authority.

The fixed export includes only standard-library Ruby common/PoC modules,
schemas, policy, templates, entrypoint and a synthetic consumer self-check.
It excludes SDK loaders/profiles/operating state, authentication helpers,
credentials, private intake, application transcripts and generated snapshots.
No third-party executable dependency or package is bundled. Ruby/Git retain
their own applicable terms; neither is redistributed here. No new license is
invented or substituted for the source/destination project's applicable terms.
Distribution remains subject to the existing approved destination and provenance
review; retain this notice and original source identity.

Checked native tasks establish implementation only. Verification and recorded
human decisions require applicable source-bound evidence. Decision coordinates
are references, not independently authenticated consent. Unknown, stale,
contradictory or dirty evidence cannot manufacture a pass. Generated output is
local and on demand; it does not start an app, retrieve a key, invoke a model,
dispatch work, refresh from a network service or advance any release gate.

Consumer commands require the export manifest and reject symlinked runtimes or
resources differing from the process-loaded implementation. The explicitly named
maintainer/unbundled option does not imply export closure or distribution review.
Six-file edit detection uses `index-footer-v1`: the HTML footer hashes the complete
snapshot, and the snapshot hashes Markdown and the HTML body excluding that footer.
This detects local edits but is not a signature or proof of authenticity.
