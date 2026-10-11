# Cold email course (7h, 2025) - what could change what we do

Source: "Free Cold Email Marketing Course for 2026 (7 Hours)", YouTube transcript. Speaker: Jay Feldman ("LeadGenJay", [1:14]), US agency owner, B2B US focus. Timestamps are h:mm. Paraphrased. Compared against COLD_EMAIL_AUDIT.md section (a) (rules 1-32, D1-D10) and COLD_EMAIL_V2.md.

**Trust level.** Says "not sponsored" ([0:09]) yet pushes affiliate links and discounts for Instantly, Mailin, Apollo, Trusted Leads, Find Email, Wormy, etc. ([0:17], [1:03], [2:56]), his $3/mailbox setup service ([0:59]), paid "Insiders" program and free community. All advanced material ends in "join Insiders". US-centric (CAN-SPAM), nothing UK. Numbers below are his own, unaudited.

## 1. Infrastructure and deliverability

| Claim | Verdict |
|---|---|
| Use Google Workspace mailboxes; Google gives best inbox placement [0:30-0:39, 1:03]. Quoted 87.2% Google vs 75.6% Microsoft [1:03-1:06] (unverified source). Keep 3 providers eventually [1:13]. | Agrees (we are Workspace). Hedge idea is new but premature at 8 inboxes. |
| Never send cold from the primary domain; secondary domains forward to main site [0:35, 0:46]. | Agrees (velarqohq/getvelarqo). |
| ~5 mailboxes per domain, ~100 emails/domain/day, so 20-25 per inbox; 50 is the ceiling, safer lower; scale by adding mailboxes [1:16, 5:49, 5:54]. | Agrees with rule 23 (~25/inbox). He admits it is a guess. |
| Domain age at least 30 days, ideally 60-90, before cold sending; warm mailboxes from day one [0:38, 2:00, 5:15]. | New to our rules. Check our domain ages before first send (~25 Oct). |
| Start at a daily cap, slow ramp (+1-2/day), max 20/day at launch, warm-up on permanently at same volume as cold limit [1:34, 2:05, 5:15]. | New/partly agrees. Warm-up "always on" matches our Instantly warm-up. |
| Set SPF, DKIM, DMARC; scan with a free checker; use the sender's "test domain setup" before activating [0:55, 1:37]. | Agrees (rule 23). |
| No open/click tracking, no links, text only; custom tracking domain only if links used [0:46, 1:40, 4:42]. | Agrees (rule 7). |
| Do not forward replies to another mailbox; reply from the sending inbox, in thread, so the conversation stays warm [1:16-1:18, 4:45]. | New. Verify our reply flow answers from the same inbox. |
| Daily real inbox-placement tests (seed inboxes); auto-pause an inbox under 50-80% placement for 30 days of warm-up only, resume slowly above 70% [1:47, 2:19, 2:31]. Health score is unreliable. | New. We only have bounce/complaint rules (24); no placement test. |
| Google Postmaster Tools on sending domains for spam-rate and reputation [2:36]. Complaints damage more than anything. | New; free; Google-only. |
| Blacklisted domain or reputation drop: stop cold, warm-only 2-4 weeks, recovery 4-8 weeks, replace after 60 days [2:10, 2:29, 2:38]. | New, fits rule 24 (pause) and gives a duration. |
| Cheap unmanaged-IP SMTP providers risky [1:06-1:12]. | Not applicable (Workspace). |
| Spintax is "mandatory" to avoid repeated-phrase filters [4:23]. | New. Contradicts nothing, but our arms are fixed text. Unverified claim. |

## 2. List building and targeting

