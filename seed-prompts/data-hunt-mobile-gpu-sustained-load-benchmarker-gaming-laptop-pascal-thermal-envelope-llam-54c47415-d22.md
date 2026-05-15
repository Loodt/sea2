# Success Pattern: data-hunt — mobile-GPU sustained-load benchmarker (gaming-laptop Pascal thermal envelope + llama.cpp steady-state TG measurements)

## Strategy
Expert type "mobile-GPU sustained-load benchmarker (gaming-laptop Pascal thermal envelope + llama.cpp steady-state TG measurements)" for data-hunt question.
Question: Does GTX 1060 Mobile (80W TDP, GP106M) sustain within 0.7x of desktop GTX 1060 6GB (120W TDP) throughput under 30+ minute continuous llama.cpp load, or does thermal throttling drop steady-state TG below the 20 t/s viability bar?

## When It Works
- Question type: data-hunt
- Converged in 2/5 iterations

## Evidence
- Dispatch: D22
- Question: LQ015
- Findings produced: 13
- Iterations: 2/5
- Status: answered

## Key Decisions
LQ015 ANSWERED: GTX 1060 Mobile sustains TG within 0.93-0.99x of desktop GTX 1060 6GB under 30+ min continuous llama.cpp CUDA load, decisively clearing both the 0.7x hypothesis threshold and the 20 t/s viability bar. Physics chain: (a) sustained core-clock derate 6-33% across laptop cooling tiers (F1178), (b) GDDR5 memory clock thermally immune at rated 192 GB/s (F1179), (c) Pascal TG is 80-85% memory-bandwidth-bound, so core-clock derate translates to only 1-7% TG loss (F1180). Derivation confidence 0.8 — primary-source access to NotebookCheck remained 403-gated across both iterations, so the final verdict is DERIVED not MEASURED. 7B Q4_K_M remains the shortlist ceiling; no step-down to 3B required. One empirical-gate new question promoted for optional on-device confirmation.