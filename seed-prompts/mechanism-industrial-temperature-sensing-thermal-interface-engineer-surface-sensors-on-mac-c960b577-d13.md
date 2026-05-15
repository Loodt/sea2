# Success Pattern: mechanism — industrial temperature sensing + thermal interface engineer (surface sensors on machinery/insulated piping)

## Strategy
Expert type "industrial temperature sensing + thermal interface engineer (surface sensors on machinery/insulated piping)" for mechanism question.
Question: What thermal-contact, insulation, and mounting-stack design is required for a peel-and-stick temperature sensor to deliver stable, actionable surface-temperature readings on painted/oxidized motors, pump casings, and insulated pipes in mineral-processing plants, and what accuracy/response-time trade-offs should be assumed for the first SKU?

## When It Works
- Question type: mechanism
- Converged in 5/5 iterations

## Evidence
- Dispatch: D13
- Question: Q013
- Findings produced: 34
- Iterations: 5/5
- Status: answered

## Key Decisions
For exposed painted/oxidized motor and pump casings, a stable peel-and-stick surface-temperature SKU must be designed as a coupled thermal-contact + ambient-shielding stack: keep the contact/bondline thin and/or thermally conductive (targeting R_contact ~ O(2–20) K/W for ~1 cm² effective contact area) and add a local insulating overpatch (“foam hat”) that forces ambient exchange through low-k foam (raising R_ambient to ~800–1600 K/W even with airflow). Under those conditions, a defensible first-SKU steady-state bias envelope is ~0.2–3°C for Δ=30–55°C across plausible R_contact bands, with response time t63 typically ~30–120 s and near-settled behavior in ~2–6 minutes; without the overpatch, airflow can drive multi-degree to tens-of-degrees bias depending on R_contact. For insulated pipes, an outside-jacket sticker should be explicitly positioned as a jacket-surface proxy (trending/hot-spot/insulation-condition indicator); if actionable decisions require pipe-wall temperature, the required mounting stack is under-insulation contact to the pipe wall plus restored insulation/jacket continuity around the sensor to suppress ambient loss.