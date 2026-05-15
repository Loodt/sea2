# Success Pattern: design-space — industrial IoT commissioning workflow designer

## Strategy
Expert type "industrial IoT commissioning workflow designer" for design-space question.
Question: What provisioning, identification, and asset-binding workflow minimizes installation labor and binding errors when an operator deploys large numbers of sensor stickers across a plant?

## When It Works
- Question type: design-space
- Converged in 2/4 iterations

## Evidence
- Dispatch: D5
- Question: Q005
- Findings produced: 8
- Iterations: 2/4
- Status: answered

## Key Decisions
I continued from the prior narrowing rather than restarting. The core comparison shows that pure asset-first binding is only locally optimal on cleanly tagged assets, while sticker-first provisional binding with a simple placement code is the only workflow family that stays operable across mixed tag quality without turning ambiguity into plant-wide cleanup debt. Optional pre-kitting survives only as a staging accelerator, not as the final source of truth, because route drift and substitutions make authoritative pre-kits brittle. The resolved answer is therefore a hybrid workflow: capture sticker identity first, capture a local placement or route cue at install, use asset-tag scanning as a fast-path overlay when available, and defer final commit to a bounded validation step against a small local candidate set.