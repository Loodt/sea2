# Success Pattern: data-hunt — video-model benchmarking analyst specialising in T2V/I2V quality-vs-cost normalization across Veo, Runway, Kling and Seedance tiers

## Strategy
Expert type "video-model benchmarking analyst specialising in T2V/I2V quality-vs-cost normalization across Veo, Runway, Kling and Seedance tiers" for data-hunt question.
Question: What is the empirical cost/quality tradeoff for brand-safe vs flagship T2V+I2V output on matched prompts (Veo 3.1 Standard vs Fast vs Lite; Runway Gen-4.5 vs Gen-4 Turbo; Kling 3.0 vs Seedance v1.5), and at what draft-iteration count does Lite/Turbo become the correct default?

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D7
- Question: Q005
- Findings produced: 17
- Iterations: 3/5
- Status: answered

## Key Decisions
Q005 answered in three stages. Stage 1 surfaced A.A. leaderboard and flagged version-slippage (Seedance v1.5 vs 2.0). Stage 2 verified tier-granularity: A.A. ranks Veo Fast/Standard and Kling/Seedance variants, but NOT Veo Lite or Gen-4 Turbo — forcing practitioner writeups for those deltas. Stage 3 closed crossover math: naive cost break-even is N=2 for all pairs (trivially, whenever cheap tier is strictly cheaper); quality-transfer-adjusted crossover is N=2 high-confidence for Veo Fast and N=2 medium-confidence for Gen-4 Turbo, with 5-10 draft practitioner convention delivering 60-70% savings. Veo Lite remains structurally gated to mobile-viewport destinations due to [UNKNOWN] blind-benchmark quality. Seedance v1.5 scope-corrected to Seedance 2.0 (v1.5 is −73 Elo below Kling 3.0 Pro — deprecated as cheap tier). Two deferrable empirical gates left for HERALD's internal A/B (Lite and Turbo rank-transfer error rates).