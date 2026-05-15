# Success Pattern: first-principles — axiom-driven failure-mode reasoner for recommender-system content pipelines

## Strategy
Expert type "axiom-driven failure-mode reasoner for recommender-system content pipelines" for first-principles question.
Question: Given verified findings on save-weight (F002), profile-content alignment (F964-F967), GR architecture (F001, F948-F955), and the human-review gate (F989-F990), derive the axiom-level failure modes for the C-prime architecture (flag-only F3003 + auto-swap F3002 + reviewer override) that are predictable without calibration. Produce 3-5 failure signatures with: premise chain from verified findings, symptom each produces in the telemetry schema (F9107), and proposed pre-calibration mitigation.

## When It Works
- Question type: first-principles
- Converged in 3/3 iterations

## Evidence
- Dispatch: D14
- Question: QQ015
- Findings produced: 11
- Iterations: 3/3
- Status: answered

## Key Decisions
Answered. Derived 6 independent axiom-level failure signatures for C-prime (F9129 Profile-Swap Collision, F9130 Measurement Drift, F9131 Silent-Success Hole, F9132 Reviewer-Override Loop, F9133 Morphological Coverage Gap, F9134 Rubric Diagnostic Opacity) each with premise chain to verified findings, F9107-field symptom, and pre-calibration architectural mitigation. Count-6 exceeds question's 3-5 target; iter-2 stress-test found the rubric→reviewer seam (F9134) mechanistically independent of the other 5, and suppressing valid axiom-level failures to hit a count would degrade the answer. Iter-3 mitigation audit passed all 6 under persona rule; two invented-number sub-guards (F9132 entropy, F9133(c) accelerated trigger) explicitly downgraded to [DEFERRED]. DAG internally consistent — symptoms partition cleanly on F9107 fields.