# SEA Postmortem Audit (v2)

**Date:** 2026-05-15
**Audit subject:** [SEA](C:\Users\mtlb\code\sea\) at conductor v081
**Audit purpose:** Decide, per component, what SEA2 ports / retunes / re-derives / drops. Blocks Phase 1 of the rebuild ([HANDOFF.md](../HANDOFF.md)).
**Spec being ported toward:** the article's reliability stack — retrieval-first, schema-enforced extract-then-verify, tiered verification (Tier 0–3), provenance DAG, conformal abstention.
**Authority for honest assessment:** SEA's `CLAUDE.md` §96 Infrastructure Debt (the honest record of what shipped without code), `failure-patterns/` (13 named incidents), `success-patterns/` (90+ durable persona artifacts), v064 HOLD's 16-dispatch validation window, and per-project lineages.

> This is the second pass of this audit. The first pass led with what went wrong and jumped to disposition too quickly. This pass takes the trichotomy seriously: **what worked**, **what worked OK**, **what did not work**. Each verdict is sourced against specific incidents, lineage windows, or shipped code. Dispositions follow the evidence rather than driving it.

---

## How SEA actually performs in 2026-05

Before judging components, the baseline:

- **v064 HOLD window (110 dispatches across 10 projects since v054):** ~52 of 55 questions resolved as answered + productively-exhausted (**94%**). Zero crashes. Zero `HOLLOW_ANSWER`. Avg 15.2 findings/dispatch on video-marketing-agent's 16-dispatch validation slice. Cumulative ~243 findings on that one project.
- **au-token (richest single project):** iterates productively from disp 1 through 50+. Sample of the lineage: iter 9 +18f, iter 12 +32f, iter 17 +28f, iter 18 +17f, iter 20 +23f, iter 24 +25f, iter 25 +19f, iter 27 +19f, iter 28 +18f, iter 36 +6f (FP, expected lower). 8 question types fire across the window with explicit rotation. Reasoning chains visibly compound: AUQ005 / AUQ018 / AUQ030 each take 3-5 iterations across multiple types to converge.
- **Self-aware reliability:** SEA is unusually honest about its own debt. CLAUDE.md §96 lists 9 critical/high/medium code-gaps with **repro IDs**, specific line-counts for remediation, and explicit project + iteration citations. This is a system that documents its own failures with surgical specificity.

A first reading of `failure-patterns/` paints a system in crisis. A reading of `changes.jsonl` and v064 HOLD paints a system that ships productive research at scale. Both are true. The honest read is: SEA works well in steady-state on data-rich domains; its failure modes are concentrated at lifecycle edges (start, closeout, cascade) and at the prompt/code seam.

---

## What worked

### W1. The five-tag epistemic taxonomy

`[SOURCE: url]` / `[DERIVED: method]` / `[ESTIMATED: basis]` / `[ASSUMED]` / `[UNKNOWN]` — defined at [`types.ts:122`](C:\Users\mtlb\code\sea\src\types.ts), unchanged from v014 (the very first conductor snapshot) through v081. Eight months and 60+ conductor revisions without revision is itself the strongest signal of fit.

The taxonomy gives every claim an explicit epistemic provenance, which makes the trust cascade computable: axioms → SOURCE → DERIVED. The auto-graduation code (`graduateFindings` at `knowledge.ts:501-564`) reads tag + confidence + age and graduates only what passes. The downgrade enforcers (`enforceSourceUrls`, `enforceDerivationChains`) catch malformed tags at write time. Reading au-token lineage iter 5, iter 19, iter 30 you can see SOURCE-and-URL claims, DERIVED claims with explicit premise chains, UNKNOWN flagged where it should be.

This is the conceptual primitive that the article's tiered verification ports onto. SEA2 inherits a *vocabulary* that's been pressure-tested for eight months.

### W2. Append-only JSONL store with atomic locking

[`knowledge.ts:7-167`](C:\Users\mtlb\code\sea\src\knowledge.ts) + `file-lock.ts`. JSONL is greppable, diffable, crash-resilient at the line level. Atomic locking via `atomicAppendJsonl` / `atomicUpdateJsonl` means concurrent writes don't corrupt. The "knowledge store is source of truth" discipline (CLAUDE.md §71) is honoured throughout: `output/` reports are downstream of `findings.jsonl`, never the other way around.

Zero failure-pattern entries cite JSONL corruption. The atomic-write infrastructure is the silently-load-bearing layer that keeps every other component honest.

### W3. Deterministic summary regeneration

`generateFallbackSummary` (`knowledge.ts:347-393`) builds the human-readable index purely from findings + questions. `enforceSummaryFreshness` (`knowledge.ts:324-341`) and `enforceSummarySize` (`knowledge.ts:244-268`) keep it ≤2KB and aligned with current store state.

A stale `summary.md` cannot persist — it gets regenerated. This is structurally a small thing and it eliminates an entire class of "I read the summary but the store said something else" bugs.

### W4. Multi-provider abstraction

[`types.ts:1-79`](C:\Users\mtlb\code\sea\src\types.ts). Three providers (`claude`, `codex`, `codex-local`). Auto-detection via `CLAUDECODE=1` / `CODEX_CLI=1` / `SEA_PROVIDER` env vars — subagents inherit the parent harness without an explicit flag. Provider config is a pure data record: binary + baseArgs + modelFlag + instructionFile.

