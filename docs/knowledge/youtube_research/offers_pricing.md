# Offers, pricing & guarantees: topic digest (189 videos, 91 creators)

- **Source:** ChatGPT's analysis of `velarqo_research/3_offers_pricing.zip` (2026-10-04), ~1.21M words. No creator dominates (Serge Gatari 16, the rest ≤7), but much of it is coaching/info-product pricing. Weighted: real agency postmortems > agency theory > coaching theory.
- **Verification (Claude, 2026-10-04):** 8 of 8 confirmed.
  - **Clay Lawrence postmortem:** switched Review Harvest from subscription to pay-per-review; "Revenue was becoming unpredictable, bad customers were coming in and… the entire business got way more complicated" [FObpNztnuug].
  - **Noah Haupt, home-services pricing on a live call:** "150 for each estimate you actually come face to face with plus a 1k onetime setup fee, or… 2K for 15 appointments" [nyx7OidDjmQ]; also "$500 upfront plus $100 per appointment" vs "$2,000 per month" [ZInH_RIDXQA]. **That is a real home-services billing event at the *attended estimate*, which is exactly the event proposed below.**
  - **Noah Haupt on believability:** an experienced owner sees "10 jobs in 30 days or we'll send you $20,000" and thinks "way too good to be true", so it disqualifies your ICP [VjtFDC0VevA].
  - **Noah Haupt on feature stacking:** adding review campaigns, DB reactivation etc. "was just taking focus away from my main service" [qoxEgridiVo].
  - **Daniel Fazio:** "Don't try to charge clients in more than two ways" (e.g. a monthly tech fee plus cost per call) [CoymBv5Rhu8].
  - **Oliver Rasmussen:** prefers lowering the client's current cost per appointment. Revenue share "requires a lot of trust that this business owner will report back". For roofing/solar he triggers payment at "contract signed" instead of installation, so he's paid at ~45 days instead of 3–4 months [03iQTUd-F1k].
  - **Nick Saraev, guarantees with no data:** "pull a number out of your ass… if you can't hit it, you will refund" [zKhRsYpFqHI]. Treated as **reckless for Velarqo** (see below).
  - **Serge Gatari:** build-and-release, i.e. sell implementation and hand it over [nIwIPweiPC0].

## Core principles
1. **Price on economic value, never hours.** If Claude Code does 6 hours of work in 10 minutes, the price shouldn't drop. The client buys recovered opportunities.
2. **Value pricing means calculating value *with* the client**, not inventing a big number. Get from discovery: average job value, gross profit, lead→quote and quote→sale rates, current cost per (attended) quote, sales capacity.
3. **Two ceilings for the per-result price:**
   - **Reference cost:** what they pay now to create an attended quote (marketing spend ÷ attended quotes).
   - **Economic value:** expected GP per attended quote = quote close rate × average gross profit per sale.
   - Price below both, with room for strong client ROI.
4. **No universal price.** Value per opportunity varies ~17× between installers (e.g. £700 GP at 10% close = £70/appointment vs £4,000 GP at 30% = £1,200). **Client selection matters more than the technology**, which reinforces the ICP from the home-services digest: winners with leakage, not dying firms.
5. **Don't copy US YouTube numbers** ($100/appointment, $3k setup…). Derive from UK installer economics.

