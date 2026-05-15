# Success Pattern: synthesis — architecture risk synthesist

## Strategy
Expert type "architecture risk synthesist" for synthesis question.
Question: What is the consolidated architecture risk register for Jarvis v0? Enumerate each remaining material risk, its evidence basis, whether it is architecture-closed vs empirical-gated, the mitigation or fallback already chosen, and the exact handoff condition to jarvis-personas or the build project.

## When It Works
- Question type: synthesis
- Converged in 3/5 iterations

## Evidence
- Dispatch: D47
- Question: Q002
- Findings produced: 11
- Iterations: 3/5
- Status: answered

## Key Decisions
[DERIVED] Q002 now closes as a three-row consolidated risk register. [DERIVED] Two rows are still architecture-open: `JQ011`, because the 7yo branch has a stable rule-level contract but not yet the sample-turn/task-class closure needed for a final persona pack; and `Q004`, because the parent-development packaging choice must still test the JQ071 discriminators against actual rollup-query sufficiency before freezing a heavier entity shape. [SOURCE+DERIVED: https://learn.microsoft.com/en-us/azure/ai-services/speech-service/language-support?tabs=stt-tts] The third row is empirical-gated and build-owned rather than architecture-open: a documented `af-ZA` stack exists, so the remaining spoken-presence risk is measured latency/quality/hot-path viability, not lack of vendor support. [DERIVED] The exact handoff boundary is now explicit: `jarvis-personas` can proceed on provisional 7yo constraints, existing coaching structures, and all text/fallback/spoken-provisional prompt work, while the build/schema project owns the remaining schema lock and voice-measurement gates.