# Success Pattern: kill-check — llama.cpp Pascal backend engineer — deep knowledge of llama.cpp CUDA vs Vulkan code paths, Mesa/NVIDIA Vulkan ICD behaviour on GP106 under Ubuntu 24.04, and GGUF inference perf characterisation. Must evaluate install-footprint trade (apt-only Vulkan vs developer.nvidia.com CUDA 12.x pin) alongside the 10-32% TG delta and judge whether Vulkan becomes the default or the CUDA-escape-hatch.

## Strategy
Expert type "llama.cpp Pascal backend engineer — deep knowledge of llama.cpp CUDA vs Vulkan code paths, Mesa/NVIDIA Vulkan ICD behaviour on GP106 under Ubuntu 24.04, and GGUF inference perf characterisation. Must evaluate install-footprint trade (apt-only Vulkan vs developer.nvidia.com CUDA 12.x pin) alongside the 10-32% TG delta and judge whether Vulkan becomes the default or the CUDA-escape-hatch." for kill-check question.
Question: Should the local-llm-stack recipe default to llama.cpp's Vulkan backend (not CUDA) on Pascal cards given Issue #19817's unfixed 10-32% TG penalty? Vulkan adds a Mesa/RADV-or-NVIDIA-Vulkan-ICD dependency but eliminates the CUDA toolkit requirement entirely — possibly simplifying the install footprint.

## When It Works
- Question type: kill-check
- Converged in 5/5 iterations

## Evidence
- Dispatch: D8
- Question: LQ014
- Findings produced: 22
- Iterations: 5/5
- Status: answered

## Key Decisions
LQ014 answered narrowed-kill: do NOT default to Vulkan on Pascal. Issue #19817's 10-32% TG bonus is the 1B-model edge of the range; on shortlist-A's 7B target the TG bonus is only +10% while Vulkan imposes a structural 2.2x PP slowdown (triangulated across 3 Pascal GPUs, 4 models, 6+ months of llama.cpp commits). On a PP-heavy agentic harness that trade loses. Footprint (100-1000x smaller Vulkan add) and post-2028 risk (NVK open-source continuation vs security-dead CUDA) favor Vulkan but don't bind the 2026 recipe choice. Recipe: CUDA 12.x + driver 580 LTSB default with documented Vulkan escape-hatch and post-2028 migration note. One deferred caveat: llama.cpp-on-NVK-Pascal perf is unverified and should be benched before 2028 migration.