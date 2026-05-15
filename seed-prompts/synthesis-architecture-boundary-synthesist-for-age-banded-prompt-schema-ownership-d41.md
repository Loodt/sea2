# Success Pattern: synthesis — architecture-boundary synthesist for age-banded prompt/schema ownership

## Strategy
Expert type "architecture-boundary synthesist for age-banded prompt/schema ownership" for synthesis question.
Question: Age-band stanza variant authoring — F2019 invariants vs variants are specified at principle level; the concrete sub-stanza wording for each age (3/7/9) inside each L1-L4 RULES.md stanza has not been drafted. Who authors these — conductor (architecture) or downstream jarvis-personas project (expert prompts)?

## When It Works
- Question type: synthesis
- Converged in 2/5 iterations

## Evidence
- Dispatch: D41
- Question: JQ081
- Findings produced: 6
- Iterations: 2/5
- Status: answered

## Key Decisions
[DERIVED: F90192/F90193] Stage 2 closed the only remaining uncertainty by decomposing L1-L4 into invariant predicates versus age-band realization slots. [DERIVED: F90192] The critic/enforcement layer checks rule-level properties such as turn shape, scaffolding discipline, repair order, and attention limits, not exact prose, so the concrete 3/7/9 sub-stanza wording is not the integrity mechanism. [DERIVED: F90193] Therefore conductor owns the schema for each age-band slot and its must-hold acceptance criteria, while downstream `jarvis-personas` authors the actual Afrikaans or bilingual wording that instantiates those slots. [SOURCE: https://platform.claude.com/docs/en/build-with-claude/prompt-engineering/claude-prompting-best-practices] External prompt guidance is consistent with this split because stable instructions belong in the contract layer and concrete examples/tone steering belong in prompt authoring.