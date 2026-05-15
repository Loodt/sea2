# seed-prompts/

330 named domain-expert prompts copied verbatim from `sea/success-patterns/`.
These are *not* loaded by any Phase 1 code path — they are Phase 2 input
material for the planner / extractor / verifier role prompts.

The "success-patterns" framing in SEA was misleading: most are role personas
(e.g. `data-hunt-bfcl-benchmark-data-analyst-…`), not patterns. Renaming to
`seed-prompts/` removes that confusion.

When Phase 2 begins building the planner and the extractor/verifier prompt
templates, this directory is the source pool. Phase 2 will define how each
prompt is selected, parameterized, and validated.
