# Success Pattern: data-hunt — quantization-factuality benchmark analyst (HalluLens / TruthfulQA / hallucination-leaderboard literature specialist)

## Strategy
Expert type "quantization-factuality benchmark analyst (HalluLens / TruthfulQA / hallucination-leaderboard literature specialist)" for data-hunt question.
Question: Does Q4_K_M quantization shift HalluLens NonExistentRefusal ranking within 7-12B band, specifically for Llama-3.1-8B-Instruct (BF16 13.18% avg) vs Qwen2.5-14B-Instruct (BF16 29.64%)?

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D23
- Question: LQ032
- Findings produced: 11
- Iterations: 3/5
- Status: answered

## Key Decisions
Iter 3 closed F1608's weakest prior (assumed symmetric ±4pp drift) by finding benchmark-type-asymmetric Qwen drift data: factual benchmarks (MMLU/MATH/GPQA) show <1pp drift, while instruction-following (IFEval) shows up to 20% relative loss. HalluLens NonExistentRefusal is factual-refusal-style, so factual profile applies to both models. Refined worst-case envelope puts asymmetric ranking flip >8pp away from observed priors. Confidence: 0.88 on ranking-preserved. Absolute Q4_K_M values remain empirical-gated.