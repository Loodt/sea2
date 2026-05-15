# Success Pattern: first-principles — uranium project-economics reasoner

## Strategy
Expert type "uranium project-economics reasoner" for first-principles question.
Question: Given the current flowsheet and verified co-mineral inventory, what explicit grade, recovery, price, regulatory, and circuit-integration thresholds must be met for uranium to become the first co-mineral that crosses the project's 5-year commercial-viability threshold?

## When It Works
- Question type: first-principles
- Converged in 2/3 iterations

## Evidence
- Dispatch: D27
- Question: Q025
- Findings produced: 6
- Iterations: 2/3
- Status: answered

## Key Decisions
I continued from the prior iteration rather than restarting. The derivation is now tightened in the two places that were still loose: the saleable-product-path threshold is explicit through `y_U,min` and `F_U,max`, and the integration gate is translated into one admissible uranium insertion family versus a killed standalone case. The answer is that uranium can be the first co-mineral crossover only if it clears the grade, recovery, price, payable, regulatory, and integration inequalities together, with the decisive integration constraint being an off-line post-gold solids add-on that preserves the current quaternary-first gold/ZLD architecture and keeps the host circuit at `f >= 0.80`. Under the present store, uranium remains the leading candidate but has not yet been shown to meet those thresholds in practice; that is a later proof question, not a remaining ambiguity about what the thresholds are.