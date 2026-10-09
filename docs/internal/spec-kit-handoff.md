# Remaining Spec-Kit stages

Generated handoff, not completion evidence. Run from this project's root. Use stages in order; both installed integrations share the local feature files. You may switch assistant for each stage. Do not run competing sessions on the same feature.

The blocks use codex syntax. Claude uses `/speckit-STAGE`; Codex uses `$speckit-STAGE`. Change only the first-line prefix when switching assistant, or regenerate with `poc-template bootstrap prompts --project . --integration claude` (or `codex`).

Manual stage execution does not update the automated workflow's completion state. Before manual continuation, stop/reconcile any live automated owner. Resolve any reported failure or pending question; these prompts do not bypass it. Let installed Spec-Kit handle its normal prerequisites, clarifications and Constitution checks.

## Stage 1: Specify

Codex: `$speckit-specify` · Claude: `/speckit-specify`

```text
$speckit-specify
Create the feature described in docs/product/intake/001.md, docs/product/intake/002.md, docs/product/intake/003.md, docs/product/intake/004.md, docs/product/intake/005.md, docs/product/intake/006.md, docs/product/intake/007.md, docs/product/intake/008.md, docs/product/intake/009.md, docs/product/intake/010.md, docs/product/intake/011.md, docs/product/intake/012.md, docs/product/intake/013.md, docs/product/RFP/README.md.
Background draft User Stories and Persona mappings: docs/product/user-stories.md. Reconcile with supplied intake.
Selected Persona constraints: docs/product/personas.md.
```

## Stage 2: Clarify

Codex: `$speckit-clarify` · Claude: `/speckit-clarify`

```text
$speckit-clarify
```

## Stage 3: Plan

Codex: `$speckit-plan` · Claude: `/speckit-plan`

```text
$speckit-plan
```

## Stage 4: Tasks

Codex: `$speckit-tasks` · Claude: `/speckit-tasks`

```text
$speckit-tasks
```

## Stage 5: Analyze

Codex: `$speckit-analyze` · Claude: `/speckit-analyze`

```text
$speckit-analyze
```

## Stage 6: Implement

Codex: `$speckit-implement` · Claude: `/speckit-implement`

```text
$speckit-implement
```
