# Success Pattern: design-space — SA fund-structuring + cross-border tax architect (FSCA CIS regime, SARB exchange-control, Mauritius/Jersey/Guernsey/IOM PCC comparator, SA corporate-tax + dividend WH + DTA overlay)

## Strategy
Expert type "SA fund-structuring + cross-border tax architect (FSCA CIS regime, SARB exchange-control, Mauritius/Jersey/Guernsey/IOM PCC comparator, SA corporate-tax + dividend WH + DTA overlay)" for design-space question.
Question: Which SPV architecture is optimal for Au-Token: (a) single SPV per TSF (one Pty Ltd / private co per dam); (b) master fund of SPVs (umbrella CIS or partnership that invests across multiple per-TSF SPVs); (c) protected cell company (PCC / incorporated cell in a cell-friendly jurisdiction — Mauritius, Jersey, Guernsey, Isle of Man — with SA operating subsidiaries); (d) hybrid (SA Pty Ltd per-TSF SPV held under an offshore cell company)? Design-space axes: ring-fencing strength (bankruptcy-remote, creditor-isolation); tax efficiency (SA corporate tax + MPRRA + dividend wh + DTA overlay); investor governance (voting granularity per-TSF vs pooled); capital-raising flexibility (can new tranches be issued without re-papering the whole structure); SARB exchange-control treatment; regulatory fit with FSCA CIS regime vs private-fund regime. Build a decision matrix with a scored recommendation.

## When It Works
- Question type: design-space
- Converged in 3/4 iterations

## Evidence
- Dispatch: D4
- Question: AUQ009
- Findings produced: 14
- Iterations: 3/4
- Status: answered

## Key Decisions
AUQ009 answered: option (a) single SA Pty Ltd per TSF dominates with composite 4.60 > (d) 3.50 > (b) 2.85 > (c) 2.45. The 1.10-point gap to runner-up (d) is decisive (22% margin), exceeding ordinal-scoring variance, and rank-order is stable across all sensitivity tests (investor-mix from 100% SA-resident to 100% non-resident, AUM scale to >R500m, DTA PPT outcome, CFC trigger, weight re-assignment). Pre-architected migration hooks (F928) convert the 'add a cell later' 10x-cost failure-mode into a 3x controlled migration with positive NPV even at 50% Phase-2 probability. Pilot go-live footprint: three per-TSF Pty Ltd SPVs, debenture-interest tokens, Platform Co holds CASP+FSP+FIC, zero cross-border regulator. Phase-2 (option d) triggers defined; Phase-3 (option b) gated at AUM >R1bn; option (c) not on roadmap.