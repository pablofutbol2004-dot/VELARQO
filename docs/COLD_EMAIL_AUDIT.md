# Cold email audit (pre-launch, 2026-10-04)

Scope: copy in `config/experiments/cold_offer_v1.json`, `cold_angle_v1.json`, `pricing_p1.json`, follow-ups in `outreach/send_engine/compose.py` (`outreach/sequences/` holds only an empty `__init__.py`; the sequence lives in `compose.py` + `guards.FOLLOW_UP_GAPS = {2: 3, 3: 5}` business days). Nothing was changed; everything below is a proposal for Pablo to approve.

Short version: the copy is already in good shape (all emails 40-68 words including signature and opt-out, plain, no links, no claims). The real problems are **(1) the test plan can't finish in 4-6 weeks, (2) follow-up 2 contradicts arm B's offer, (3) arm B's first-email ask is bigger than it looks, (4) the angle test is confounded and contains one unbacked claim.**

---

## (a) Rulebook: how to do cold email properly (from our own research)

Source key: **CO** = `docs/knowledge/youtube_research/cold_outreach.md`, **TH** = `youtube_research/taylor_haren.md`, **HS** = `youtube_research/home_services.md`, **OP** = `youtube_research/offers_pricing.md`, **CG** = `youtube_research/corey_ganim.md`, **SK** = `.claude/skills/velarqo-outreach/SKILL.md`, **P03** = `pass_03_velarqo_execution/outbound/cold_email_experiment_v0.md`, **P12** = `pass_12.../prospecting/outreach_experiment_rules.md`, **P13M** / **P13F** = `pass_13_first_10_installers/outreach/experiment_matrix.md` / `followups_and_reply_router.md`, **P14** = `pass_14_acquisition_factory/playbooks/`, **TP** = `docs/TESTING_PLAN.md`, **SP** = `docs/SALES_PLAYBOOK.md`, **PR** = `docs/PRICING.md`, **AP-E** / **AP-O** / **AP-C** / **AP-H** / **AP-F** / **AP-Q** = `docs/knowledge/ad_pack/ad/` `formats/email/essentials.yaml`, `growth/outbound_acquisition/essentials.yaml`, `craft/copywriting/essentials.yaml`, `craft/hooks/essentials.yaml`, `business_mechanics/offer_framing/essentials.yaml`, `business_mechanics/qualification/essentials.yaml`.

