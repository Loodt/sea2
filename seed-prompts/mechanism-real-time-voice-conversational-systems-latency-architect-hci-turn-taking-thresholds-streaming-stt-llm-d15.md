# Success Pattern: mechanism — real-time voice/conversational-systems latency architect (HCI turn-taking thresholds + streaming STT/LLM/TTS pipeline design)

## Strategy
Expert type "real-time voice/conversational-systems latency architect (HCI turn-taking thresholds + streaming STT/LLM/TTS pipeline design)" for mechanism question.
Question: What end-to-end voice latency is acceptable for a child to feel 'a person is talking to me' vs. 'a machine is responding'? What latency budget breakdown (STT + LLM + TTS + UI) supports that? What architectural patterns (streaming TTS, speculative response, partial-result UI) close the gap?

## When It Works
- Question type: mechanism
- Converged in 3/5 iterations

## Evidence
- Dispatch: D15
- Question: JQ044
- Findings produced: 22
- Iterations: 3/5
- Status: answered

## Key Decisions
JQ044 answered. Adult-baseline perception thresholds (F910-F914) with child-adjusted +200ms extrapolation (F915) yield a four-band model (F916): simple-turn P50 500-1000ms, reflective-turn P50 1000-1700ms, simple-turn P95 <=1500ms, hard ceiling 2500ms. Budget decomposition (F935): 930ms simple-turn P50 = VAD 300 + STT 150 + hops 50 + LLM 280 + TTS 90 + transport 30 + UI 30, achievable with WebRTC + Groq/Haiku/Flash-Lite + Cartesia + streaming partials + barge-in. Simple-turn P95 sits at the 1500ms edge with zero margin. Architectural patterns (F933) — filler, speculative dual-track, streaming everywhere, barge-in — are required not optional. Cascaded pipeline is the only controllable path given Jarvis locked-persona constraints; unified speech-to-speech's 200-250ms is forfeit. Three follow-up questions surfaced: empirical child pilot (data-gap), Afrikaans TTS availability (capability check), persona-consistent filler design.