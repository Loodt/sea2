# Success Pattern: landscape — South African freight technology and logistics systems analyst

## Strategy
Expert type "South African freight technology and logistics systems analyst" for landscape question.
Question: What digital freight platforms, TMS providers, telematics systems, and load-board services currently serve South African long-haul carriers on the JHB-DBN and JHB-CPT corridors, what integration interfaces (API, EDI, file export) do they expose, and which represent the most likely integration dependencies or competitive overlaps for a blind-neutral exchange?

## When It Works
- Question type: landscape
- Converged in 3/5 iterations

## Evidence
- Dispatch: D16
- Question: Q020
- Findings produced: 24
- Iterations: 3/5
- Status: answered

## Key Decisions
The SA freight tech ecosystem serving JHB-DBN/JHB-CPT long-haul carriers consists of telematics (Big 5 with only 2 of 5 having public APIs — Cartrack strongest, MiX limited), fragmented TMS (no public APIs), digital load boards (Linebooker dominant but closed), and mandatory SARS EDI for cross-border. GoMetro Bridge is the most aligned existing product for solving telematics fragmentation. No SA freight-specific settlement platform exists — the exchange must build matching, settlement (POD-to-cash), and constraint gates internally. Only Linebooker represents true competitive overlap; all other platforms are integration dependencies or different segments. Critical pilot path: internal build for core functions, Cartrack API as first external integration, GoMetro Bridge for multi-provider scaling.