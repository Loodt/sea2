# SEA2 Phase 2 — Retrieve + Extract + Tier 0/1 verification

**Date:** 2026-05-15
**Status:** Approved, ready to execute
**Estimated effort:** ~4–5 days of focused work
**Prerequisites:** Phase 1 closed (commit 55f9498). Comparison protocol pre-registered (commit 7aa3fe2).

---

## Context

Phase 1 left SEA2 with a runnable skeleton: schema, store, events, conductor gates, DAG, Tier 0 URL+ledger, integrate. Extract is a `noop` that admits hand-built fixtures. Phase 2 makes SEA2 actually research: a real retrieve → real extract → expanded Tier 0 + Tier 1 verification pipeline, built around the architectural commitment that **extract sees only chunks that retrieve has already admitted to the store**.

Three settled decisions before this plan:
1. **Retriever = harness subprocess + chunk store, not external API.** Claude Code (or Codex) has `WebSearch`/`WebFetch` built in — SEA2 spawns it for retrieve, captures what comes back, and persists chunks with stable IDs. No Tavily/Exa cost.
2. **Two Searcher implementations to start.** `SubprocessSearcher` (harness-driven web search) and `LocalCorpusSearcher` (pre-indexed regulatory PDFs for au-token's bedrock sources — MPRDA, NEM:WA, FSCA Crypto Declaration, the 2025 Bill, key cases). Camoufox/Tavily/etc. remain in the toolbox as future Searchers behind the same interface.
3. **Embeddings local, on CPU.** `sentence-transformers` + a small numpy index in sqlite. Sufficient for au-token scale; swappable later.

## Deliverables

### D1. Chunk schema + chunk store (~3 hours)

**Files:** `src/sea2/chunks.py`, integrate into `src/sea2/store.py`.

- `Chunk(BaseModel)` per article §4.3 retrieve output:
  - `chunk_id: str` — `sha256(url + start_offset + text)` truncated to 16 hex chars. Stable; the integrate step references findings to chunks by this.
  - `url: str`, `title: str | None`, `fetched_at: str`, `searcher: str`, `query: str`.
  - `text: str`, `start_offset: int`, `end_offset: int` (char offsets within the source page/document).
  - `source_hash: str` — sha256 of the full retrieved source body, so multiple chunks from the same fetch dedupe to the same source.
  - `mime: Literal["text/html", "application/pdf", "text/plain"]`.
  - `embedding: list[float] | None` — populated by D2's indexer, optional at admit time.
- `chunks_path(project_dir)`, `read_chunks()`, `find_chunk_by_id()` in `store.py`.
- Chunks are append-only JSONL like findings/events.
- Tests: schema roundtrip; chunk_id determinism; dedupe semantics.

### D2. Searcher interface + first two implementations (~1 day)

**Files:** `src/sea2/retrieve/{__init__,searcher,subprocess_searcher,local_corpus,fetcher,chunker}.py`.

- `Searcher` ABC: `search(query: str, *, k: int) -> list[ChunkCandidate]`. `ChunkCandidate` is a not-yet-stored hit — has the raw text + URL + searcher tag.
- `fetcher.py`: `fetch_url(url) -> FetchedSource` — `httpx` + `trafilatura` for HTML, `pymupdf` for PDFs. Strict timeout, retries with backoff, fails loudly via events.
- `chunker.py`: `chunk_text(text, *, target_tokens=500, overlap=50) -> list[ChunkSpan]`. Splits on paragraph then sentence boundaries; tracks char offsets.
- `subprocess_searcher.py`: spawns the configured provider (`claude` / `codex` / `codex-local`) with a structured search-and-fetch prompt. **The subprocess invocation is injected as a `Callable[[str], str]`** so tests can fake it. Output schema is JSON with a Pydantic validator at the boundary; malformed output emits `PRODUCE_FAIL`.
- `local_corpus.py`: BM25 (via `rank_bm25`) + cosine over `sentence-transformers/all-MiniLM-L6-v2` embeddings over a pre-built sqlite index. Pure-local, no network.

### D3. Retrieve stage (~half day)

**File:** `src/sea2/conductor/retrieve.py`.

- `retrieve(project_dir, question, *, searchers, k_per_searcher) -> RetrieveResult`.
- For each Searcher: search → fetch (if needed) → chunk → store. Each persisted chunk emits a `RETRIEVE_OK` event with `chunk_id`. Failures emit `RETRIEVE_FAIL` with reason.
- Dedupe by `chunk_id` — re-running retrieve on the same query reuses existing chunks rather than re-fetching.
- Returns the ordered list of admitted `chunk_id`s for the extract stage to consume.

### D4. Local-corpus pre-indexer (~3 hours)

**File:** `src/sea2/retrieve/index_corpus.py` (also a `__main__`).

- `python -m sea2.retrieve.index_corpus <path>` — walks a directory, extracts text from PDFs (pymupdf), HTML (trafilatura), and markdown, chunks per D2, embeds, writes to `corpus.sqlite`.
- For au-token: a `corpora/au-token-regulatory/` directory will hold the bedrock PDFs/HTML. Indexing is a one-time op per corpus.
- Verification: re-indexing the same directory is idempotent (chunk IDs identical).

### D5. Extract stage (~half day)

**File:** `src/sea2/conductor/extract.py`.

- `extract(project_dir, question, admitted_chunk_ids, *, subprocess_runner) -> ExtractResult`.
- Spawns a subprocess with a prompt that:
  - Receives the question + the admitted chunks' text inline.
  - **Forbids tool use** (`WebSearch`, `WebFetch`, etc.). The prompt template states this; we also pass `--disallow-tools` where the provider supports it.
  - Requires JSON output matching a list of `Finding`-shaped dicts, each carrying `admitted_chunk_id`.
- Validates each candidate against the schema. Drops any whose `admitted_chunk_id` is not in the provided set. Emits `PRODUCE_FAIL` for malformed JSON, `VALIDATE_FAIL` for schema misses.
- Returns the list of validated (but not yet integrated) Findings.
- Tests inject a fake `subprocess_runner` returning canned JSON.

### D6. Tier 0 expanded (~half day)

**File:** extend `src/sea2/verification/tier0.py`.

- `check_quote_supported(finding, chunk)` — substring-match `verbatim_quote` inside the chunk text. Normalises whitespace; emits `TIER0_QUOTE_OK` / `TIER0_QUOTE_FAIL`.
- `check_doi_resolves(finding)` — CrossRef API `https://api.crossref.org/works/{doi}`; emits `TIER0_DOI_OK` / `TIER0_DOI_FAIL`.
- `check_arxiv_resolves(finding)` — arXiv API head; same shape.
- `check_pdf_page_exists(finding, chunk)` — if `finding.source.page` is set and the chunk's `mime == "application/pdf"`, verify the page is within the document's page count (uses chunk's stored `source_hash` to look up the cached PDF metadata).

### D7. Tier 1 NLI (~half day)

**File:** `src/sea2/verification/tier1.py`.

- `check_entailment(finding, chunk) -> Tier1Result` — runs DeBERTa-v3-MNLI (`microsoft/deberta-large-mnli`) locally via `transformers`/`torch` or — if `SEA2_NLI_BACKEND=hf-inference` — via Hugging Face Inference API. Returns label ∈ {entailment, neutral, contradiction} + score.
- A finding's `verifier_status` graduates to `VERIFIED` only when Tier 0 (URL or DOI or arXiv) AND Tier 0 quote OK AND Tier 1 == entailment. Otherwise `FLAGGED` or `FAILED`.
- Feature-flagged by `SEA2_TIER1_ENABLED` env var, default off in CI (the model is ~750MB and downloads on first use).

### D8. Wire integrate (~2 hours)

- Update `integrate()` to:
  1. Resolve `admitted_chunk_id` against the chunk store. Reject if missing.
  2. Run `check_quote_supported` against the resolved chunk.
  3. Run `check_doi_resolves` / `check_arxiv_resolves` based on `source.id` prefix.
  4. Run Tier 1 NLI if enabled.
  5. Aggregate verifier status from all Tier 0 + Tier 1 signals.
- The existing Tier 0 URL + ledger checks stay.

### D9. End-to-end Phase 2 integration test (~2 hours)

`tests/test_phase2_e2e.py`:
- Build a tiny fixture corpus (one HTML + one PDF in a temp dir).
- Index it via `LocalCorpusSearcher`.
- Run retrieve → extract (fake subprocess returning JSON tied to chunks) → integrate.
- Verify: chunks persisted with stable IDs; findings reference real chunks; Tier 0 quote-check fires; events ledger has the expected event types in order.

## Explicitly NOT in Phase 2

- Tier 2 isolated cross-family LLM claim-verifier (Phase 3).
- Tier 3 adversarial falsifier (Phase 3).
- Conformal abstention (Phase 4).
- Citation Grounding Score and the three-axis citation audit (Phase 3).
- Real Anthropic web-search via SDK (Phase 3 — only when we have a reason to bypass the Claude Code subprocess path).

## Verification

Phase 2 is done when:
1. `uv sync && pytest && ruff check && mypy --strict src/sea2` clean.
2. End-to-end Phase 2 test (D9) green using a fake subprocess runner and a fixture corpus.
3. A manual smoke test of the LocalCorpusSearcher against the au-token regulatory bedrock PDFs returns sensible hits for at least 3 queries (e.g. "pre-2004 dumps regulatory regime", "FSCA crypto asset declaration", "MPRRA royalty residue stockpile").
4. The chunk store's `chunk_id`s are stable across re-runs of the same fixture (regression-tested).
5. Tier 1 is feature-flagged; with the flag off, the whole pipeline still runs and produces FLAGGED findings.

## References

- Phase 1 plan: `.claude/plans/sea2-phase-1-foundation.md`
- Article §15 build-order: `C:\Users\mtlb\Downloads\x article - agentic reseach reliability\agentic_research_reliability.md`
- Pre-registration: `docs/comparison-protocol.md`
