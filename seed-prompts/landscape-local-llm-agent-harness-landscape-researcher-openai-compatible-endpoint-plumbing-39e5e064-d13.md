# Success Pattern: landscape — local-LLM agent harness landscape researcher (OpenAI-compatible endpoint plumbing + headless CLI conventions)

## Strategy
Expert type "local-LLM agent harness landscape researcher (OpenAI-compatible endpoint plumbing + headless CLI conventions)" for landscape question.
Question: Which currently-maintained agent harnesses can be driven headlessly (single-shot non-interactive mode, comparable to `claude -p '<prompt>' --output-format text`) and pointed at a local OpenAI-compatible endpoint instead of a cloud provider? Enumerate: Claude Code (with router?), Codex, Aider, Opencode, OpenHands, Continue, Cline, Roo Code, smolagents, a custom minimal harness. For each: local-endpoint support mechanism, instruction-file convention (CLAUDE.md / AGENTS.md / other), exposed tool surface (web search, file I/O, bash, code-exec), output format options, license, active maintenance status.

## When It Works
- Question type: landscape
- Converged in 4/5 iterations

## Evidence
- Dispatch: D13
- Question: LQ003
- Findings produced: 40
- Iterations: 4/5
- Status: answered

## Key Decisions
LQ003 resolved after 4 iterations. All 10 enumerated harnesses (Claude Code, Codex, Aider, OpenCode, OpenHands, Continue, Cline, Roo Code, smolagents, Goose) support headless single-shot invocation AND local OpenAI-compatible endpoints as of 2026-04. Tier-1 open-source drop-ins for SEA = Codex CLI, OpenCode, OpenHands, Cline, Roo Code, Goose. Tier-1 proprietary baseline = Claude Code. Tier-2 (require flag/adapter) = Aider, Continue cn, smolagents. Top-3 SEA shortlist picks: OpenCode (MIT, AGENTS.md originator, 10M+ downloads), Codex CLI (Apache-2.0, MCP bidirectional), OpenHands (MIT, Jupyter+browser distinctive). Claude Code remains reference fallback. One new question opened on SEA harness-interface extension for streaming vs blob output.