# Success Pattern: synthesis — local-LLM stack consolidation analyst with SEA-workload familiarity — produces structured trade-off matrices with verified-citation traceability

## Strategy
Expert type "local-LLM stack consolidation analyst with SEA-workload familiarity — produces structured trade-off matrices with verified-citation traceability" for synthesis question.
Question: Produce the final consolidated local-stack shortlist deliverable: a single document presenting the 2-4 viable end-to-end stacks (model + quantization + inference server + agent harness + web-search + ingestion + SEA provider-adapter scope) with side-by-side trade-off matrix, pros/cons per stack, quality-tolerance characterization vs Claude Opus baseline, risk register, and citations to verified findings — as specified in the project goal.

## When It Works
- Question type: synthesis
- Converged in 5/5 iterations

## Evidence
- Dispatch: D31
- Question: LQ047
- Findings produced: 12
- Iterations: 5/5
- Status: answered

## Key Decisions
LQ047 ANSWERED. Stage-5 Evaluator-pass executed: read output/lq047-final-shortlist.md end-to-end; applied persona §3 convergence checklist (all six items PASS) and §2 breakage-checklist (all five patterns PASS or PASS-conditional). Spot-checked 10 random F-id citations — 6 resolve as distinct findings, 4 are phantoms inherited from F434's inline citation narrative; broader audit surfaced 14 phantom F-ids total. Appended F990 (Evaluator outcome) and F991 (citation-integrity audit) to findings.jsonl, and appended Section 12 Stage-5 addendum to the deliverable documenting both caveats. Deliverable meets goal.md §v0-Test: 4 viable stacks (A, A′, B, C) with 6-layer composition, 7-axis trade-off matrix, per-stack pros/cons, quality-tolerance characterization vs Claude Opus baseline (IFEval + BFCL V4 with honest UNKNOWN on three specific gaps), 13-row risk register, 6-row empirical-gate register, and per-stack SEA provider-adapter LoC estimates.