# Sales playbook: from a reply to a pilot

One page you use daily once emails are going out. It's built from the
ChatGPT passes (`docs/knowledge/pass_03`, `pass_13`), cut down to the current
offer. Run every reply through `python -m pipelines.outbound replies`.

**Goal of every reply:** get a 15-20 minute call. Goal of the call: get a
small sample export. Goal of the sample: a bounded pilot.

## 1. Answering replies (same day, short, plain text)

**Interested / "tell me more"**
> Thanks {name}. Simple version: you send me a list of quotes that went
> quiet, I follow those homeowners up in your company's name, and anyone
> who's still interested gets booked back in for a survey. You only pay for
> surveys that get booked.
>
> Easiest is a 15-minute call so I can see if your old quotes are worth
> doing. What day suits, or what's the best number to ring you on?

**"How much?"** (no price in marketing copy or emails. Prices are tested on calls, see `docs/PRICING.md`. The price goes in the signed agreement and invoices only.)
> No setup fee, and you only pay for surveys that get booked.
> The exact number depends on how many old quotes you've got and what a
> job's worth to you, so it's easier on a quick 15-minute call. When suits?

**"Send me info"**
Send `docs/delivery/01_send_info_email.md`
(already half a page; it ends with: *"Roughly how many
quotes from the last 1-2 years never turned into a job?"*

**"We already follow up"**
> Good, a lot don't. Out of interest, what happens after the second or
> third chase? If every quote gets to a clear yes or no, this probably
> isn't for you and I'll leave you be.

Disqualify honestly if their follow-up really is solid.

**"Is this GDPR-OK?" / "Where did you get my email?"**
Answer it yourself, never with a template. Say where it came from (their
website), that you only email companies, and that you've removed them if
they want that. Then `suppress` them if they ask.

**"No" / unsubscribe / angry**: already suppressed automatically. Don't reply
to argue. Mark handled.

## 2. The 15-20 minute call

1. **Frame (1 min):** "I want to understand what happens to a quote when the
   homeowner goes quiet, and whether there's a sensible pilot here. If
   there isn't, I'd rather tell you."
2. **Numbers (4 min):** enquiries, surveys and quotes per month, jobs won,
   typical job value. Ranges are fine.
3. **Follow-up reality (4 min):** after the quote goes out, who chases, how
   many times, when do they stop? Why do homeowners stall?
4. **Backlog and systems (4 min):** rough count of unclosed quotes from the
   last 2 years. Where they live (CRM, quoting software, spreadsheet,
   inbox). Can they export date, product, value, status?
5. **Where the data came from (2 min):** website form, phone, showroom,
   bought leads? Opt-outs recorded?
6. **Capacity (2 min):** "If 5 extra surveys landed next week, could you
   cover them?"
7. **Next step (2 min):** see section 3.

Write down: monthly quotes, backlog size, oldest useful quote, system, job
value. These answer the biggest open questions in the business.

## 3. The close (small, not big)

> "The next step isn't a contract or touching your whole database. Send me
> a sample of 20-50 old quotes (date, product, value, status; names and
> numbers can be blanked out for now). I'll check what's usable. If it
> looks good, we agree what counts as a booked survey, you approve the
> messages, and we run a small first batch."

Export request email: `docs/delivery/02_export_request_email.md`.

### Free first 50 (cold test arm B)

Some firms reply to "I'll chase your first 50 for free". The close is the
same as above, but the first batch is 50 quotes and costs them nothing.
Three rules, because the risk is your time, not money:

1. **Cap: at most 3 free pilots running at once.** Anyone else goes on an
   honest waiting list: "I run a few at a time so each gets done properly.
   I can start you on [date]."
2. **Agree the next step before starting:** "If it books surveys, the rest
   of your old quotes carry on at the per-survey price." Say it on the call
   and in the confirmation email, so the free 50 leads into a paid deal.
3. **Keep it light:** data-processing agreement, export of the 50, one
   message template they approve, one calendar link, about 2 weeks. No full
   GHL build until they agree to continue (GHL trial covers the first one
   or two).

### No-export start (when "send me your old quotes" is the scary step)

Pre-mortem (`PATH_6_MONTHS.md` section 8): replies come, nobody sends data.
Asking a stranger to export their customer list is the biggest ask in the
whole process. So don't make it the first step. Offer one of these on the
call, smallest first:

1. **Read me five.** "Open your quotes, pick five from last year that never
   went ahead, and read me the date, what it was for, and roughly the
   price." Pablo types them into a 5-row CSV (`clients/<slug>/first5.csv`:
   date, product, value, status, first name, mobile). That's the sample.
