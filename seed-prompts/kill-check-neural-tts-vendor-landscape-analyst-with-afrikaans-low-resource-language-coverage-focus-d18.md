# Success Pattern: kill-check — neural TTS vendor-landscape analyst with Afrikaans/low-resource-language coverage focus

## Strategy
Expert type "neural TTS vendor-landscape analyst with Afrikaans/low-resource-language coverage focus" for kill-check question.
Question: Does Afrikaans TTS (Jarvis locked language) exist at Cartesia/Deepgram/ElevenLabs TTFA tier, or does Afrikaans voice synthesis force a higher TTFA floor that breaks the F935 budget?

## When It Works
- Question type: kill-check
- Converged in 2/5 iterations

## Evidence
- Dispatch: D18
- Question: JQ076
- Findings produced: 5
- Iterations: 2/5
- Status: answered

## Key Decisions
Afrikaans TTS is not available at the Cartesia/Deepgram/ElevenLabs-Flash 40-135ms TTFA tier. Cartesia (F901) and Deepgram (F902) omit Afrikaans entirely; ElevenLabs Flash v2.5/Turbo v2.5 (F906) omit Afrikaans; only Eleven v3 covers Afrikaans (F903) but is explicitly not a real-time model (F907) with likely 500-1500ms TTFB (F908). Azure af-ZA AdriNeural (F909) exists at ~200-400ms TTFB — viable but 2-4x higher floor than the F935 90-150ms TTS allocation. The tier-1-Afrikaans hypothesis is KILLED (F910); the survival path requires either (a) Azure af-ZA with budget recalibration, (b) relaxed ~1700ms ceiling for Afrikaans children, or (c) OSS self-host. Two residual uncertainties spawned as follow-ups: measured Azure af-ZA TTFB and Piper/XTTS Afrikaans voice availability.