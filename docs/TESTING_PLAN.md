# Testing plan: what we test, in what order, and how we decide

Every stage of the business is a test. Each test is a JSON file in
`config/experiments/` with a hypothesis, a single changed variable, a
primary metric, guardrails, a minimum sample and a decision rule written
**before** it runs. Results: `python -m pipelines.outbound results <name>`.
Decisions go in `docs/experiments/LOG.md`.

## The honest maths

We have **1,918 installers** in the queue. If roughly 2 in 100 reply
positively (unknown; that's what we're measuring), 300 emails per arm gives
about 6 positive replies per arm. So:

- **We can only detect big differences** (e.g. 1% vs 4%), not wording tweaks.
  Test big swings: offer, angle, who we email. Not commas.
- **One cold-email test at a time** (about 600 emails each). That allows roughly
  three tests across the current list.
- Judge on **downstream** results (calls, samples, pilots), with positive
  replies as the early read.
- Grow the list to unlock more tests: add named contacts at the same firms,
  find emails for the 9,933 tier-C firms that have none, and add the next
  vertical (a kitchens ICP already exists).

## The funnel and what we test at each stage

| Stage | Question | How we test | Metric | When |
|---|---|---|---|---|
| Deliverability | Do we land in the inbox? | Test sends to Gmail/Outlook seed inboxes; bounce tracking | Inbox placement, bounce rate under 3% | Before the first batch, then weekly |
| Targeting | Which installers reply? | Pre-chosen splits on every send: priority score, generic vs named inbox, accredited vs not, years trading | Positive replies per segment | Read after about 600 sends |
| **Offer** | Free look at their quotes vs no-win-no-fee chasing? | `cold_offer_v1` (2 arms, same opener) | Positive reply rate, then calls | **First: about the first 600 emails** |
| Angle | Question opener vs "money already spent"? | `cold_angle_v1` (status waiting; uses the winning offer, ~30% of the list left after the offer test) | Positive reply rate | Second, about week 5-6 |
| Ask / CTA | "Want me to take a look?" vs "Reply with a rough number" | `cold_cta_v1` (to write) | Positive reply rate | Third |
| Follow-ups | Do follow-ups 2 and 3 earn their keep? | Count replies by the step they came after | Replies per step, opt-outs per step | Ongoing, free |
| Reply speed | Does answering within an hour book more calls? | Log reply times (not randomised; a habit, not a test) | Positive reply to call | Ongoing |
| Sales call | Which call structure gets a sample sent? | Qualitative: scorecard after every call (`pass_13.../sales/call_scorecard.csv`) | Call to sample rate | Ongoing |
| **Price** | Which price level, then which model? | `pricing_p1` on every call, then P2 menu | Sample-sent rate, objections, margin | **From the first call** |
| Pilot (the product) | Do old quotes really turn into surveys and jobs? | Holdout: a random slice of each client's old quotes isn't contacted, so we can prove lift (`pass_12.../measurement/holdout_design.md`) | Booked, attended and won vs holdout | Every pilot |

The offer test and the pricing test can run at the same time: they change
different things at different stages, and the price arm is assigned
independently of the email arm.

## Guardrails that stop any test

- Any complaint pauses all sending automatically (built in).
- Bounce rate over 5% (once 20+ emails have gone out) pauses sending (built in). Investigate above 3%.
- Opt-out rate over 2% on an arm: stop that arm.
- An arm that brings replies but no calls loses, whatever its reply rate.

## Running a test

1. Write or edit the JSON in `config/experiments/` (the tests check every
   arm for length, opt-out line, banned words and no prices).
2. `create-cohort --experiment <name> --size 50`, then `review`, then `activate`.
3. Weekly: `results <name>`. The readout says "too early", "keep X" or "no clear winner".
4. Decide, log it in `docs/experiments/LOG.md`, and start the next test.