**Offer and targeting**
1. The offer beats the copy. Front-end offer = specific outcome + low risk + little effort for the buyer. (CO #1, TH "offer matters more than copy")
2. Diagnose in order: deliverability -> offer -> positioning/copy -> targeting -> small tweaks. Don't rewrite copy to fix a list or inbox problem. (TH, P12)
3. Pick an ICP where the same offer fits nearly everyone emailed; UK Ltd/LLP only (PECR). (CO #2, SK legal 2)
4. Position as recovering sales from leads they already paid for, never "AI"/agency. (HS, OP)
5. One transformation on the front end, no feature soup. (OP)

**Copy**
6. Keep it boring: short subject, one problem, one concrete offer, one tiny ask. Subject tweaks are overrated. (CO #4)
7. Under ~90 words (SK); founder target under 80. Plain text, no links or attachments in touch 1. (SK)
8. One soft ask that can be answered in one line; get a reply first, qualify, then call. No calendar link in email 1. (CO #5, P03)
9. Tradesperson words (quotes, surveys, diary, fitters); banned: leverage, solutions, pipeline, funnel, campaigns. (SK, `compose.py` docstring)
10. Personalise relevance, not biography; never fake personalisation. Drop a sentence if the data isn't real. (CO #3, TH, SK)
11. No claims we can't back: no results, clients, percentages, "we've helped". Evidence on hand = none. (SK, `PRODUCT.md`)
12. No price in writing. (PR, SP) - see disagreement D3.
13. Every email: who we are + working opt-out; honour suppression forever. (SK legal 2-4)

**Follow-ups**
14. Every follow-up gives a new reason to reply and makes yes easier; never "bumping". (CO #6, `compose.py`)
15. A good follow-up ask: a rough-size question ("tens, hundreds or thousands?") - a one-word reply. (P03, P13F)
16. Follow-ups must match the offer the prospect actually got in email 1. (derived from CO #6 + one-variable rule 19)
17. Track replies and opt-outs per step to see whether steps 2-3 earn their keep. (TP)

**Testing and measurement**
18. Test big swings (offer, angle, segment), not wording; at our volume only large differences are detectable. (TP, CO #9, TH)
19. Change one variable per test; keep audience and infrastructure stable. (P03, P12, TP)
20. Judge on the deepest outcome: positive reply -> call -> sample -> pilot. Ignore opens. An arm with replies but no calls loses. (TH, CO #10, P03, TP)
21. No outside benchmark is an expectation until our own sends set a baseline. (P12)
22. Prove at ~50/day before scaling; don't overengineer. (CO #9, #14, TH)

**Deliverability and safety**
23. ~20-25 emails per inbox per day max (folklore, not law); SPF/DKIM/DMARC; complaints <0.1%. (CO #8)
24. Stop rules: any complaint pauses; bounce >3% investigate, >5% pause; opt-out >2% on an arm stops it. (TP, P03)

**From the ad pack (founder's agency/scraper-style check)**
26. Each email must work on its own if the earlier one wasn't read; follow-ups advance a new question, not the same argument reworded. (AP-E body_and_readability, AP-O sequencing)
27. Personalise around decision-relevant context, never trivia that only proves a scraper found them; truthful identity and reason for contact, no manufactured familiarity or urgency. (AP-O message_and_relevance, compliance)
28. Risk reversal must answer a specific fear and name an observable, verifiable success criterion ("pay only when a survey is booked", not "unless it works"). (AP-F risk reversal, success criteria)
29. First ask proportional to trust: a reply or permission step, not a meeting or data hand-over. (AP-O message_and_relevance)
30. Use the reply to qualify on the conditions that decide success (volume of old quotes, where they're stored, who decides). (AP-Q)
31. Stop the sequence on any reply, opt-out or ineligibility. (AP-O sequencing)
32. Short active sentences, domain-native words, delete throat-clearing; no unsupported numbers. (AP-C, AP-H)

**Replies**
25. Answer same day, short, plain; GDPR/source questions answered personally, never templated; opt-outs suppressed without argument. (SP, P13F)

### Where sources disagree
- **D1 Length of sequence.** TH sends usually 1 email (but admits a client's 5th follow-up was their best); P03 uses 4 touches (+3/+5/+7 days); P13F uses 3 follow-ups; we send 3 (gaps 3, 5). Keep 3: it's cheap, and TP measures per step.
- **D2 Word limit.** SK says ~90; founder says 80. All current copy already passes 80.
- **D3 Price in replies.** P13F says answer "how much?" with £0 setup + £75 per booked survey; PR/SP say never in writing and test £60/£110/£175 on calls. Follow PR (it's newer and is the decision record).
- **D4 Sample size.** TH says ~1,000 per variant; TP uses 300 and admits only big gaps show. TH also warns his number isn't universal. With 1,918 contacts, 300 is the only option, so test big swings only.
- **D5 Test shape.** P12 proposes a 2x2 (opener x CTA); P03 four cells; TP one variable at a time. At our volume one variable wins.
- **D6 Voice.** P13M/P03 use "I'm testing a founder pilot", "commercial model tied to valid booked surveys", "quick question" subject. SK/`compose.py` ban this agency tone. Current copy correctly follows SK.
- **D7 Personalisation.** P03 proposes testing a `{town}` line vs control; nothing else in our plan does. Low priority at our volume.
- **D9 Length.** AP-E says choose length per job and test it, not "short is always better"; SK/founder fix a cap (90/80). Keep the cap for cold first touches; length isn't worth a test at our volume.
- **D10 Sequence depth.** AP-E/AP-O say set sequence length from the number of distinct jobs and test spacing; our gaps (3, 5 days) are fixed. Fine: we have exactly two distinct follow-up jobs (explain + close).
- **D8 Channel ranking.** CG ranks cold email B-tier, but CG admits little cold email experience; CO/TH treat it as the main controllable channel. Not a blocker.

---

## (b) Findings, ranked by impact

| # | Change X | To Y | Because |
|---|---|---|---|
| 1 | **Three experiments planned for launch window** (offer 600 emails, angle 600, pricing 24 calls) | **Run only `cold_offer_v1` in weeks 1-6.** Start `cold_angle_v1` only if the offer test is decided with list to spare. Treat `pricing_p1` as directional and cut to 2 arms (see (d)). | Rules 18, 20, 22. At 25-50 first-touches/day, 600 first emails = 12-24 sending days (3-5 weeks) plus 8 business days for follow-ups to land. The angle test can't also finish inside 6 weeks. |
| 2 | **Follow-up 2 is shared by every arm and describes chasing** ("Anyone who says yes gets a survey booked into your diary") | **Arm-specific follow-up 2** (see (c)): arm B's explains the free look; both end with "tens, hundreds?" | Rules 16, 14, 15, 19. A prospect who got the free-audit offer then hears a different offer in email 2: the arms stop being clean, and B's result is muddied. |
| 3 | **Arm B asks for the list in email 1** ("send me a list of them (names blanked out is fine)") | **Offer the free look without asking for data**: "I'll look over your old quotes for free and tell you honestly whether any are worth chasing." Data questions come after a reply. | Rules 8, 29, 1. Sending customer lists to a stranger is a big, GDPR-scary ask; "names blanked" raises the issue it tries to calm. Rule 25: data is handled personally later. |
| 4 | **`cold_angle_v1` arms differ in subject, opener, CTA and offer line** ("quotes that went quiet" vs "old quotes"; "how it works?" vs "Worth a look for {company}?") | **Same subject, same offer line, same CTA; only the opening sentence differs.** | Rule 19. Otherwise a win can't be attributed to the angle. |
| 5 | **Angle B claims "Most of those homeowners never actually said no."** | **Cut it.** | Rule 11. We have no data for "most". |
| 6 | **"Nothing to pay unless it works"** (offer A, angle B) | **"Nothing to pay unless surveys get booked."** | Rules 1, 28 (concrete, verifiable risk reversal) and matches SP's wording, so the reply and the email say the same thing. |
| 7 | **Follow-up 2 asks "Want a bit more detail?"** | **"Roughly how many old quotes are we talking: tens, hundreds?"** | Rules 15, 30: a one-word answer that also qualifies the lead (useful for the call). |
| 8 | **`cold_angle_v1` is written with arm A's offer line baked into both arms** | **Placeholder for the winning offer line** until `cold_offer_v1` is decided. | The JSON already says "swap it in"; if B wins, both arms must change. Avoids launching the stale version by accident. |
| 9 | **Subject lines vary between arms** | **Keep "quotes that went quiet" for every arm** (lowercase, 4 words, no "quick question"). | Rules 6, 19. Subject isn't what we test. |
| 10 | **No per-step readout yet confirmed** | Make sure `results` splits replies/opt-outs by step 1/2/3. | Rule 17 (free test in TP). |

Checked and fine: word counts (below); one ask per email; no links; opt-out line and sender identity enforced by `compose.problems()`; "Re:" subject on follow-ups is a real thread reply (`in_reply_to_message_id`), not a fake; volume 25-50/day over 4 mailboxes = 6-13 per inbox (rule 23); no prices in copy (rule 12); no banned words. Ad-pack agency/scraper check (rules 26-27, 32): passes - no fake personalisation, no hype, no "campaign/solution" words; `{company}` is the only merge field. Engine stops follow-ups on reply/opt-out (rule 31) - confirm in a dry run.

### Current word counts (body / with signature + opt-out, +10)

| Email | Body | Sent total |
|---|---|---|
| cold_offer_v1 A_chase_no_win_no_fee | 52 | 62 |
| cold_offer_v1 B_free_quote_audit | 56 | 66 |
| cold_angle_v1 A_question | 52 | 62 |
| cold_angle_v1 B_money_already_spent | 58 | 68 |
| Follow-up 2 (all arms) | 54 | 64 |
| Follow-up 3 (all arms) | 30 | 40 |

All under 80. Length is not a problem.

---

## (c) Proposed emails (all under 80 words including signature + opt-out)

Signature and opt-out are appended by `compose._finish()` as now: `Pablo / Velarqo, velarqo.com / Reply "no" and I won't email again.` (+10 words). Subject for every arm: **quotes that went quiet**; follow-ups thread as `Re: quotes that went quiet`.

### cold_offer_v1 (run first)

**A - chase, pay on results** (body 51, sent 61)
```
Hi,

How many quotes has {company} sent in the last year where the homeowner just went quiet?

I chase those people up for you, in your company's name, and book anyone still interested back in for a survey. Nothing to pay unless surveys get booked.

Worth me explaining how it works?
```

**B - free look at old quotes** (body 49, sent 59)
```
Hi,

How many quotes has {company} sent in the last year where the homeowner just went quiet?

I'll look over your old quotes for free and tell you honestly whether any are worth chasing. No cost, no commitment.

Want me to take a look?
```

**Follow-up 2 for arm A** (+3 business days; body 55, sent 65)
```
Hi,

To put it simply: I'd message homeowners you quoted in the last year or two, in your company's name, and ask if they're still thinking about it. Anyone who says yes gets a survey in your diary. Anyone who says no is left alone.

Roughly how many old quotes are we talking: tens, hundreds?
```

**Follow-up 2 for arm B** (+3 business days; body 51, sent 61)
```
Hi,

To be clear what the free look is: you tell me roughly how many old quotes you've got and where they sit (spreadsheet, quoting system, inbox). I tell you whether they're worth chasing. You don't send any customer details at this stage.

Roughly how many are we talking: tens, hundreds?
```

**Follow-up 3, both arms** (+5 business days; body 31, sent 41)
```
Hi,

Last one from me. If old quotes aren't something you want to look at right now, fair enough.

If that changes, just reply to this and I'll pick it up.
```

### cold_angle_v1 (only after cold_offer_v1 is decided)

Same subject, same offer line, same CTA; only the opener changes. `[OFFER]` = the winning first-email offer sentence(s) from above (A: 28 words; B: 20 words). Counts below assume offer A, the longer one. Follow-ups = the winning arm's follow-ups 2 and 3 unchanged.

**A - question opener** (body ~56, sent ~66)
```
Hi,

How many quotes has {company} sent in the last year where the homeowner just went quiet?

[OFFER]

Worth me explaining how it works?
```
(If B wins, use B's CTA "Want me to take a look?" in both arms.)

**B - money already spent** (body ~57, sent ~67)
```
Hi,

Every quote that goes quiet has already cost {company} a survey visit and an evening of paperwork.

[OFFER]

Worth me explaining how it works?
```

---

## (d) Recommended experiment plan

**The maths.** 1,918 contacts. At 25-50 first-touches/day (weekdays), 600 first emails take 12-24 sending days. At an unknown ~2% positive reply rate, that is ~6 positives per arm; the 90%-probability rule only fires on roughly 2-3x gaps (e.g. 1.5% vs 4%). Free look vs pay-on-results is a big enough swing to have a chance; question vs "money spent" opener probably isn't.

**Weeks 0-1 (before 25 Oct):** seed-inbox placement test, confirm per-step readout exists, apply the edits in (c) to `cold_offer_v1` and follow-ups (need code change: follow-up 2 per arm). Founder approves.

**Weeks 1-5: `cold_offer_v1` only.** 300 first emails per arm, ramp 25/day -> 50/day as bounces/complaints stay clean. Read weekly; decide at 300/arm + 8 business days for follow-ups. Primary: positive replies; tie-breaker: calls booked and samples sent (rule 20).

**Weeks 5-6+: the remaining ~1,300 contacts.** If the offer test is decided, send ~70% of the remainder with the winner and use the rest for `cold_angle_v1` (it will not finish inside 6 weeks; expect a readout around weeks 8-9). If undecided, keep the arm with more calls and move on, as the JSON already says. Grow the list (named contacts, tier-C firms, kitchens ICP) before planning a third test (TP).

**`pricing_p1`: run, but expect only a direction.** Realistic call volume from 600-1,200 emails is perhaps 5-20 calls in 6 weeks, so 3 arms x 8 calls (24) won't be reached. Recommend **2 arms (e.g. £75 vs £150)** so each gets ~half the calls, keep the three pre-price questions on every call, and call it a direction, not a result. (This is a config change; not made.)

**Do not test now:** subject lines, CTA wording (`cold_cta_v1`), `{town}` personalisation, send times. Too small to read at our volume (rules 18, 21).

### Open items (not copy)
- LSSI art. 21 remains an accepted risk, not cleared (SK legal 1).
- PECR: Ltd/LLP-only filter must hold for every row in the cohort (enforced in code per SK).
