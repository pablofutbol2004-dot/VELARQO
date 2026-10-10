# Testing plan: what we test, in what order, and how we decide

Every stage of the business is a test. Each test is a JSON file in
`config/experiments/` with a hypothesis, a single changed variable, a
primary metric, guardrails, a minimum sample and a decision rule written
**before** it runs. Results: `python -m pipelines.outbound results <name>`.
Decisions go in `docs/experiments/LOG.md`.

## The honest maths

We have about **4,800 emailable Ltd companies** on company addresses: roughly
2,400 window and door firms and 2,400 roofers. If roughly 2 in 100 reply
positively (unknown; that's what we're measuring), 300 emails per arm gives
about 6 positive replies per arm. So:

- **We can only detect big differences** (e.g. 1% vs 4%), not wording tweaks.
  Test big swings: offer, angle, who we email. Not commas.
- **One offer test, with segment tests alongside it.** The offer test
  (`cold_offer_v1`) is the main one. The segment tests run in parallel on
  different slices of the list: `cold_nopressure_v1`, `cold_survey_line_v1`
  and `cold_roofing_v1`. `cold_angle_v1` waits for the offer result. The
  segment results are directional, not proof, because the groups are small.
- Judge on **downstream** results (calls, samples, pilots), with positive
  replies as the early read.
- Grow the list to unlock more tests: add named contacts at the same firms,
  find emails for the tier-C firms that have none, and add the next
  vertical (a kitchens ICP already exists).

## The funnel and what we test at each stage

| Stage | Question | How we test | Metric | When |
|---|---|---|---|---|
| Deliverability | Do we land in the inbox? | Test sends to Gmail/Outlook seed inboxes; bounce tracking | Inbox placement, bounce rate under 3% | Before the first batch, then weekly |
| Targeting | Which installers reply? | Pre-chosen splits on every send: priority score, generic vs named inbox, accredited vs not, years trading | Positive replies per segment | Read after about 600 sends |
| **Offer** | Pay per booked survey (A) vs first 50 free (B)? | `cold_offer_v1` (2 arms, same opener) | Positive reply rate, then calls | **First: about the first 600 emails** |
| Segment | Does a tailored line help a group of firms? And do roofers reply like window firms? | `cold_nopressure_v1` (~223 firms whose site promises no-pressure selling), `cold_survey_line_v1` (~140 firms whose site says they visit to survey), `cold_roofing_v1` (roofers; same two offers as the window test). Each runs on its own slice alongside the offer test. | Positive reply rate (directional only: the segments are small) | From the first send |
| Angle | Question opener vs "money already spent"? | `cold_angle_v1` (status waiting; uses the winning offer, ~30% of the list left after the offer test) | Positive reply rate | After the offer test has a winner |
| Ask / CTA | "Want me to take a look?" vs "Reply with a rough number" | `cold_cta_v1` (to write) | Positive reply rate | Third |
| Follow-ups | Do follow-ups 2 and 3 earn their keep? | Count replies by the step they came after | Replies per step, opt-outs per step | Ongoing, free |
| Reply speed | Does answering within an hour book more calls? | Log reply times (not randomised; a habit, not a test) | Positive reply to call | Ongoing |
| Sales call | Which call structure gets a sample sent? | Qualitative: scorecard after every call (`pass_13.../sales/call_scorecard.csv`) | Call to sample rate | Ongoing |
| **Price** | Which price level, then which model? | `pricing_p1` on every call, then P2 menu | Sample-sent rate, objections, margin | **From the first call** |
| Pilot (the product) | Do old quotes really turn into surveys and jobs? | Holdout: a random slice of each client's old quotes isn't contacted, so we can prove lift (`pass_12.../measurement/holdout_design.md`) | Booked, attended and won vs holdout | Every pilot |

The offer test and the pricing test can run at the same time: they change
different things at different stages, and the price arm is assigned
independently of the email arm.

## Later: second campaign to non-repliers (not built)

About 60 days after a company's sequence ends with no reply, send them one
email with a different offer, most likely speed-to-lead and quote follow-up on
new enquiries. Keep about 10% of sends for new concepts like this once the
offer test has a winner (Taylor Haren's 70/20/10). Other services (speed-to-lead,
reviews, missed calls) are sold as upsells to reactivation clients, never mixed
into the first sequence.

## Guardrails that stop any test

- Any complaint pauses all sending automatically (built in).
- Bounce rate over 5% (once 20+ emails have gone out) pauses sending (built in). Investigate above 3%.
- Opt-out rate over 2% on an arm: stop that arm.
- An arm that brings replies but no calls loses, whatever its reply rate.

## Running a test

1. Write or edit the JSON in `config/experiments/` (the tests check every
   arm for length, opt-out line, banned words and no prices).
2. `python -m pipelines.outbound create-cohort --experiment <name> --size 25`
   (25 is the default), then `review`, then `activate`.
3. Weekly: `results <name>`. The readout says "too early", "keep X" or "no clear winner".
4. Decide, log it in `docs/experiments/LOG.md`, and start the next test.
