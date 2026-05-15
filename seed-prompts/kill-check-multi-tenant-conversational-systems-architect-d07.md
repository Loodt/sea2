# Success Pattern: kill-check — multi-tenant conversational systems architect

## Strategy
Expert type "multi-tenant conversational systems architect" for kill-check question.
Question: One Jarvis that adapts to whichever boy is talking, OR three differently-configured Jarvis instances sharing infrastructure? Architectural fork (divergence B3): what are the actual implications for memory, persona drift, family-shared context, and the 'consistent presence' constraint?

## When It Works
- Question type: kill-check
- Converged in 2/5 iterations

## Evidence
- Dispatch: D7
- Question: JQ013
- Findings produced: 9
- Iterations: 2/5
- Status: answered

## Key Decisions
Stage 1 had already killed the three-instance fork on identity and drift grounds. [DERIVED: F1027] Stage 2 closes the remaining gap by showing that shared-device assistants only expose private data after speaker recognition, while current multi-user speech tech improves recognition but does not make it perfect. [SOURCE: https://support.google.com/googlenest/answer/16687976?hl=en] [SOURCE: https://developer.amazon.com/en-GB/docs/alexa/custom-skills/personalization-and-account-linking.html] [SOURCE: https://research.google/pubs/multi-user-voicefilter-lite-via-attentive-speaker-embedding/] Therefore the viable architecture is one Jarvis with explicit scope routing and three persistence layers: child-private, family-shared, and global persona. [DERIVED: F1031] [DERIVED: F1032] That structure preserves consistent presence, limits persona drift, and prevents sibling leakage without turning the system into three separately-governed agents. [DERIVED: F1032]