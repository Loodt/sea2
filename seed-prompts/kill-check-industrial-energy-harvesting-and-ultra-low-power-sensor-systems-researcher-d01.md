# Success Pattern: kill-check — industrial energy-harvesting and ultra-low-power sensor systems researcher

## Strategy
Expert type "industrial energy-harvesting and ultra-low-power sensor systems researcher" for kill-check question.
Question: What is the realistic harvested-power envelope for CT-current, thermoelectric, and piezoelectric energy harvesting on representative gold-plant assets, and what sensing/transmit duty cycles does each envelope support for current, temperature, and vibration stickers?

## When It Works
- Question type: kill-check
- Converged in 4/5 iterations

## Evidence
- Dispatch: D1
- Question: Q001
- Findings produced: 20
- Iterations: 4/5
- Status: answered

## Key Decisions
The remaining weak link was the clip-on CT branch, and this iteration tightened it with a stronger published anchor: a self-powered line-clamped CT current sensor that runs from an equivalent 1-100 A line-current range, consumes 0.84 mW at 1 A, and reports every 7.2 s at 1 A, 1.06 s at 5 A, and 0.62 s at 10 A [SOURCE: https://www.mdpi.com/1996-1073/14/6/1561]. Combined with the earlier split-core result showing about 112 uW at 170 mA and buffered burst operation, the realistic installed-feeder CT envelope is now defensibly current-centric rather than generically power-rich: about 0.1-1 mW is realistic, enough for current stickers with sparse-to-frequent telemetry but not a strong sole source for continuous vibration analytics [DERIVED: F901+F905+F910+F918]. The thermoelectric branch remains the strongest practical sticker source on ordinary rotating assets, with motor housings in the sub-mW to few-mW class and hot process pipes effectively energy-abundant at sticker scale [SOURCE: https://www.mdpi.com/1424-8220/26/5/1644] [SOURCE: https://www.mdpi.com/2227-9717/11/6/1714]. The piezo branch remains bifurcated: tuned harvesters on vibrating screens are plausibly low-mW, while ordinary pump and motor housings are more realistically low-uW to low-tens-uW and therefore better treated as trickle-assist sources [DERIVED: F914+F916].