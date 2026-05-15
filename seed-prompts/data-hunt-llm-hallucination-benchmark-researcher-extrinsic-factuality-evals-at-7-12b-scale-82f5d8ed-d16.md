# Success Pattern: data-hunt — LLM hallucination-benchmark researcher (extrinsic/factuality evals at 7-12B scale)

## Strategy
Expert type "LLM hallucination-benchmark researcher (extrinsic/factuality evals at 7-12B scale)" for data-hunt question.
Question: Which 7-12B open-weight Instruct model has the LOWEST extrinsic hallucination rate on HalluLens or comparable benchmarks (Mistral-Nemo-12B, Hermes-3-8B, Tulu-3-8B as candidates)? Could change shortlist composition under URL-veracity-dominant verdict.

## When It Works
- Question type: data-hunt
- Converged in 4/5 iterations

## Evidence
- Dispatch: D16
- Question: LQ018
- Findings produced: 20
- Iterations: 4/5
- Status: answered

## Key Decisions
HalluLens Table 4 (arxiv 2504.17550v1) resolves LQ018 under URL-veracity-dominant verdict by supplying directly-comparable NonExistentRefusal false-acceptance rates across the substitute-candidate sweep: Llama-3.1-8B-Instruct wins decisively at 13.18% avg vs Mistral-Nemo-12B's 83.49%, with Qwen2.5-14B (29.64%) and Gemma-2-9B (40.09%) as middle options. Among the 3 named candidates, only Mistral-Nemo has data and it ranks near-worst. Recommendation: substitute Llama-3.1-8B-Instruct for Mistral-Nemo-12B on the shortlist, with refusal-calibration caveat (83% false-refusal on PreciseWikiQA makes Llama-3.1-8B safe-but-reserved; Qwen2.5-14B is the balanced alternative when attempts are operationally required). Hermes-3-8B and Tulu-3-8B remain data-gap and would need a local URL-veracity probe to rank.