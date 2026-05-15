# Success Pattern: mechanism — LinkedIn recommender-pipeline causal analyst (GR sequential architecture + AI-content classifier layer tracing)

## Strategy
Expert type "LinkedIn recommender-pipeline causal analyst (GR sequential architecture + AI-content classifier layer tracing)" for mechanism question.
Question: What is the causal chain from F3002 vocabulary substitution through GR ranker signals to save rate? Specifically: given (a) GR's sequential/token-level architecture, (b) profile-content alignment scoring, and (c) the 'AI-generated content without substantial rewriting is detected and down-ranked' finding, does banned-vocab swapping change detection outcome, or only hide a surface symptom while leaving structural slop detectable? What layer of LinkedIn's pipeline (embedding, sequence model, classifier, reviewer) actually gates the penalty?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D13
- Question: QQ014
- Findings produced: 15
- Iterations: 3/5
- Status: answered

## Key Decisions
QQ014 answered. F3002 vocabulary substitution is predominantly symptom-hiding at strict layer-gating view (NO-AFFECT at L2 embedder / L3 retrieval / L6 policy / L7 diversity) but has one architecturally-supported INDIRECT mechanism path via L5 engagement-flywheel: LinkedIn Engineering's dwell-time post confirms P(skip) and Auto Normalized Long Dwell are measured reader-behavior signals feeding 360Brew's multi-task ranker — so F3002 can move save-rate if readers perceive the synonym swaps. L4a SVM remains UNKNOWN direct-mechanism candidate contingent on undisclosed feature family. The original binary framing ('symptom-hiding OR mechanism-fix') splits by architecture into three paths; C-prime's mandatory F3002 decision is justified as reader-experience optimization cycling back into GR via dwell telemetry. F9127 specifies a three-segment F9107 discriminator test (f3002-only vs untouched vs co-triggered) for calibration week 4 decision.