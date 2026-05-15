# Success Pattern: landscape — industrial wireless systems architect for low-power sensing in heavy-process plants

## Strategy
Expert type "industrial wireless systems architect for low-power sensing in heavy-process plants" for landscape question.
Question: Which wireless architecture and protocol stack best fit a first commercial deployment of self-powered retrofit sensors in a representative mineral-processing plant, given harvested-power limits, steel-heavy RF conditions, gateway density, and the data needs of the likely first wedge?

## When It Works
- Question type: landscape
- Converged in 3/5 iterations

## Evidence
- Dispatch: D3
- Question: Q003
- Findings produced: 16
- Iterations: 3/5
- Status: answered

## Key Decisions
[DERIVED: F946] Q003 now resolves to a single-hop local-cell LoRaWAN Class A architecture, with gateways placed per pump gallery or adjacent process block rather than a whole-plant mesh or dense BLE relay fabric. [SOURCE: https://www.fluke.com/en-us/product/condition-monitoring/vibration/3562] [SOURCE: https://www.ifm.com/il/en/shared/products/condition-monitoring/vvb/installation-guidelines-and-sensor-position] The likely first wedge sends summarized machine-health indicators on roughly minute-scale cadences, not raw waveforms, and the useful payload is a small set of scalar values such as v-RMS, a-RMS, a-Peak or crest factor, temperature, and alarm state. [SOURCE: https://lora-alliance.org/wp-content/uploads/2021/11/LoRaWAN-Link-Layer-Specification-v1.0.4.pdf] [SOURCE: https://resources.lora-alliance.org/technical-specifications/rp002-1-0-5-lorawan-regional-parameters] LoRaWAN Class A fits because it tolerates long sleep intervals and can carry these small summaries comfortably, but confirmed traffic and all downlink-dependent behavior should be exceptional because acknowledgments only ride the post-uplink receive windows. [DERIVED: F946] The recommended protocol pattern is unconfirmed uplinks for normal trends, repeated or confirmed alarm delivery only for rare high-value exceptions, and infrequent maintenance downlinks for configuration, time sync, or firmware operations.