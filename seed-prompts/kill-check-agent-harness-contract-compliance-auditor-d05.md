# Success Pattern: kill-check — agent-harness contract-compliance auditor

## Strategy
Expert type "agent-harness contract-compliance auditor" for kill-check question.
Question: Of the harnesses surveyed in LQ003 / LQ009, which actually meet the F901–F910 spec end-to-end? Specifically: (a) stdin-piped single-shot mode that returns on stdin-EOF (F907), (b) auto-discovered instruction file in cwd (F906), (c) web search + web fetch + file append exposed by default (F905), (d) reliable file-append semantics that do not rewrite whole files (F910), (e) permission-bypass flag suitable for unattended execution (F905). Score each candidate pass/fail per criterion.

## When It Works
- Question type: kill-check
- Converged in 3/5 iterations

## Evidence
- Dispatch: D5
- Question: LQ012
- Findings produced: 15
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ012 answered. Of the 5 TIER-1 candidates, only Codex CLI matches Claude Code at full F901-F910 spec parity (5/5). Goose hits 4/5 with MCP web-search plumbing; OpenCode and gptme hit 3.5/5; Aider 3/5 (worst architectural fit despite best edit primitive). The F972 'Claude-Code structural lock-in' claim is REFUTED — at least one drop-in substitute (Codex CLI) and three wrapper-rescuable substitutes exist. The remaining risk is empirical: documentation says apply_patch is surgical, but the F910 jsonl-append canary should run before production substitution.