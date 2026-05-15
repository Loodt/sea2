# Success Pattern: data-hunt — LLM cost-optimization and multilingual deployment analyst

## Strategy
Expert type "LLM cost-optimization and multilingual deployment analyst" for data-hunt question.
Question: What's the cheapest LLM API + model that meets the bar for a sustained child-mentor session? Bar: instruction-following at age-3-vocabulary, age-7-vocabulary, age-9-vocabulary; Afrikaans fluency; latency <1.5s for voice; per-session cost target <ZAR 1; willingness to maintain the locked persona/doctrine without excessive guardrails breaking character.

## When It Works
- Question type: data-hunt
- Converged in 4/5 iterations

## Evidence
- Dispatch: D26
- Question: JQ042
- Findings produced: 22
- Iterations: 4/5
- Status: answered

## Key Decisions
The cheapest LLM API meeting all Jarvis criteria is Gemini 2.5 Flash-Lite at $0.10/$0.40 per MTok — all three age bands fit under ZAR 1 without any optimization (3yo=ZAR 0.11, 7yo=ZAR 0.44, 9yo=ZAR 0.80). A critical pricing correction (F2057) eliminated Claude Haiku 4.5 from contention: at $1.00/$5.00 per MTok it's 10× more expensive and fails the 9yo cost target even with maximum caching. The recommended architecture is a tiered model router: 2.5 Flash-Lite for 3yo/7yo, 3.1 Flash-Lite for 9yo Socratic sessions (needs sliding window + caching but delivers 2.1× intelligence uplift). Four binding unknowns — Afrikaans fluency quality, persona/doctrine lock under Gemini's child safety floor, verbosity control, and 9yo Socratic quality — require an empirical trial (F2061: 30 test dialogues on Google free tier at $0 cost).