# Success Pattern: mechanism — gptme codebase and documentation reader (harness instruction-file convention auditor)

## Strategy
Expert type "gptme codebase and documentation reader (harness instruction-file convention auditor)" for mechanism question.
Question: Does gptme auto-load any per-cwd instruction file (e.g. .gptmehints, gptme.toml [project], or a markdown convention), or is system_prompt the only injection path? One focused docs read upgrades gptme axis-(b) UNKNOWN to PASS or FAIL.

## When It Works
- Question type: mechanism
- Converged in 2/5 iterations

## Evidence
- Dispatch: D15
- Question: LQ020
- Findings produced: 7
- Iterations: 2/5
- Status: answered

## Key Decisions
gptme auto-loads per-cwd instructions via two documented mechanisms (explicit gptme.toml at workspace root + implicit fallback to CLAUDE.md/GEMINI.md/README.md/etc. when files= is unset). AGENTS.md is opt-in only. system_prompt is not the sole injection path — axis-(b) UNKNOWN → PASS for gptme. Because Claude-Code, Codex, and Cursor also pass axis-(b), this axis no longer differentiates the harness shortlist, so no new question is spawned. No-new-questions is intentional (closure-mode compatible).