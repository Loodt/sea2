# Success Pattern: kill-check — open-source GPU driver researcher with Vulkan compute queue and NVK/Nouveau GSP-firmware expertise

## Strategy
Expert type "open-source GPU driver researcher with Vulkan compute queue and NVK/Nouveau GSP-firmware expertise" for kill-check question.
Question: Does the GSP firmware story on Turing+ (RTX 20xx and later) actually solve the reclocking problem for NVK, or does Turing have a different open-source-driver constraint (compute-queue maturity, VK_KHR_cooperative_matrix throughput parity, GSP availability) that partially-kills NVK inference viability post-2028?

## When It Works
- Question type: kill-check
- Converged in 4/5 iterations

## Evidence
- Dispatch: D35
- Question: LQ053
- Findings produced: 16
- Iterations: 4/5
- Status: answered

## Key Decisions
LQ053 ANSWERED. GSP firmware does solve the reclocking problem on Turing+ (F1454 empirical 8.5x Pascal->Turing), AND Turing no longer has a separate partially-killing constraint: NVK coopmat throughput reached 92% of proprietary (Karol Herbst XDC2025, F1457), closing the axis-c uncertainty. Post-2028 NVK-inference verdict: RTX 20xx TU10x PASSES (envelope ~33-40 t/s TG, above SEA floor). GTX 16xx TU116/TU117 STRUCTURALLY KILLED (no Tensor Cores, hardware-level — parity figure doesn't apply). Ampere+ remains safer floor for longevity but Turing TU10x now qualifies as viable, not fallback. Direct ggml-vulkan NVK-Turing tg128 devbox measurement is confirmatory only, not determinative.