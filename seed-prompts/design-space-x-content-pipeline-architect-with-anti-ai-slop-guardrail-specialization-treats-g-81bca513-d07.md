# Success Pattern: design-space — X content-pipeline architect with anti-AI-slop guardrail specialization — treats generator/lint/review as distinct enforcement surfaces and reasons about per-content-type placement trade-offs against algorithmic filters and developer-audience trust thresholds

## Strategy
Expert type "X content-pipeline architect with anti-AI-slop guardrail specialization — treats generator/lint/review as distinct enforcement surfaces and reasons about per-content-type placement trade-offs against algorithmic filters and developer-audience trust thresholds" for design-space question.
Question: How should the X Social Operator spec incorporate the anti-ai-slop writing layer (findings F3001-F3003) — as generator system-prompt constraint, post-generation lint pass with rewrite, reviewer checklist in the human-review gate, or rejected entirely? Evaluate against X-specific failure modes: slop fatigue, developer-audience distrust (2.6% high-trust vs 20% high-distrust), and the MutedKeywordFilter/AuthorSocialgraphFilter hard pre-scoring exclusion (F939A). Decide placement per content type (posts vs threads vs Articles), calibrate F3002 (vocab) vs F3003 (structural) independently, and specify the rewrite loop contract.

## When It Works
- Question type: design-space
- Converged in 3/4 iterations

## Evidence
- Dispatch: D7
- Question: QQ007
- Findings produced: 11
- Iterations: 3/4
- Status: answered

## Key Decisions
Iter 3 of 4 packed Stage-3 option evaluation + Stage-4 render into a single convergence pass. Option D killed (violates C3 HARD-constraint F946 sub-sig coverage). Options A/B/C evaluated: A necessary-but-insufficient, B necessary-and-sufficient, C orthogonal-additive. Placement decision: hybrid A+B+C with per-content-type parameter dispatch (POST piece-level rewrite; THREAD tweet-level-within-thread-context with E.H.A.-exempt substance-gate for rule-of-three; ARTICLE deferred per C8 pending QQ009). F3002 vs F3003 calibration formalized as two independent jobs (Job-A lexical FP bands, Job-B structural per-threshold sweep) with disjoint FP budgets — handoff to QQ010 extension. C6 rewrite-loop contract rendered as pseudocode with iter-cap=3, preservation invariant over {numeric, URL, tag, R6-fact}, anti-gaming via full F321 guard-chain re-run, escalate to F271 §6b Tier-2 queue. F946 sub-sig coverage sanity check confirms all C3-required covered, all C3-excluded correctly out-of-scope. QQ007 answered; no searches used.