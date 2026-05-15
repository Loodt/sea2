# Success Pattern: first-principles — editorial-workflow threshold reasoner (diff-driven revision loop calibration; sets defensible numeric gates from architectural constraints + published content-production benchmarks)

## Strategy
Expert type "editorial-workflow threshold reasoner (diff-driven revision loop calibration; sets defensible numeric gates from architectural constraints + published content-production benchmarks)" for first-principles question.
Question: What CP3 reject-rate and revision-cycles-to-approve targets define the Phase-1→Phase-2 D→B switch-trigger T1? Must be set before Phase-1 ships to avoid arbitrary triggers.

## When It Works
- Question type: first-principles
- Converged in 2/3 iterations

## Evidence
- Dispatch: D14
- Question: Q021
- Findings produced: 8
- Iterations: 2/3
- Status: answered

## Key Decisions
Q021 answered. T1 = rolling N=40 CP3 dispatches, trip-in at p* ≥ 0.42 OR median C* ≥ 1.7 (joint-OR), upper kill-ceiling at p > 0.60 (generator-replacement branch), one-shot fire (no hysteresis — additive switch per F361/F365), with rebaseline rule after 20 Phase-1 dispatches eliminating arbitrariness. Iter-2 revised iter-1's N=20 placeholder via power analysis (N=20 only 50% power vs 74% at N=40, and rolling-window dwell-2 doesn't recover power due to rho≈0.95 correlation). Web-search validated bucket-B (25-40% AI-content edit rate confirms p0=0.30) and supplied the 0.60 upper kill-ceiling as a kill signal that Pattern-B can't fix tool-mismatch. Hard precondition: F943 InvalidationEvent telemetry must ship with Phase-1.