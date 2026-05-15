# Success Pattern: mechanism — llama.cpp grammar-compiler source reader

## Strategy
Expert type "llama.cpp grammar-compiler source reader" for mechanism question.
Question: Does llama.cpp's current json_schema_to_grammar.py compiler reliably handle the HybridResult schema feature subset (string, integer, enum-of-4-strings, array-of-string, required) without timeouts or silent feature drops? Single docs/code lookup against grammars/README.md and json_schema_to_grammar.py in the user's targeted llama.cpp version.

## When It Works
- Question type: mechanism
- Converged in 2/5 iterations

## Evidence
- Dispatch: D14
- Question: LQ022
- Findings produced: 11
- Iterations: 2/5
- Status: answered

## Key Decisions
Stage-2 per-feature dispatch audit confirms the HybridResult minimal schema (string, integer, enum-of-4, array-of-string, required) is fully and reliably supported by both the Python CLI reference and the C++ server-runtime port of llama.cpp's JSON-Schema-to-GBNF compiler at master pin 4fbdabdc (2026-04-16). All 5 primitives have explicit, tested dispatch branches with no documented limitation intersecting the subset and no Python-to-C++ drift. F908 (prior iter-2 provisional) graduates to 0.95 with pinned line cites; F905 drift-risk flag closes; F278 risk-register entry #4 closes. F1201 recommended-minimum constraint surface can be adopted without further compiler verification.