Zero incidents in `failure-patterns/` mention provider abstraction. The `codex-local` config has a brief comment documenting a real quirk (approval-policy lives in `$CODEX_HOME/config.toml`) — that comment is the entire interaction history with this subsystem since it shipped.

67 LOC. Boring. Production-ready. The cleanest piece in the codebase.

### W5. Independent-critic structural separation

[`context.ts:336-410`](C:\Users\mtlb\code\sea\src\context.ts). The `assembleEvaluate` prompt does not receive persona or goal — by *construction*. `evaluateModel: "sonnet"` (different model from producer — Axiom 1 isolation). The critic produces a parseable scores block; the loop infrastructure persists scores so the critic cannot rewrite its own metrics.

This is a clean instance of "structure beats intention". The critic *cannot* confirmation-bias toward the producer's framing because it has no access to it. The article's Tier 2 (isolated cross-family LLM verifier) maps directly onto this pattern.

### W6. The shipped enforcement layer (caps, guards, snapshots)

These are listed in CLAUDE.md §108 "Closed":

- `question-caps.ts` (263 LOC) — code-enforced per-dispatch, iter-boundary, and type-queue caps. Emits `QUESTION_CAP_TRIMMED`. Catches the jarvis-architecture-class "15 open design-space vs 4 cap" overflow at integration time.
- `selection-guards.ts` (206 LOC) — non-open-redispatch guard, re-dispatch type-mismatch guard, same-type-cap guard. Comment at line 11-14 cites the empirical impact: kill-check yield went from 9.8 avg → 24.0 under rotation. Emits `SELECTION_GUARD_INTERVENED`.
- `store-snapshot.ts` — pre-integration snapshot + auto-restore on zero-out / >50% loss / verified-finding removal. Emits `STORE_CLOBBER_RESTORED`.
- `enforceSourceUrls` (`knowledge.ts:175-199`) — downgrades `[SOURCE]` without `http://` URL to `[UNKNOWN]`. Catches bare labels like `"sprout-social-2026"`.
- `enforceDerivationChains` (`knowledge.ts:206-227`) — downgrades `[DERIVED]` without a premise array to `[ESTIMATED]`.
- `appendLineageEntry` (`conductor.ts:1136-1148`) — every iteration including no-change holds.
- `type-debt-mandates.ts` (340 LOC) — pure `evaluateMandates`, template `buildMandateQuestion`, override `applyMandateHardBlock`. Env-gated for staged rollout.

Every one of these has a named event-type. The system tells the operator *exactly* what it just did and why. This is the working subset of the fail-loudly discipline and it covers more ground than the failure-patterns-only reading would suggest.

### W7. The lineage as a reasoning artifact

`changes.jsonl` is not just an audit log — it's *the system's exposed reasoning trace*. Sampled au-token entries:

- iter 10 AUQ005: "answered via three-stage workflow: Stage 1 (F901-F905, prior iter) confirmed no on-point SARS doctrine; Stage 2 (F906-F912, prior iter) anchored statutory text and collapsed analysis to three archetypes (A=crypto asset / B=share in Pty Ltd SPV / C=CIS participatory interest); Stage 3 (F913-F918, this iter) populated the full 5-event × 3-archetype matrix…"
- iter 17 AUQ040: "GAAR risk for Au-Token tokenisation is DEFENSIBLE as a documentation/counsel workstream separate from BPR (BPR-408 §7 carve-out confirmed). Five-stage analysis: gateway-kill failed → NWK 5-element decomposition…"
- iter 24 AUQ030: "Iter-5 cracked the cycle-time axis via offline PDF download of SARS step-by-step procedure (20/45/60-day targets…published, just not on the public ATR landing page that prior iters scraped)."

These entries cite finding IDs, name verification stages, surface unexpected discoveries ("the BPR landing page didn't have it; the offline PDF did"), and quantify economic outcomes. They constitute *durable, sourced research output* that a human reviewer can audit without re-running the system. The format — `changeType` + `changeSummary` + `reasoning` + finding-ID provenance — is a port-verbatim primitive.

### W8. The success-patterns library

90+ named domain-expert persona templates accumulated across 14+ projects, e.g.:
- `mechanism-gold-coordination-chemist-specializing-in-thiolate-bond-chemistry-and-oxidative-ligand-displacement-d07.md`
- `first-principles-recommendation-systems-reasoner-specializing-in-sequential-user-modeling-feed-ranking-architectures-and-developer-audience-behavioral-patterns-d04.md`
- `mechanism-plural-form-governance-and-incentive-design-reasoner-d12.md`
- `synthesis-south-african-neutral-freight-exchange-architecture-synthesist-d04.md`

Each file is a working expert prompt with strategy, convergence speed, evidence tie-back. These are *the durable knowledge output* of SEA's persona-evolution loop, separable from the per-project `library.jsonl` (which is mostly scoring metadata). The first audit pass dismissed the persona library wholesale — that judgement does not survive contact with this directory.

