# Success Pattern: first-principles — formal-grammar + structured-output reasoner (llama.cpp GBNF semantics, BNF expressive limits, SEA HybridResult contract surface)

## Strategy
Expert type "formal-grammar + structured-output reasoner (llama.cpp GBNF semantics, BNF expressive limits, SEA HybridResult contract surface)" for first-principles question.
Question: Can llama.cpp GBNF constrain SEA's full markdown+JSON HybridResult contract (markdown findings with tags + trailing JSON HybridResult block), or only the JSON portion? What grammar surface area does SEA's emission contract require?

## When It Works
- Question type: first-principles
- Converged in 1/3 iterations

## Evidence
- Dispatch: D6
- Question: LQ017
- Findings produced: 5
- Iterations: 1/3
- Status: answered

## Key Decisions
GBNF can constrain SEA's full HybridResult contract IF you want to (all 5 surviving layers are CFG-expressible — JSON is famously context-free), but layer 6 (finding array in JSON) collapses on code inspection: HybridResult JSON is metadata-only (counts + status + summary), not finding payload. Findings flow via inline epistemic-tagged prose and tool-call appends to findings.jsonl, OUTSIDE the GBNF-constrainable chat stream. Recommended minimum surface: JSON-Schema mode on the trailing fenced JSON block ONLY — both Ollama and llama.cpp can satisfy this (F975), so no architectural lock-in. The 7B tag-format failures from F968 (38-69pp) live in prose layer 2; constraining that layer risks F963 semantic-emptiness more than it gains tag-shape, so defer to post-emission regex repair before escalating. Empirical residue: delimiter-emission reliability under prompt-only discipline (LQ021), schema-feature support (LQ022), tag-failure syntactic-vs-semantic split (LQ023).