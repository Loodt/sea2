# Success Pattern: design-space — T2V provider-abstraction architect (video-API contract designer with multi-provider SDK experience)

## Strategy
Expert type "T2V provider-abstraction architect (video-API contract designer with multi-provider SDK experience)" for design-space question.
Question: Which T2V provider abstraction patterns (unified schema, capability flags, cost-aware router) are documented in production AI video agents, and what is the minimum capability contract (aspect ratios, max duration, audio, seed control, I2V start frame) needed to swap providers without re-authoring prompts?

## When It Works
- Question type: design-space
- Converged in 4/4 iterations

## Evidence
- Dispatch: D5
- Question: Q004
- Findings produced: 17
- Iterations: 4/4
- Status: answered

## Key Decisions
Q004 answered. Pattern: P2/P4-unified (adapter-over-natives + first-class router with optional direct-adapter escape hatch) — only shape that satisfies F1001's R.dispatch contract AND structurally prevents silent-downgrade across N caller sites. Capability contract: 14 required + 2 optional CapabilityProfile fields covering aspectRatios, durationSec, audio, seed (default unsupported), i2v start-frame, async mode, promptDialect, costUnit + normalized-per-sec, failureTaxonomy, plus optional advancedFeatures escape hatch and deprecation slot for F979 Sora 2 sunset. Adapter owns prompt-dialect translation (HC-D prompt-portability satisfied — caller never re-authors prompts on swap), per-flag graceful degrade, async normalization, and native-error→canonical taxonomy mapping. Router owns provider selection across 5 policies (cheapest/fastest/quality-tier/sticky/custom), fallback cascade on supports()=false or dispatch failure, and cost/latency telemetry per persona SP-b. Production precedent: LiteLLM (LLM domain) + Fal.ai (T2V domain, F1009) + OpenTelemetry (observability) all ship the same two-layer pattern. Final artifact at scratch/q004-final-answer.md.