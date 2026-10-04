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
> who's still interested gets booked back in for a survey. Nothing to pay
> unless surveys get booked.
>
> Easiest is a 15-minute call so I can see if your old quotes are worth
> doing. What day suits, or what's the best number to ring you on?

**"How much?"** (no price in writing. Prices are tested on calls, see `docs/PRICING.md`)
> No setup fee, and nothing to pay unless it gets surveys in your diary.
> The exact number depends on how many old quotes you've got and what a
> job's worth to you, so it's easier on a quick 15-minute call. When suits?

**"Send me info"**
Send `docs/knowledge/pass_12_launch_evidence_pack/client_handoff/pilot_one_pager.md`
(trim it to half a page first) and end with one question: *"Roughly how many
quotes from the last 12-24 months never turned into a job?"*

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

Export request detail: `docs/knowledge/pass_13_first_10_installers/handoff/export_request.md`.

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

## 4. Objections

| They say | You say |
|---|---|
| "They're my leads, I'd have got them anyway." (the biggest objection, per the YouTube research) | "Only if someone was still chasing them. We only touch quotes that have had no contact for 3-6 months, the ones you've written off. And we keep a slice of them uncontacted, so you can see what we added compared with doing nothing." |
| "How do I know it works?" | "You don't yet, and neither do I on your data. That's why it's a small pilot and you only pay for booked surveys." |
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

## Pricing on calls

Before every call: `python -m pipelines.outbound call-sheet <email>`. It
shows their history and **which test price to quote** (pricing test P1).
Ask the three questions in `docs/PRICING.md` before saying the price, then
log the call: `python -m pipelines.outbound outcome <email> call_held --reaction ok|hesitant|objected --note "..."`.
