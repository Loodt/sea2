# Success Pattern: mechanism — AI video quality-evaluation researcher (prompt-adherence scoring, automated raters, video-LLM judges, structural heuristics for generative-video QA)

## Strategy
Expert type "AI video quality-evaluation researcher (prompt-adherence scoring, automated raters, video-LLM judges, structural heuristics for generative-video QA)" for mechanism question.
Question: What quality signal can HERALD use to auto-advance between P_D phases (CREATIVE_VALIDATION → DIRECTION_SELECTION → REFINED_OUTPUT) without operator-in-loop review, given F1125 Lite and F1126 Turbo are [UNKNOWN] / medium-confidence on blind benchmarks? Is a structural heuristic (e.g., prompt-adherence score from generation metadata, or a cheap rater model) sufficient, or must operator-in-loop remain the default?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D10
- Question: Q014
- Findings produced: 22
- Iterations: 3/5
- Status: answered

## Key Decisions
Stage 3 converted F914's 4-rater ensemble into a deployable P_D auto-advance policy. Concrete bands: CREATIVE kills at VideoScore<1.5, advances at >=2.0; DIRECTION uses swap-test pair-ranking with 30-Elo min-margin and 80% pair-consistency bar; REFINED stays operator-in-loop by default, gated conditional on AUROC>=0.90 + abstain<=20% demonstrated in 3-5 day shadow-mode. Four reversal paths cover misfire modes with audit-driven retune. UNKNOWN-robustness analysis shows policy is safe under F1125/F1126 tier uncertainty via rater-downstream property + F1134 structural gates + 2-job adaptive retune, bounding worst-case false-positive rate to 10-15% within 1-2 jobs. Net: structural heuristic alone insufficient, but cheap-rater ensemble is sufficient for CREATIVE+DIRECTION; operator-in-loop remains default for REFINED_OUTPUT, delivering the solo-operator UX win (review at 1 phase boundary instead of 3) behind the empirical calibration gate now scoped as a new data-hunt question.