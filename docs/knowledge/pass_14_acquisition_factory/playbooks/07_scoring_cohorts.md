# 07 — Scoring and cohort assignment

## Score dimensions (0–5 each)

- homeowner_fit
- quote_process_signal
- dormant_db_likelihood
- decision_maker_reachability
- company_activity
- service_value
- data_confidence
- delivery_capacity_signal

Keep hard gates separate from scores. A suppressed or non-compliant record never becomes sendable because it scores 39/40.

## Cohorts

For the first learning phase, stratify by:
- company size proxy
- geography
- contact type (named vs generic)
- data-confidence band
- offer angle

Freeze cohort membership before sending. Do not move poor performers into another variant after seeing outcomes; that contaminates experiments.
