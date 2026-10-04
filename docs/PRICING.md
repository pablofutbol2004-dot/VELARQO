# Pricing: options, starting choice, tests

Status: **undecided, being tested.** Never put a price in a cold email.
Prices come up only on calls, from the pricing test (`call-sheet` tells you
which one to quote).

Sources: the pricing and unit-economics rules in the `ad` pack, Pass 02
(`pricing_and_unit_economics.md`, `window_door_market_economics.md`), Pass 07
(DB reactivation model), Pass 12 economics rules.

## What we know (and don't)

- **Outside option:** a UK window/door lead vendor advertises *fresh* booked
  appointments from about £130 (vendor claim, checked 2026-09-30). Installers
  already buy appointments, so "pay per booked survey" is a unit they understand.
- **What a booked survey is worth to them** is
  job value × margin × show rate × close rate. Illustration only:
  £6,000 × 25% × 80% × 25% ≈ £300. Real numbers come from calls.
- **Unknown until pilots:** how many old quotes turn into bookings, no-show
  rate, our time per booking, and therefore our cost floor.

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
| 9 | Monthly retainer | Ongoing chasing of every new quote | Only after proof | Recurring revenue | Low | **The long-term model** once the old backlog is used up |
| 10 | Software subscription | They run it themselves | Low (trades want done-for-you) | Product to build | n/a | Not now |

Payment terms we can test independently of price: weekly invoice, a cap per
batch (so the bill can't run away), a deposit/credit pack, card on file.

## Starting choice (for the test, not forever)

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

## Pricing tests

### P1: price level (running from the first call)

Config: `config/experiments/pricing_p1.json`. The model stays fixed at
per-booked-survey. The price on each call is **£60, £110 or £175**,
assigned per company by `call-sheet` (stable, so a prospect always hears
the same price).

Before saying the price, ask the same three questions on every call and
write the answers in the `outcome ... --note`:
1. "What do you pay now to get a survey in the diary (leads, ads, Checkatrade)?"
2. "Out of 10 surveys, how many turn into a job, and what's a typical job worth?"
3. "If I booked a survey back in from your old quotes, at what price would that be a no-brainer, and at what price would you not bother?"

Then quote the arm's price and log the reaction:
`python -m pipelines.outbound outcome <email> call_held --reaction ok|hesitant|objected --note "..."`

Decision (directional, about 8+ calls per price): take the highest price where at least half
of qualified prospects send a sample and price isn't the most common objection.
`python -m pipelines.outbound results pricing_p1`.

### P2: model (after about 3 pilots)

With real no-show rates, booking rates and our time per booking, offer a
menu on calls:
- per booked survey;
- per attended survey (at a higher price);
- flat batch fee;
- **small refundable deposit** (e.g. £150-250), credited against the first
  fees. Added 2026-10-04 from the YouTube research
  (`docs/knowledge/youtube_research/`): a fully zero-risk offer attracted the
  worst clients in Clay Lawrence's case, and a deposit filters out tyre-kickers.
  Test it rather than assume it: the free start may still close faster at our stage.

Record which one they pick. Choices reveal preference with fewer calls than
yes/no tests.

### P3: payment terms and expansion

Test weekly invoicing against a prepaid credit pack. Then test a retainer
for ongoing follow-up once a client's backlog is used up.

## Rules we hold ourselves to

- Judge prices on samples sent, pilots, margin and disputes, not on "they said yes on the call".
- One prospect objecting is not evidence. Look at the pattern across the arm.
- If many prospects say yes instantly at the top price, the price may be too low.
- Every price must cover our cost per booking once pilots show what that is (track it in `pass_12.../economics/unit_economics.csv`).
- Log every pricing decision in `docs/experiments/LOG.md`.
