# Article-Alignment Audit

**Date:** 2026-05-15
**Subject:** SEA at v081 vs the spec (`agentic_research_reliability.md`)
**Companion doc:** [`sea-postmortem.md`](sea-postmortem.md) — the SEA-anchored audit. This doc is article-anchored.
**Purpose:** Catch what a SEA-anchored audit structurally cannot — gaps where the spec asks for something SEA doesn't have a name for, and credit where SEA already does something the spec describes.

> The two prior audits asked "what about SEA works?" This one asks "what about the spec is SEA already doing, and what is it not doing at all?" Different question, different findings.

---

## 1. The article's six load-bearing pillars vs SEA

The article opens with six pillars (§1). Each is a candidate to assess SEA against directly.

### P1. Retrieval-first architecture (§4.1)

> "Evidence enters at retrieval, not at generation. The generator operates over a tightly constrained context of vetted chunks. Anything outside the admitted evidence is, by construction, unavailable to the answer."

**SEA's state:** SEA has nothing here. The expert-loop step assembles a prompt with persona + summary + relevant findings, dispatches a single LLM call that does its own web search inside the model harness, parses the output for findings, and persists what survives. There is no `retrieve` stage that admits chunks before `extract` runs. Web search and synthesis happen in the same model call.

**Evidence:** `failure-patterns/upstream-crash-silent-bypass.md` is exactly the failure mode this pillar prevents. When sewage-gold iter 3's research step crashed, synthesis produced a 24KB report with 11+ phantom finding IDs — the model interpolated from training data because the architecture allows it to. Retrieval-first by construction makes this unrepresentable.

**Phase 1 implication:** The current SEA2 Phase 1 plan (per `sea-postmortem.md` §"Phase 1 implications") defers retrieve to Phase 2. The article ranks retrieval pipeline #3 in its build order (§15), ahead of NLI Tier 1 and Tier 2 verifier. The pillar this most directly serves is *the* central commitment.

### P2. Schema-enforced extract-then-verify (§4.2, §4.3)

> "Constrain the agent to extract claims *only* from admitted chunks. Verifier checks claim-to-chunk derivation. Output that does not parse against the schema is rejected by code, not by another LLM."

**SEA's state:** Partial. SEA's `Finding` interface is a TypeScript type with runtime validators (`enforceSourceUrls`, `enforceDerivationChains`) — these are shape-level enforcement. The schema is much thinner than the article's reference schema (§4.3), which adds: `verbatim_quote`, `char_range`, `paraphrase_of_quote`, `source.page/section/paragraph_id`, `derived_from` array (typed), `verifier_status` enum. SEA's enforcement is "URL starts with http" and "DERIVED has a premises array" — the latter is good, but the schema doesn't carry the fields the Tier 0 verification chain needs.

**Phase 1 implication:** Port `Finding` to Zod (commitment 2). Expand the schema to article-§4.3 shape. Reject non-parsing outputs in code. This is article-§15 build order #1, the cheapest immediate win.

### P3. Layered verification (Tier 0–3, §5)

> "Run cheap checks on everything, expensive checks only on what survives. Pipeline economics: total verification overhead 20–40% of researcher cost."

**SEA's state:** SEA has no Tier 0, no Tier 1, partial Tier 2, no Tier 3.
- **Tier 0** (deterministic, §5): SEA's `enforceSourceUrls` is a microscopic slice — it checks that the URL string is well-formed, not that it resolves. No DOI lookup, no CrossRef cross-check, no PDF parsing, no `char_range` validation, no quote string-match, no existence-in-retrieval check.
- **Tier 1** (NLI entailment, §5): nothing. SEA has no embedding model, no NLI head, no semantic claim-vs-source check.
- **Tier 2** (isolated LLM verifier, §5): SEA's independent-critic pattern (`assembleEvaluate`) is verifier-isolation done well *at output-level, not claim-level*. The critic scores an entire iteration's output against rubrics, not individual claims against source chunks. Same architectural primitive, wrong granularity.
- **Tier 3** (adversarial falsifier, §5): SEA has nothing. The critic asks "is this output well-scored?" — never "find evidence this claim is wrong."

**Phase 1 implication:** Tier 0 ships in Phase 2 alongside retrieve. Tier 1 (NLI) is Phase 2 or 3. Tier 2-at-claim-level repurposes the independent-critic pattern. Tier 3 is high-stakes-only; not Phase 1.

### P4. Formal methods on the formalisable subset (§8)

> "Lean, Z3, TLA+, policy-based automated reasoning for the parts that admit specifications. Formalise the load-bearing inferences."

**SEA's state:** SEA has nothing. No TLA+ workflow spec, no Z3 invariants, no Lean for math. au-token's quantitative claims (R690K-R2.13M cost band, 20/45/60-day SARS targets, R21-47m/yr non-liability) are exactly the kind of claim that should encode as Z3 constraints — they don't, currently.

