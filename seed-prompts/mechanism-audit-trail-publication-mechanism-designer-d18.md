# Success Pattern: mechanism — audit-trail publication mechanism designer

## Strategy
Expert type "audit-trail publication mechanism designer" for mechanism question.
Question: How should the existing lineage, metrics, and conductor/expert traces be consolidated into an emitted run-log artifact now so Goal 5 is met with a reproducible audit trail of question selection, expert recursion, findings integration, and publication-relevant decisions?

## When It Works
- Question type: mechanism
- Converged in 5/5 iterations

## Evidence
- Dispatch: D18
- Question: Q019
- Findings produced: 26
- Iterations: 5/5
- Status: answered

## Key Decisions
[DERIVED: F90133-F90135] The run log should emit per-dispatch bundles with six primary row kinds: selection, boundary, expert-iteration, integration, publication-decision, and lineage-closeout. [DERIVED: F90134-F90135] Each row only needs a thin normalized field set built from native IDs, timestamps, counters, metadata, and evidence refs, with deterministic phase/time tie-break rules that explicitly preserve zero-duration boundary rows, idempotent integrations, and lineage-as-closeout ordering. [DERIVED: F90136] Because the existing metrics, spans, lineage, question state, and markdown traces already reconstruct selection, recursion, integration, publication decisions, and closeout, Goal 5 can now be met without inventing a second decision schema or waiting on `deep_cuts.md`.