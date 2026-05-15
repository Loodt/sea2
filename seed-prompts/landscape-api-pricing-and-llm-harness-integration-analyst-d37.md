# Success Pattern: landscape — API pricing and LLM harness integration analyst

## Strategy
Expert type "API pricing and LLM harness integration analyst" for landscape question.
Question: Which cheapest API or subscription-backed LLM options in April 2026 can run SEA research projects through the minimal harness with acceptable quality? Compare direct metered APIs (OpenAI-compatible providers, Anthropic, Google Gemini, OpenRouter/aggregators if credible) against subscription CLI products usable headlessly or semi-headlessly (Codex, Claude Code, Gemini CLI). For each candidate capture: current pricing or quota terms, effective cost per SEA conductor iteration, context window, tool/function-calling support, structured-output reliability, headless automation constraints, minimal-harness integration path, and expected quality risk versus the Claude Opus baseline.

## When It Works
- Question type: landscape
- Converged in 5/5 iterations

## Evidence
- Dispatch: D37
- Question: LQ056
- Findings produced: 39
- Iterations: 5/5
- Status: answered

## Key Decisions
LQ056 is answered. [DERIVED: F955-F957] The cheapest production-safe direct path is GPT-5.4 mini through the existing OpenAI-compatible minimal-harness provider at about $0.11 per typical SEA iteration, while Gemini 2.5 Flash is cheaper at about $0.05 but needs OpenAI-compat tool/JSON smoke testing. [DERIVED: F956] Subscription CLIs can beat metered APIs for repeated work, but require a CLI-runner adapter and live quota telemetry: Gemini CLI is cheapest for scouting, Codex is the best OpenAI-quality automation route, and Claude Code is highest-quality but quota-opaque. [DERIVED: F957] OSS-hosted/OpenRouter routes remain experimental cost scouts until they pass model/provider-specific tool-loop and handoff-validity tests.