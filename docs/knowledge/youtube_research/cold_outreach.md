# Cold outreach: topic digest (529 videos, 164 channels)

- **Source:** ChatGPT's analysis of `cold_outreach_transcripts.zip` (2026-10-04), about 2.5M words. By its own account it analyzed the corpus with scripts and read the highest-signal videos manually; it did not read every word.
- **Selection bias:** Aaron Shepherd/GrowthFlare (57) and Taylor Haren (48) are about 20% of the corpus, and most creators sell agency services, courses, tools or infrastructure.
- **Verification (Claude, 2026-10-04):** 4 of 5 checks confirmed:
  - Charlie Morgan: "If you can't book appointments with 50 cold emails a day, you're not going to book any with 1,000" [IFLM1LrPNtc]
  - Christian Krause: 25 LinkedIn DMs a day with Sales Navigator [3uw_qwvwAw4]
  - Oliver Rasmussen: 20 emails per inbox per day [GExjqEBXKN4]
  - "This is a cold call, but a well-researched one" opener (30 Minutes to President's Club, enterprise SaaS) [xe0MqfuKAZk]
  - **NOT verified:** Aaron Shepherd's "each follow-up must make sense without email #1" doesn't appear in his transcripts as worded. Likely a paraphrase; the principle is still sound.
- **Second verification (Claude, 2026-10-05), searched the bundle texts in `chatgpt/cold-outreach-leadgen/`:**
  - **Taylor Haren, "Cold email is officially dead"** [0RZ4b2cIw9Q]: confirmed. It announces "Halo" (full-HTML sends through a partner platform he won't name) and claims "as high as 96%" opens and a 55.4 figure. It's a product pitch, and the numbers are his own.
  - **Inbox limits:** "15 to 20 emails per inbox" is the most common figure across many videos (e.g. Aaron Shepherd, Nick Saraev) and "20 to 25" the second most common. Operator folklore, as the digest says.
  - **Aaron Shepherd on subject lines:** confirmed, "I will repeat this until the day I die, but they really don't matter" [XZtkfPDsU88 ~20:10].
  - **Jordan Platten:** only half confirmed. He says to send "a minimum of a thousand emails per day" [aYTX4cfK64U@48:16]. I did not find him recommending 10,000 a day. The 10,000/day pitches are Aaron Shepherd's live experiment [Ayz5ML_DkSY] and Leon Matschke [AMzjqCGgV3k], so drop that attribution.

## The core conclusion
Cold outreach still works. The edge is no longer the script. It's **market × offer × delivery × message × follow-up × sales conversion**, and if any of those is near zero, more volume won't save you. AI makes each part cheaper; it doesn't rescue a weak offer.

## Principles
1. **The offer beats the copy.** Separate the core service from the **front-end cold offer**: a specific outcome + a timeframe + low risk + little effort for the buyer. Generic guarantees ("3x ROI or you don't pay") are commoditized; concrete ones ("3 vetted candidates in 5 days, pay only if you hire") still work.
2. **Targeting:** choose an ICP where the same offer is relevant to almost everyone you contact. Signals only matter if they're **strongly linked to buying intent**; many popular ones are overused trivia. Don't shrink the market just because a tool lets you.
3. **Personalize relevance, not biography.** "You run X but don't seem to have Y; we did Y for [similar company] → Z." Use segmentation at scale and real research only for high-value accounts.
4. **Keep the copy boring:** a short subject, context, one problem or outcome, a concrete offer, optional proof, and a tiny CTA. Subject-line tweaks are overrated.
5. **Small CTAs:** "worth sending over?", "want the 2-min breakdown?" Get a reply, then qualify, then book a call. Send a Loom only *after* someone shows interest.
6. **Follow-ups add value, never just "bumping".** Each one should make it easier to say yes: a short video, "I'll just send you the first 100 prospects", and so on.
7. **Lead → conversation → appointment → show → sale is where the value is** (Charlie Morgan's lead-nurture material). Speed-to-lead, contacting through several channels, reminders and no-show recovery may be a bigger moat than the AI-written messages. This supports Velarqo's full conversion system.
8. **Deliverability really is getting harder.** Google requires SPF/DKIM/DMARC and wants spam complaints under 0.1%. Operators' rule of thumb is about 20–25 emails per inbox per day and 2–3 inboxes per domain on secondary domains. **That's folklore, not law.** Taylor's "Halo" claims are unverified.
9. **Don't copy industrial scale.** Prove the machine at ~50 a day first. Test material changes (offer, segment, pain angle), not "quick question" vs "quick idea". Use 70/20/10 once something works.
10. **Measure deep:** contacted → site visits → reply → qualified → booked → showed → closed → £. Demote open rates; Google says it can't verify them.
11. **Other channels:**
    - **LinkedIn** (connection requests, real DMs, profile as proof, content + DMs as one system) is strong if your prospects actually use it. Small window fitters may not.
    - **Cold calling** works well for trades and local SMBs, but it's hard on you.
    - **Instagram/X DM automation:** low confidence, and not your market.
    - **Commission-only setters** scale a machine that already works; they don't help you find one.
12. **Scraping is nearly free now.** The moat is *which* companies to target and what signal you derive, not the raw list.
13. **AI's real role:** research, enrichment, segmentation, offer variations, first drafts, reply classification, qualification, follow-up and reporting. It lets a tiny team run an SDR operation.
14. **The biggest trap: overengineering before outreach.** Go manual proof → semi-automation → automation → scale.

## UK legal note (verified against the ICO, not from the videos)
Under PECR, **corporate subscribers** (Ltd companies, LLPs) can receive unsolicited B2B email. **Sole traders and some partnerships count as individuals** and need consent or a soft opt-in. UK GDPR still applies, so always identify yourself and include an opt-out. **The lead database needs a legal-entity-type field.**

## Strongest sources to revisit
- **Aaron Shepherd/GrowthFlare:** the best practical library (offers, lists, follow-ups, copy, infrastructure).
- **Taylor Haren:** experimentation and attribution; see `taylor_haren.md`.
- **Charlie Morgan:** systems thinking, lead follow-up, prove before you scale.
- **Leon Matschke:** realistic infrastructure math.
- **Christian Krause:** LinkedIn.
- **Nick Saraev:** scraping and automation tooling.

**Ignore** thumbnail claims: "cold email is dead/easy", "10k a day minimum", exact templates, "unlimited leads", open-rate brags.

## Applied to Velarqo
- **Start small:** UK **Ltd** window/door installers → owner/director → a specific database-reactivation outcome → a performance-based pilot.
- **Channels:** cold email as the main controllable one, LinkedIn where the owner is active, a strong website and proof page, and the phone only after a prospect shows interest.
- **Front-end offer, for example:** "Give us a segment of your dormant enquiries. We'll turn them into qualified opportunities. You only pay for agreed outcomes."
- **Milestones, in order:** a positive reply → database access → leads reactivated → a qualified opportunity → real revenue for them → a happy, paying client. Industrialize only after that repeats.
- **Cold email is how you get clients; the business is the system** that turns the demand they already have into attributable revenue.
- **The next information you need is empirical:** what happens when UK installers actually receive the offer.
