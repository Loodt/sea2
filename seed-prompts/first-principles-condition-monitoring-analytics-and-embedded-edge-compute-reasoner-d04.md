# Success Pattern: first-principles — condition-monitoring analytics and embedded edge-compute reasoner

## Strategy
Expert type "condition-monitoring analytics and embedded edge-compute reasoner" for first-principles question.
Question: What minimum viable analytics set per sensor class delivers enough maintenance value within the available energy and bandwidth budget, especially for the most promising first wedge asset class?

## When It Works
- Question type: first-principles
- Converged in 2/3 iterations

## Evidence
- Dispatch: D4
- Question: Q004
- Findings produced: 7
- Iterations: 2/3
- Status: answered

## Key Decisions
I continued from the prior narrowed result rather than restarting, using the existing spine from F912, F930, F943, F946, F948, and F949. The derivation now closes the fault-to-feature map for the slurry-service pump/motor wedge: temperature is required for thermal distress, and compact vibration is required for the dominant non-thermal rotating faults. I pruned the vibration payload to the smallest transmitted pair that still changes maintenance action relative to temperature-only, which is v-RMS plus one impulsiveness metric; crest factor is the lightest surviving transmitted choice, while a-RMS or a-Peak can remain optional edge helpers. I also killed routine FFT-peak transmission from MVP scope because it adds interpretability more than essential first-wedge screening value under the known energy, compute, and robustness constraints.