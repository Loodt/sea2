# Success Pattern: mechanism — agent-harness CLI interface analyst (cross-tool evaluation, subprocess/stdin-stdout contracts, JSON output shapes, instruction-file conventions)

## Strategy
Expert type "agent-harness CLI interface analyst (cross-tool evaluation, subprocess/stdin-stdout contracts, JSON output shapes, instruction-file conventions)" for mechanism question.
Question: How do Aider, Opencode, OpenHands, Continue, Cline, and Roo Code each dispatch a single-shot task to an LLM and collect structured output? Specifically for each: (a) is there a non-interactive / scripted mode equivalent to `claude -p '<prompt>'`? (b) does it load an instruction-file convention like CLAUDE.md / AGENTS.md / .aiderignore? (c) what tool calls are exposed and can they be restricted per-task? (d) what output formats does it emit (stdout / JSON / file diffs / other)? (e) how much code would it take to wrap each as a SEA Provider in src/types.ts?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D17
- Question: LQ009
- Findings produced: 16
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ009 answered across all 6 tools × 5 sub-questions. Stage-1 (F921-F929) anchored the SEA ProviderConfig shape and confirmed all 6 tools ship a standalone CLI. Stage-2 (F930-F935) filled and verified the 5-axis contract matrix from primary docs, superseding F927's Cline stdin-inference with F931's positional-arg-primary measurement. Stage-3 (F936) composed the per-tool per-sub-question answer and the wrap-cost ranking: Continue (~5-8 LOC) is the only naive drop-in; all others force a runner.ts promptMode/outputMode generalisation. Persona's IDE-kill prediction was invalidated. Downstream impact: confirms Continue as the strongest Claude-Code-adjacent swap-in and Opencode as the strongest AGENTS.md-native swap-in without reversing the Claude Code + Codex primary pick from LQ003/LQ012.