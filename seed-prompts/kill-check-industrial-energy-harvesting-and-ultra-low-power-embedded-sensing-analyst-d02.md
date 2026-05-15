# Success Pattern: kill-check — industrial energy-harvesting and ultra-low-power embedded sensing analyst

## Strategy
Expert type "industrial energy-harvesting and ultra-low-power embedded sensing analyst" for kill-check question.
Question: What is the realistic harvested-power envelope for CT-current, thermoelectric, and piezoelectric energy harvesting on representative non-hazardous plant assets, and what sensing plus transmit duty cycles does each envelope support?

## When It Works
- Question type: kill-check
- Converged in 3/5 iterations

## Evidence
- Dispatch: D2
- Question: Q002
- Findings produced: 18
- Iterations: 3/5
- Status: answered

## Key Decisions
This iteration completed Stage 3 by converting the prior modality envelopes into explicit duty-cycle ladders against the existing node baseline from F913-F915. CT harvesting is now well anchored by a demonstrated self-powered LoRa current sensor: at 1 A line current it sustains about 0.84 mW average and multi-second reporting, which is enough for scalar sensing and sparse-to-frequent bursts while energized, but still weak for continuous rich vibration analytics [SOURCE: https://www.mdpi.com/1996-1073/14/6/1561] [DERIVED: F930]. Thermoelectric harvesting remains the strongest ordinary non-hazardous plant source: a real 0.25 kW motor-housing TEG delivered about 0.64 mW average at a 4-5 C gradient with estimated 2.6-4.4 minute transmission intervals, while earlier favorable 9 K cases still support a few-mW upper envelope [SOURCE: https://www.mdpi.com/1424-8220/26/5/1644] [SOURCE: https://www.researchgate.net/publication/333849525_Thermoelectric_Energy_Harvesting]. Piezoelectric harvesting is now resolved as a split branch rather than a single envelope: ordinary pump and motor housings sit in a much weaker vibration regime than vibrating screens, so piezo is generally a trickle-assist or very sparse-event source there, while tuned high-vibration assets can reach low-mW output and support periodic feature reporting [SOURCE: https://engdatabase.com/data/vibration-severity/iso108163summary] [SOURCE: https://www.chemicalprocessing.com/home/article/11310315/give-vibratory-screens-a-fair-shake-chemical-processing] [SOURCE: https://www.researchgate.net/publication/399011309_Performance_Study_of_a_Piezoelectric_Energy_Harvester_Based_on_Rotating_Wheel_Vibration].