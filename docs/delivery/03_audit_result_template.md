# Audit result: the one page we send after checking a sample

Send after `python -m client_onboarding.sample_audit` (map step 4.5). Copy the
counts from the `audit.md` it writes. Plain text email or a one-page PDF.
**Counts only. Never names, addresses, numbers or single quotes that could
identify a homeowner.** No price in writing; the price is agreed on the call.

---

Subject: your old quotes: what I found

Hi [name],

I've been through the [total] quotes you sent. Here's what I found.

**[worth chasing] of [total] look worth chasing.**

That means: not won, not opted out, quoted between 3 and 24 months ago, and
[with a phone number or email / with a usable date; contact details weren't in the sample, so I'll check those on the full list].

**By age**

| Quoted | Worth chasing |
|---|---:|
| 3-6 months ago | [n] |
| 6-12 months ago | [n] |
| 12-24 months ago | [n] |

**By product**

| Product | Worth chasing |
|---|---:|
| [windows] | [n] |
| [doors] | [n] |
| [other] | [n] |

[Optional, only if values were in the sample: Those quotes add up to about
£[total quoted value], around £[average] each. That's what was quoted, not
what you'd win.]

**Why I'd leave the others alone**

| Reason | Quotes |
|---|---:|
| Already won or booked | [n] |
| Asked not to be contacted | [n] |
| Too recent (under 3 months, you may still be chasing them) | [n] |
| Too old (over 24 months, most will have moved on) | [n] |
| No usable date | [n] |
| [Came from a lead site or another company, so we can't message them] | [n] |
| [Outside your area] | [n] |

**What I'd suggest**

- Start with the full list of quotes from the last 3-24 months, sorted the
  same way. On this sample, that's roughly [worth chasing ÷ total] of
  your list.
- First batch: [50-100] homeowners, then the rest in batches of
  [size] once we've checked the first one went well.
- About [15]% of the eligible quotes are picked at random and left alone.
  Nobody contacts them. Comparing the two groups shows what the follow-up
  actually added, compared with doing nothing.
- Each homeowner gets up to 3 texts and 1 email over about 2 weeks, in
  [company]'s name. Anyone who says no or STOP is never contacted again.
- You only pay for surveys that get booked. If the homeowner doesn't turn
  up, that one isn't charged.

**What I'd need from you**

1. Sign two short documents: the pilot terms and a data agreement (you own
   the data, I only use it to run this for you).
2. Fill in a 2-page form: your area, survey slots, who replies, and how the
   quotes were collected.
3. Approve the exact messages, word for word.
4. Send the full export of the quotes above, plus your do-not-contact list
   if you keep one.

**Next step:** a 15-minute call to go through this and agree the details.
Does [day] or [day] work?

Pablo
Velarqo, velarqo.com

---

Notes for Pablo
- If fewer than about [100] look worth chasing, say so plainly. A tiny list
  may not be worth a pilot, and the holdout comparison won't mean much.
- If the sample shows a lot of Checkatrade/Bark/bought leads, say they can't
  be messaged (see `06_compliance_notes.md`) and count them as excluded.
- If the sample had no source column, ask on the call how the quotes were
  collected. Don't promise anything about the full list until you know.
- Log it: `python -m delivery.pilot advance <pilot_id> audited`.
