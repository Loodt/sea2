# Success Pattern: design-space — solo-operator creative-workflow UX designer (AI-video agent checkpoint review, revision-injection API)

## Strategy
Expert type "solo-operator creative-workflow UX designer (AI-video agent checkpoint review, revision-injection API)" for design-space question.
Question: What does the operator see and do at each of the four Q003 checkpoints (CP1 post-storyboard, CP2 post-first-shot continuity-lock, CP3 post-rough-cut, CP4 pre-export), and what UI/API surface does the HERALD subagent expose for checkpoint review + revision injection?

## When It Works
- Question type: design-space
- Converged in 4/4 iterations

## Evidence
- Dispatch: D11
- Question: Q007
- Findings produced: 21
- Iterations: 4/4
- Status: answered

## Key Decisions
Q007 answered. Four patterns evaluated (A unified / B per-CP / C chat / D approve+reject-only); Pattern A eliminated as weight-dominated despite pareto-optimality — it wins no single dimension. Recommended: Phase-0 shared E1-E7 backend → Phase-1 Pattern D for fastest shippable loop → Phase-2 Pattern B per-CP specialised surfaces gated by reject-rate telemetry (CP3 first hypothesis) → Phase-3 optional Pattern C chat overlay only if HERALD call-volume >5%. Per-CP cells in F935 spec artifact/decisions/RIM/re-entry/blast-radius/HERALD-API for CP1-CP4. HERALD API surface is the same E1-E7 endpoints as human UI via strict API-UI symmetry enforced by the {patch|replace|annotate|branch} RIM taxonomy. Binding constraint: Phase-0 shared-backend discipline — without it, pattern overlay is not cheap. Three new questions surfaced (telemetry thresholds, CP4 send-back semantics, annotate mis-parse rate).