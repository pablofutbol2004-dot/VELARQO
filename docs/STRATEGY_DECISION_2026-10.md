# Strategy decision, 11 Oct 2026

The answer to "do we pivot, change the offer, find a more painful problem, or
a better channel?" Built from five research files and a red-team review done
today (listed at the bottom), plus our own database. This overrides
`PATH_6_MONTHS.md` and `HARD_TO_FAIL_PLAN.md` where they disagree. Next
review: Fridays only, on the dates in section 7. **Research freeze until
15 Dec**: from here, only real replies change the plan.

## 1. The verdict

**No pivot. Same country, same niche, rebuilt offer.** Nothing we found beats
UK home-improvement firms clearly enough to justify starting over, and the
first 1,000 cold emails are the only research that matters now. Ship on
**25 October**.

What does change:

1. **How we contact old quotes.** Texting or emailing a homeowner about an
   old quote is legal only if the installer offered a marketing opt-out when
   the homeowner first asked for the quote. Our scan of 14,384 trade websites
   found one on about 2%, and phone enquiries get none. The ICO says that
   without it, those texts "would breach PECR"; a "can we keep in touch?"
   text is itself marketing. So **old quotes get a letter** in the
   installer's name with "text YES to this number if you're still thinking
   about it". Post isn't covered by PECR, and once the homeowner texts us,
   every message after that is a reply. (A UK solicitor confirms before the
   first letter goes out.)
2. **What the business is.** Old quotes are the **door-opener**: one-off,
   small (about £300-1,200 per client) and a "nice to have" for most owners.
   The **business** is the monthly service that wins *new* quotes. That's
   legal from day one because we add the opt-out when the enquiry comes in.
3. **Who we email first.** Established window firms (2,130) and kitchen
   firms (612): 5+ years trading, filed accounts. Roofers under 5 years old
   stay out of the first 1,500 sends; established roofers come after.

## 2. What we sell

**Door-opener: "Quotes that went quiet, followed up properly."**
- We write to the homeowners they quoted in the last 3-24 months: a calm
  letter from them. Anyone still interested texts back, and we book them
  into the diary.
- The installer pays postage at cost (about £0.80-1.30 a letter). That's
  their money, not ours, so the "no spend before the first sale" rule
  holds.
- Two arms to test in the first emails: **A** pay per booked survey; **B**
  first batch free, then per survey.
