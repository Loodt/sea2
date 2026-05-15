# Success Pattern: data-hunt — Linux distribution lifecycle and legacy-driver operations engineer

## Strategy
Expert type "Linux distribution lifecycle and legacy-driver operations engineer" for data-hunt question.
Question: What hardware-shortlist alternatives exist for users with sunk-cost Pascal GPUs (GTX 10-series) post Oct-2028 NVIDIA proprietary driver sunset — is there a kernel/distro/Mesa pinning recipe that retains the legacy NVIDIA proprietary driver indefinitely on a frozen Linux base, and what are the security/compatibility tradeoffs?

## When It Works
- Question type: data-hunt
- Converged in 3/5 iterations

## Evidence
- Dispatch: D36
- Question: LQ051
- Findings produced: 18
- Iterations: 3/5
- Status: answered

## Key Decisions
LQ051 ANSWERED. Pascal retention post Oct-2028 is viable on a frozen Linux base for ~3-5yr (bounded by distro-LTS, not driver). Six-distro survey ranks NixOS best (declarative legacy_580 + atomic rollback) followed by Ubuntu 24.04 LTS (official nvidia-driver-580 + HWE-freeze + Pro to 2034); RHEL-9 derivatives weakest (no ELRepo kmod-nvidia-580xx). The R580 branch is the load-bearing pin target across all paths; sunset means no NVIDIA CVE patches after Oct-2028, mitigated by air-gapping. Major shortlist implication: sunk-cost Pascal users can remain on proprietary CUDA through ~2031-2033 without switching to NVK, reopening Pascal as a viable inference baseline within that horizon.