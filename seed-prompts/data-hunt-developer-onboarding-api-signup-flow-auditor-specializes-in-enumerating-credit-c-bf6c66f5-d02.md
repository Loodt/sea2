# Success Pattern: data-hunt — developer-onboarding / API signup-flow auditor (specializes in enumerating credit-card/phone/KYC/geo requirements from provider TOS + signup pages; familiar with ZA-IP restrictions on US/CN providers)

## Strategy
Expert type "developer-onboarding / API signup-flow auditor (specializes in enumerating credit-card/phone/KYC/geo requirements from provider TOS + signup pages; familiar with ZA-IP restrictions on US/CN providers)" for data-hunt question.
Question: Score sign-up friction for every provider surfaced by FLQ001 + FLQ005. For each: (a) is a credit card required at account creation? (b) is phone verification required? which country codes accepted? (c) is real-name / KYC authentication required (common for Chinese providers per local-llm-stack F1237/F1259)? (d) geographic IP restrictions (is the signup flow accessible from ZA / South African IPs, and from common VPN exits like US/SG/JP)? (e) corporate-only vs individual signup? (f) email-domain restrictions? Rank providers on a 0–3 friction score (0 = email-only; 1 = + phone; 2 = + card OR KYC; 3 = + phone + card + KYC or geographic exclusion). Identify the lowest-friction provider that still passes the minimum-fit bar from FLQ001.

## When It Works
- Question type: data-hunt
- Converged in 4/5 iterations

## Evidence
- Dispatch: D2
- Question: FLQ006
- Findings produced: 24
- Iterations: 4/5
- Status: answered

## Key Decisions
FLQ006 ANSWERED. Extended 16-provider friction matrix synthesized across iters 1-4. SCORE 0 (email-only): 9 Western providers including Cerebras, NVIDIA NIM, Groq, GitHub Models, Cloudflare Workers AI, OpenRouter, HuggingFace, Fireworks, DeepInfra. SCORE 1 (+phone or Google account): Gemini /v1beta/openai (min-fit VERIFIED F927), Mistral Experiment, Together.ai. SCORE 2 (+card/KYC, ESTIMATED): 6 Chinese-cluster providers. SCORE 3: none. Lowest-friction-passing-min-fit: Cerebras (score 0, gpt-oss-120b VERIFIED tools+strict-json F926). User goal <10-min-no-card RESOLVED via Cerebras primary + 6 SCORE-0 Western tertiary options. Empirical-gate residuals (Mistral ZA-OTP, Chinese-cluster precise scoring) are not blockers.