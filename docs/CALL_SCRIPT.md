# The 15-minute call: exact words

For calls with installers who replied to a cold email. Phone, not video.
Goal of the call: understand their old quotes and get five of them read to
you, or a sample sent. Not to pitch. Full detail: `docs/SALES_PLAYBOOK.md`.
Before the call: `python -m pipelines.outbound call-sheet <email>` (history,
which price to quote).

## Before you dial (2 minutes)

- Their website open: trade, town, years, what they fit.
- Pen and the three numbers you want: quotes per month, old quotes, job value.
- Say out loud once: "I'm here to understand, not to sell."

## 0:00 Opening (30 seconds)

> "Hi [name], it's Pablo from Velarqo, you replied to my email about last
> year's quotes. Is now still OK for ten or fifteen minutes?"

If yes:

> "Quick version of why I asked for a call: I don't want to tell you how it
> works before I understand how quotes go quiet at [company]. So I'll
> mostly ask questions, and if it's not a fit I'll say so. Fair?"

## 1:00 Their numbers (4 minutes)

Ask, then shut up. Write the answers down.

1. > "Roughly how many quotes do you send a month?"
2. > "Out of ten quotes, how many turn into a job?" then "What's a typical job
   > worth?"
3. > "After a quote goes out and the homeowner goes quiet, what happens?
   > Who chases, how many times, when do you stop?"

Follow-ups if short answers: "What do they usually say when they go
quiet?" "Is it price, timing, or they just vanish?"

3b. > "After a survey, when does the quote go out: on the night, next day,
    > later? When do you actually write them?"
3c. > "How do you send it: WhatsApp, text, email, paper?"
3d. > "Be honest: what's the bigger headache right now, getting enough
    > enquiries, or turning the ones you get into jobs?"

## 5:00 The backlog (3 minutes)

4. > "If you looked at the last two years, how many quotes never turned into
   > a yes or a no? Tens, hundreds?"
5. > "Where do they live: CRM, quoting software, spreadsheet, email?"
   If "nowhere really": "Do you use Xero or FreeAgent? The customer list
   exports in two clicks, that's often enough to start."
5b. > "When people ask you for a quote, how do they do it: phone, web form,
    > Checkatrade? Does the form say anything about contacting them
    > later or opting out?" (Legal: decides whether we may text/email old
    > quotes. Note the exact answer.)
5c. > "Does your software or your fabricator already send chasers? Do you
    > actually use it?"
6. > "Could you pull one up while we're talking? Just tell me the date, what
   > it was for, and roughly the value. Names not needed."

If they pull one up, ask for four more, one at a time. That's the sample.
Write each: date, product, value, status. Then:

> "Right, so that one's nine months old, eight grand, never heard back.
> That's exactly the kind I'd chase."

## 8:00 What they pay now (2 minutes)

7. > "What do you pay today to get a survey in the diary? Leads, Checkatrade,
   > ads?"
8. > "If I put a survey back in your diary from one of those old quotes, what
   > would that be worth to you? What price would be a no-brainer, and at
   > what price wouldn't you bother?"

Only now, if they ask, say the price from the call sheet. Never before.

## 10:00 How it works (1 minute, no more)

> "Here's all I do. I take those old quotes, I text and email the homeowner
> in [company]'s name, something like: 'Hi, it's [company], we quoted for
> your windows a while back, did you ever get that sorted?' Anyone who says
> no is left alone for good. Anyone who says yes, I get a date in your
> diary. You only pay for surveys that get booked."

Pause. Let them react. Common reactions and the one-line answers are in
`SALES_PLAYBOOK.md` section 4 (they're my leads anyway / booked solid /
don't annoy my customers / how do I know it works / can't guarantee).

## 11:00 The close (2 minutes)

Pick one, smallest first:

**A. They read you five quotes already:**
> "Those five are enough to start. Send me twenty to fifty like that,
> names blanked if you like, and I'll tell you honestly which are worth
> chasing. If it looks good, you approve every word before anything goes
> out, and the first batch starts the week after. I can start Monday."

**B. Nothing read yet:**
> "Easiest next step isn't a contract. Send me a sample of twenty old
> quotes, date, product, value, status. I check them, no cost, and tell you
> what I find. Can you do that this week?"

**C. If the free-50 arm (cold_offer_v1 B) or they hesitate on price:**
> "I'll chase your first fifty for free so you can see it work. If it books
> surveys, the rest carry on at the per-survey price. I run three of these
> at a time, so the next slot is [date]."

Then:
> "Who's the best person to send the export, you or someone in the
> office? And what's the best email?"

## 14:00 End (30 seconds)

> "Thanks [name]. I'll send a two-line email in the next hour with what I
> need from you. If you decide it's not for you, just say so, no hard
> feelings."

## Within the hour: the recap email

Subject: `Re: last year's quotes` (same thread)

> Hi [name],
>
> Good to talk. What I need from you: a sample of 20-50 old quotes (date,
> what it was for, value, status; names can be blanked). Reply with it
> attached or tell me who's sending it.
>
> Then: I check them (no cost), you approve the exact messages, first
> batch starts the following week. You only pay for surveys that get
> booked.
>
> Pablo

Log it: `python -m pipelines.outbound outcome <email> call_held --reaction ok|hesitant|objected --note "quotes/month X, backlog Y, job value Z, system W"`.
Add anything new they said to the "questions installers ask" file.

## Signals to log after every call (these can change the strategy)

Write yes/no for each in the outcome note, then add a line to
`docs/LEARNINGS.md` if anything is new. Thresholds come from
`knowledge/web_research/2026-10-11_strategy_pain_offers.md` section 6.

- **More enquiries > chasing?** (6+ of the first 10 say yes → shift to
  booked surveys from live enquiries / leads.)
- **Quoting eats evenings or goes out days late?** And would they let
  someone else write/send quotes in their name? (3+ and 2+ → run the
  free "quote that sells + same-day" test, roofers first.)
- **Original enquiry form offered an opt-out?** (Mostly no → old-quote
  texting becomes letters / installer-sent / consent-only.)
- **Already chasing with software and actually using it?**
- **Backlog size and age** (tens / hundreds; how far back).
- **What they pay per survey/lead today** (£).
- **Exact words** they used for the problem. Copy them into the copy bank.

## Things that kill the call

- Talking first. Ask, then wait.
- Saying the price before question 8.
- Explaining how the messages work for more than a minute.
- Asking for the whole database.
- Promising a number of bookings. "I don't know yet, that's what the first
  batch tells us both."
- Ending without a specific next action and a date.

## Practice plan (before 25 October)

1. Read the script aloud twice.
2. Five practice calls with Claude playing the installer (friendly,
   busy, sceptical, "we already follow up", "how much?"). Record them on
   your phone. After each: what did I ask well, where did I talk too much,
   did I get the five quotes.
3. One practice call in Spanish with a friend playing a UK installer, just
   to hear your own voice under pressure.
4. The first three real calls are practice too. Score each: numbers
   collected (yes/no), sample asked for (yes/no), next step with a date
   (yes/no).