## Performance pricing: use it as the wedge, not the business
- **Why early:** no proof, authority or case studies, so risk reversal has to replace proof (Fazio: a cold offer needs a quantifiable outcome + proof + risk reversal). It also protects you while you don't yet know your own conversion rates.
- **Why not forever (Clay's postmortem):**
  - Zero risk **attracts the worst clients**: tiny firms, few billable outcomes, lots of support.
  - **Revenue becomes unpredictable**, while your costs continue.
  - **Attribution disputes** ("that wasn't from you"), much worse at £10k window jobs than for Google reviews.
- **Reactivation is front-loaded:** the historical pool runs out (8,000 → 500 records), so pure DB reactivation doesn't create stable MRR. Pay-per-recovery also rewards leads *dying*. The long-term system should earn from **preventing** leakage (speed-to-lead, quote follow-up, nurture) plus recovery.
- **Revenue share / pay-per-sale:** dependent on the client's honest reporting, slow cash (30–90+ days), cancellations, discounts, sales-team quality. Avoid early.

## The billable event (most important decision)
**Rule: charge on the deepest economically meaningful outcome that Velarqo substantially controls, can verify objectively, and can define without argument.**
- "Lead replied maybe" → too shallow, the client resents paying.
- "Sale closed" → too deep, depends on the salesperson, pricing, finance and competitors.
- **Sweet spot: a qualified recovered homeowner who *attends* a new survey/quote appointment** (attended > booked, so no fears about fake bookings or no-shows). Noah Haupt already bills home services exactly like this.
- **Definitions matter more than the number.** Write down eligible (correct homeowner, serviceable postcode, relevant need, genuine interest, not already active, timeframe), and rules for cancellations, reschedules, no-shows, duplicates, existing customers and invalid records. Use the installers' own words for it after the interviews; don't invent jargon.

## Pilot structure to test first
**Dormant Pipeline Recovery Pilot:** a defined cohort with no meaningful activity for 90/120/180+ days. Velarqo cleans, segments, contacts, follows up, qualifies, books, reminds, hands over and tracks.
- **Price structure: small activation deposit + fee per qualified attended appointment**, with the deposit **credited against the first performance fees**. That's max two charging mechanisms (Fazio).
- **Not literally free:** £0 clients ignore onboarding, send bad data and don't show up. A small deposit creates commitment while their downside stays tiny.
- **No numerical guarantee in the first pilots.** Pay-on-result is already the risk reversal. Pilots exist to learn the funnel (reachable → replies → positive → qualified → booked → attended → quoted → sold).
- **Guarantees later, after 5–10 campaigns**, based on real distributions (e.g. "min X attended per 1,000 eligible records"), with **causal conditions only**: CRM access, minimum eligible cohort, accurate statuses, timely handoff, appointment capacity, no overlapping campaign on the same cohort, reporting access. No 17-clause escape guarantees.
- **Believability beats boldness.** An 18-year owner reads "30 sales in 30 days or £20k" as a scam. Never guarantee revenue or anything the installer's sales team controls.

## Offer design
- **One transformation on the front end:** "recover qualified sales opportunities your team stopped working". No feature soup (AI receptionist + ads + reviews + CRM + websites for £4,999/mo). **Simple front end, sophisticated backend.** You can deliver more than you advertise and expand later.
- **No low-ticket** (£99 AI CRM scans etc.): Velarqo has onboarding, data access, personalization and B2B complexity.
- **Build-and-release** (Serge Gatari) is a later option: a "Revenue Recovery Infrastructure Build" for a one-time fee. Don't start there: you don't yet know the right system, and pure handoff loses recurring revenue, data and cross-client learning. Prefer build + ongoing managed layer.

## Risk migrates as proof grows
Zero proof → performance-heavy → small base + performance → meaningful base/retainer + performance → mostly fixed recurring + upside. Performance pricing is the **customer-acquisition offer**; the business model is the continuous revenue-recovery system on hybrid recurring + performance pricing. Still being "free unless you close" in three years means you failed to build pricing power.

## Unresolved (carried from #2)
Owners may still feel you're extracting value from leads they own. The current answer: a truly written-off cohort → demonstrate incremental lift (holdout) → bill a concrete event → bundle prevention and new-demand mechanisms.

## Ratings (pricing models for Velarqo)
| Model | Score |
|---|---|
| Small credited activation deposit + per qualified attended appointment | 9 (now) |
| Base monthly fee + performance fee | 9 (later) |
| Pure pay per qualified attended appointment | 8 |
| Fixed monthly retainer | 7 now, 9 later |
| Pay per signed sale | 6 |
| Revenue share | 5 |
| Large upfront setup fee | 4 now |
| Free unlimited pilot | 4 |
| Hourly | 1 |