2. **Forward me twenty.** "Forward the last 20 quote emails that went
   quiet to pablo@velarqo.com; I'll do the rest." Pablo pulls the rows out
   by hand (20-30 min) into the same CSV. No export, no CRM login.
3. **A screenshot** of the quotes list, if that's easier for them.

Then: `sample_audit` on the CSV, the `03` counts email the same day, and
the message approval sheet (`09`). The first batch is those 5-20 people.
When the first replies come in, send them the **"still keen" list**: who
replied, who wants a survey. That's when the full export and the data
agreement come: "Want me to do this for the rest? Send me the full list
from the last two years, and here are the two short documents."

Two rules so this stays legal (the lawyer confirms the wording,
`PABLO_TODO.md`):

- Before touching even five names, get a one-line written instruction by
  email: *"Please follow up these quotes for us by text and email in our
  name; the details stay ours and you delete them when we say."* They
  reply "agreed". That is the processing instruction UK GDPR needs; the
  full DPA (`05`) replaces it when they continue. Never message anyone
  before that reply exists.
- The five or twenty must be quotes **they** collected (website, phone,
  showroom), not Checkatrade/Bark leads. Ask on the call; it's a two-second
  question and it decides whether the messages are allowed.

Everything else is the same path (`docs/delivery/DRY_RUN_2026-10.md`
section 5): the CSV goes through `pilot import` like any export, the
holdout can be 0 for a batch this small (`create --holdout 0`), and the
canary is the whole batch.

## 4. Objections

| They say | You say |
|---|---|
| "They're my leads, I'd have got them anyway." (the biggest objection, per the YouTube research) | "Only if someone was still chasing them. We only touch quotes that are 3-24 months old and weren't won, and anyone who's opted out is left alone. These are the ones you've written off. And we keep a slice of them uncontacted, so you can see what we added compared with doing nothing." |
| "We're booked up for months." (good installers often run 8-12 week lead times) | "Good problem. This isn't about this week: it fills next season and the gaps when a job falls through, from people who already know your prices. We can pace it to your diary." |
| "How do I know it works?" | "You don't yet, and neither do I on your data. That's why it's a small pilot and you only pay for surveys that get booked. Be clear that this means booked, not sold: they pay for a booked survey even if the job doesn't follow." |
| "Why not call them ourselves?" | "You can. If your team already works every old quote, you don't need me. This is for the quotes nobody gets round to." |
| "I don't want to annoy old customers." | "Neither do I. Short messages from your business, anyone who says no is never contacted again, and you approve the wording." |
| "Our data's a mess." | "Most is. Send a small sample and I'll tell you if it's usable before anything goes out." |
| "Can you guarantee sales?" | "No. I can't control your survey or your price. I only charge for what I can deliver: the booked survey." |
| "That's too much." | "What does a booked survey cost you now, and how many turn into jobs? If the numbers don't work for you, we shouldn't do it." |

## 5. Never

- Promise a response rate, number of bookings, or sales.
- Mention clients, results or case studies (there are none yet).
- Give a legal verdict on their data before seeing it.
- Ask for the full homeowner database on day one.

## After the sample

Audit the sample with `python -m client_onboarding.sample_audit`, then send
the audit result (`docs/delivery/03_audit_result_template.md`). If they want
to go ahead, the pilot agreement and data processing agreement are
`docs/delivery/04_pilot_agreement.md` and `05_data_processing_agreement.md`.
Both are **drafts**: a UK lawyer must check them before a client signs.
Everything after that is in `docs/delivery/README.md`.

## Pricing on calls

Before every call: `python -m pipelines.outbound call-sheet <email>`. It
shows their history and **which test price to quote** (pricing test P1).
Ask the three questions in `docs/PRICING.md` before saying the price, then
log the call: `python -m pipelines.outbound outcome <email> call_held --reaction ok|hesitant|objected --note "..."`.
