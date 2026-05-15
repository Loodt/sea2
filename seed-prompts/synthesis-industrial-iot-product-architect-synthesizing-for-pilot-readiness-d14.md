# Success Pattern: synthesis — industrial-IoT product architect synthesizing for pilot-readiness

## Strategy
Expert type "industrial-IoT product architect synthesizing for pilot-readiness" for synthesis question.
Question: Consolidate verified findings on energy budgets (F020-F022, F1024, F1132, F1133), wireless architecture (F031, F032, F046, F946), competitive wedge (F970-F976), BOM/COGS (F073, F078), show-stopper risks + mitigations (F088, F089), phased pilot plan (F924, F925), thermal-stack design (F1126-F1128, F1132), and CT-installation constraints (F1024) into an integrated MVP SKU specification: per-SKU sensor class + harvester + radio + mounting stack, deployment workflow with permit/MOC touchpoints, BOM-cost envelope per SKU, and the residual decision-relevant gaps that must close before pilot commit. Output must net-reduce open questions by retiring those whose answers are now derivable from the consolidated picture, and surface only gaps that are genuinely empirical (not synthesizable from store).

## When It Works
- Question type: synthesis
- Converged in 5/5 iterations

## Evidence
- Dispatch: D14
- Question: Q017
- Findings produced: 14
- Iterations: 5/5
- Status: answered

## Key Decisions
Q017 answered: the integrated MVP SKU specification is a 3-SKU architecture with two pilot waves and exactly three orthogonal residual empirical gates. SKU-1 (vibration-roll, primary-cell pilot variant, walk-and-stick), SKU-2 (thermal-roll, foam-hat overpatch, walk-and-stick) and SKU-3 (current-monitor, non-roll, electrician-touch with PTW per F1024) cleanly resolve the cost-envelope x install-friction partitioning. Wave-1 (SKU-3 + SKU-2a roll-with-primary-cell) is empirically pilot-ready today subject to F020 bench replication and Q016; Wave-2 (self-powered roll variants) is gated on Q012 vendor RFQ. Q018 retires into Q016 because the foam-hat geometry choice is empirically downstream of measured (R_contact, t63), not an independent design decision. Open count net-reduces 5 -> 3 (Q012, Q015, Q016 — all genuinely empirical: vendor-evidence, document-discovery, bench-measurement).