# SEA2

Clean rebuild of [SEA](C:\Users\mtlb\code\sea) on retrieval-first + full reliability stack. Spec: `C:\Users\mtlb\Downloads\x article - agentic reseach reliability\agentic_research_reliability.md`. Plan: `C:\Users\mtlb\.claude\plans\see-the-research-done-cozy-diffie.md`. Resume doc: `HANDOFF.md`.

## Architectural commitments (non-negotiable)

1. **Retrieval-first.** Extract stage cannot call web search. Findings must reference an `admitted_chunk_id` produced by a separate retrieve stage.
2. **Schema-enforced.** Every finding parses against a Zod schema or is rejected at extraction. No post-cleanup hacks.
3. **Tiered verification from day one.** Tier 0 (deterministic) on every finding; Tier 2 (isolated cross-family LLM) on samples; Tier 1 (NLI) and Tier 3 (adversarial) gated by flags/triggers.
4. **Provenance DAG, first-class.** derivation.premises is a typed graph; cycle + orphan detection on every integrate; summary rendered FROM the DAG.
5. **Code-enforced or nonexistent.** No prompt-only mandates. Every behavioral rule lives in code or it does not exist. See `feedback_prompt_only_mandates`.
6. **Fail loudly.** No silent catch blocks. Every error is a structured event with full context. Lint enforces.
7. **One canonical counter.** Metrics computed from the store on demand, not maintained as mutable state. No `newQuestionsCreated`-style divergence.

## What SEA2 is NOT

- An upgrade or fork of SEA — separate repo, separate history.
- A place to port SEA's accumulated CLAUDE.md prose (~400 lines of rules). SEA2 CLAUDE.md is short by design.
- Ready for use. Currently scaffolded only; first runnable system at end of Phase 1.

## Status

Scaffolded 2026-05-15. Phase 1 audit deliverable pending. See `HANDOFF.md`.
