# Success Pattern: mechanism — freight telematics and logistics knowledge-graph architect

## Strategy
Expert type "freight telematics and logistics knowledge-graph architect" for mechanism question.
Question: How should a South African neutral freight exchange capture driver route intelligence as structured network data on the JHB-DBN and JHB-CPT corridors without exposing carrier, customer, or live lane strategy, and what verification and incentive rules make that data reliable enough for matching and execution?

## When It Works
- Question type: mechanism
- Converged in 2/5 iterations

## Evidence
- Dispatch: D7
- Question: Q007
- Findings produced: 11
- Iterations: 2/5
- Status: answered

## Key Decisions
A neutral South African freight exchange should publish only derived corridor facts, not raw trip exhaust, because the safe boundary is a restricted evidence layer plus a participant-visible derived layer [SOURCE: https://www.transportation.gov/office-policy/transportation-policy/faq-waze-data] [DERIVED: synthesis from F976-F986]. Both target corridors can be modeled as public segment-and-facility graphs using N3TC anchors for JHB-DBN and SANRAL N1 plaza anchors for JHB-CPT, which avoids storing carrier- or customer-linked stop sequences [SOURCE: https://www.n3tc.co.za/toll-tariffs/] [SOURCE: https://www.sanral.co.za/e-toll/portal/publicpages/Toll_Plaza.pdf]. Verification should be observation-based and adversarially robust: require authority or road-operator evidence or at least two temporally separated independent contributor observations before a fact becomes match-visible, and carry freshness, validity, evidence count, and contradiction handling in the fact record [SOURCE: https://developer.tomtom.com/traffic-api/documentation/traffic-incidents/incident-details] [SOURCE: https://support.google.com/waze/answer/13739612?hl=en] [DERIVED: synthesis]. Incentives should vest on corroborated reports that survive the validity window without contradiction, while duplicate, stale, spammy, or over-identifying submissions earn zero credit and reduce trust weight, making the data reliable enough for matching while reserving sensitive detail for execution-only workflows [SOURCE: https://support.google.com/waze/answer/12237550?hl=en] [DERIVED: synthesis].