- Verify every email; exports labelled "verified" still come out 70-80% valid, "about half" of risky/catch-all addresses are deliverable; send to good only, check catch-alls separately [3:38, 3:40]. Lists older than 3-6 months decay [2:15]. **New/partly agrees** with our 3%/5% bounce rules; adds re-verify before send and catch-all handling.
- Bounces also come from content blocks, not only bad addresses [2:14, 3:33]. Auto-pause campaigns on high bounce [1:51]. Agrees (rule 24).
- Blue-ocean logic: industries that get few cold emails reply more; decision-makers beat mid-level staff; young and small companies reply more; big companies reply less [2:44-2:50]. **Agrees** with our UK Ltd installer/roofer focus; trades are explicitly the "not on LinkedIn" case ([2:52], use Google Maps scrapers [3:17-3:20]).
- AI yes/no qualification of each lead (website/description) removes 30-50% of poor fits and "2-3x" reply rates [3:44-3:47]. Number unverified, but the mechanism is **new** for us.
- Check the list by reading actual companies, exclude keywords [3:27]. Agrees.
- Signal-based lists (job posts, funding, social, new roles) give 5-20% reply but are limited and complex; build only after a control works [3:14, 6:25]. Mostly not relevant to installers. One transferable idea: an event reason to email (e.g. recent hire ad, new van wrap) - speculative.
- Recycle non-repliers after at least 3 months with a different angle; skip those who replied either way [5:42-5:45]. Agrees with our 90-day rule; **new**: change the pain point on recycle.
- Block-list sheet for customers/competitors [1:52]. Agrees.
- Small TAM warning: if the list is small, never burn it on one weak message; use extended sequences only then [4:31]. Our 5,700 is small; supports one clean offer test first (audit finding 1).

## 3. Copy

- "Triple tap": (1) subject plus first line must earn the open, (2) body states the problem and mechanism plus a little credibility, (3) CTA is a one-word reply [4:08-4:17]. **Agrees** with rules 6, 8.
- Preview = subject + first sentence; do not signal a sale; curiosity questions get opens, but do not bait-and-switch [4:11-4:14]. **Agrees**; V2's question opener fits.
- Max ~6 sentences, 6th-grade language, match tone to ICP (blunt sales language for older male trade owners) [4:17-4:19]. Agrees (rules 7, 9, 32).
- Do not overpromise; give the mechanism for any claim; no bait-and-switch [4:20]. Agrees (rule 11). Credibility without case studies: own media, social following, free service to earn an anchor case [4:19]. Agrees with V2 case-study playbook.
- Personalisation: always use first name; avoid company name (Ltd/LLC/caps break the illusion) and location; AI personalisation hurts 95% of users [4:21, 4:22]. **Mixed**: our only merge field is {company}, greeting has no name. New risk: audit {company} normalisation (strip Ltd/Limited, fix caps); consider first name from director data.
- **Contradicts rule 13 / our legal base:** drop unsubscribe links and opt-out text in email 1 because it hurts deliverability; add "wrong tree, just say so" from email 2 [4:41-4:42]; his evidence is that no one he knows was fined under CAN-SPAM [4:46-4:47]. That is US law; UK PECR/ICO and our written LIA require identity and a working opt-out. **Do not adopt.** Useful only as wording: avoid the word "unsubscribe" (we already use "Reply no").
- "Reverse lead magnet": instead of "want the PDF?", offer to personally research/prepare something for them; perceived value rises with perceived effort [4:03-4:05]. Claims 2-3% replies on his hardest offer. **Agrees** with arm B (free look); supports wording like "I'll go through X for you".
- Ask permission before sending a video/asset as email-1 CTA [4:44]. New option.
- Trojan horse / loss leader framing [3:54-3:56] (e.g. pose as a journalist). Conflicts with rule 11/27 honesty; do not use.

## 4. Follow-up sequence

- Three emails max (stop there; spam risk grows) [4:26]; spacing 2-5 days [4:30]. **Agrees** with D1 (3 touches, gaps 3 and 5 business days).
- Email 1 usually performs best. Email 2 is a plain same-thread nudge; email 3 may "dump" extra info/links, same or new thread [4:30-4:31]. Email 2 as a bump **contradicts** rule 14 (never bump). Email 3 link idea is new: once in the inbox links are lower risk, use only well-known domains and no tracking [4:43].
- Split-test thread vs new thread on email 3 [4:39]. New, cheap.
- Extended 4-7 emails only for small TAM or when each email adds new value [4:31]. Agrees with D1 for now.
- Subject shared with email 1 so it stays threaded [4:52]. Agrees.

## 5. Replies and booking

