# Pricing: options, starting choice, tests, monthly product

Status: **pilot price being tested; monthly tiers are anchors to test, not
fixed.** Never put a price in a cold email, reply or on the website. Prices
come up only on calls, from the pricing test (`call-sheet` tells you which
one to quote), and in writing only in agreements, one-pagers sent after a
call, and invoices.

Sources: the pricing and unit-economics rules in the `ad` pack, Pass 02
(`pricing_and_unit_economics.md`, `window_door_market_economics.md`), Pass 07
(DB reactivation model), Pass 12 economics rules, and the 2026-10-10 web
research (`docs/knowledge/web_research/2026-10-10_monthly_product_renewables.md`,
`2026-10-10_competitors.md`).

## What we know (and don't)

- **Outside option:** a UK window/door lead vendor advertises *fresh* booked
  appointments from about £130 (vendor claim, checked 2026-09-30). Installers
  already buy appointments, so "pay per booked survey" is a unit they understand.
- **What a booked survey is worth to them** is
  job value × margin × show rate × close rate. Illustration only:
  £6,000 × 25% × 80% × 25% ≈ £300. Real numbers come from calls.
- **What a tradesperson can already buy monthly:** quote-chasing templates
  inside their job software for about £37-44 per user; missed-call text-back
  for £35-100; an AI receptionist for £99-500; a bundle (site + reviews +
  follow-up) for £197. Nobody sells "someone runs it and books the survey"
  as a priced installer retainer. Pure text-back is a commodity; above
  about £200 a month the price has to come with booked outcomes.
- **Unknown until pilots:** how many old quotes turn into bookings, no-show
  rate, our time per booking, and therefore our cost floor. For the monthly
  product, also unknown: how many new quotes a client sends a month, and how
  many missed calls and enquiries they get.

## Every way we could charge

| # | Model | How it works | Easy yes? | Our risk / cash | Disputes | Verdict |
|---|---|---|---|---|---|---|
| 1 | **Per qualified booked survey** | £X each time a homeowner confirms interest and agrees a date | High: they only pay for something real | Paid within a week of the work | Low with a written definition + no-show credit | **Test now (P1)** |
| 2 | Per attended survey | Pay only if the homeowner is in when they visit | Very high | Slower; their calendar affects our pay | Medium (who caused the no-show?) | Test later (P2), once we see no-show rates |
| 3 | Per won job (flat fee) | £X per sale from a reactivated quote | High | Slow; their selling decides our pay | High (attribution, honesty of reporting) | Later, maybe as a bonus on top of 1 |
| 4 | % of won revenue | e.g. 5-10% of job value | Feels fair | Very slow, depends on them reporting | Highest | **No** as the main model |
| 5 | Per handed-over hot lead | Pay per interested homeowner; they do the booking | Medium | Cheaper unit, we do less | Medium ("not really interested") | Fallback if we can't book on their behalf |
| 6 | Flat fee per batch | e.g. £X to work up to 300 old quotes | Low before proof | Cash up front; we carry the risk of no results | Low | P2 menu option once we have proof |
| 7 | Setup fee + lower per-survey | e.g. £Y setup + smaller £X | Lower | Covers data cleaning on messy lists | Low | P2, for big or messy lists |
| 8 | Free first few surveys | First 3-5 bookings free, then model 1 | Very high | Costs only our time | Low | A lever for 1-2 proof pilots, traded for data access + permission to share results |
| 9 | **Monthly fee + per booked survey** | Every new quote chased, enquiries answered; a smaller fee per survey on top | Only after a pilot | Recurring revenue; fixed costs covered | Low (same booked-survey definition) | **The long-term model.** Terms below and in `docs/delivery/11_monthly_terms.md` |
| 10 | Software subscription | They run it themselves | Low (trades want done-for-you) | Product to build | n/a | Not now |

Payment terms we can test independently of price: weekly invoice, a cap per
batch, a deposit/credit pack, card on file, first month in advance.

## Starting choice (for the pilot, not forever)

**Model 1: per qualified booked survey.** No setup fee, no-shows credited, the
first batch capped (e.g. max 20 billable), invoiced weekly.

Why this one:
- The unit matches something they already buy.
- We control the booking, so we can see the billable event ourselves.
- Cash arrives quickly.
- It's easy to say yes to before we have any proof.

It's the "clean billing trigger, low dispute surface" rule from Pass 02.