**Phase 1 implication:** None. The article correctly flags (§8.6, §16) that cost-of-formalisation often exceeds cost of research. Phase 1 builds the seam where Z3-on-quantitative-claims could later plug in (the schema's `fact_type: "quantitative"` field). Actual formal methods deferred.

### P5. Statistical guarantees (§9 — conformal prediction, selective generation)

> "Conformal prediction for finite-sample coverage, selective generation for abstention."

**SEA's state:** SEA has nothing. No conformal calibration, no abstention thresholds, no risk-coverage curves. SEA's `confidence` field on findings is a float the LLM emits unconditionally; there is no calibration step that maps confidence to empirical reliability.

The plan commits to conformal abstention (CLAUDE.md commitment — implicit; the approved plan calls it out). This is one of the largest deltas SEA2 needs to build from scratch.

**Phase 1 implication:** None directly. But Phase 1's schema design must carry the fields conformal will eventually read — `confidence` plus enough provenance for risk-bucket assignment. Don't paint into a corner.

### P6. Process-aware evaluation and provenance artifacts (§11, §12)

> "Trace trees, evidence matrices, provenance DAGs, three-tier benchmarks."

**SEA's state:** Mixed.
- **Page-anchored citations (§11.1):** SEA's `Finding.source` is a URL string. No page, no section, no paragraph_id, no char_range. Tier 0 quote-verify is impossible without these.
- **Evidence matrix (§11.2):** SEA has nothing — no claim × source tabular artifact.
- **Provenance log (§11.3):** SEA's `changes.jsonl` is a per-iteration log; SEA2's planned `events.jsonl` is a closer match. Partial.
- **Provenance DAG (§11.4):** SEA's `Finding.derivationChain.premises` is a 1-deep premise array, not a graph. No cycle detection, no orphan detection, no "render prose from DAG" pattern. The conceptual primitive exists; the graph machinery doesn't.
- **Cryptographic ledgers (§11.5):** SEA has nothing. Not Phase 1.
- **Trace tree monitoring (§11.7):** SEA has flat span logs (`spans.jsonl`), not hierarchical. Article specifies hierarchical per planner / retriever / synthesiser / citation-extractor / verifier.

**Phase 1 implication:** Page-anchored fields go into the schema now. Provenance DAG mechanics (cycle/orphan detection) go into the integrate-step. Evidence matrix is a derived artifact, Phase 2.

---

## 2. Article's 8 failure classes vs SEA's 13 failure-patterns

The article (§3) defines 8 distinct failure classes. SEA's `failure-patterns/` library has 13 named patterns. Mapping each direction.

### 2.1 Article classes that SEA's evidence specifically validates

| Article class (§3) | SEA pattern that confirms it | Strength of confirmation |
|---|---|---|
| 3.1 Out-of-context (OOC) citation | `citation-reference-swap.md` | **Strong.** PMC 7581288 and PMC 8756590 swapped in sewage-gold report. Both papers exist; both metadata-check pass; the claim mapping is inverted. Article calls OOC "the most pernicious class because it passes structural checks." SEA's incident is the textbook example. |
| 3.2 Inference error / domain reasoning error | `derived-claim-blindspot.md` | **Strong.** Au-S bond claimed at 88 kJ/mol (actual ~209), compared to C-C at 345; comparison inverted. Article: "the math, chemistry, statistics, or domain logic is wrong even when inputs are correct." SEA's incident is exactly this. |
| 3.4 Mirage reasoning / plausible-but-unsupported | `upstream-crash-silent-bypass.md` | **Strong.** Sewage-gold iter 3: research step crashed (exit 1, 0 bytes); synthesis produced 24KB report with 11+ phantom finding IDs and 11+ new source citations, almost certainly from training data. Article: "fluent final outputs with no audit trail demonstrating the work was actually done." |
| 3.4 Plausible-but-unsupported (silent partial output) | `silent-truncation-cascade.md` | **Strong.** Sewage-gold iter 8-9: exit-0 with partial findings persistence; downstream synthesis cited phantom IDs; phantom rate 27% → 71%. Article does not name this sub-case explicitly but it falls cleanly under §3.4. |
| 3.5 Memory poisoning (loose mapping) | `additive-evolution-trap.md` | **Medium.** Persona grew monotonically (113 lines at iter 3) until catastrophic crash. Not "injected content" per article's strict definition, but the structural failure (unchecked accumulation across sessions) is the same shape. |

**Reading:** SEA's failure-pattern library is, in significant part, an in-the-wild instantiation of article §3 classes. The article describes the species; SEA's library documents the specimens. This is strong evidence that the article's taxonomy is *the right taxonomy* for the rebuild to organize around.

### 2.2 SEA failure-patterns the article does not name directly

These are SEA-discovered patterns that don't sit cleanly in article §3:

| SEA pattern | Closest article fit | Note |
|---|---|---|
| `heuristic-layer-ceiling.md` | §1 ("mechanical checks, not prompted rules") | Article asserts this as a principle; SEA's pattern is the operational diagnosis. Should port as "Anti-pattern A1" or similar in SEA2's architectural docs. |
| `closeout-drift.md` | (none) | A lifecycle-edge pathology specific to long-horizon agents. Article §3.4 covers some of it ("plausible-but-unsupported success" — re-surfacing prior research as new). Article doesn't separately name the "no completion gate" cause. SEA-novel. |
| `operator-kill-ignored-cascade.md` | §11.7 (trace-tree localisation) | The cascade depth-3 pattern is a workflow-control failure; article §11.7 frames it as a *monitoring* problem; SEA frames it as an *enforcement* problem. Both are right. |
| `protocol-artifact-loss-on-crash.md` | §11.3 (provenance log) | Article's "append-only log of every retrieval, every tool call, every claim emission" sidesteps this by construction. SEA's pattern is what happens without it. |
| `pipeline-step-deferral.md` | §4.2 (extract-then-verify) | Each step owning its writes is implicit in article's extract-step contract. SEA's pattern is the empirical proof that batched deferred writes are unsafe. |
| `evolution-persistence-failure.md` | §11.5 (cryptographic ledgers, loose) | Article's ledger pattern makes "lineage claims X but file is at Y" detectable by hash mismatch. SEA shipped neither. |
| `fix-resistant-identical-failure.md` | (none) | Diagnostic discipline pattern: "after 2 identical failures, the diagnosis is wrong." Article doesn't name it; SEA's lesson is sharper than anything in the article. Worth porting. |
| `context-exhaustion.md` | §3.3 (ranking bias / duplication) loose | SEA's context-exhaustion is more about persona+history bloat than retrieval ranking. Article would say: better retrieval reduces context pressure; SEA's experience suggests it's also a persona-size problem. |

**Reading:** SEA has 4-5 *lifecycle and infrastructure* failure-patterns the article doesn't address. These are SEA's institutional contribution. They should travel with the rebuild as named anti-patterns in `docs/anti-patterns.md` (Phase 1 doc).

### 2.3 Article classes SEA hasn't faced yet

Article classes with no SEA failure-pattern corresponding:

- **3.1 Fabricated citations** (DOI doesn't resolve) — SEA has nothing for this because it has no DOI resolution. The failure mode would manifest as graduated `[SOURCE]` findings citing dead URLs that nobody checks.
- **3.1 Metadata errors** (paper exists, wrong authors/year) — same reason.
- **3.1 Quotation errors** (verbatim quotes that don't appear in source) — same reason. SEA's `Finding` doesn't even have a `verbatim_quote` field.
- **3.3 Retrieval-stage failures** (coverage miss, ranking bias, duplication, off-topic) — SEA has no retrieve step, so no retrieval-pathology library. These will arrive in SEA2 once retrieve ships.
- **3.5 Inter-agent sycophancy** — SEA's multi-agent pattern is single-agent + critic (no debate); the sycophancy mode requires debate. Won't apply in SEA2 either unless multi-agent debate is added.
- **3.5 Lookup-as-memory confusion** — applies; see §3 below.
- **3.6 Adversarial failures** (prompt injection, encoding obfuscation) — SEA has nothing. au-token reads SARS regulatory documents; the indirect-prompt-injection surface is real and untested.

**Reading:** Roughly half of article §3 names failure classes SEA has no defensive position against because the architecture doesn't admit them yet. As SEA2 ships retrieve / extract / Tier 0, an equal-volume failure-pattern library should accumulate around the new failure surfaces. Budget for it.

---

## 3. Article mechanisms SEA partially has (port credit, not greenfield)

These are pieces of SEA that are already the article's mechanism in disguise. The first two audits didn't credit them as such. They should be ported to SEA2 with the article-mechanism label attached.

### W-A1. Verifier isolation (§4.4) — SEA has this at the wrong granularity

SEA's `assembleEvaluate` (`context.ts:336-410`) implements the article's verifier-isolation pattern almost verbatim: separate model (`evaluateModel: "sonnet"`), separate context (no persona, no goal), source materials only (output + rubrics + score trend), different prompt (framed as critique). The article-§4.4 box-tick is complete *at iteration granularity*.

What SEA does not do: run this verifier *at claim granularity*. Article §5 Tier 2 expects per-claim verification, sampled. SEA2's job is to preserve the architectural primitive and re-aim it.

### W-A2. Ledgered memory (§10) — SEA has the structural primitive

Article §10 mitigations name "ledgered memory — explicit append-only logs of accepted facts with provenance; rejection of contradictory writes; periodic audit." SEA's `findings.jsonl` is exactly this. The atomic-locking infrastructure makes "rejection of contradictory writes" a one-call away. SEA already lives in the article's recommended memory architecture for this pillar.

What SEA does not do: confidence-decayed retrieval (older / single-source facts retrieved with degraded confidence), explicit quarantine of new facts (`needsReview` is close but only fires on human-detected red flags, not on every new claim).

### W-A3. Provenance-log primitive (§11.3) — SEA has lineage + plans events.jsonl

SEA's `changes.jsonl` is a per-iteration provenance log; SEA2's planned `events.jsonl` (commitment 6, fail-loudly framework) is a per-event one. Together they cover article §11.3's "append-only log capturing every retrieval, every tool call, every claim emission." SEA2 should explicitly label its `events.jsonl` as the article-§11.3 implementation.

### W-A4. Trust cascade (§11.4 confidence propagation) — SEA has it for DERIVED

Article §11.4: "Confidence propagates through the graph: a claim derived from three `ESTIMATED` inputs cannot itself be `SOURCE`."

SEA's `graduateFindings` (`knowledge.ts:539-557`) enforces this for DERIVED → verified: every premise-ID in `derivationChain.premises` that points at a `F`-finding must itself be verified. The article's pillar exists in code at this seam. It needs upgrading to a full DAG, but the cascade discipline is real.

### W-A5. The independent-critic seam-as-Tier-2-foundation

Combining W-A1 with W-A3 + the events.jsonl plan: SEA2's Tier 2 isolated LLM verifier is *not* greenfield work. It is:
- The existing `assembleEvaluate` prompt structure, re-scoped to claim-level.
- The existing `evaluateModel` config (different model family).
- A new event type (`TIER2_VERIFICATION_REQUESTED` / `_PASSED` / `_FAILED`) in events.jsonl.
- A new caller site at extract-step output, sampled per article §5 economics (10-20%).

This is maybe 2-3 days of work, not 2-3 weeks. The architectural primitive is paid-for.

### W-A6. Asymmetric agent sizing (§4.5) — partial alignment

Article §4.5: "The researcher agent benefits from the strongest available model. The verifier does not need to match." SEA's `DEFAULT_LOOP_CONFIG` has `evaluateModel: "sonnet"` with the default researcher unspecified (typically the larger model). The asymmetry is partly there. SEA2 should formalise it: researcher = Opus-class, Tier 1 NLI = small specialised model, Tier 2 verifier = Sonnet-class different family, Tier 3 = Opus or larger different family.

---

## 4. Article mechanisms SEA explicitly lacks (greenfield work)

Ordered by article §15 priority. Each item is something the rebuild has to build, not port.

### G1. Tier 0 deterministic verification (§5, build-order #2)

The full Tier 0 stack:
- **DOI / arXiv / OpenAlex / Semantic Scholar Graph resolution** — verify the cited identifier resolves to a real record.
- **URL fetch with content hash** — verify the URL returns 200 and the content matches when re-checked.
- **PDF parsing** (pymupdf / pdfplumber / pypdf) — load source as text.
- **Quote string-match against source** at `char_range`, Levenshtein ≥ 0.95.
- **Metadata cross-check** — authors, year, title, venue.
- **Existence-in-retrieval check** — the chunk being cited was actually returned by the retriever this iteration.
- **Ledger consistency check** — claim doesn't contradict previously accepted facts in session.

SEA has the URL-shape check only. ~50-200 ms per claim per article §5. Catches fabricated citations, quote drift, metadata errors, conflation.

**Build window:** Phase 2, after retrieve ships (the existence-in-retrieval check has retrieve as a hard prerequisite).

### G2. Tier 1 NLI / embedding semantic verification (§5, build-order #4)

DeBERTa-v3-MNLI or RoBERTa-large-MNLI for entailment. Sentence-transformers for embedding-similarity threshold. SEA has nothing. ~50-500 ms per claim.

**Build window:** Phase 2 or 3. Article §15 puts it ahead of Tier 2. Local model + commodity GPU runs the cost down.

### G3. Tier 3 adversarial falsifier (§5, build-order #8)

A different model family, different prompt ("find evidence this claim is wrong"), search behaviour pointed at counter-evidence rather than support. Reserved for major decisions, regulatory claims, financial-model invariants, safety-critical conclusions. SEA has nothing.

**au-token relevance:** au-token's regulatory work (GAAR analysis, BPR strategy, MPRRA exclusion) is exactly the kind of high-stakes claim Tier 3 targets. If SEA2 ships Tier 3 only by the comparison-protocol run, au-token will be the proof.

**Build window:** Phase 3.

### G4. Citation Grounding Score (§6.2)

```
CGS = QuoteFidelity × CitationDensity × ProvenanceCoverage × EntailmentGrounding
```

Multiplicative (any zero collapses the score). SEA's scoring (accuracy 0.25 / coverage 0.20 / coherence 0.15 / insight 0.20 / process 0.20) is additive, weighted, and *prompt-generated by the critic* rather than computed from artifacts. Different mechanism entirely.

**Build window:** Phase 2-3 once Tier 0 + Tier 1 ship (CGS reads their outputs).

### G5. Three-axis citation audit (§6.3)

Pre-publication audit on (existence × metadata-correctness × context-appropriateness). Each cited reference gets a directive: Keep / Fix / Replace / Remove.

**Build window:** Phase 3, before any "release" of a research output.

### G6. Conformal prediction / selective generation (§9.3-§9.5)

Calibration set + held-out validation, conformity scores, quantile thresholds for abstention. Selective generation publishes only when score `s(X) ≥ τ`; expected correctness of accepted items ≥ τ.

**Build window:** Phase 3-4. Needs a calibration corpus (au-token retrospectively is one candidate).

### G7. Workflow verification (§8.1) — optional

TLA+ spec for agent state machine. Article calls out: `G(publish → citations_attached)`, `G(factual_claim → F verify_support)`, `G(high_risk_claim → F human_review)`. This proves the *control flow*, not the content.

**Build window:** Probably never, in scope. Article's §16 cost-of-formalisation honesty applies. Worth keeping as a future option for the conductor state machine.

### G8. Formal methods on quantitative claims (§8.3) — optional

Z3 on mass balances, stoichiometry, internal-consistency arithmetic. au-token has plenty of quantitative claims (R600k-800k/yr Δsavings, 12% Δrate, R 5.83M/yr distribution flow) — if any pair contradicts via simple arithmetic, Z3 catches it.

**Build window:** Optional Phase 4. Cheap to plug into the schema's `fact_type: "quantitative"` records.

### G9. Evidence matrix (§11.2)

Tabular `claim × source` with cell-level support type (verbatim / paraphrase / inference / contradiction). Derived artifact, rendered from the provenance DAG.

**Build window:** Phase 2, alongside provenance DAG.

### G10. Page-anchored citation fields in schema (§11.1)

`source.page`, `source.section`, `source.paragraph_id`, `char_range`, `verbatim_quote`, `paraphrase_of_quote`. Phase 1 should bake these into the Zod schema even if Tier 0 doesn't ship until Phase 2.

**Build window:** Phase 1 (schema fields); Phase 2 (the Tier 0 code that reads them).

### G11. Trace tree monitoring (§11.7)

Hierarchical trace separating planner / retriever / synthesiser / citation-extractor / verifier actions. SEA has flat `spans.jsonl`. The article's outcome-aware tail sampling (target edge cases, high-latency, anomalous outputs) layers on top.

**Build window:** Phase 2 (tree shape comes once the steps differentiate); Phase 3+ (sampling policy).

### G12. Three-tier evaluation (§12.1)

Tier 1: controlled offline on fixed corpora (FACTS Grounding, ALCE candidates). Tier 2: dynamic knowledge (FreshQA, LiveBench). Tier 3: interactive agent (BrowseComp-Plus, WebArena).

SEA evaluates per-iteration with a critic. There are no fixed-corpus benchmarks, no time-sensitive eval, no interactive harness.

**Build window:** Phase 3-4. The comparison-protocol au-token run is itself a Tier-3-flavoured eval but on one task, not a benchmark.

### G13. Decomposed A/G/U targets (§12.2)

World accuracy, groundedness, contextual appropriateness — measured separately. SEA conflates them in a single overall score.

**Build window:** Phase 3. Phase 1's schema should carry enough provenance that G and U can be computed retroactively from the store.

### G14. Calibration metrics suite (§12.5)

Expected Calibration Error, Brier score, NLL, risk-coverage curves, AURC. SEA has nothing.

**Build window:** Phase 3, alongside conformal.

### G15. Security / adversarial-input handling (§13)

Content sanitisation of retrieved chunks (strip instruction-like patterns), tool sandboxing, allowlists for domains/tools, human gates for side-effectful actions, prompt-injection test suites. SEA has nothing — au-token reads SARS regulatory documents and FSCA PDFs, exactly the indirect-prompt-injection surface.

**Build window:** Phase 3. Phase 1's retrieve plan should bake in content sanitisation hooks.

### G16. Memory consolidation / quarantine / confidence-decayed retrieval (§10)

Quarantine new facts in a holding area before promotion to retrievable memory. Confidence decays with age + single-source provenance. Source-trust-weighted aggregation.

**Build window:** Phase 2 (quarantine = staging area for un-Tier-0'd findings); Phase 3 (decay + aggregation).

---

## 5. Where SEA's evidence pushes back on or qualifies article claims

The article is the spec, but it is not above empirical correction. A few places SEA's experience adds nuance:

### Q1. Article §5 verification overhead target of 20-40%

The article asserts that with proper tiering, total verification overhead can be kept to 20-40% of researcher token cost. SEA hasn't run anything like this — its independent-critic runs at 100%+ overhead (one full critic call per iteration, with sonnet at output-rate). SEA cannot validate or push back on the 20-40% claim, but **it can be the first empirical test**. The comparison-protocol au-token run should measure: tokens for retrieve + extract + Tier 0 + Tier 1 sample + Tier 2 sample, vs tokens for SEA's existing pipeline. If SEA2 lands at 60-80% overhead the article's target is missed and needs revisiting.

### Q2. Article §10 lookup-as-memory generalisation ceiling

> "Agents accumulate disjointed facts indefinitely without developing internalised expertise, creating a generalisation ceiling."

SEA's `success-patterns/` library (90+ named domain-expert prompt templates, accumulated across 14+ projects, validated at v064 with 94% answered+productively-exhausted in the validation window) is a *partial* refutation of this. It is not "internalised expertise" in the neuroscience sense — the article is correct that there is no neocortical-style consolidation — but it is *durable*, *useful*, and *transferable* domain knowledge that the system produced via the persona-evolution loop.

The honest reading: the article's claim is correct in principle but SEA's experience suggests the gap between "lookup" and "consolidated expertise" is narrower than the framing implies, *if* the lookup output is high-quality persona prompts rather than raw retrieval chunks. SEA2 should not abandon the persona-evolution loop wholesale.

### Q3. Article §11.7 outcome-aware tail sampling vs SEA's dense full-trace

> "Outcome-aware tail sampling beats uniform random sampling for catching rare critical failures."

SEA logs everything — every dispatch, every iteration, every meta-evolution event. au-token's 76-entry `changes.jsonl` is dense, sourced, and audit-grade *without any sampling*. The article's tail-sampling pattern is the right answer at high volumes; at SEA's volume (~10 iterations/day per project, ~10 projects) it's premature optimisation. The pattern matters when the trace volume crosses operator-readability; SEA hasn't.

SEA2 should adopt full-trace by default, switch to sampled-tail when volume requires it. Not the other way around.

### Q4. Article §7 multi-agent debate — SEA doesn't use it, so doesn't validate either way

SEA's pattern is single-agent + critic, not multi-agent debate. The article's case against unrestricted MAD (§7.3 token explosion + sycophancy + accuracy regression) is well-supported but doesn't apply to SEA. The article's selective debate triggering pattern (§7.4) is also out of scope for SEA2's first build. Treat as Phase 4+ optional.

### Q5. Article §1 "prompted instructions are advisory"

SEA's `heuristic-layer-ceiling.md` is the strongest in-the-wild proof of this claim found in the audit. Three iterations of progressively-refined prose heuristics; none worked; the diagnostic conclusion was specifically "persona heuristics cannot fix harness-layer execution mechanics." The article asserts this as principle; SEA's pattern is the operational confirmation across 4+ projects. SEA2 should *cite SEA's pattern as evidence* in its architectural docs, not just inherit the article's claim.

---

## 6. Implementation-priority alignment: article §15 vs SEA2 Phase 1

The article specifies a 12-step build order. SEA2's current Phase 1 plan (per `sea-postmortem.md` §"Phase 1 implications") is infrastructure-heavy: types, providers, store, events, conductor skeleton. Where does the article say Phase 1 should add?

| Article §15 priority | Phase | Current SEA2 Phase 1 has it? | Should bring forward? |
|---|---|---|---|
| 1. Schema enforcement | 1 | Partial — Zod port planned, but minimal schema. Article's reference schema is richer (verbatim_quote, char_range, page, section, paragraph_id, derived_from, verifier_status). | **Yes — bake the article's full schema into Phase 1** even if Tier 0 doesn't ship yet. Don't paint into a corner. |
| 2. Tier 0 deterministic checks | 1-2 | No. | **Yes — at least the URL-resolve check (~50 LOC) and ledger-consistency check (~30 LOC) in Phase 1.** Quote-verify requires PDF parsing and retrieve; deferred to Phase 2. |
| 3. Retrieval pipeline | 2 | No. | No — Phase 1 builds the seam where retrieve plugs in (the `retrieve` step type + `admitted_chunk_id` field on Finding). |
| 4. NLI Tier 1 | 2-3 | No. | No. Phase 2. |
| 5. Tier 2 isolated verifier | 2-3 | Partial — the `assembleEvaluate` primitive is portable. | Re-aim at claim-level in Phase 2. Phase 1 just keeps the primitive intact. |
| 6. Workflow verification | n/a | No. | No. Optional, possibly never. |
| 7. Provenance DAG as authoritative output | 2 | Partial — `derivationChain.premises` exists. | **Yes — Phase 1 should add cycle + orphan detection** at integrate-step (~30 LOC). DAG-renders-prose is Phase 2. |
| 8. Tier 3 adversarial | 3 | No. | No. |
| 9. Formal methods | 4+ | No. | No. |
| 10. Evaluation harness | 3-4 | No (comparison-protocol au-token is custom, not a benchmark harness). | No. |
| 11. Conformal abstention | 3-4 | No. | No. Phase 1 just keeps the `confidence` field on Finding so calibration can run later. |
| 12. Security audit | 3 | No. | No, but **content-sanitisation hooks in the retrieve-step plan** (Phase 2). |

**Net adjustment to Phase 1:** the audit's currently-recommended Phase 1 ships *less* schema than the article wants. Specifically, the Phase 1 schema should add:

```typescript
// Additions to Finding interface per article §4.3
verbatim_quote?: string;
paraphrase_of_quote?: string;
char_range?: [number, number];
source: {
  id: string;       // doi:... | arxiv:... | url:https://...
  page?: number;
  section?: string;
  paragraph_id?: string;
};
fact_type: "quantitative" | "logical" | "citation" | "qualitative" | "inferred";
verifier_status: "pending" | "verified" | "failed" | "flagged";
admitted_chunk_id?: string;  // ties to retrieve step output
```

And `derived_from` becomes the renamed `derivationChain.premises` (the field name follows the article).

These fields can be optional in Phase 1 (no producer fills them yet) but must be defined so the Tier 0/1/2 work in Phase 2-3 doesn't trip over schema migrations.

---

## 7. Tooling reference vs SEA's stack

Article §15 lists specific tools by function. SEA's choices:

| Function | Article default | SEA's existing | SEA2 likely |
|---|---|---|---|
| Schema enforcement | Pydantic / JSON Schema / DSPy / Instructor | TS + handwritten validators | **Zod** (per CLAUDE.md) — sound choice, TS-idiomatic |
| Reference resolution | CrossRef / OpenAlex / Semantic Scholar Graph / arXiv API | (none) | Build wrappers per provider; cache resolutions |
| PDF parsing | pymupdf / pdfplumber / pypdf | (none) | Probably `pdf-parse` or `pdfjs-dist` (TS-native) |
| NLI / entailment | DeBERTa-v3-MNLI | (none) | Local model via `@xenova/transformers` or Python subprocess |
| Embedding similarity | sentence-transformers / OpenAI / Cohere / Voyage | (none) | Anthropic embeddings or OpenAI ada-002 |
| RAG evaluation | RAGAS / TruLens | (none) | Probably custom in TS — RAGAS is Python-only |
| Formal workflow | TLA+ / PRISM | (none) | Optional / probably skip |
| Theorem proving | Lean 4 + mathlib | (none) | Skip |
| SMT | Z3 / CVC5 | (none) | z3-py via subprocess only if Phase 4 fires |
| Calibration | netcal / conformal libraries | (none) | Custom in TS (small) |
| Conformal prediction | MAPIE / crepes | (none) | Custom in TS |
| Evaluation harnesses | HELM / lm-evaluation-harness / Inspect AI | (none — uses changes.jsonl + critic) | Inspect AI if Python is acceptable; else custom |
| Tracing | LangSmith / LangFuse / OpenTelemetry | spans.jsonl (own) | Keep events.jsonl; consider OpenTelemetry export hook in Phase 3 |
| Orchestration | LangGraph / CrewAI / Pydantic AI / Claude Agent SDK / OpenAI Agents SDK | own conductor | Stay with own conductor for control; **consider Claude Agent SDK** for the extract-step caller — gives session resumption, structured tool use, batch out of the box |

**The single largest tooling decision:** TypeScript vs Python. SEA is TS. The article's reference stack is Python-heavy (Pydantic, DSPy, MAPIE, RAGAS, lm-evaluation-harness, z3-py). Some SEA2 components (NLI, PDF parsing, Z3) are easier in Python. The honest options:

- **Stay TS, use subprocesses for Python tooling** (NLI, SMT). Simple, slow at boundary.
- **Stay TS, write minimal TS substitutes** (Zod for Pydantic; custom NLI prompt as Tier 2 substitute for Tier 1; skip SMT). Lower fidelity but uniform.
- **Mix: TS for store/conductor/extractor, Python for Tier 1 / Tier 0 PDF / future formal methods.** Two-language complexity, but matches the article's expected stack.

This decision is Phase 2, not Phase 1, but worth surfacing now.

---

## 8. Honest limits to acknowledge (article §16)

Article §16 calls out six open problems. Each affects SEA2's design:

1. **Open-world fact verification at scale.** au-token's tax-regulatory domain is exactly this: many paywalled SARS documents, ambiguous interpretations, source authority hierarchies that vary by case. The "evidence committee" pattern (downstream open-access papers that cite the inaccessible primary) is plausibly applicable to regulatory work via subsequent BPRs and case law citations — but expensive.

2. **Memory consolidation.** SEA's `success-patterns/` library is the closest thing to consolidation in the system and the article correctly flags it as not-quite-memory. SEA2 should preserve the directory as Phase 2 input *and explicitly mark this as an open problem in the rebuild's architectural docs* rather than pretending the persona prompts solve it.

3. **Conditional coverage.** The comparison-protocol metric "operator confidence" maps onto a conditional claim ("reliable on this au-token instance"). The article (§9.8) is clear that distribution-free conditional coverage is impossible. The honest framing for the comparison-protocol decision rule is: "SEA2 produces marginal-coverage guarantees across the au-token instance's claim distribution; operator confidence is a domain-expert judgement, not a mathematical guarantee."

4. **Multi-agent debate calibration.** Out of scope for SEA2 v1.

5. **Adversarial robustness on live web.** SEA's failure-patterns library has zero entries on prompt-injection. au-token reads regulatory PDFs that *could* contain instruction-like patterns. SEA2 should at minimum sanitise retrieved content patterns matching `^(IMPORTANT|SYSTEM|INSTRUCTION):` and similar — defensive even without a full attack surface model.

6. **Cost-of-formalisation.** Affects G7 / G8 dispositions. The audit's recommendation: don't.

7. **Evaluation of long-horizon agents.** au-token (40+ iterations) and video-marketing-agent (~20 iterations) are already long-horizon by article-§16 standards. The comparison-protocol is itself a long-horizon eval — itself a contribution if done well.

---

## 9. Revised Phase 1 implications

The SEA-anchored audit (`sea-postmortem.md` §Phase 1 implications) is mostly compatible with the article-anchored view. Additions and corrections:

**Carry forward unchanged:**
- `src/types.ts` core port (epistemic tag union, Finding/Question shape).
- `src/providers.ts` verbatim port.
- `src/store.ts` (atomic JSONL + summary regen + tag-shape gates).
- `src/events.ts` new module with typed event log + lint rule rejecting empty catches.
- `src/conductor/` skeleton with completion gate + haltReason reader + reflection-veto parser.
- `src/lineage.ts` with score-piping fix.
- Symlink `sea/failure-patterns/` and `sea/success-patterns/` as Phase 2 inputs.

**Adjust:**
- **Expand the Phase 1 schema** to article §4.3 shape (G10 above). Add `verbatim_quote`, `char_range`, `paraphrase_of_quote`, `source.page/section/paragraph_id`, `fact_type`, `verifier_status`, `admitted_chunk_id`, rename `derivationChain.premises → derived_from`. All optional in Phase 1; required when retrieve / Tier 0 ship in Phase 2.
- **Add Tier 0 stubs in Phase 1** (G1 partial): URL-resolve check (HEAD request, 200/404 → set `verifier_status`), ledger-consistency check (does this finding contradict an already-verified one in this session). ~80 LOC total. Doesn't need retrieve to ship.
- **Add DAG cycle + orphan detection at integrate-step** (G — article §11.4): when a Finding has `derived_from`, verify no premise points at the finding itself (cycle) and every premise resolves to an existing finding (orphan). ~30 LOC.

**Add to Phase 1 deliverables (was not in sea-postmortem.md):**
- `docs/anti-patterns.md` — port SEA's `failure-patterns/heuristic-layer-ceiling.md` + `closeout-drift.md` + `pipeline-step-deferral.md` + `fix-resistant-identical-failure.md` as named anti-patterns the rebuild commits not to reproduce. Each becomes a regression test in Phase 2+.

**Defer to Phase 2+ (per article §15):**
- Retrieve step (build #3).
- Tier 0 full stack — quote-verify needs PDF parsing + retrieve (build #2).
- Tier 1 NLI (build #4).
- Tier 2 claim-level verifier (build #5).
- Provenance DAG render-prose-from-graph (build #7).
- Citation Grounding Score (G4).
- Evidence matrix (G9).
- Tier 3 adversarial (build #8).
- Conformal abstention (build #11).
- Three-tier evaluation harness (build #10).

---

## 10. Net findings

1. **The article's failure taxonomy (§3) is the right taxonomy.** SEA's failure-patterns specifically instantiate at least 5 of the 8 article classes, with OOC citation, mirage reasoning, inference error, and plausible-but-unsupported as the strongest matches.

2. **SEA's failure-patterns add 4-5 lifecycle/infrastructure patterns the article does not name.** Worth porting as `docs/anti-patterns.md` — institutional contribution from SEA's 8 months of operation.

3. **SEA has more article-mechanisms-in-disguise than either prior audit recognised.** Verifier isolation, ledgered memory, provenance log primitive, trust cascade, asymmetric agent sizing — all partial implementations that the rebuild should explicitly inherit with article-mechanism labels.

4. **The largest greenfield work is the Tier 0–3 verification stack**, especially Tier 0 (DOI / CrossRef / URL-fetch / PDF-parse / quote-verify). SEA has nothing for this. Article ranks it #2 in build order; the rebuild must respect that.

5. **Phase 1 schema must be the article's full schema, not a minimal port of SEA's Finding type.** Adding 7-8 optional fields now prevents a Phase 2 schema migration. Cost is ~30 lines of Zod.

6. **A small set of cheap Tier 0 checks (URL-resolve + ledger-consistency, ~80 LOC) belongs in Phase 1**, not Phase 2. These run without retrieve, catch fabricated citations immediately, and prove the architecture before retrieve lands.

7. **SEA's success-patterns library is a partial refutation of the article's "lookup-as-memory generalisation ceiling" claim.** The article is correct in principle; SEA's evidence narrows the gap. Don't drop the persona-prompt asset.

8. **The TS-vs-Python tooling decision is the single largest Phase 2 architectural choice** and should be surfaced before retrieve / Tier 0 begin.

9. **The article's §16 honest-limits list applies to SEA2 directly.** au-token's regulatory domain is the open-world-verification-at-scale benchmark. The rebuild's claims about it should follow the article's defensible-claim template (§9.9 / §12.9).
