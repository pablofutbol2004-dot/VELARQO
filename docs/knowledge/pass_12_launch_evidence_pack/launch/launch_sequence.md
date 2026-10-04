# Launch sequence — evidence before scale

## Stage 0 — founder precommitment
Freeze the current offer hypothesis, billable outcome, acquisition variants and pilot success/failure definitions before observing results.

Outputs:
- `pilot/pilot_config.json` completed;
- `learning/decision_log.csv` initial row;
- predicted ranges written down.

## Stage 1 — installer evidence
Run substantive conversations rather than pitch-only calls. Capture workflow, volumes, backlog, follow-up behavior, CRM/exportability, acquisition spend, economics, capacity and objections.

Exit criterion: at least 10 useful conversations **or** strong convergence plus evidence that an assumption is already dead.

## Stage 2 — export evidence
Obtain 3 real or appropriately redacted exports if possible. Audit fields, age, statuses, provenance, suppression information, data cleanliness and usable fraction.

Exit criterion: enough evidence to know whether the offer has real inventory to act on.

## Stage 3 — Client 1 P0 gate
Run every gate in `client_gate/client1_gate.csv`.

Statuses allowed: `PASS`, `FAIL`, `NOT_APPLICABLE`, `OPEN`.

**No launch while any non-waivable row is FAIL or OPEN.**

## Stage 4 — freeze the test
Create an immutable pilot cohort, holdout where feasible, message variants and success metrics. Generate stable contact IDs. Keep suppressed/ineligible contacts outside the send cohort.

## Stage 5 — canary
Send a very small batch. Inspect delivery, replies, opt-outs, routing, bookings, duplicates and client handling manually.

Do not expand because one person books.

## Stage 6 — micro-pilot
Run the frozen test. Record contact-level events and manual minutes. No outcome-metric switching after launch.

## Stage 7 — downstream reconciliation
The campaign is not complete at “booked”. Reconcile:

`booked → attended → requoted → won → cancelled/refunded? → cash collected`

## Stage 8 — economics
Calculate both sides:
- installer economics: cost/result, cost/sale, revenue and preferably contribution value;
- Velarqo economics: fees, direct delivery cost, founder time, payment lag, disputes, contribution.

## Stage 9 — evidence update
Every meaningful result updates:
- empirical question status;
- claim/evidence ledger;
- assumption status;
- next experiment.

## Stage 10 — decision
Choose one:
1. **DOUBLE DOWN** — mechanism works and constraint is scalable.
2. **REPAIR** — mechanism promising but one stage is clearly broken.
3. **CHANGE OFFER / PRICE** — demand exists but commercial packaging is wrong.
4. **CHANGE SEGMENT / NICHE** — structural market assumption failed.
5. **KILL** — economics or feasibility do not justify another iteration.