- Reply in 5-10 minutes, speed over personalisation; "within 30 min = 60% higher conversion" [5:17-5:18, 6:41] (unverified). Agrees with rule 25; makes the target explicit.
- Answer the specific question first (e.g. price range), then one clear next step; never info-dump; give a booking step [5:27-5:29]. Price answer **contradicts** rule 12/D3 (no price in writing); keep ours.
- Reply to "soft no" politely once and leave the door open; AI tags are wrong sometimes, so read "not interested" threads daily [5:24-5:26]. New, cheap.
- Set a reminder to follow up one week after your reply to an interested lead; claims +50% booked [5:29]. New; unverified number.
- Check the "other"/unattached replies: people reply from different addresses or months later [5:21]. New; check our engine matches replies from other senders.
- Do not move a replier into the main CRM until they book/opt in [5:35]. Agrees.
- Automation of replies only above ~10 replies/day [6:52]. Agrees (not needed).
- Skip hostile prospects, block-list instantly [5:36]. Agrees (rule 25).
- SMS and AI cold calling: do not [7:02]. Agrees (no cold calling). Voicemail drops, direct mail, retargeting ads: not applicable.

## 6. Testing and metrics

- Judge on positive reply / opportunity rate, not reply rate or opens [1:42, 5:10]. **Agrees** with rule 20.
- Campaigns split audiences; variations split offer/copy; test offers first because big swings show, change one chunk (subject, body, CTA) at a time, keep a control [4:34-4:37, 5:10]. **Agrees** with rules 18-19, D5.
- Benchmarks (US B2B, his history, not ours): 1-2% reply and ~1% opportunity = scalable; under 1% reply / 0.5% opportunity = weak; over 5% = flag; ignore "Instantly porn" (signal or hyper-targeted lists) [4:57-5:01]. **Conflicts mildly** with rule 21 (no outside benchmark); treat as hypotheses only.
- Significance is just "enough data, big gap"; pasting the table into an LLM is his method [5:11]. Equivalent to D4.
- Scaling maths: find J, emails per booked call, then required mailboxes = target emails / 25 [5:48-5:51]. New; compute our J after 200-300 sends.
- Code red signs: reply rate falls sharply, placement drops: pause, warm, change copy first [5:46]. Agrees.

## 7. Offers and local/trades

- Offer beats everything: boring or competitive offers need a foot-in-the-door front-end offer that is specific, low-effort and low-risk [3:49-3:53]. Agrees (rule 1).
- Offer killers: boring, same as everyone, absurd guarantees with no mechanism, complex [3:50-3:52]. Agrees; our "pay per booked survey" has a mechanism.
- Cold email works for high-ticket B2C only if there is a way to target the right person (he cites roofing and solar) [3:29]; our B2B Ltd route avoids that. Neutral.
- One anecdote: a commercial window-replacement client got "a ton of replies" from a problem picture in email 2 [4:44] (unverified). Weak support for showing the homeowner text in email 1 (V2).
- No pricing guidance for trades; nothing on selling to installers specifically.

## Ranked changes worth adopting

1. **Before first send: daily real inbox-placement test plus Google Postmaster**, with a rule: placement under ~70-80% (or any blacklist) pauses that inbox for warm-only, resume gradually. Fills the gap in rule 24.
2. **Check domain age and ramp**: domains at least 30 days old (60 ideal), start at 10-20/inbox/day, +1-2/day, warm-up never off.
3. **Re-verify addresses just before each batch**, handle catch-all/unknown separately, keep auto-pause on bounce.
4. **Audit {company} merge**: strip Ltd/Limited, fix ALL CAPS; consider first name only if director data is reliable.
5. **Reply handling checklist**: reply from the same inbox and thread, 5-10 minute target, answer the question first with one next step, courtesy reply to soft nos, 7-day nudge, match replies from other addresses.
6. **Use positive replies per 100 sends as the one metric**, keep a control, and treat his benchmarks as hypotheses until our baseline exists.
7. **Light spintax** on greeting and sign-off only (identical offer text per arm), previewed so every variant reads naturally.
8. **Test thread vs new thread, and one link, in follow-up 3** (after the offer test decides), well-known domain only.
9. **Quick yes/no fit screen** on the list (is it an installer or roofer doing domestic work) before the batch to cut poor fits.
10. **Recycle non-repliers after at least 3 months with a different angle**; keep the 90-day rule as the floor.

Not adopting: no opt-out in email 1, any "pretext" framing, pricing in writing, signals/Clay stack, bump-only email 2.
