# Success Pattern: landscape — self-hosted agent tooling surveyor (web-scraping + document-extraction focus)

## Strategy
Expert type "self-hosted agent tooling surveyor (web-scraping + document-extraction focus)" for landscape question.
Question: Which currently-maintained self-hostable web-search components and document → markdown converters can expose structured results to an agent in 2026? For search: SearXNG, camofox-browser, browser-use, Playwright-based scrapers, Searx, YaCy, self-hosted wrappers around Brave / Tavily. For doc ingestion: markitdown (Microsoft), Docling (IBM), MarkerPDF, MinerU, Unstructured, pandoc. For each: input coverage, output quality on non-trivial PDFs, compute cost, rate-limit / bot-detection exposure for search, license, active maintenance.

## When It Works
- Question type: landscape
- Converged in 4/5 iterations

## Evidence
- Dispatch: D11
- Question: LQ004
- Findings produced: 40
- Iterations: 4/5
- Status: answered

## Key Decisions
LQ004 answered across 4 iterations (228→233 findings, +5 this iter). Final 14-tool × 6-dimension matrix complete. Recommended stack: SearXNG + patchright/rebrowser-playwright for search+render, Docling (MIT, v2.89.0 ultra-active) primary for ingestion with MinerU (AGPL, OmniDocBench rank 3) as subprocess-isolated fallback, markitdown for PPTX, pandoc for text interchange. Skip Brave/Tavily (not self-hostable), Marker (OpenRAIL non-compete), and Unstructured OSS for PDF (paid-API capability ceiling). Supply-chain hardening required per 2026-03-24 litellm backdoor. Residual empirical-gate: YaCy index coverage + Docling exact OmniDocBench score - non-blocking for stack decision.