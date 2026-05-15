# SEA2 Phase 1 Foundation — Plan

**Date:** 2026-05-15
**Status:** Approved, ready to execute
**Estimated effort:** ~2 days of focused work to a runnable skeleton
**Prerequisites:** SEA postmortem audit ([`docs/sea-postmortem.md`](../../docs/sea-postmortem.md)) + article alignment audit ([`docs/article-alignment-audit.md`](../../docs/article-alignment-audit.md)) — both complete.

---

## Context

SEA2 is a clean rebuild of [SEA](C:\Users\mtlb\code\sea) committed to the article's full reliability stack from day one (retrieval-first, schema-enforced extract-then-verify, tiered verification Tier 0–3, provenance DAG, conformal abstention). The two audits produced an aligned view of what Phase 1 builds; this plan turns that view into concrete commits.

Three decisions were taken before this plan was written, each documented in the audit chain:

1. **The fork is justified.** SEA's accumulated prose mandates ([`feedback_prompt_only_mandates`]) cannot be cleanly removed from inside SEA; rebuild is the cheaper path. (Approved plan: `~/.claude/plans/see-the-research-done-cozy-diffie.md`.)
2. **The architecture is article-spec, not SEA-port-with-fixes.** Seven non-negotiable commitments in [`CLAUDE.md`](../../CLAUDE.md): retrieval-first, schema-enforced, tiered verification from day one, provenance DAG first-class, code-enforced or nonexistent, fail loudly, one canonical counter.
3. **The language is Python.** SEA is TypeScript; SEA2 is Python. Reasoning in [`docs/article-alignment-audit.md`](../../docs/article-alignment-audit.md) §7 + the conversation that approved this plan: article's reference stack is Python (Pydantic, Instructor, DSPy, MAPIE, sentence-transformers, pymupdf, z3-py, Inspect AI); Tier 0–3 verification is the central commitment; mixed-language is the worst option; cost-of-being-wrong asymmetry favours Python. The SEA port becomes a ~2-day rewrite, not a multi-week migration.

## Deliverables

### D1. Toolchain bootstrap (~2 hours)

