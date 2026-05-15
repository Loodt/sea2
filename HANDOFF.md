# SEA2 — Handoff Doc (resume here in a fresh session)

**Status:** Repo scaffolded 2026-05-15. SEA postmortem audit complete (2026-05-15) — see [`docs/sea-postmortem.md`](docs/sea-postmortem.md). Phase 1 foundation work (per audit's Phase 1 Implications section) is the next concrete deliverable. No code written yet.

---

## What this repo is

SEA2 is a clean rebuild of [SEA](C:\Users\mtlb\code\sea) committed to the article's full reliability stack from day one — retrieval-first architecture, schema-enforced extract-then-verify, tiered verification (Tier 0-3), provenance DAG, conformal abstention.

It is NOT an upgrade of SEA. SEA stays running and productive at `C:\Users\mtlb\code\sea\`. SEA2 will be validated by running au-token apples-to-apples against SEA and comparing on 12 pre-registered metrics.

---

## Required reading before resuming work

In this order:

1. **The article (the spec):** `C:\Users\mtlb\Downloads\x article - agentic reseach reliability\agentic_research_reliability.md`
2. **The approved plan:** `C:\Users\mtlb\.claude\plans\see-the-research-done-cozy-diffie.md` — full architecture commitments, build phases, comparison protocol
3. **The fallback (do NOT touch unless SEA2 fails comparison):** `C:\Users\mtlb\code\sea\.claude\plans\reliability-uplift-fallback.md`
4. **SEA reference (do NOT modify):** `C:\Users\mtlb\code\sea\` — read CLAUDE.md, src/types.ts, src/runner.ts, src/knowledge.ts, src/conductor.ts, src/type-debt-mandates.ts

Relevant memories: `feedback_fork_over_refactor`, `project_sea2`, `reference_reliability_architecture_article`, `feedback_prompt_only_mandates`, `feedback_fail_loudly`.

---

## Next concrete deliverable: SEA postmortem audit

**File to produce:** `C:\Users\mtlb\code\sea2\docs\sea-postmortem.md`

**Estimated effort:** 1-2 days of focused reading through SEA's history + writing the audit.

**Format per the plan (Part A.4):** for each of the following components, answer:

1. What problem did SEA's implementation solve? (one paragraph, sourced from CLAUDE.md or CLAUDE-history)
2. Did it work? (cite incidents or stable behavior)
3. SEA2 disposition: port verbatim / port and re-tune / re-derive / drop
4. If re-derive: from what first principles?

**Components to audit:**
- Tag taxonomy (SOURCE / DERIVED / ESTIMATED / ASSUMED / UNKNOWN)
- Knowledge store layout (findings.jsonl + questions.jsonl + summary.md)
- Lineage chain (changes.jsonl)
- Multi-provider abstraction (Anthropic / Ollama / Cerebras / z.ai / Gemini)
- Independent evaluator pattern
- Conductor thresholds (v081 caps, mandates, exhaustion gates, yield-decay)
- Expert persona library + utility scoring
- Question type taxonomy (landscape / kill-check / data-hunt / mechanism / synthesis / first-principles / design-space)
- Step gates (crash, persistence, hollow-answer, completion, etc.)
- Finding graduation rules
- Type-debt mandate scaffolding

**Sources to read:**
- `C:\Users\mtlb\code\sea\CLAUDE.md` — current state of accumulated rules
- `C:\Users\mtlb\code\sea\CLAUDE-history\` — history of conductor evolution, repro IDs
- `C:\Users\mtlb\code\sea\projects\*\changes.jsonl` — incident lineages
- `C:\Users\mtlb\code\sea\failure-patterns\` and `success-patterns\` — distilled learnings
- `C:\Users\mtlb\code\sea\src\type-debt-mandates.ts` — the one shipped code-enforced mandate system

**Plan-mode discipline:** the postmortem is a substantial research + writing exercise. Recommend running it in plan mode so the next session produces only the audit doc, no code yet. Phase 1 foundation work (project structure, multi-provider port, append-only store, fail-loudly framework) starts AFTER the audit informs it.

---

## After the audit, Phase 1 deliverables

(from plan Part C.1)

- This repo's `src/` layout: types, store, providers, events, conductor skeleton
- Append-only store with structured logging (every write emits to `events.jsonl`)
- Multi-provider abstraction (port from SEA — pattern in `sea/src/providers/`)
- Fail-loudly framework (typed error events, lint rule rejecting empty catches)
- CLAUDE.md scaffold — kept short by design; behavior lives in code, not prose
- `package.json`, `tsconfig.json`, basic build pipeline

**DO NOT** at this stage:
- Port SEA's CLAUDE.md prose mandates — they are explicitly what SEA2 reverses
- Port SEA's conductor v081 thresholds before audit decides per-mechanism
- Write retrieval, extraction, or verification code (Phase 2+)
- Add prompt-only behavioral rules anywhere — see `feedback_prompt_only_mandates`

---

## Comparison commitments to remember

The validation test is au-token apples-to-apples (Plan Part D). Before running SEA2 on au-token for the first time, the 12 pre-registered metrics from Plan D.3 must be locked. Don't reverse-rationalise after seeing results.

Decision rule (Plan D.5):
- SEA2 wins ≥7/12 including operator-confidence → supersedes SEA
- SEA wins ≥7/12 → fork was wrong, revert to fallback uplift plan
- Mixed → run sa-tax-loophole-agent comparison before deciding

---

## Resume checklist for a fresh session

1. Read this file
2. Read the plan: `C:\Users\mtlb\.claude\plans\see-the-research-done-cozy-diffie.md`
3. Skim the article: `C:\Users\mtlb\Downloads\x article - agentic reseach reliability\agentic_research_reliability.md`
4. Check `git log` and `git status` in this repo to see what's been done since this handoff
5. Proceed with the audit, or whatever the most recent commit message indicates is next
