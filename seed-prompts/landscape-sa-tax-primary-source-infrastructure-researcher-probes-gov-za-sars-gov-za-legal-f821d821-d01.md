# Success Pattern: landscape — SA tax primary-source infrastructure researcher — probes gov.za, sars.gov.za/legal-counsel, saflii.org/za, gpwonline.co.za, taxcom.org.za; characterises URL patterns, indexes, update cadence, and retrieval mechanisms per source system

## Strategy
Expert type "SA tax primary-source infrastructure researcher — probes gov.za, sars.gov.za/legal-counsel, saflii.org/za, gpwonline.co.za, taxcom.org.za; characterises URL patterns, indexes, update cadence, and retrieval mechanisms per source system" for landscape question.
Question: What is the structural shape of the SA tax primary-source ecosystem — the accessibility, completeness, update cadence, URL patterns, citation-stability, and machine-retrievability of (a) Acts of Parliament consolidated current text, (b) SARS Legal Counsel publications (Interpretation Notes, Binding General Rulings, Binding Private Rulings, Practice Notes, Guides), (c) SAFLII tax case law (Tax Court, Tax Board, High Court, SCA, ConCourt), (d) Government Gazette for regulations and TLABs, (e) Davis Tax Committee reports? For each source: what is the canonical URL pattern, is there a published index, what is the update latency after a change, and what retrieval mechanism (direct fetch / scrape / RSS / API / none) is available?

## When It Works
- Question type: landscape
- Converged in 4/5 iterations

## Evidence
- Dispatch: D1
- Question: Q001
- Findings produced: 28
- Iterations: 4/5
- Status: answered

## Key Decisions
Q001 answered. Iter 4 closed the three tuple-grade gaps left after iter 3: (1) SARS BGR range sub-pages are HTML-tabulated with per-BGR metadata + Issue-N reissue marker, and the individual per-BGR URL is a semantic slug that returns the PDF directly — a high-value ingestion primitive (range = discovery, slug = retrieval) that generalises across all SARS Legal Counsel publication types. (2) SARS operates a /legal-counsel-archive/ surface with seven categories and distinct LAPD-prefixed URL scheme that encodes archive-vs-live status; child archive pages are freshly maintained even when the archive landing is stale. (3) sars.mylexisnexis.co.za is JS-rendered and subscription-boundaried — not zero-cost for an autonomous agent, forcing synthetic consolidation from gov.za as-enacted PDFs as the only zero-cost path to consolidated ITA text. Final architectural consequence: sa-tax-corpus-fetcher is feasible at Auditor Mode A across all 5 classes without paywall, subject to five build decisions on headless-browser, synthetic consolidation, SAFLII UA policy, SharePoint gazettes, and a unified SARS range+slug fetch template. Three downstream questions surfaced (amendment-Act enumeration for synthetic consolidation; SARS change-detection primitive for incremental polling; SAFLII compliant-UA policy).