- `pyproject.toml` with Python 3.12 pin, configured for [`uv`](https://docs.astral.sh/uv/) (faster than poetry, simpler than rye)
- Dependencies (pinned):
  - `pydantic>=2.6` — schema enforcement
  - `httpx` — URL resolution (Tier 0 stub)
  - `filelock` — atomic JSONL locking
  - `anthropic` — Anthropic SDK provider
  - Dev: `ruff` (lint + format), `mypy` (strict), `pytest`, `pytest-asyncio`
- `.gitignore` — Python-shape (`__pycache__/`, `.venv/`, `.pytest_cache/`, `*.egg-info/`)
- `ruff.toml` — strict lint config including: `BLE001` (broad exception caught), `TRY` (tryceratops — catches empty `except`), custom rule that flags any file added to `docs/mandates/` without a corresponding `src/sea2/*.py` test reference. (The code-enforced-or-nonexistent commitment defended at CI.)

### D2. Schema (D2 is the most load-bearing single Phase 1 commit)

**File:** `src/sea2/models.py`

Port from `sea/src/types.ts` AND expand to the article §4.3 reference schema. **All article fields go in even though no producer fills most yet**, to prevent a Phase 2 schema migration.

```python
# Sketch — final form in code.
class EpistemicTag(StrEnum):
    SOURCE = "SOURCE"
    DERIVED = "DERIVED"
    ESTIMATED = "ESTIMATED"
    ASSUMED = "ASSUMED"
    UNKNOWN = "UNKNOWN"

class FactType(StrEnum):
    QUANTITATIVE = "quantitative"
    LOGICAL = "logical"
    CITATION = "citation"
    QUALITATIVE = "qualitative"
    INFERRED = "inferred"

class VerifierStatus(StrEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    FAILED = "failed"
    FLAGGED = "flagged"

class Source(BaseModel):
    id: str  # doi:10.1000/xyz | arxiv:2503.12345 | url:https://...
    page: int | None = None
    section: str | None = None
    paragraph_id: str | None = None

class Finding(BaseModel):
    id: str
    claim: str
    tag: EpistemicTag
    fact_type: FactType
    source: Source | None = None
    verbatim_quote: str | None = None
    paraphrase_of_quote: str | None = None
    char_range: tuple[int, int] | None = None
    confidence: float
    domain: str
    iteration: int
    status: Literal["provisional", "verified", "refuted", "superseded"]
    verified_at: int | None = None
    superseded_by: str | None = None
    derived_from: list[str] = Field(default_factory=list)
    verifier_status: VerifierStatus = VerifierStatus.PENDING
    admitted_chunk_id: str | None = None  # ties to retrieve step
    needs_review: NeedsReview | None = None
    # Optional engineering classification (carry from SEA)
    engineering_type: EngineeringType | None = None
```

Plus `Question`, `LineageEntry`, `ConductorMetric` ported from SEA's TS shapes (carry-over, not greenfield).

`Event` is new — see D4.

Tests: roundtrip serialize/deserialize each model against fixture JSONL; assert article-required fields are validated (e.g., `EpistemicTag.SOURCE` with `source=None` should be flagged at validation, not silently allowed).

### D3. Providers (~1 hour, mostly port)

**File:** `src/sea2/providers.py`

Port `sea/src/types.ts:1-79` provider abstraction verbatim. Add a 4th provider for direct Anthropic SDK (needed for Tier 2 cross-family verification — Tier 2 should not go through Claude Code CLI):

- `claude` (Claude Code CLI, default)
- `codex` (Codex CLI)
- `codex-local` (Codex + Ollama)
- `anthropic-sdk` (new — direct SDK, for verifier work)

`detect_provider()` mirrors SEA's env-var auto-detection (`CLAUDECODE=1`, `CODEX_CLI=1`, `SEA_PROVIDER`).

### D4. Append-only store + events (~half day)

**Files:** `src/sea2/store.py`, `src/sea2/events.py`

Per article §10 ledgered memory + commitment 6 fail-loudly.

`store.py`:
- `atomic_append_jsonl(path, entry: BaseModel)` — uses `filelock`; serialises Pydantic model; appends one line.
- `atomic_update_jsonl(path, mutator)` — read all, mutate in memory, atomic rewrite via temp file + rename.
- `read_findings(project_dir)`, `read_questions(project_dir)`, `read_events(project_dir)` — typed reads, fail loudly on parse error.
- `regenerate_summary(project_dir)` — port `enforceSummaryFreshness` + `enforceSummarySize` from `sea/src/knowledge.ts:244-393`. Deterministic; no LLM. 2KB cap.
- **No mutable cumulative counters.** All counts computed on demand from the store. (Commitment 7.)

`events.py`:
- `Event(BaseModel)` — typed union with `event_type` discriminator. Initial types:
  - `PRODUCE_OK`, `PRODUCE_FAIL`
  - `VALIDATE_OK`, `VALIDATE_FAIL`
  - `STORE_APPEND_OK`, `STORE_APPEND_FAIL`
  - `HALT_REQUESTED` (from reflection-veto parser)
  - `CAP_TRIMMED`, `SELECTION_GUARD_INTERVENED`
  - `STORE_CLOBBER_RESTORED`
  - `TIER0_URL_OK`, `TIER0_URL_FAIL`, `TIER0_LEDGER_CONFLICT`
- `emit(event)` — appends to `<project>/events.jsonl` atomically.
- Lint rule (ruff config) rejects `try/except: pass` and bare `except:` — every catch must `emit(PRODUCE_FAIL(...))` or rethrow.

### D5. Tier 0 cheap-wins (~half day)

Per article §15 build-order #2 and audit-alignment finding #6: ship the Tier-0 checks that don't need retrieve.

**File:** `src/sea2/verification/tier0.py`

- `check_url_resolves(finding: Finding) -> Tier0Result` — `httpx.head()` with timeout, follows redirects, returns `(verified, status_code, final_url)`. Populates `finding.verifier_status`. Emits `TIER0_URL_OK` / `TIER0_URL_FAIL`.
- `check_ledger_consistency(finding: Finding, existing: list[Finding]) -> Tier0Result` — naive contradiction detection: scan for findings in same domain with directly-opposing claims (heuristic v1: string-match negation tokens; v2: NLI in Phase 2). Emits `TIER0_LEDGER_CONFLICT` on hit.
- Both functions are pure (take inputs, return results); called from integrate-step in D6.

Total LOC target: ~150. Tests: each function gets unit tests with mocked `httpx` and fixture findings.

### D6. Conductor skeleton (~half day)

**Files:** `src/sea2/conductor/__init__.py`, `src/sea2/conductor/selector.py`, `src/sea2/conductor/integrate.py`

Minimal — enough to validate the events-and-store loop end-to-end with a no-op extract step.

- **Completion gate** (fixes [`closeout-drift.md`](https://docs/anti-patterns.md#closeout-drift) in code): at top of `select`, if `len(open_questions) == 0 and active_question_id is None`: transition state to `completed`, write summary terminus, exit clean. ~15 LOC.
- **haltReason reader** (fixes [`operator-kill-ignored-cascade.md`](https://docs/anti-patterns.md#operator-kill-ignored-cascade) in code): before any LLM call, read `state.halt_reason`; if non-null and status == "completed", exit with `HALT_REQUESTED` event. ~5 LOC.
- **Reflection-veto parser**: regex-light on prior critic output for "do not dispatch" / "should be completed" / "halt pending"; emits `HALT_REQUESTED`. ~20 LOC.
- **Question-cap trim** (port `sea/src/question-caps.ts` shape, minus prose modes): per-dispatch cap, iter-boundary cap, type-queue cap. Drop the prose-only modes (exploit / closure / non-closing / thin-closure) — those re-derive in Phase 2 from retrieval/extraction/verification metrics.
- **Selection guards** (port `sea/src/selection-guards.ts`): non-open-redispatch, re-dispatch type-mismatch, same-type-cap. Verbatim port.
- **Integrate step**: validates incoming `Finding` against schema (D2), runs Tier 0 checks (D5), runs DAG cycle + orphan detection (D7), atomic-appends to store via D4.

No retrieve, no real extract — Phase 2. A stub `extract_noop()` that returns hardcoded fixtures is enough to prove end-to-end flow in tests.

### D7. Provenance DAG primitive (~2 hours)

**File:** `src/sea2/verification/dag.py`

Per article §11.4 and audit-alignment finding #3. SEA's `derivationChain.premises` is a 1-deep array; this adds the graph mechanics.

- `validate_dag(finding: Finding, existing: dict[str, Finding]) -> DagResult` — for `finding.derived_from`: check no premise is `finding.id` (immediate cycle); transitively walk premises and detect cycles; check every premise-ID resolves to an existing finding (orphan detection). Returns `(valid, cycle_path | None, orphans | None)`.
- `propagate_confidence(finding: Finding, existing: dict) -> EpistemicTag` — article §11.4: "a claim derived from three ESTIMATED inputs cannot itself be SOURCE." If any premise is `ESTIMATED` or weaker, the derived finding's effective tag is bounded by the weakest premise. Returns the bounded tag.

Called from integrate-step in D6. Fails loudly via `VALIDATE_FAIL` event on cycle/orphan.

### D8. Lineage (~1 hour, port)

**File:** `src/sea2/lineage.py`

Port `sea/src/conductor.ts:1125-1148` `appendLineageEntry` shape. Add **score-piping fix** at the lineage write site (one-line fix for infra-debt #5, [SCORE_FIELD_LOSS]). Phase 2 adds the typed-DAG upgrade.

### D9. CLAUDE.md (already drafted, no change)

The [`CLAUDE.md`](../../CLAUDE.md) in repo is already short by design. Phase 1 does not touch it. The 7 commitments are the spec.

### D10. Documentation

- **`docs/anti-patterns.md`** — new Phase 1 deliverable surfaced in alignment audit. Port the 4 SEA failure-patterns the article does not name:
  - [`heuristic-layer-ceiling.md`](C:\Users\mtlb\code\sea\failure-patterns\heuristic-layer-ceiling.md) — the meta-pattern: prose mandates fail to fix harness-layer execution.
  - [`closeout-drift.md`](C:\Users\mtlb\code\sea\failure-patterns\closeout-drift.md) — no completion gate → score decay across closeout iterations.
  - [`pipeline-step-deferral.md`](C:\Users\mtlb\code\sea\failure-patterns\pipeline-step-deferral.md) — "deferred to summarize" loses writes.
  - [`fix-resistant-identical-failure.md`](C:\Users\mtlb\code\sea\failure-patterns\fix-resistant-identical-failure.md) — diagnostic discipline: after 2 identical failures, the diagnosis is wrong.

  Each becomes a regression-test target in Phase 2+. Rebuild commits not to reproduce these.

- **`seed-prompts/`** — copy SEA's `success-patterns/` (90+ named domain-expert prompts) renamed from "patterns" framing. Phase 2 input for planner/extractor/verifier role prompts.

- **`docs/sea-postmortem.md`** and **`docs/article-alignment-audit.md`** — already written; leave in place.

## Execution order

Within Phase 1, run sequentially (each depends on the previous):

1. D1 — toolchain (1-2 hours)
2. D2 — schema (3-4 hours; this is the load-bearing commit, give it the time)
3. D3 — providers (1 hour, mostly port)
4. D4 — store + events (3-4 hours)
5. D5 — Tier 0 cheap-wins (3-4 hours)
6. D6 — conductor skeleton (3-4 hours)
7. D7 — DAG primitive (2 hours)
8. D8 — lineage port (1 hour)
9. D10 — docs (2 hours)

Total: ~20 hours of focused work, ~2 working days at a sustained pace.

Each step closes with: `pytest` passing, `ruff` clean, `mypy --strict` clean. No commits with failing checks.

## Explicitly NOT in Phase 1

Deferred to Phase 2 per article §15 build order:

- Retrieve step. **Worth re-visiting if Phase 2 doesn't start within 2 weeks of Phase 1 close.** The audit's adjusted recommendation is that retrieve may want to come forward if there's any latency between phases — a thin retrieve (Anthropic web-search tool + chunk store + `admitted_chunk_id` plumbing) is ~1-2 days and makes the system demonstrable end-to-end.
- Full Tier 0 (DOI / arXiv / CrossRef / quote-verify / PDF parse). Quote-verify needs PDF parsing and retrieve; the URL-resolve + ledger stubs are the Phase 1 down-payment.
- Tier 1 NLI / embedding verification.
- Tier 2 isolated LLM claim-verifier (the primitive ports from SEA's `assembleEvaluate`; re-aim at claim-level in Phase 2).
- Tier 3 adversarial falsifier.
- Citation Grounding Score, evidence matrix, three-axis citation audit.
- Conformal abstention.
- Three-tier evaluation harness.
- TLA+ workflow verification (probably never).
- Z3 / Lean on formalisable claims (probably never; optional Phase 4).

## Open decisions surfaced but not resolved in Phase 1

These need answers before Phase 2 but not before Phase 1:

1. **Retriever architecture.** Options: (a) Anthropic web-search tool (cheap, native), (b) hybrid sparse + dense with a local vector store (article §15 hint at hybrid ranking, ontology re-ranking), (c) commercial RAG like Exa / Tavily. Decision shapes the chunk schema and the events.jsonl chunk-record format.

2. **NLI model choice.** DeBERTa-v3-MNLI is the article's default; smaller distilled options exist. Local GPU vs CPU vs hosted-inference is a deploy-environment question.

3. **Embedding provider.** OpenAI / Cohere / Voyage / Anthropic / sentence-transformers local. Cost vs latency vs quality tradeoff.

4. **The 12 comparison-protocol metrics.** Plan Part D commits to 12 pre-registered metrics for the au-token apples-to-apples run. **Must be enumerated before SEA2's first au-token dispatch** to avoid reverse-rationalising post-results. Plausibly ~1 hour of work — should happen after Phase 1 closes and before Phase 2's retrieve dispatches anything.

5. **Adversarial content-sanitisation policy.** au-token reads SARS regulatory PDFs and FSCA documents — indirect prompt injection is a real surface. Phase 2's retrieve step needs at minimum a basic sanitisation pass (strip `^(IMPORTANT|SYSTEM|INSTRUCTION):` and similar patterns from retrieved content).

6. **Calibration corpus plan.** Conformal prediction (Phase 3-4) needs a calibration set; au-token alone isn't one. The comparison-protocol run should produce calibration data as a byproduct — every claim logged with confidence + Tier 0/1/2 verdicts + post-hoc human-judged accuracy. Phase 1's events.jsonl schema should already accommodate this even though calibration is far downstream.

## Verification

Phase 1 is "done" when:

1. `uv sync && pytest && ruff check . && mypy --strict src/sea2/` all pass clean.
2. An integration test exists that runs the full pipeline end-to-end with `extract_noop()`: appends a fixture finding via the integrate-step, runs Tier 0 (URL + ledger), runs DAG validation, persists via store, emits the corresponding events to events.jsonl. Read-back roundtrip confirms.
3. `docs/anti-patterns.md` exists with the 4 ported anti-patterns and explicit "rebuild commits not to reproduce" framing.
4. `seed-prompts/` directory contains the success-patterns copy.
5. CI lint rule rejecting `try/except: pass` is wired and tested.
6. The completion gate, haltReason reader, and reflection-veto parser are each individually testable with unit tests demonstrating the failure modes they prevent (closeout-drift, operator-kill-ignored-cascade, ignored-critic-veto).

After Phase 1 closes: take a beat, re-read the 12-metrics gap (open decision #4), then enter Phase 2 with retrieve + Tier 0 quote-verify + Tier 1 NLI as the next concrete deliverables.

## References

- Article (spec): `C:\Users\mtlb\Downloads\x article - agentic reseach reliability\agentic_research_reliability.md`
- Approved fork plan: `~/.claude/plans/see-the-research-done-cozy-diffie.md`
- SEA postmortem audit: [`docs/sea-postmortem.md`](../../docs/sea-postmortem.md) — per-component disposition (port verbatim / port and re-tune / re-derive / drop)
- Article alignment audit: [`docs/article-alignment-audit.md`](../../docs/article-alignment-audit.md) — gap analysis vs spec
- SEA failure-patterns library: `C:\Users\mtlb\code\sea\failure-patterns\` (13 files) — read as the spec for what SEA2 must not reproduce
- SEA success-patterns library: `C:\Users\mtlb\code\sea\success-patterns\` (90+ files) — copied to `seed-prompts/` as Phase 2 input
