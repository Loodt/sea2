# Success Pattern: design-space — local-inference stack architect (Pascal-class GPU constraints, agentic-harness integration)

## Strategy
Expert type "local-inference stack architect (Pascal-class GPU constraints, agentic-harness integration)" for design-space question.
Question: Given the hardware ceiling (6 GB VRAM, 12 GB usable RAM, Pascal CUDA 6.1), enumerate the distinct architectural choices for a local SEA stack across axes: (a) GPU-only / hybrid GPU+CPU / CPU-only, (b) single-model / multi-model-router (e.g., small for selection, large for expert-research), (c) existing-harness-wrapped / custom-minimal-harness, (d) Ollama-API / llama.cpp-server / vLLM-API / TabbyAPI. Produce the cross-product and mark which combinations are (i) physically viable, (ii) integration-feasible with SEA's provider layer, (iii) architecturally distinct enough to make the shortlist.

## When It Works
- Question type: design-space
- Converged in 2/4 iterations

## Evidence
- Dispatch: D4
- Question: LQ010
- Findings produced: 10
- Iterations: 2/4
- Status: answered

## Key Decisions
LQ010 answered in 2 iterations via pure derivation (1 validation search on Ollama structured-output internals). Stage 1 killed 38 of 48 cross-product cells (vLLM, TabbyAPI, custom-harness, GPU-only-router). Stage 2 killed hybrid-router, demoted CPU-only to contingency, and collapsed Ollama vs llama.cpp to a sub-tactical backend choice. Final shortlist = 2 architecturally distinct strategies: '7B-rescue-GPU-only' and '14B-hybrid-no-rescue', both wrapping Claude Code. Backend pick deferred to LQ011 empirical benchmark. Result aligns with the F968 existing shortlist direction — confirms we haven't missed a variant.