- A booked window survey is worth about £330-670 in gross profit to them:
  £3,700-7,400 jobs × ~30% close (Glasgrowth's published client data) ×
  ~30% margin (guess). £100-150 per survey is an easy yes on the numbers.
  The obstacle is trust, not price. Price stays off emails as before.
- **20% of their old quotes get nothing, chosen at random** (the holdout).
  That proves the bookings came from us, answers "they're my leads anyway",
  and makes the case study believable.

**The business: the monthly "quote desk", £300-500 a month.**
- An opt-out added to their web form, a phone line and the quote footer
  (day 1 of every pilot).
- Every new enquiry answered fast: speed-to-lead as a feature, never sold
  on its own (commodity under £50).
- Quotes written and sent **the same evening** from their notes and price:
  clear, branded, showing what's included and why it costs that.
- Every new quote followed up until yes or no.
- Agreed **before** the pilot ends. Offered on every results call.

**Dropped or parked:** missed-call text-back as a product, reviews, finance
introducing, recruitment (needs calls), dental (until we have a case study),
ads for clients (until 2-3 named case studies), white-label to agencies
(answer if one asks; don't chase it).

## 3. Who

| Order | Who | Why |
|---|---|---|
| 1 | Established window/door firms | Most old quotes; owner ~51; quote software exists for some, so lead with done-for-you + letters |
| 1 | Established kitchen firms (parallel slice) | Slowest decisions (6% of kitchen retailers confirm within a month); bigger jobs |
| 2 | Established roofers | Smaller backlog per firm; no UK roofing quote tool, so the quote desk fits |
| 3 | Extensions / lofts / garden rooms | Scored 28/40, above bathrooms/driveways |
| Plan B | UK B2B service firms (commercial cleaning, fit-out, signage) | Customers are businesses, so no homeowner-consent problem; the engine we built *is* the product. Only if the 15 Dec trigger fires |

Greeting: the director's first name when there's one director. Skip any firm
a competitor already serves (e.g. Glasgrowth's named clients).

## 4. How we get clients (90 days, €0)

1. **Cold email, fixed** (8 Google inboxes, ~53 new firms a day): name + one
   true fact about the firm; show the letter, not a text; easy one-word reply
   ("tens or hundreds?"); 3 emails; test offers, not wording; check whether
   each firm's email is Google or Microsoft (free lookup) and send
   accordingly.
2. **Warm intros and referral asks from day 1.** Every call ends with "who
   else do you know who quotes a lot?" Pablo lists anyone he knows with a
   UK trade link.
3. **Partners from week 3** (owner-led fabricators, trade bodies, quoting
   software). Normal terms here are pay-on-result: about £150 per client or
   20% recurring.
4. **First pilot → case study → video** of the owner, on day 1 of the pilot
   ask for permission.
5. **Not yet:** ads, letters *to installers*, content publishing,
   Upwork/Fiverr. Facebook groups: listen only.

## 5. Honest numbers

| | Low | Mid | High |
|---|---|---|---|
| Paying clients per 1,000 firms emailed (cold, no proof) | 0.3 | 1 | 2.5 |
| Pilots by day 90 | 0-1 | 1-3 | 4 |
| Monthly income, month 12 | ~£750 | ~£2,400 | ~£5,400 |

Assumptions and arithmetic are in `knowledge/2026-10-11_red_team.md` §4.

**Plainly:** this gets to a real income in a year if it works, not to rich.
At 10-20 hours a week Pablo can serve 2-3 monthly clients in term and 6-8 in
summer. Getting rich from here takes three more levers, in order:
1. **Proof.** One case study with numbers.
2. **Leverage.** AI-drafted quotes approved in one tap, then a VA by summer
   2027, then partners who bring installers in batches.
3. **Price.** Raise new-client prices to £450+ once there's proof. Glasgrowth
   charges £1.5-2k a month to about 10 installers.

Cash received is the only scoreboard.

## 6. Must be done before 25 Oct

| By | What | Who |
|---|---|---|
| 18 Oct | Rewrite cold email 1 + follow-up 2: show the letter line, no texting promise; keep the A/B on the offer line | Claude drafts, Pablo approves |
| 18 Oct | Send queue: established windows + kitchens first, young roofers out, director first name | Session card "Send established firms first" |
| 22 Oct | Letter pack: template with a logo slot, a demo letter for calls, the intake opt-out pack (form wording, phone line, quote footer), holdout rule, print-and-post provider chosen | Claude |
| 22 Oct | Ask a UK solicitor for a fixed-fee quote (asking is free; pay after the first sale) on: letters + text-back, the one-message service question, intake wording, processor vs joint controller, UK representative, lead-site contacts by post, liability cap | Claude drafts, Pablo sends |
| 24 Oct | Instant auto-reply with a booking link; human answer within 4 UK working hours (not 1); exam weeks in the calendar; max 2 pilots at a time until March | Claude + Pablo |
| 24 Oct | Pablo's existing launch items: Google OAuth client, legal name/address on the site, sign the LIA, booking page | Pablo (`PABLO_TODO.md`) |

## 7. Kill and pivot triggers (Fridays only)

| Date | Test | Fail → | Pass → |
|---|---|---|---|
| 27 Nov | ≥2 positive replies from ~500 established firms (seed test passed) | Next 500 get arm 2: "quotes going out late / evenings lost to quoting → we write them tonight". Check deliverability before blaming copy | Same offer, next 500 |
| 15 Dec | ≥1 sample of quotes **and** ≥3 calls held (~1,500 firms) | Plan B slice (B2B service firms) in January; trades continue at low volume | Pilot letters print the week of 4 Jan (nothing lands 15 Dec-5 Jan) |
| Any time | Solicitor says letters are unsafe too | Old quotes become installer-made calls only; lead with the quote desk | — |
| 14 Feb | First pilot: ≥300 letters, holdout in place | <1% booked over the holdout → old quotes are a hook only; sell the monthly alone | ≥2% → case study, video, re-contact the "not now" replies |
| 31 Mar | ≥2 paying clients **and** ≥£1,000 received | Trades stop being the main bet; the arm with a paying client gets the hours; decide 30 Apr without guilt | Prices up to £450+, push partners, plan a summer VA |
| Any time | A homeowner complaint | Pause that client; review wording and data source; tell the solicitor | — |

## 8. What we learned that changed our minds

- The "38% never heard back" figure is about homeowners who never *got* a
  quote. It supports the quote desk, not old-quote recovery. The 4%/27%/55%
  quote-speed numbers come from a vendor's CEO and cover none of our trades.
  Use neither in old-quote arguments; cite carefully if at all.
- Glasgrowth names 10 installers and publishes ~30% appointment-to-job
  rates. It's stronger than we thought, and it proves installers pay
  £1.5k+/month.
- Kitchens: 48% of retailers convert over 60% of enquiries, so their dead
  pool may be smaller even though decisions are slow.
- Google Workspace's acceptable use policy bans unsolicited mass email. Keep
  volumes low (~20 a day per inbox), verify addresses, and add a second
  provider after the first sale.

## Sources

`knowledge/web_research/2026-10-11_niche_ethnography_web.md`,
`knowledge/kb_digest_2026-10-11_niche_owners.md`,
`knowledge/web_research/2026-10-11_strategy_pain_offers.md`,
`knowledge/web_research/2026-10-11_strategy_alt_niches.md`,
`knowledge/web_research/2026-10-11_strategy_channels.md`,
`knowledge/2026-10-11_red_team.md`, `NICHE_PROFILE.md`, `LEARNINGS.md`.
