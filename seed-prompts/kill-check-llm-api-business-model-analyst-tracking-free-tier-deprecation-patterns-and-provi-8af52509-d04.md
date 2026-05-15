# Success Pattern: kill-check — LLM-API business-model analyst tracking free-tier deprecation patterns and provider monetization pressure

## Strategy
Expert type "LLM-API business-model analyst tracking free-tier deprecation patterns and provider monetization pressure" for kill-check question.
Question: For each free tier surfaced, assess sustainability — will this free tier still exist 6 / 12 months from now for a solo developer? Investigate: (a) historical pattern of the provider's free-tier changes (announcements, deprecations, quota cuts in the last 24 months); (b) current T&C clauses that reserve unilateral modification of free access; (c) public signals of paid-tier pressure (funding round, new paid SKUs, stricter TOS enforcement); (d) whether the free tier is advertised as indefinite vs trial-with-cliff; (e) precedent from comparable providers that ended free tiers (e.g., any prior 'free AI inference' program that later became paid-only). For NVIDIA NIM specifically: what's the written policy on the free tier's continuation and what triggers forced migration to NVIDIA AI Enterprise?

## When It Works
- Question type: kill-check
- Converged in 4/5 iterations

## Evidence
- Dispatch: D4
- Question: FLQ007
- Findings produced: 24
- Iterations: 4/5
- Status: answered

## Key Decisions
FLQ007 ANSWERED iter 4. Sub-question (d) advertising-language audit found a NULL-pattern across 4/5 surviving providers — neither 'free forever' commitment nor explicit 'trial cliff' language is published, leaving free-tier continuation in maximum unilateral-discretion territory; NVIDIA NIM is the sole exception with explicit trial-credits framing. Final 12m survival ranking: Cerebras ~80% (HW-vendor loss-leader, $20B enterprise contract decouples free-tier economics), Z.AI Flash ~70-75% (Chinese-incumbent dual-SKU, post-IPO discretion-risk flagged), Mistral Experiment ~60% (pre-IPO funnel, beta-label dominant risk), Gemini 2.5 Flash ~40% (Google consolidation pattern), NVIDIA NIM ~5% sustainable-free (5000-credit lifetime cap + 40 RPM + commercial-use EULA = evaluation-only classification). Three providers above 60% satisfy persona's ≥2 viable free options bar.