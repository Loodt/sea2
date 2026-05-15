# Success Pattern: landscape — security-token standards architect with SA regulatory + custody-platform expertise

## Strategy
Expert type "security-token standards architect with SA regulatory + custody-platform expertise" for landscape question.
Question: For a permissioned SA security token backed by an SPV, which token standard is optimal: ERC-20 (plain fungible, no transfer restrictions), ERC-1400 (partitionable security-token suite with forced transfers, document attachment, corporate actions), ERC-3643 / T-REX (permissioned transfers with on-chain identity + compliance checks), or a bespoke chain-specific design? For each: (a) maturity + audit coverage + production deployments; (b) custody support on SA-accessible platforms (VALR, Luno, AltCoinTrader + global: Fireblocks, BitGo); (c) ability to encode SA-specific compliance (FICA KYC, SARB exchange-control flags, lock-up windows); (d) transfer-restriction enforcement primitives; (e) gas / fee costs at expected throughput; (f) interoperability with existing tokenised-gold infrastructure (XAUT, PAXG, KAU).

## When It Works
- Question type: landscape
- Converged in 3/5 iterations

## Evidence
- Dispatch: D18
- Question: AUQ008
- Findings produced: 17
- Iterations: 3/5
- Status: answered

## Key Decisions
AUQ008 ANSWERED. Stage-3 custody-pathway verification confirms ERC-3643 / T-REX as default-preferred for Au-Token v1 across all 6 criteria. New evidence: (i) Fireblocks-Tokeny ERC-3643 turnkey custody is operational at scale across 1,300+ institutional customers, Polygon as reference chain (F1311); (ii) BitGo's RWA pathway routes through Polymesh L1, not ERC-3643 — creates Polymesh-bespoke as a live-candidate only-if BitGo is chosen custodian (F1312); (iii) VALR/Luno currently list Backed Finance xStocks (SPL Token-2022 + ERC-20 trackers without shareholder rights) — not precedent for permissioned ERC-3643 listing on SA platforms (F1313); (iv) Apex Group/Tokeny T-REX Ledger on Polygon + Apex's USD 3T fund-admin AUM materially strengthens ERC-3643 institutional infrastructure (F1314); (v) FSCA has no published token-standard position — SA pathway runs through Au-Token's own CASP licence application (F1315). Final ranking F1316: ERC-3643 default; CMTAT parallel-track for confidential-DvP only; Polymesh-bespoke conditional on BitGo custody; ERC-1400 risk-elevated; ERC-20 killed. Residual gap (SA-CASP listing precedent) is commercial discovery, not architectural blocker.