# Success Pattern: kill-check — energy-harvesting unit-economics analyst (TEG/PV/piezo BOM + SKU scoping)

## Strategy
Expert type "energy-harvesting unit-economics analyst (TEG/PV/piezo BOM + SKU scoping)" for kill-check question.
Question: Can the harvester hardware path be redesigned or narrowed enough to meet the USD 0-3 residual harvester burden required by the roll-of-stickers cost envelope, or does the self-powered thesis need to exclude TEG-based stickers from the first commercial SKU?

## When It Works
- Question type: kill-check
- Converged in 2/5 iterations

## Evidence
- Dispatch: D8
- Question: Q010
- Findings produced: 12
- Iterations: 2/5
- Status: answered

## Key Decisions
Stage-2 BOM decomposition indicates a TEG-based sticker harvester requires (at minimum) a TEG element/module, an energy-harvesting PMIC (often with added magnetics), storage, and—critically—thermal-mechanical structures (heat exchanger/contact + heat sink/spreader) to sustain ΔT. Supplier list pricing anchors a dedicated TEG-class harvesting PMIC at about $4.07 even at 1ku list, already above the USD 0–3 residual-harvester target before the TEG element or mechanics. A 2023 open-access iScience review reports module-cost scaling for mainstream BiTe TEG modules (down to ~$0.8/W at 300k installed modules) and that modules can dominate system cost (~75%), implying the TEG element remains a major cost driver even at scale. Therefore, the roll-of-stickers cost envelope is not plausibly compatible with TEG-based self-powered stickers for the first commercial SKU; the self-powered thesis should exclude TEG stickers from the initial roll SKU and treat any future TEG option as requiring a fundamentally different (currently unproven) architecture and vendor-cost evidence.