"Qualified booked survey" means all of these:
- the homeowner is from their own quote list;
- they confirm they're still interested in something the installer offers;
- they're in the installer's area;
- they aren't already back in the installer's pipeline;
- a specific date and time is agreed;
- it's written in the shared booking log.

The full definition with edge cases (rebooks, same person, direct contact,
cancellations) is section 4 of `docs/delivery/04_pilot_agreement.md`. The
monthly product reuses it unchanged.

## Pricing tests

### P1: price level (running from the first call)

Config: `config/experiments/pricing_p1.json`. The model stays fixed at
per-booked-survey. The price on each call is **£75 or £150** (two prices, because only about 5-20 calls are expected in the first 6 weeks),
assigned per company by `call-sheet` (stable, so a prospect always hears
the same price).

Before saying the price, ask the same three questions on every call and
write the answers in the `outcome ... --note`:
1. "What do you pay now to get a survey in the diary (leads, ads, Checkatrade)?"
2. "Out of 10 surveys, how many turn into a job, and what's a typical job worth?"
3. "If I booked a survey back in from your old quotes, at what price would that be a no-brainer, and at what price would you not bother?"

Then quote the arm's price and log the reaction:
`python -m pipelines.outbound outcome <email> call_held --reaction ok|hesitant|objected --note "..."`

Decision (directional, about 6+ calls per price): take the highest price where at least half
of qualified prospects send a sample and price isn't the most common objection.
`python -m pipelines.outbound results pricing_p1`.

### P2: the menu (from the end of each pilot; a read after about 3 pilots)

With real no-show rates, booking rates and our time per booking, offer a
menu on the results call. Record which one they pick: choices reveal
preference with fewer calls than yes/no tests.

**How the menu is offered on a call** (never in a cold email; prices only
spoken, then in the one-pager `docs/delivery/11_monthly_terms.md` sent
after the call):

1. Start with their own numbers from the weekly reports: homeowners
   contacted, replies, surveys booked, attended, no-shows, anything won.
   No percentages in the headline, small-numbers warning as usual.
2. Ask what they'd like to keep: "Do you want this running on your new
   quotes as they come in, or just another batch of the old ones?"
3. Offer in this order, one at a time, and stop at the first yes:
   - **Monthly Chase** (new quotes chased as they come in; the default).
   - **Monthly Chase + Answer** only if they said on the call or in the
     intake that they miss calls or are slow to answer enquiries. Don't
     pitch it to a firm with a receptionist who answers everything.
   - **Another batch of old quotes** at the pilot price per booked survey
     (model 1), or **per attended survey** at a higher price (model 2), or a
     **flat batch fee** (model 6) if they'd rather know the bill up front.
   - **Small refundable deposit** (£150-250, credited against the first
     fees, refunded if no survey is booked in the batch) when a firm wants
     a second batch but is slow to send data or approve messages. Added
     2026-10-04 from the YouTube research (`docs/knowledge/youtube_research/`):
     a fully zero-risk offer attracted the worst clients in Clay Lawrence's
     case, and a deposit filters out tyre-kickers. Test it rather than
     assume it; the free start may still close faster at our stage.
4. Log the choice: `python -m pipelines.outbound outcome <email> call_held
   --note "P2 menu: chose <option>; also offered <options>"`.

### P3: payment terms and expansion

Test weekly invoicing against a prepaid credit pack for batches. For the
monthly product: first month in advance, then monthly in advance with the
per-survey fees added in arrears (see below).

### Free first 50 (offer test, not a price)

`cold_offer_v1` arm B offers to chase a firm's first 50 old quotes free.
Anything after that is billed per booked survey at the firm's `pricing_p1`
price. Max 3 free pilots at once; the continuation is agreed before the free
batch starts (rules in `SALES_PLAYBOOK.md`, section 3).

## The monthly product (what a pilot turns into)

Two tiers. Prices are **anchors to test on the first three results calls,
not fixed**; move them the same way as P1 (take the highest level where
at least half of pilots that booked a survey continue, and price isn't the
most common objection). Client-facing wording: `docs/delivery/11_monthly_terms.md`.
What has to exist in GoHighLevel to deliver each tier:
`docs/delivery/12_monthly_setup_checklist.md`.

