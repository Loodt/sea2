# Success Pattern: design-space — evaluation-dataset and rubric-calibration architect for child-mentor dialogue systems

## Strategy
Expert type "evaluation-dataset and rubric-calibration architect for child-mentor dialogue systems" for design-space question.
Question: Critic rubric empirical calibration — what annotated turn corpus (child-mentor exchanges) is needed to tune D1-D6 thresholds and few-shot exemplars for the F2024 rubric? Can iter-2/3 synthetic examples plus TalkMoves-tagged classroom data bootstrap this, or does Jarvis need to generate its own pilot-session corpus first?

## When It Works
- Question type: design-space
- Converged in 3/4 iterations

## Evidence
- Dispatch: D44
- Question: JQ078
- Findings produced: 10
- Iterations: 3/4
- Status: answered

## Key Decisions
The derivation now closes JQ078 at the architecture level. Synthetic iter-2/3 examples and TalkMoves-tagged classroom data are useful bootstrap assets, but only for annotation-guide authoring, cue vocabulary, and provisional exemplar drafting; they are not valid final threshold evidence. The required corpus is an in-domain Jarvis pilot built as annotated exchange windows, split functionally into refinement, exemplar-authoring, and held-out threshold-check pools. The minimum corpus requirement is coverage-based rather than count-based: each age band needs contrastive in-domain cases across opening, scaffolding, repair, and closure, especially for the ambiguous ordinal dimensions D2, D5, and D6. Jarvis therefore does need its own pilot-session corpus first, though it can keep that pilot small by using Wizard-of-Oz capture, dual annotation, and stopping when held-out confusion on D2/D5/D6 stabilizes.