The success-patterns library is a Phase 2 *asset*: a starter set of expert prompts that SEA2's planner/extractor/verifier roles can draw from even if SEA2 does not replicate the score-based reuse machinery.

### W9. The failure-patterns library as institutional memory

13 named patterns, ~2600 lines, each with: signature, root cause, observed impact (project + iterations), prevention, distinction from related patterns. `heuristic-layer-ceiling.md` and `closeout-drift.md` in particular are *the* documents that explain why prose-only mandates fail in SEA. Reading them is reading the system's own self-diagnosis.

`feedback_prompt_only_mandates` and `feedback_fail_loudly` (the user's stored memories that drive CLAUDE.md commitments 5 and 6) crystallise lessons whose underlying evidence lives in this directory. SEA2 inherits the lessons by inheriting the architectural commitments; the patterns themselves are worth reading as the spec for what SEA2 must not reproduce.

### W10. Meta-evolution cadence as a self-improving rhythm

`metaEveryN: 3` (`DEFAULT_CONDUCTOR_CONFIG`). au-token's lineage shows meta-evolution firing reliably at iter 3, 6, 9, 12, 15, 18, 21, 24, 27, 30, 33, 36 — every third iteration writes a CLAUDE.md change-record. The history files (`CLAUDE-history/v014.md` through `v064.md`) are the materialised output of this loop. v064 HOLD is a meta-evolution explicitly *holding* on changes pending validation — i.e. the meta-loop knows how to wait, not just how to change.

The mechanism itself is sound. The thing the loop produces — prose CLAUDE.md mandates — is what doesn't always survive (see F1). But the rhythm of "produce, observe, hold, revise" is a working pattern that SEA2 inherits in spirit, even if the artifact it produces shifts from prose mandates to code commits.

---

## What worked OK

### O1. Conductor question selection (in steady state)

`question-caps.ts` + `selection-guards.ts` + the soft-prior boosters in `type-debt-mandates.ts` produce visibly correct rotation in au-token's 36-iteration window: 8 distinct types fire, no same-type-cap violations, kill-check yield holds at 24 avg, AUQ012 / AUQ018 / AUQ025 take 3-5 dispatches to converge across multiple types. This works.

It works *less well* at lifecycle edges and on lopsided projects. The prose-only modes (exploit, closure, non-closing answer, thin-closure — infra-debt #1) don't reliably override the LLM selector. Two well-documented breakdowns:

- au-token iter 50-53: canonical exploit-mode-skip — 4/4 answered, attrition=0, avg findings ≥9 → threshold met, selector still picked non-synthesis.
- au-token iter 26-47: 22-dispatch reasoning-axis blackout (#8) — selector ranks by yield + open-queue, no `WINDOW_COVERAGE_BOOST` event ever emitted.

Disposition this lands at: **port the shipped pieces (caps + guards + soft-priors machinery); re-derive the prose-only modes**. The selection logic is a load-bearing component with a 60% shipped / 40% prose-only split; the rebuild ports the 60% and rederives the 40% from article first principles.

### O2. Persona library + utility scoring

[`expert-library.ts:1-167`](C:\Users\mtlb\code\sea\src\expert-library.ts). Hash-keyed entries, `LibraryEntry.score = avgIG × log(dispatches+1)`, 0.4 keyword-overlap + 0.6 normalized-score match. Adapt threshold 2.0; global-library promotion at ≥2.0, dispatches ≥2.

The code runs. Entries accumulate. Reuse happens. But:

- `additive-evolution-trap.md` (sewage-gold iter 1-4): personas grew to 113 lines, catastrophic crash at iter 4. The "60-line persona budget" remedy is a band-aid on top of the library — and as `heuristic-layer-ceiling.md` later showed, persona edits cannot fix harness-layer bugs no matter how well-reasoned.
- `evolution-persistence-failure.md` (sewage-gold iter 5-7): lineage claimed three persona evolutions but the file never changed. Three iterations ran with a stale persona.
- The scoring's input metric (`findingsAdded`) is corrupted upstream by infra-debt #2 (PERSISTENCE_GAP) and #7 (counter-drift). So the *scores* are downstream of broken counters.

But — and this is what the v1 audit got wrong — the *output* of the persona-evolution loop is the success-patterns library (W8), which is a durable, useful artifact independent of the per-project scoring.

Disposition lands at: **drop the per-project `library.jsonl` + utility-score-driven adaptation, but preserve the success-patterns/ directory as a Phase 2 asset and consider porting the persona templates as starter prompts for SEA2's planner/extractor/verifier roles.**

### O3. Tag enforcement at extract time

`enforceSourceUrls` and `enforceDerivationChains` (knowledge.ts:175-227) are tag-shape gates. They catch:
- `[SOURCE: sprout-social-2026]` (no URL) → downgrade to `[UNKNOWN]` with bad-source preserved in the claim.
- `[DERIVED: heuristic-reasoning]` with no `derivationChain` → downgrade to `[ESTIMATED]`.

These work. They run code, not prompts. But they enforce *shape*, not *truth*:

- `citation-reference-swap.md`: `[SOURCE: PMC 7581288]` passes the URL gate but the paper described under that PMC ID doesn't support the cited claim. Tag is well-formed; semantics are inverted.
- `derived-claim-blindspot.md`: Au-S bond energy claimed at 88 kJ/mol (actual ~209); claim has a valid `derivationChain` but the *number* was never sanity-checked. C-C BDE was supposed to be ~345 kJ/mol; the claim inverted the comparison entirely.

Disposition: **port the gates verbatim; add Tier 0 (URL resolves + quoted span matches) and Tier 2 (cross-family LLM number-check) on top.** The shape gates are the floor; the rebuild adds the semantic ceiling.

### O4. Finding graduation

`graduateFindings` (`knowledge.ts:501-564`). SOURCE: confidence ≥0.85 + URL (http/https) + age ≥3 + not refuted. DERIVED: confidence ≥0.90 + `derivationChain` ≥2 verified premises + age ≥3 + not refuted. `needsReview` blocks all auto-graduation (sound human-in-the-loop escape hatch).

The function is clean, code-enforced, and the trust cascade is real (DERIVED can't graduate before its premises do). Fast-track was correctly deprioritised in v064 ("1-disp speedup, confidence cliff at 0.90, undercuts graduation gate").

The hole: graduation is an *after-the-fact promotion gate*, not a verification step. It can't catch citation-reference-swap or derived-claim-blindspot because verification depth is "URL syntax is well-formed". The article's Tier 0–2 verification chain should be the precondition for graduation, not graduation itself.

Disposition: **port the function shape + criteria + `needsReview` mechanism + trust cascade; replace the URL-pattern check with Tier 0 (URL resolves + quoted span), Tier 1 (NLI claim-vs-source), Tier 2 (cross-family LLM check). Drop fast-track (already deprioritised).**

### O5. Lineage chain as iteration record

`appendLineageEntry` (`conductor.ts:1136-1148`). Per-iteration JSONL entry: `iteration, target, changeType, changeSummary, reasoning, scoreBefore, scoreAfter`. Required even for no-change holds. Drives meta-evolution input.

As an iteration record this works extremely well (W7). What it does *not* capture is finding-level provenance: there's no record of "F1154 was derived from F1151+F1152+F1153 via deductive integration" beyond a free-text field on the finding itself. The integration step doesn't validate the premise graph.

A related hole: `scoreBefore` / `scoreAfter` are *null throughout au-token's lineage*. That's infra-debt #5 (SCORE_FIELD_LOSS) manifest at the lineage layer — scores are computed in reflection but not piped through to the lineage entry.

Disposition: **port the lineage shape; upgrade finding-level provenance to a typed DAG (article commitment 4) with cycle/orphan detection at integrate; fix the score-piping (one-line write at the lineage append site).**

### O6. Question type taxonomy

`QuestionType` union (`types.ts:330`): 8 types with per-type iteration caps, search budgets, dispatch caps. Stable for diagnostics — au-token's lineage is readable because each entry is labelled `landscape`/`kill-check`/`data-hunt`/etc.

But:
- `divergence` is dead (removed from v057 selection prose, retained in the union for safety).
- `first-principles` and `design-space` never settled across nine history files (mandatory after iter 4 in v033 → soft-boost only in v064 → still subject to type-debt mandates in v081). They are the most prompt-only types, and not coincidentally the types implicated in infra-debt #8's reasoning-axis blackouts.

The 5 working types (landscape, kill-check, data-hunt, mechanism, synthesis) carry the productive load.

Disposition: **port the 5 working types verbatim; drop divergence + first-principles + design-space as separate types (reasoning lives in verification under the article's architecture); keep iteration/dispatch cap shape; retie budgets from search-call counts to retrieval coverage.**

### O7. Step gates (the shipped subset)

Crash circuit-breaker (`expert-loop.ts:74-78`, 2 consecutive crashes → forced handoff) works. Store-clobber-restore works. Summary-size enforcement works. Same-type-cap works (it's coded in `selection-guards.ts`).

These are real gates that catch real failures and emit named events.

The other 7+ items in CLAUDE.md §53 (persistence, hollow-answer, completion, reflection-veto, dispatch-integrity, harvest/closure, closeout-halt-cascade, non-closing-answer, thin-closure, exhaustion-unresolved) are prose-only or partly-shipped. See F1, F2, F3, F4 below.

Disposition: **port the 4 shipped gates; re-derive the 7+ prose gates from the article's invariant + typed-event architecture (most collapse to "events.jsonl emits typed completion-or-error, conductor reads events not exit codes").**

### O8. Type-debt mandate scaffolding (as instrumentation, not as mechanism)

[`type-debt-mandates.ts:1-340`](C:\Users\mtlb\code\sea\src\type-debt-mandates.ts). Pure `evaluateMandates` (4 conditions: synthesis-missing > synthesis-cadence > fp-missing > mechanism-missing, priority-ordered). Template-driven `buildMandateQuestion` (no LLM in the question-construction path — deterministic and cheap to test). Override-the-selector `applyMandateHardBlock` respecting same-type-cap. Env-gated rollout via `SEA_MANDATE_AUTOCREATE` and `SEA_MANDATE_HARDBLOCK`.

The architecture is exemplary. This is what every prose mandate should have been from the start. But v064 HOLD explicitly states: **"AUTOCREATE has 0 fires across all v062+ activity — soft-priors + organic rotation absorb the gap; AUTOCREATE remains as defensive scaffolding for genuinely lopsided projects, not a load-bearing mechanism."**

So: built well, instrumented well, ~0 fires in practice. That's data, not failure. The lesson is that the *content* (force FP / mechanism / synthesis when missing) presupposes SEA's specific question taxonomy — which SEA2 is partially dropping — and the *pattern* (typed mandate + env-gated rollout + structured event) is the right pattern for converting any prose rule to code.

Disposition: **drop the file; port the pattern.** Phase 1's fail-loudly framework re-emerges the pattern as a uniform shape for any future code-enforced invariant.

---

## What did not work

### F1. Prose-only conductor selection modes (infra-debt #1, HIGH)

CLAUDE.md §10 carries 40+ lines of selection-mode prose: exploit, closure, non-closing answer, thin-closure, harvest/closure, type-queue-drain, kill-check yield-guard, type rotation, yield decay, reasoning-branch closer, hot-streak, mechanism promotion. The selector LLM is asked to honour all of this every dispatch.

Canonical breakdown: **au-token iter 50-53** — exploit-mode threshold met (4/4 answered, attrition=0, avg findings ≥9), selector picked non-synthesis anyway. CLAUDE.md commitment 5 ("code-enforced or nonexistent") and feedback_prompt_only_mandates point at exactly this class of failure. Every additional prose mode is another instance of the same class.

**This is the central failure mode of SEA's design.** The history files show the prose accumulating monotonically (v014: 88 lines → v081: 118 lines) while the shipped enforcement layer grew slower. Every infra-debt entry is a variant of "prose says X, code doesn't enforce X".

### F2. Completion gate (infra-debt #3, CRITICAL)

The conductor's `select` step has no terminal check. When `dispatchableOpen==0 && activeQuestionId==null`, the system dispatches into an empty store rather than transitioning to `status="completed"` and exiting. Manifest as `closeout-drift.md`:

- total-value-recovery iter 1-4: persona unchanged at v004, score path 7.35 → 7.15 → 6.15 → 4.3. Closeout iterations re-surfaced prior research as if new, or crashed with 0 KB output, or emitted attestation-style `F99xxx` findings.

Remediation is documented: pre-LLM check on `(dispatchableOpen, activeQuestionId, openTotal)`; on terminal, write `status="completed"` + summary terminus, exit 0; never enter LLM ranking. The fix is small. It hasn't been written.

### F3. `state.haltReason` reader (infra-debt #6, CRITICAL, ~5 LOC)

The conductor never reads `state.haltReason`. When evolve emits `terminal-halt` and sets `haltReason='terminal-iteration-loop'`, the next operator tick relaunches the project anyway. Manifest as `operator-kill-ignored-cascade.md`:

- total-value-recovery iter 10-12: cascade depth 3 (terminal-halt → TERMINAL_HALT_ESCALATED → TERMINAL_HALT_CASCADED). All three iterations consumed full conductor cycles. All three produced zero domain findings. All three correctly identified the failure layer as harness, not persona.

Five lines of code. Unshipped.

### F4. Reflection-veto enforcement (infra-debt #4, MEDIUM)

The independent critic (W5) emits explicit go/no-go signals: "do not dispatch iter-N+1", "should be completed", "halt pending evolution review". The conductor has no parser for these. The critic's signal is well-formed and ignored.

This is the same structural bug as F2 and F3: a high-quality signal is generated by one layer and not read by the next. `heuristic-layer-ceiling.md` is the meta-pattern of which F2/F3/F4 are instances.

### F5. Metric counter drift (infra-debt #7, HIGH)

`newQuestionsCreated=0` while cumulative `openQuestionsDelta=+50` and 57 resolved, across **57/57 dispatches in six non-overlapping au-token windows**. The integrator creates questions that don't get tallied in the metric, so any selector heuristic that reads `newQuestionsCreated` reads as permanently-firing or never-firing.

Coupled failures: the synthesis-cadence "new questions capped at 1" rule (CLAUDE.md §10) reads this same broken counter — au-token iter 55-56 both opened ≥2 net questions unobserved.

The fix lives at the architectural layer: **no mutable cumulative counters**. Metrics computed from the store on demand (CLAUDE.md commitment 7).

### F6. PERSISTENCE_GAP root cause (infra-debt #2, CRITICAL)

~12 repros across 4 projects. The expert-loop produces N findings to scratch JSONL; only some make it to `findings.jsonl`. Scratch parses cleanly. The append path silently drops. Detection is *incidental*, via next-iter `[DERIVED]` chains pointing at missing premise IDs.

The detection-and-recovery half works: video-marketing-agent iter 9 has an explicit `PERSISTENCE_GAP` lineage entry with manual `cat`-append restoration documented and supersedes-tracking maintained. But the root cause has not been identified in 12 repros across 4 projects.

The article's retrieval-first architecture *dissolves* this bug: extract writes to `findings.jsonl` as each finding validates against the Zod schema. There is no scratch-then-integrate hop that can silently drop. The rebuild gets to skip the fix by skipping the architectural seam.

### F7. Score-field-loss (infra-debt #5, MEDIUM)

total-value-recovery iter 5 + iter 10: reflection scored 6/5 but `scores.jsonl` persisted 0/0. Additionally manifest at the lineage layer — au-token's `scoreBefore`/`scoreAfter` fields are null throughout. The score is computed and lost between layers.

Remediation: post-write equality check at every persist site. Unshipped.

### F8. Silent truncation cascade

`silent-truncation-cascade.md` (sewage-gold iter 8-9). Exit-0 with partial output: iter-8 produced 11 findings, only 8 persisted; synthesis cited all 11; 3 phantom IDs. Iter-9 same pattern at 71% phantom rate. The crash gate checks exit code, not completeness.

The architectural fix is the same as F6: schema-validated writes-as-you-go, downstream pre-flight check (every finding-ID a synthesis cites must exist in the store). Neither shipped.

### F9. Upstream crash silent bypass

`upstream-crash-silent-bypass.md` (sewage-gold iter 3). Research step crashed (exit 1, 0 bytes output). Synthesis produced a 24KB report with 11+ phantom finding IDs and 11+ new source citations — almost certainly drawn from model training data, never verified through the pipeline.

The output *looked* well-sourced (proper PMC IDs, author names). Quality scores landed at 7-8 across content dimensions. The bypass was invisible to content-based gating.

The article's retrieval-first architecture *also* dissolves this: extract has no web call; it has only retrieved chunks. A crashed retrieve cannot be silently compensated by training data because extract has no path to training data — its inputs are admitted chunks or nothing.

### F10. Protocol artifact loss on crash

`protocol-artifact-loss-on-crash.md`. Every high-content sewage-gold iteration except iter 2 lost its audit trail — experiment logs, trace files, references/links.md. Pattern: deliverable writes first, artifacts after, context exhausts during the deliverable, artifacts never written.

Fix is "interleave artifact writes with deliverable writes". The fail-loudly framework (commitment 6) re-emerges this as "every step emits typed completion events to events.jsonl as it runs, not as a batch at exit". Unshipped in SEA.

### F11. Pipeline step deferral

`pipeline-step-deferral.md`. Agents defer write-side-effects to a final "summarize" step ("will update in summarize"). If summarize doesn't run — context exhaustion, early termination — all deferred writes are lost. Persona heuristics ("do it incrementally") were tried for 3 consecutive iterations and the agent interpreted "incrementally" as "in the summarize step".

This is a clean case of `heuristic-layer-ceiling.md`: persona cannot fix pipeline mechanics. The article's commitment 1 (retrieval-first) and commitment 6 (fail-loudly) collapse this: extract writes findings at validation; there is no separate "summarize step" to defer to.

### F12. Window-coverage code-graduation (infra-debt #8, HIGH)

au-token iter 26-47 = **22-dispatch reasoning-axis blackout**. The "window-coverage-per-type" prose rule (CLAUDE.md §10) says: if the last 10 dispatches contain 0 of type T and ≥1 open of T, boost T. No `WINDOW_COVERAGE_BOOST` event ever emitted in 22 dispatches. The escape at iter 48-49 was incidental queue rotation, not the prompt-only mandate firing.

Same pattern as F1, but specific enough to call out: a major intended self-corrective mechanism never executed.

### F13. Synthesis-cadence prior (infra-debt #9, HIGH)

au-token broke a 53-dispatch synthesis blackout at iter 55-56. Per CLAUDE.md §10 line 17, two priors should have triggered synthesis (zero-ever at ≥60 findings; cadence at ≥100 findings + ≥8 disp since last + growth ≥30). Neither emitted `MANDATE_EVALUATED` for synthesis in 53 prior dispatches. The two synthesis fires at iter 55-56 likely came from exploit-mode prompt language, not the cadence prior.

Same class as F1 + F12. A specific working mechanism (the cadence prior) was specified in prose and never wired to code.

---

## Per-component dispositions

(Refined from the v1 audit, with disposition reasoning anchored to specific What-Worked / What-OK / What-Failed entries above.)

| # | Component | Disposition | Anchored to |
|---|---|---|---|
| 1 | Tag taxonomy (SOURCE/DERIVED/ESTIMATED/ASSUMED/UNKNOWN) | **port and re-tune** | W1 (vocabulary verbatim) + O3 (gates port, add semantic layer) |
| 2 | Knowledge store (findings.jsonl + questions.jsonl + summary.md) | **port and re-tune** | W2 + W3 verbatim; F6 + F8 dissolved by retrieval-first |
| 3 | Lineage chain (changes.jsonl) | **port and re-tune** | W7 + O5: port iteration record verbatim; upgrade finding-level provenance to typed DAG |
| 4 | Multi-provider abstraction | **port verbatim** | W4 |
| 5 | Independent evaluator pattern | **port verbatim** (structure) + **re-tune** (consumption) | W5 verbatim; F4 (reflection-veto parser) added as code |
| 6 | Conductor thresholds (caps, mandates, exhaustion, yield-decay) | **port code surface; re-derive thresholds** | W6 ports; O1 + F1 + F12 + F13: rederive prose modes from article's retrieval/extraction/verification metrics |
| 7 | Expert persona library + utility scoring | **drop the library; preserve success-patterns/ as Phase 2 asset** | O2 — library is corrupted-input scoring; W8 — the durable artifact is independent and worth keeping |
| 8 | Question type taxonomy | **port the 5 working types; drop divergence + FP + design-space** | O6 |
| 9 | Step gates | **port the 4 shipped; re-derive the rest from events.jsonl invariants** | O7 + F2 + F3 + F4 + F8 + F9 + F10 + F11 |
| 10 | Finding graduation rules | **port and re-tune (add Tier 0–2 verification)** | O4 |
| 11 | Type-debt mandate scaffolding | **drop the file; port the pattern as fail-loudly events** | O8 |

Disposition counts: **2 verbatim**, **5 port-and-retune**, **2 port-with-re-derive**, **2 drop (with W8 preserved as asset)**.

---

## Cross-cutting findings

### A. The prose / code seam is where almost everything fails

Of the 9 infra-debt items in CLAUDE.md §96, 9 of 9 are "prose says X, code doesn't enforce X". Of the 13 failure-patterns, `heuristic-layer-ceiling.md` is the meta-pattern: every persona-layer fix that targeted a harness-layer bug failed regardless of how well-reasoned. Of the 60+ conductor revisions in `CLAUDE-history/`, the dominant motion is *adding prose mandates*; the shipped code grew slower.

`feedback_prompt_only_mandates` is the lesson SEA already learned about itself. Commitment 5 ("code-enforced or nonexistent") is the architectural answer. The rebuild enforces this with a lint rule: any new mandate in CLAUDE.md without a corresponding shipped code module fails CI.

### B. Counter-drift and PERSISTENCE_GAP are one bug wearing two hats

Infra-debt #2 (PERSISTENCE_GAP: produce-vs-persist drift) and #7 (counter-drift: `newQuestionsCreated` vs `openQuestionsDelta`) share a root cause: SEA maintains *mutable counters and intermediate scratch files* outside the store. Every counter is a place that can drift from the source of truth; every intermediate file is a place where writes can silently drop.

Article commitments 1 (retrieval-first) and 7 (one canonical counter) collapse both: extract validates and writes findings to the store as it produces them — no scratch hop — and all metrics are computed from the store on demand — no mutable counters. The rebuild gets to skip *fixing* these bugs by skipping the architectural seam that produced them.

### C. The critic exists; the harness ignores it

F2 (completion gate), F3 (haltReason reader), F4 (reflection-veto) and `closeout-drift.md` + `operator-kill-ignored-cascade.md` are all instances of the same structural pattern: an upstream layer produces a high-quality halt/veto/transition signal, and the conductor does not read it. The conductor is parsing exit codes when it should be parsing typed events.

Article commitment 6 (fail-loudly) re-emerges this as: every transition is a typed event written to `events.jsonl`. The conductor reads events at the top of every loop iteration. F2/F3/F4 become unrepresentable.

### D. SEA's failures are concentrated at lifecycle edges

`failure-patterns/` is dominated by start-of-life and end-of-life pathologies:

- Start-of-life: additive-evolution-trap (early iterations grow persona before catastrophic crash at iter 4), context-exhaustion, upstream-crash-silent-bypass (sewage-gold iter 3).
- End-of-life: closeout-drift, operator-kill-ignored-cascade (cascade depth 3).
- Cascade: silent-truncation-cascade (sewage-gold iter 8-9: 27% → 71% phantom rate), fix-resistant-identical-failure.

The steady-state middle is where SEA works (au-token iter 9-50, video-marketing-agent iter 5-20). SEA2's reliability stack needs to harden the edges specifically: explicit completion gate, explicit halt-reason honour, schema-enforced extract from disp 1, conformal abstention as the disciplined exit.

---

## Phase 1 implications

Per the audit, Phase 1 of SEA2 builds:

1. **`src/types.ts`** — port verbatim (W1 + W4):
   - `EpistemicTag` (5-tag union) from `sea/src/types.ts:122`.
   - `Finding`, `Question` shapes (keep `needsReview`; drop already-removed `quantitative`, `linkedFindings`, `humanReviewRequired`).
   - `LineageEntry` from `conductor.ts:1125-1134`.
   - `QuestionType` union reduced to the 5 working types (O6): landscape, kill-check, data-hunt, mechanism, synthesis. No divergence / first-principles / design-space.

2. **`src/providers.ts`** — port verbatim (W4) from `sea/src/types.ts:1-79`. Likely add a 4th provider for direct Anthropic-SDK (rather than CLI), needed for Tier 2 cross-family verification.

3. **`src/store.ts`** — port and re-tune (W2 + W3 + W6, with F6 + F8 dissolved):
   - JSONL append + atomic locking from `sea/src/file-lock.ts` and `knowledge.ts:7-167`.
   - Auto-regen summary from `knowledge.ts:244-393`.
   - Tag downgrade enforcers (`enforceSourceUrls`, `enforceDerivationChains`) ported as-is.
   - Graduation function shape from `knowledge.ts:501-564` — Tier 0/1/2 verification calls deferred to Phase 2.
   - **No mutable counters.** All metrics are pure functions over the store.

4. **`src/events.ts`** — new module per commitment 6 (fail-loudly):
   - Typed event records (`PRODUCE_OK`, `PRODUCE_FAIL`, `VALIDATE_OK`, `VALIDATE_FAIL`, `HALT_REQUESTED`, `CAP_TRIMMED`, `SELECTION_GUARD_INTERVENED`, `STORE_CLOBBER_RESTORED`, `MANDATE_EVALUATED`, …).
   - Append-only `events.jsonl`.
   - Lint rule (eslint plugin or codegen) rejecting `catch {}` blocks and any catch that doesn't emit an event.
   - This module is also the structural answer to F2/F3/F4: the conductor reads events.

5. **`src/conductor/` skeleton** — minimal (W6 ported, F2/F3/F4 fixed inline):
   - Selector entry point + **completion gate** (`open==0 && activeQuestionId==null` → transition + exit, before any LLM call). Fixes F2 in ~10 LOC.
   - **`state.haltReason` reader** before dispatch (~5 LOC). Fixes F3.
   - **Reflection-veto parser** (regex-light on critic output). Fixes F4.
   - Question-cap trim (port `question-caps.ts` shape).
   - Selection guards (port `selection-guards.ts`).
   - **Defer to Phase 2:** retrieve step, extract step (Zod schema), Tier 0/1/2 verifiers. The Phase 1 conductor skeleton can dispatch a no-op step to validate the events-and-store loop end-to-end.

6. **`src/lineage.ts`** — port (W7) + re-tune (O5):
   - Port `appendLineageEntry` shape verbatim.
   - **Fix score-piping** at the lineage write site (one-line fix for F7).
   - Phase 2: add finding-level typed-DAG provenance (article commitment 4).

7. **Repository assets to inherit (not code, but inputs to Phase 2):**
   - `sea/failure-patterns/` (13 files) — read as the spec for what SEA2 must not reproduce. Symlink or copy.
   - `sea/success-patterns/` (90+ files) — durable domain-expert prompts (W8). Treat as a starter library for the planner/extractor/verifier roles; do *not* port the per-project `library.jsonl` or scoring machinery.

8. **`CLAUDE.md`** (in repo, not the global one) — short by design (already drafted). No prose mandates. The CLAUDE.md grew from 88 lines in v014 to 118 lines in v081 by accumulating prose mandates; SEA2's CLAUDE.md must not undergo that growth.

**Explicitly excluded from Phase 1**:
- CLAUDE.md §10 prose (40+ lines of selection-mode prose) — re-derived in Phase 2 from the article's metrics, not inherited.
- `type-debt-mandates.ts` (O8 — pattern is re-emerged in events.ts; file is not ported).
- `expert-library.ts` + per-project `library.jsonl` (O2 — drop the scoring loop; preserve success-patterns/ as inputs).
- `expert-loop.ts` inner-iteration scaffolding (F9 + F10 + F11 — re-derived from retrieval-first; not ported).
- Persona evolution + meta-evolution writing into CLAUDE.md (W10 — preserve the *cadence* as a Phase 2 rhythm, drop the prose-mandate output target).

---

## Open questions

The audit could not answer without running SEA2 itself:

1. **Is the article's Tier 2 (isolated cross-family LLM verifier) feasible within Phase 2 cost budgets?** SEA's evaluator pattern works because it runs at iteration-rate (~minutes per call). Tier 2 on every finding at extract-rate could be 100× the calls. Conformal abstention's sample-rate parameter is the lever; the budget needs an empirical floor on a small au-token subset before Phase 2 commits.

2. **Does retrieval-first dissolve enough of `failure-patterns/` to justify dropping the persona/library?** This audit says yes. The comparison protocol (`see-the-research-done-cozy-diffie.md` Part D, au-token apples-to-apples on 12 pre-registered metrics) is the empirical test. If SEA2 underperforms on au-token, the success-patterns library may need to come back as a planner-prompt repository (not as a per-project JSONL).

3. **Does the article's provenance DAG schema accommodate SEA's `[DERIVED: exhaustive-search]` synthetic findings cleanly?** SEA creates a synthetic finding when a question exhausts — it has no premises, just a record-of-search-completed. The DAG schema needs a non-derived "negative result" variant or those records become orphans on cycle/orphan validation.

4. **What happens to au-token's `[DERIVED]` chains under SEA2's Tier 0 quote-match enforcement?** SEA2 will fail more findings on Tier 0 than SEA does on graduation. The question is whether the higher reject rate produces strictly better remaining findings, or fewer findings total (the comparison-protocol risk). au-token's iter 50-57 yield decay banner ("recent avg 9.4 f/disp vs prior 15.7"; "domain saturation: last 5 findings in previously-covered domains") is a natural place to run the comparison.

5. **Is meta-evolution worth keeping as a separate loop, or does it collapse into "the developer reviews events.jsonl weekly"?** SEA's `metaEveryN: 3` produced the 60+ CLAUDE.md revisions in `CLAUDE-history/`. Most of those revisions were prose mandates that SEA2 won't produce. The question is whether the *cadence* — a forced "stop and read your own debt" rhythm — is worth preserving as a Phase 2 mechanism, or whether it becomes a human-operated review of events.jsonl.