| | **Chase** | **Chase + Answer** |
|---|---|---|
| Monthly fee (anchor) | £149 | £349 |
| Per booked survey (anchor) | £35 | £20 |
| Who it's for | A firm that quotes steadily and lets quotes go quiet | A firm that also misses calls or is slow to answer web and email enquiries |
| Every new quote chased | Yes: every quote they send us gets a 5-touch text and email sequence over about 30 days, in their name, wording approved once | Yes, same |
| Replies answered | By a person, within 1 working hour, 9am-7pm Mon-Sat | Same |
| Surveys booked into their diary | Yes, with confirmation and reminder texts | Yes |
| Missed-call text-back on a UK number | No | Yes: an unanswered call gets a text within a minute, and a person follows up |
| Instant reply to new enquiries (web form, email, text) | No | Yes: an automatic first reply within 5 minutes in hours, a person within 1 working hour |
| Out-of-hours | Nothing sent 7pm-9am or Sundays | An automatic reply that says when someone will call back and asks the two or three questions a surveyor needs |
| Old quotes re-chased | No (buy a batch at the pilot price) | Yes, once a quarter, on quotes that have gone 3+ months quiet |
| Review request after a completed job | Yes, when they tell us a job is done | Yes |
| Report | Monthly, plus the booked-survey log any time | Monthly, plus the log |
| Weekly booking cap (default) | 5 billable surveys a week | 8 billable surveys a week |
| Notice | 30 days, either side | 30 days, either side |

### Why a monthly fee *and* a per-survey fee

- **The monthly fee pays for the system that has to exist whether or not a
  survey gets booked this week:** the sub-account, the UK number, the
  sequences, someone watching replies every working day. Pure
  per-survey pricing would make us carry that cost for a client who sends
  three quotes a month.
- **The per-survey fee keeps us paid for the outcome,** which is the thing
  they said yes to in the pilot. A pure retainer is exactly what the
  Glasgrowth-style agencies sell against ("no retainer"), and the installer's
  first fear is paying for nothing.
- **The per-survey fee is lower than the pilot price** (£35 or £20 against
  £75-150) because the monthly fee already covers the work. It is far below
  what a fresh booked appointment costs them (from about £130), on a quote
  they already paid to create.
- **It's lower again on Chase + Answer** because that tier's monthly fee is
  bigger and more of the bookings come from calls and enquiries we only
  answered rather than chased for weeks.
- **Both fees together must stay under what they pay today for one fresh
  appointment per month.** If a client books fewer than one survey a month
  for two months running, the product isn't working for them; say so on the
  report and offer to pause.

### Rules that carry over from the pilot

- A booked survey is defined exactly as in the pilot agreement, section 4.
  Chase + Answer adds one case: a homeowner who rang or enquired and was
  booked by us from that call or enquiry counts too; a homeowner the
  installer booked themselves without our message or reply doesn't.
- No-show credited in full if the installer turned up or tried to reach the
  homeowner; charged if the installer caused it. A cancellation not rebooked
  within 14 days is a no-show. A rebook is still one survey. One charge per
  person per 90 days.
- **Attended option:** a client can choose to pay per *attended* survey
  instead, at a higher fee (anchor: £50 on Chase, £30 on Chase + Answer).
  Then they must record attended / no-show within 2 working days; a survey
  with no outcome recorded within 7 days is treated as attended. Offer this
  only once the first pilots show the no-show rate.
- **Weekly cap:** the client sets the cap on the terms sheet from how many
  surveys they can actually attend. Once the week's cap is reached we offer
  the homeowner dates in the following week instead of booking more. The
  cap can be raised by email any time.
- **Billing:** monthly fee in advance on the 1st (first month pro rata from
  the start date); per-survey fees for the previous month on the same
  invoice, less credits; 14 days to pay; disputes within 5 working days from
  the booking log. VAT wording to confirm with the gestor (as in `04`).
- **Notice:** 30 days by email, either side. Sequences already running
  finish or stop as the client prefers; surveys already in the diary stay
  and are billed; the UK number stays with us and any call diversion is
  removed on the end date; data returned or deleted within 30 days under
  the data processing agreement.
- **No setup fee** if the monthly plan starts within 30 days of the pilot
  ending; approved wording carries over. Otherwise a setup fee is a P2
  option (model 7), not a default.

### Offer check (honest version of the value equation)

- Dream outcome: surveys in the diary from quotes they already paid for,
  without anyone in the office having to remember to chase.
- Likelihood: their own pilot numbers, not our claims. No results promise,
  ever (`11`, "What we don't promise").
- Time: live within 5 working days of the sheet being signed; the first
  chase goes out the day a quote reaches us.
- Effort: they forward quotes (or we take a weekly export) and attend the
  surveys. Nothing to learn, no software to log into.
