# Success Pattern: kill-check — NVIDIA Pascal/CUDA support-matrix archaeologist with llama.cpp build-flag fluency

## Strategy
Expert type "NVIDIA Pascal/CUDA support-matrix archaeologist with llama.cpp build-flag fluency" for kill-check question.
Question: Does NVIDIA GTX 1060 Mobile (Pascal GP106M, compute capability 6.1, 6 GB VRAM) run reliably under current NVIDIA driver (550.x / 560.x / 570.x branches) and CUDA 12.x on Ubuntu Server 24.04 in 2026, with no performance regression on llama.cpp's CUDA backend? Check: NVIDIA's official support matrix, latest Pascal-supported driver, CUDA 12.x Pascal deprecation status, llama.cpp's stated compute-capability floor, community reports of recent regressions. If Pascal is EOL or broken, the GPU-offload path collapses and every stack becomes CPU-only.

## When It Works
- Question type: kill-check
- Converged in 3/5 iterations

## Evidence
- Dispatch: D2
- Question: LQ005
- Findings produced: 16
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ005 ANSWERED: Pascal GTX 1060 Mobile runs reliably under nvidia-driver-580 + CUDA 12.x toolkit + llama.cpp on Ubuntu 24.04 in 2026, with sm_61 unconditionally in the upstream cmake default arch list (primary-source confirmed). Empirical baseline: ~28 t/s TG and ~417 t/s PP on Llama 2 7B Q4_0 — comfortably above 20 t/s viability bar. One non-fatal caveat: Issue #19817 documents 10-32% slower CUDA-vs-Vulkan TG on Pascal in 2026, with Vulkan as a clean workaround. Recipe valid through ~Aug 2028 (R580 LTSB security window). The GPU-offload assumption underlying the local-llm-stack shortlist holds; no collapse to CPU-only.