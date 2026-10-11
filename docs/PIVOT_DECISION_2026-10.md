# Pivot decision: what Velarqo sells next (draft, 11 Oct 2026)

This takes over from ChatGPT's JP Middleton handoff (`knowledge/chat_research/2026-10-11_chatgpt_jp_handoff/`). It replaces the installer plan in `STRATEGY_DECISION_2026-10.md`. Every idea was run through `IDEA_RED_TEAM.md`. Pablo decides by **Fri 16 Oct**. The first send goes out around **2 Nov**.

## 1. The answer

**Sell to UK commercial service firms whose customers are other businesses.** Start with commercial cleaning and with fire & security installers. What we sell is **"win more contracts by email"**:

1. **The way in (pilot):** we follow up the proposals they sent in the last 3-18 months that never got a yes or no. For each one we either get it moving again, or get the date the prospect's current contract ends.
2. **The monthly service:** we follow up every new proposal until it's a yes or a no. We keep a calendar of competitors' contract end dates and re-contact each prospect before renewal. And we send cold email to new businesses in their area, booking site walk-throughs into their diary.

Why this and not the rest, in one breath:
- **It's legal at every step.** Our emails go to companies, and so do theirs. The ICO says you can email "any corporate body" without consent, as long as you identify yourself and give an opt-out. This is the exact problem that killed the installer plan.
- **It adds money,** not just time saved.
- **It's delivered by email, without phone calls, in a few hours a week per client.**
- **It reuses everything we've built:** the list pipeline, the sending engine and the follow-up logic.
- **Nobody we found sells old-proposal follow-up to these firms.** Our earlier niche review had already said commercial services would go to the top if the opt-out rule turned out to be strict. It did, so this was decided before today's frustration, not because of it.

## 2. How the options compare

Each option scored 1-5 on the `IDEA_RED_TEAM.md` §3 criteria. Evidence labels are as in the research files.

