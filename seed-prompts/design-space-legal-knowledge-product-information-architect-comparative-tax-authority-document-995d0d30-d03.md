# Success Pattern: design-space — legal-knowledge-product information architect (comparative tax-authority documentation across SARS, SAIT/SAICA, Juta/LexisNexis, IRS, HMRC, ATO)

## Strategy
Expert type "legal-knowledge-product information architect (comparative tax-authority documentation across SARS, SAIT/SAICA, Juta/LexisNexis, IRS, HMRC, ATO)" for design-space question.
Question: What does a Library-equivalent entry look like in existing tax-knowledge products — SARS's own Interpretation Note structure, SAIT / SAICA technical material, Juta / LexisNexis annotated statutes, and international analogues (IRS Treasury Regulations + Revenue Rulings, HMRC Technical Manuals, ATO Public Rulings) — and what structural elements do they share or omit? Which elements of the SC2 schema (exact text + intended meaning + SARS view + BPRs + case studies + judicial trajectory + cross-reference edges + litigation frequency + divergence + amendment history + currency + audit trail) are load-bearing vs. ornamental when stress-tested against those reference classes?

## When It Works
- Question type: design-space
- Converged in 3/4 iterations

## Evidence
- Dispatch: D3
- Question: Q002
- Findings produced: 10
- Iterations: 3/4
- Status: answered

## Key Decisions
Q002 graduated to answered. Iter-3 upgraded 2 of 4 DERIVED reference-class cells to SOURCE via WebFetch: IRS 26 CFR 1.61-1 (Cornell LII mirror) and HMRC BIM00500 — both confirm F961's key structural claims (no litigation-frequency field, no typed judicial trajectory, no typed divergence; untyped-prose or syntactic-only cross-refs). Reference-class grade ledger now 4 SOURCE + 2 DERIVED (ATO, Juta/LN remain DERIVED-from-product-architecture priors); F969 argues verdict is robust to this residual gap because F962's load-bearing classification rests on goal.md SC dependency analysis, not on reference-class presence. ARCHETYPE D RECOMMENDATION STANDS unchanged with the four F966 schema refinements (E8 explicit [PIPELINE-NOT-YET-OPERATIONAL] tag, E9 typed-as-derived from E2-E5, E12 separated to metadata block, E7 MANDATORY-SEMANTIC-TYPED edges) and four distinct no-content tags. Three follow-up questions spawned: litigation-frequency pipeline scoping (unlocks SC10 + EV model), authoring protocol (SC2 second deliverable), and stress-test provision selection for the 15+ samples.