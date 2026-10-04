# Holdout / incrementality design

Attribution answers “did this contact interact after our campaign?” Incrementality asks “did the campaign cause more outcome than would otherwise have happened?”

## Default design
If the eligible pool is large enough:
1. freeze the eligible population;
2. stratify by major predictors available before treatment (especially quote-age cohort; optionally source/product/value band);
3. deterministically randomize within strata into treatment vs holdout;
4. do not market the holdout during the test window through this campaign;
5. measure the same downstream outcomes for both groups;
6. reconcile contamination from client staff/other campaigns.

## Minimum reporting
For treatment and holdout report:
- sample size;
- organic/client contact contamination;
- positive interest where observable;
- booked;
- attended;
- requoted;
- won;
- cash collected.

Compute absolute lift as treatment outcome rate − holdout outcome rate.

Do not over-interpret tiny samples. If the pool is too small for a useful holdout, capture a pre-campaign baseline and mark causal confidence lower rather than pretending attribution is causality.
