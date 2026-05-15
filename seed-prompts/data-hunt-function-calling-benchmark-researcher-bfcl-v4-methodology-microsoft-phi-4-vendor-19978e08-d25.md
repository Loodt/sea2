# Success Pattern: data-hunt — function-calling benchmark researcher (BFCL V4 methodology + Microsoft Phi-4 vendor-reported scores)

## Strategy
Expert type "function-calling benchmark researcher (BFCL V4 methodology + Microsoft Phi-4 vendor-reported scores)" for data-hunt question.
Question: What is the Phi-4-14B BFCL V4 absolute score? Berkeley leaderboard is JS-rendered un-fetchable; closeable via Phi-4 vendor page or BFCL V4 paper arxiv:2GmDdhBdDk. Closing this gap upgrades Stack-B verdict from AMBER-leaning-RED on instruction-following to a fully-quantified two-axis matrix.

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D25
- Question: LQ039
- Findings produced: 8
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ039 closed in 3 iters. Phi-4-14B BFCL V4 Overall = 28.79% (rank ~70, 2025-12-16). Vendor-side paths (tech-report, HF card) were ruled out iter-2 as null on BFCL. Iter-3 drilled the HuanzhiMao/BFCL-Result GitHub archive (date-indexed, not model-indexed) → latest date dir → score/data_overall.csv. Per-category breakdown reveals bimodal profile: static AST competent (Non-Live 69.56 / Live 60.70) but agentic categories collapse (Multi-Turn 3.88 / Web Search 4.50 / Memory 24.73) — V4 aggregate dragged down by V4-new categories. Upgrades Stack-B verdict from 'AMBER-leaning-RED' to a conditional: viable for single-turn tool-calling, non-viable for agentic workloads.