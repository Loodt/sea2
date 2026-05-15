# Success Pattern: data-hunt — threshold-calibration researcher for content-moderation rule sets (literature-synthesis across spam/marketing-language classifiers, embedding-similarity thresholds, posting-frequency caps, and author-diversity filters; output: per-threshold defensible starting value + calibration-path cost estimate + refinement plan)

## Strategy
Expert type "threshold-calibration researcher for content-moderation rule sets (literature-synthesis across spam/marketing-language classifiers, embedding-similarity thresholds, posting-frequency caps, and author-diversity filters; output: per-threshold defensible starting value + calibration-path cost estimate + refinement plan)" for data-hunt question.
Question: What are empirically-calibrated values for the 5 [UNKNOWN] thresholds in the QQ008 minimal rule set: THRESHOLD_MF (R5 marketing-fluff), SIM_THRESHOLD (R11 template similarity + R5 AI-structural), sigma_min (R12 value-density floor), CAP_FREQ (R10 24h frequency cap), DIVERSITY_FLOOR (R10 7d author-diversity)? Each needs cheapest-path calibration method (A/B test, reference corpus, literature).

## When It Works
- Question type: data-hunt
- Converged in 5/5 iterations

## Evidence
- Dispatch: D9
- Question: QQ010
- Findings produced: 24
- Iterations: 5/5
- Status: answered

## Key Decisions
QQ010 answered. All 5 thresholds (SIM_THRESHOLD template 0.85/structural 0.78, THRESHOLD_MF 0.70, sigma_min conjunction LD>=0.40∧H>=3.5∧WR>=0.45, CAP_FREQ three-tier 3-5/6-8/10 + intra-day burst caps, DIVERSITY_FLOOR HHI<0.15/0.15-0.25/>=0.25 + s_max<50%/<80%) land with starting values, named embedding-model/classifier/corpus, calibration method, cost, error-direction, and refinement trigger. The non-obvious finding is that the 5 thresholds split cleanly into two rollout tracks: Track A (R10 pair — CAP_FREQ + DIVERSITY_FLOOR) is zero-label and ships day 1 with 90-day owned-Analytics refinement; Track B (R5/R11/R12) requires ~1,500 hand-labeled posts before safe deployment. Error-bias inverts between tracks — principled, driven by the asymmetry between single-post voice-damage (Track B) and multi-day shadowban reach-loss (Track A).