| Niche × first offer | Money pain | Will pay (evidence) | Easy to deliver | Legal | List | Fast result | Engine fit | Total | Verdict |
|---|---|---|---|---|---|---|---|---|---|
| **UK commercial cleaning × old proposals → new-proposal chase + outbound walk-throughs** | 3 | 3 (PromoSEO £500/mo; per-lead sellers) | 4 | 5 | 5 (13.1k trading 5y+; 5.9k not micro) | 3 | 5 | **28** | **Test (arm A)** |
| **UK fire & security installers × same** | 4 (bigger, recurring maintenance contracts: guess) | 2 (no specialist seller found) | 4 | 5 | 4 (9.2k trading 5y+; 4.6k not micro) | 3 | 5 | **27** | **Test (arm B)** |
| UK facilities management × same | 4 | 2 | 3 | 5 | 2 (4.5k; 2.1k not micro) | 2 | 5 | 23 | Fold into arm A later |
| UK architecture/engineering × tender finding + bid drafts | 3 | 3 (bid writers £300-700/day) | 2 (quality bar high) | 5 | 5 (13.3k architects 5y+) | 1 (tenders take months) | 2 | 21 | Park. Pablo's background fits; revisit with proof |
| US janitorial × same offer | 3 | 4 ($130/appointment market) | 3 | 4 (CAN-SPAM) | 2 (no free register with directors or size) | 3 | 3 | 22 | Second market after a UK case study |
| US home services (tree care/HVAC) × new-enquiry conversion (ChatGPT's pick) | 3 | 2 (software does it under $50) | 2 (needs their lead volume, consumer texts = TCPA) | 2 | 3 | 3 | 2 | 17 | Reject: commodity, consumer-side law |
| Gyms × reviews & referrals (JP's beginner offer) | 2 | 2 ($250-500/mo; JP's students saturate it) | 4 | 2 (consumer messages) | 3 | 3 | 2 | 18 | Reject: saves time more than it adds money |
| Generic B2B appointment setting (MSPs, recruiters) | 3 | 4 | 3 | 5 | 5 | 2 | 4 | 26 | Reject for now: crowded, buyers already spammed, no angle |

The generic appointment-setting row scores close. What separates our pick is the **old-proposal way in**. It works from an asset the client already has, nobody sells it, and it gives a result within days instead of months. That's JP's real lesson ("extract value from what they already have before buying traffic"), applied where the law allows it.

## 3. The offer, exactly

**Who:** UK limited companies or LLPs with SIC 81210/81222/81229/81299 (cleaning) or 80200/80100 + fire-protection names (security & fire). Trading 5+ years, accounts not dormant (prefer non-micro), a named director, a website. No sole traders.

**Cold email 1** (plain, one question): who we are, one true fact about the firm, and the ask: *"Roughly how many proposals did you send this year that never got a yes or a no?"* **Follow-up:** the same ask, plus the sentence that explains what we do with them. No price, no claims we can't prove.

**Pilot (30 days):**
- **They send us:** an export of proposals from the last 3-18 months: company, contact, email, site, date, rough value. Proposals to sole traders are removed.
- **We send:** a short, polite chase in their name: two emails over ten days. Every email asks either "still looking?" or "when does your current contract end?".
- **Replies:** warm ones go to the owner the same day, with a walk-through slot offered. Renewal dates go into their calendar.
- **Holdout:** 20% of proposals get nothing, so we can show the difference.
- **Price for the first two pilots:** free. Their proof becomes our case study. After that, a fixed pilot fee (guess: £300) or a fee per booked walk-through (guess: £75-100). Test the two in cold email, not on calls.

**Monthly (guess: £400-600), agreed before the pilot ends:**
- Every new proposal followed up until it's a yes or a no.
- The renewal calendar worked: re-contact 90 days before each competitor contract ends.
- About 300-500 cold emails a month to businesses in their area that fit their size, with booked walk-throughs.
- Sending runs from inboxes on a separate domain the client owns. The client pays for the inboxes (about £5-7 per inbox a month, Workspace pricing: verify).

**Why it's worth it to them:**
- A small office contract is worth about £8-10k a year (VENDOR) over 2-3 years.
- At 15-25% margin (VENDOR), one extra contract is worth about **£2.5-7.5k of gross profit**.
- One extra win every few months pays for the service. That's a guess until a pilot measures it.

**Who does what:**
- **Pablo:** copy, lists, sending, reply handling, the weekly report.
- **The client:** sends the export, takes the walk-throughs, sends the proposals.

## 4. The 30-day test

- **Send:** 8 inboxes × about 20 sends a day (keep to the Google limit; see ledger 35) × 2 touches gives about **1,600 new firms a month**.
- **Split:** first 1,000 firms as **500 cleaning + 500 fire/security**.
- **Starts** around 2 Nov. Both touches are done around 20 Nov.

**Measure:**
- Delivered rate.
- Replies.
- Positive replies.
- The answer to "how many proposals?" (this sizes the pool).
- Calls held.
- Pilots started.

**Gates (judged on Fridays):**

| Date | Pass | Fail → do this |
|---|---|---|
| 20 Nov | Bounces under 3%; at least 5 positive replies from 1,000; at least 3 firms say 20+ open proposals | Check deliverability first. An arm with 1-4 positive replies runs to 3,000 sends before it's judged. An arm with 0 from 1,000 is stopped: change the hook, not the niche |
| 4 Dec | At least 3 calls held, at least 1 pilot export received | Same offer to the next 1,000 (facilities management + larger cleaning firms) |
| 15 Dec | At least 1 pilot showing booked walk-throughs over the holdout | If replies say "we only win by tender or price": test the AEC/tender slice in January |

Building work is limited to what the first pilot needs: a proposal-list importer and a renewal calendar. **Nothing is built before a firm says yes.**

## 5. What could kill it (honest)

- **Small contracts.** At £8-10k a year, a win is worth a few thousand pounds of profit. Our fee has to stay modest, and there's less room for "£1.5k a month" pricing. This pushes us towards bigger cleaning firms and fire/security.
- **Price-driven buying.** Facilities managers may just pick the cheapest quote, so chasing won't change much. The pilot's holdout will show this.
- **No records.** Small firms may not keep proposal lists. The first-email question checks this before we build anything.
- **Zero proof.** We've never booked a meeting for anyone. The first case study is the whole game, which is why the first two pilots are free.
- **Founder drift.** This is the third direction in a week. The research freeze applies again from the day Pablo decides. Only replies change the plan after that.

## 7. Changes after 11 more transcripts (11 Oct evening)

Source: `D:\knowledge_base\wl_reviews\2026-10-11_batch_offers_sales_coldemail.md`. The niche stands, with five adjustments.

1. **Two hooks in the first emails, not one.**
   - **Hook A** asks about old proposals. Nobody sells that, which could mean an opening or could mean there's no demand. In an empty niche, ask why it's empty (Danes).
   - **Hook B** offers booked walk-throughs with local offices. Buyers for that are proven: the US appointment-setting market for cleaning firms is crowded at about $130 per appointment.
   - Each niche gets both hooks: 4 cells of about 250 firms. Whichever hook wins becomes the way in; the other becomes part of the monthly service.
2. **Bigger jobs first.** Danes' rule is that the client should make at least $2,500 profit per deal, up front. A small office cleaning contract makes about £1.2-2.5k a year, so it fails.
   - Cleaning firms are limited to non-micro accounts, and we prefer sites that mention schools, healthcare, multi-site or contract cleaning.
   - Fire & security stays as the second niche: installation jobs plus recurring maintenance.
3. **A trust page before the first send.** One page per niche. It shows Pablo's real name and face, the demo (a sample follow-up sequence and a sample renewal calendar), plain prices for the pilot, and no fake proof. Cold emails link to it only in the signature. It's needed by 30 Oct.
4. **Engine upgrades before the first send** (Nowoslawski):
   - Per-inbox weekly reply rate: an inbox with 100+ sends and under 1% replies is paused.
   - An auto-reply seed test.
   - Word-level spintax, including the signature and the opt-out line.
   - A sudden-drop alert.
   - Partner outreach (trade bodies, cleaning software vendors) from the same inboxes from week 3. It's a "positive" campaign that also keeps the inboxes healthy.
5. **The offer gets an easy first yes.** "Send us 10 proposals that went quiet and we'll write the follow-ups free; you send them or we do." This is a free sample before a pilot (Nowoslawski's free sample, Siu's work up front). Any guarantee gets built from the objections on the first 5 calls (Danes, Mills), not invented now.

**Income check (honest):** at £400-600 a month and 3-5 clients, this is £1.5-3k a month by summer if it works. Getting bigger means one of two things. Either per-walk-through pricing at the bottom of the UK B2B range (£150+ per walk-through, against the £150-600 per appointment UK agencies charge), or a move to bigger-ticket niches once there's a case study. Decide prices after the first 3 calls, not now.

## 6. Still open (for Pablo)

1. Agree the niche and offer, or name what's wrong with it, by Fri 16 Oct.
2. Keep "Velarqo" as the name? (It's generic enough; the website copy needs rewriting either way.)
3. Free first two pilots: yes or no?
