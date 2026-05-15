# Success Pattern: data-hunt — BFCL benchmark data analyst (agentic tool-use eval)

## Strategy
Expert type "BFCL benchmark data analyst (agentic tool-use eval)" for data-hunt question.
Question: What is the BFCL V4 Overall score for the peer Stack-B candidate models (Qwen-2.5-7B-Instruct-FC, Llama-3.1-8B-Instruct-FC, Mistral-Small-Instruct-FC) from the same 2025-12-16 snapshot, to populate a two-axis (AST vs agentic) comparison matrix?

## When It Works
- Question type: data-hunt
- Converged in 2/5 iterations

## Evidence
- Dispatch: D26
- Question: LQ041
- Findings produced: 10
- Iterations: 2/5
- Status: answered

## Key Decisions
Modified-peer-set path committed. Matrix delivered with three annotations: Qwen3-8B substitutes absent Qwen-2.5-7B (generation), Llama-3.1-8B-Prompt substitutes absent FC variant (mode), Mistral-small-2506 substitutes target Small checkpoint (checkpoint). Phi-4 14B is last on AST and third on agentic across the cohort, refuting the parameter-scale hypothesis behind LQ036 Stack-B. Stack-B AMBER verdict hardens toward RED. Spawn LQ041c to test Qwen3-8B-FC as Stack-A' alternative.