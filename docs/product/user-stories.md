# User Stories — draft and index

Stage 0 background, not approved scope or completion evidence. Supplied stories, journeys and scenarios remain verbatim in intake. These seeds do not assert that intake lacks stories; reconcile it first during native Specify.

**Origin** (specified/inferred) is separate from **scope** (proposed/accepted/deferred). Inferred story wording can describe an explicitly required capability; preserve that requirement. Acceptance of an inference does not change its origin. Persona labels and drafts grant no permissions.

## Supplied sources

- [Intake 1](intake/001.md)
- [Intake 2](intake/002.md)
- [Intake 3](intake/003.md)
- [Intake 4](intake/004.md)
- [Intake 5](intake/005.md)
- [Intake 6](intake/006.md)
- [Intake 7](intake/007.md)
- [Intake 8](intake/008.md)
- [Intake 9](intake/009.md)
- [Intake 10](intake/010.md)
- [Intake 11](intake/011.md)
- [Intake 12](intake/012.md)
- [Intake 13](intake/013.md)
- [Intake 14](RFP/README.md)

## Native specification index

After Specify, link the feature `spec.md` User Scenarios & Testing sections here. Move reconciled draft detail into those native stories and replace it here with links, retaining Persona pins and origin/source labels there. Native `tasks.md` tracks implementation; this is not another progress ledger.

## Provisional seeds

### DRAFT-01 — Jules

- **Persona:** Jules · poc-template-seed-v1:56e6af21-d1e4-4698-8485-83a341d77031@1 · actor type: human ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Jules, I want to Find and explicitly confirm a mock appointment, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given A clear scheduling request; When A provider and slot are selected; Then Show exact proposal without booking until explicit confirmation.

### DRAFT-02 — Billy-June

- **Persona:** Billy-June · poc-template-seed-v1:0de53f87-1856-40ac-84fe-ec4d890e3770@1 · actor type: human ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Billy-June, I want to Coordinate convenient continuity of appointments, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given Stated location and time constraints; When Available options are shown or a constraint changes; Then Honor supported constraints or explain no match; invalidate old proposal.

### DRAFT-03 — Amy-Lou

- **Persona:** Amy-Lou · poc-template-seed-v1:aae4b004-4bbf-4ac5-b532-2d7af776e168@1 · actor type: human ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Amy-Lou, I want to Complete a scheduling journey with help when needed, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given Email is unavailable; When Contact information is discussed; Then Do not demand email; explain limitation and prepare truthful assistance.

### DRAFT-04 — Ellie-Rae

- **Persona:** Ellie-Rae · poc-template-seed-v1:cb706720-85fb-42ef-9318-2bcec4c2b621@1 · actor type: human ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Ellie-Rae, I want to Select and confirm with minimal input, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given Numbered options are visible; When One number or an invalid choice is entered; Then Select one with a number; invalid input preserves context; keyboard flow works.

### DRAFT-05 — Nina-Jean

- **Persona:** Nina-Jean · poc-template-seed-v1:5d4d7083-1479-4637-90cd-5e841bfe080d@1 · actor type: human ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Nina-Jean, I want to Understand choices and correct preferences, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given An ambiguous request; When Clarification or a corrected preference is supplied; Then Ask one useful scheduling question; visibly update and invalidate old proposal.

### DRAFT-06 — Morgan-Rae

- **Persona:** Morgan-Rae · poc-template-seed-v1:657aedfe-4a4a-4ec4-83c0-52614111f07c@1 · actor type: human ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Morgan-Rae, I want to Understand request and unresolved work without repetition, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given A handoff request is prepared; When Support summary is presented; Then Separate known facts, missing information and booking outcome; no false delivery.

### DRAFT-07 — Sam-Rae

- **Persona:** Sam-Rae · poc-template-seed-v1:98e1dcd5-8ee9-4b2b-b7fe-2045d389b9b4@1 · actor type: agent ([card](personas.md)).
- **Origin:** INFERRED from the selected Persona; not specified product scope.
- **Scope:** proposed; priority and benefit need input reconciliation.
- **Story seed:** As Sam-Rae, I want to Expose unsafe confirmations and recovery, so I can achieve this outcome within my documented constraints.
- **Acceptance seed:** Given A stale yes, injected fixture or unknown outcome; When An evaluation attempts replay or retry; Then Do not create a booking or unsafe retry; show truthful state.

## Support/Admin coverage

Persona mapping: Morgan-Rae (poc-template-seed-v1:657aedfe-4a4a-4ec4-83c0-52614111f07c@1). See the corresponding seeds above.

- **Origin:** INFERRED generic teammate need; scope proposed, not a required admin UI.
- **Story seed:** As the mapped support/admin teammate, I want accurate outcome and recovery context, so I can help without making the user repeat work or taking unsafe action.
- **Acceptance seed:** Given an unresolved case; When a permitted summary or diagnostic is inspected; Then known facts, missing information, attempted/completed/unknown outcomes and a truthful next step are distinguishable, with sensitive data excluded as required.

Always retain this coverage or an explicit documented deferral. It may be served by existing help, diagnostics or documentation; do not silently add a console, authentication, live handoff or new permissions. Validate against actual policy and interfaces.