- Risk reversal is structural, not a guarantee: no setup fee, 30-day notice,
  no-shows credited, weekly cap. We do not offer "money back if no surveys";
  it would be a results claim in disguise.
- No scarcity. There are no "spots". Never invent any.

## Rough margin per tier (estimates, not results)

All of this is a guess until a client runs for a month. Usage figures are
labelled estimates; the real numbers go into
`pass_12.../economics/unit_economics.csv` as they arrive. Assumptions:

- GoHighLevel plans (USD, converted at about $1.30 to £1, so check the rate):
  Starter $97 (about £75, up to 3 sub-accounts), Unlimited $297 (about
  £230, unlimited sub-accounts, needed from client 4 and for rebilling
  usage). Agency Pro ($497) is for selling software and isn't needed.
- SMS: UK outbound about 3.5p a segment, inbound under 1p, UK number about
  £1.50 a month (GHL LC Phone, Twilio-backed; verify on the LC Phone price
  list before the first client). A filled text under 160 GSM characters is
  one segment; the sequence texts are written to stay under 300, so count
  two segments each to be safe.
- Email: negligible (fractions of a penny each).
- AI: none on Chase (a person answers). On Chase + Answer the out-of-hours
  reply is a fixed template, not AI, for the first clients. If Conversation
  AI is switched on later, budget about 1.5p a message (pay as you go);
  the flat "AI Employee" add-on at about £75 a sub-account a month would
  eat most of the tier's margin and is off until a client asks for it.
- Volumes per client per month (estimates): Chase, 40 new quotes, about
  200 segments, 5 booked surveys. Chase + Answer, the same plus about 30
  missed calls, 20 enquiries and a share of a quarterly re-chase, about 500
  segments, 8 booked surveys.
- Founder time per client per month (estimates): Chase about 4 hours,
  Chase + Answer about 7 hours. Solo capacity about 120 hours a month on
  delivery before anything else suffers.

Per client, per month:

| | Chase | Chase + Answer |
|---|---:|---:|
| Monthly fee | £149 | £349 |
| Per-survey fees (5 × £35 / 8 × £20) | £175 | £160 |
| **Revenue** | **£324** | **£509** |
| SMS + number (estimate) | £9 | £19 |
| Gross margin before GHL plan and time | £315 | £490 |

At 5 / 10 / 20 clients, all on one tier (GHL Unlimited from 4 clients):

| Clients | Tier | Revenue / month | Usage (est.) | GHL plan | **Margin before time** | Founder hours (est.) |
|---:|---|---:|---:|---:|---:|---:|
| 5 | Chase | £1,620 | £45 | £230 | **£1,345** | 20 |
| 5 | Chase + Answer | £2,545 | £95 | £230 | **£2,220** | 35 |
| 10 | Chase | £3,240 | £90 | £230 | **£2,920** | 40 |
| 10 | Chase + Answer | £5,090 | £190 | £230 | **£4,670** | 70 |
| 20 | Chase | £6,480 | £180 | £230 | **£6,070** | 80 |
| 20 | Chase + Answer | £10,180 | £380 | £230 | **£9,570** | 140 (over solo capacity) |

What the table says:
- Usage is small. The real cost is founder time, and Chase + Answer costs
  nearly twice the hours of Chase. Per hour, both tiers land near £65-70
  before tax, so neither subsidises the other on these guesses.
- 20 Chase + Answer clients is past what one person can run; that's the
  setter/VA point in `docs/PATH_6_MONTHS.md` (July onwards), not before.
- With 3 clients or fewer, GHL Starter (about £75) is enough; the step to
  Unlimited adds about £155 a month, so client 4 should be signed before
  the upgrade, not after.
- The per-survey line is a big share of Chase revenue (over half). If
  pilots show fewer than 5 bookings a month per client, the monthly fee
  anchor needs to go up or the product is a £149 retainer in disguise.

## Rules we hold ourselves to

- Judge prices on samples sent, pilots, margin and disputes, not on "they said yes on the call".
- One prospect objecting is not evidence. Look at the pattern across the arm.
- If many prospects say yes instantly at the top price, the price may be too low.
- Every price must cover our cost per booking once pilots show what that is (track it in `pass_12.../economics/unit_economics.csv`).
- Monthly prices are spoken on calls and written only in `11` and invoices. Never on the site, in a cold email or in a written reply before a call.
- Log every pricing decision in `docs/experiments/LOG.md`.
