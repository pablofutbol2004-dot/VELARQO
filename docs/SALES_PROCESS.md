# From today to money in your pocket: the whole process

One page. Each step: what happens, who does it, how long it takes, what you
do, where the detail lives. Dates assume the first send on 25 Oct 2026.

```
 1 send  →  2 reply  →  3 call  →  4 sample  →  5 audit  →  6 agree
 →  7 approve messages  →  8 first batch  →  9 bookings  →  10 invoice  →  11 paid
 →  12 "carry on monthly?"
```

| # | Step | Who | Takes | What you actually do |
|---|---|---|---|---|
| 1 | **Emails go out.** Engine sends email 1, then follow-up 2 three business days later, ~25/inbox/day, Mon-Fri UK hours. | Engine | From 25 Oct, continuous | Monday: `create-cohort`, read `review`, `activate`. Daily 5 min: `status`. |
| 2 | **Someone replies.** Classifier sorts it; a positive / "how much" / "send info" pings your phone. | Engine → you | Replies start ~1-3 weeks after first send (early Nov) | **Within the hour:** reply from the same inbox, same thread. Ask one question + two time options + "best number?" (`SALES_PLAYBOOK.md` §1). Never a link, never a price. If they give a number, ring them today. |
| 3 | **The call.** 15 min, phone. You ask about quotes, get five read to you, or ask for a sample. | You | 1-5 days after the reply | `call-sheet <email>` before. Script: `CALL_SCRIPT.md`. After: `outcome <email> call_held ...` and the recap email within the hour. |
| 4 | **They send a sample.** 20-50 old quotes (date, product, value, status; names blanked is fine). Or the five from the call. | Them | 1-7 days; chase once at day 3 with a short nudge, once more at day 7 (voice note) | Export request email: `docs/delivery/02`. If nothing after two nudges: park, re-contact in 60 days. |
| 5 | **You audit it.** The tool sorts quotes into worth chasing / why not, flags marketplace-sourced rows and opt-outs. | You + tool | Same day, 30 min | `python -m client_onboarding.sample_audit`, then send `docs/delivery/03` (audit result) with a one-line verdict and the next step. |
| 6 | **They say yes.** Agree the terms: what counts as a booked survey, the price per survey (from the call sheet; or free first 50 on arm B), no-shows credited, weekly cap, attribution window, "if it books surveys the rest carries on at the per-survey price". Sign the pilot agreement + data processing agreement. | Both | 1-7 days (2-3 weeks for cautious ones) | `docs/delivery/04` and `05` (drafts; lawyer before the first real one). Fill `07` intake form with them (who signs messages, their phone, diary, where the data came from). Register as autónomo the week this happens. |
| 7 | **They approve the exact messages.** Every word they'll send to homeowners. | Them | 1-3 days | `docs/delivery/08` (messages) + `09` (approval sheet). Any wording change = re-approve. GHL trial starts here; sub-account cloned, UK number. |
| 8 | **First batch goes to homeowners.** Texts + one email over ~2 weeks, from the installer's name, with a holdout slice kept back so the lift can be shown. | Engine/GHL | Day 0-14 | You watch replies daily; the "yes" ones get a survey time offered; anything odd goes to the installer. |
| 9 | **Surveys get booked.** Each booking written in the shared log with date and time; installer confirms. | You | Bookings come in days 1-14 | Weekly report `docs/delivery/10` every Friday. |
| 10 | **Invoice.** Weekly, per booked survey, no-shows credited. | You | Friday | Engine's invoice step; first invoice ~2-3 weeks after batch start. |
| 11 | **Paid.** 7-14 day terms into Revolut Pro (GBP). | Them | 1-2 weeks | Chase on day 15 if unpaid. |
| 12 | **"Carry on?"** Show the numbers, offer the monthly product (every new quote chased), or the rest of the backlog at the same price. | You | On the call after the report | `docs/delivery/11` monthly terms. Ask for two installer names. |

## Realistic calendar for client one

- 25 Oct: first emails.
- ~5-15 Nov: first positive replies; calls that week.
- ~15-25 Nov: first sample received (**the milestone**).
- ~25 Nov-5 Dec: audit, terms, messages approved.
- ~1-10 Dec: first batch out (or first week of January if it slips past 10 Dec; homeowners don't book surveys over Christmas).
- ~15-20 Dec: first bookings and first invoice.
- **~Early January: first money in your pocket.** If the batch runs in January instead, early February.

Every step after 2 happens in parallel for several installers at once; the
calendar above is one of them.

## The only numbers to track daily

sent → replies → positive → calls → samples → pilots → bookings → paid.
The scoreboard command prints them. A slow week means one of those arrows
is broken; fix that arrow, don't change the channel.

## Where it usually breaks, and what you do

| Break | Fix |
|---|---|
| Replies, no calls | Reply faster, ask for a number, ring them |
| Calls, no samples | Get five read on the call; "names blanked"; chase twice then park |
| Samples, no pilots | Too much paperwork: start with the free 50 and the intake form, lawyer docs can follow |
| Pilots, no bookings | Check the cohort (quoted-not-bought, 3-24 months) and data quality before blaming the offer |
| Bookings, no payment | Weekly invoices, written definition of a booked survey, chase at day 15 |
