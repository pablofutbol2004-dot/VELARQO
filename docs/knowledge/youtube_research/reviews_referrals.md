# Reviews & referrals: topic digest (90 videos)

- **Source:** ChatGPT's analysis of `velarqo_research/6_reviews_referrals.zip` (2026-10-04), ~647k words.
- **Bias:** 59 of 90 videos are Clay Lawrence selling Google-review automation through GHL. Andy Walker supplies most of the referral material.
- **Verification (Claude, 2026-10-04):** 7 of 7 confirmed.
  - **Andy Walker:** "I've discovered Google's number one hidden ranking factor, review velocity". Top businesses got "two to three new reviews every single week… never went more than 14 days without a new review" [75IJnTcWWr4]. **That's his own analysis, not Google's. Don't repeat it as fact.**
  - **Andy Walker on double-sided referral incentives:** both the referrer and the friend get something [5JA3cpR1ODQ, FlM8RAvq8k4].
  - **Clay review gating, confirmed ⚠:** "since negative reviews are a concern, we can set up a review filter page where instead of taking them directly to Google…" [ShHNwYXfWSk]. A tool demo sends 3-star clicks to "an internal page to leave feedback" [SDioyXyRXtk].
  - **Clay's guarantee:** "I guarantee I'll get you ranked on the first page of Google in 30 days… money back guarantee" [-_ag8qO4Ah0, YKyxLTTIy4Q].
  - **Christian Krause B2B stats:** 92% trust referrals, 84% start evaluation with a referral, 73% respond to referred reps [B-joObtg6cA]. These are B2B and unsourced, so don't port them to homeowners.
  - **Darren Shaw (Whitespark)** on Edward Sturm's podcast: the 2026 local-search ranking factors list [1awWMG1e5kY]. Many factors, with reviews one meaningful signal among them.
  - External (from ChatGPT, consistent with what I know):
    - Google's review policy forbids **discouraging negative reviews, selectively asking only happy customers, and incentives** (discounts, payment, freebies) for reviews.
    - Since **6 April 2025** the UK DMCC Act bans fake and concealed-incentive reviews, and the CMA can enforce directly.
    - Google says local rank = relevance, distance and prominence, with review count and rating contributing.

## Core finding
**Reviews and referrals are Velarqo's post-sale compounding layer, not the core offer.**
- **Review = a trust and conversion asset.** Commoditized: CRM event → SMS → link. GHL, Whitespark and dozens of SaaS tools do it, so there's no moat.
- **Referral = a new acquisition channel.** Bigger upside for W&D: the result is visible from the street, estates are full of similar-age houses, recommendation trust matters for a high-ticket job done at someone's home, and the referred homeowner is already in the service area. **A completed install becomes an acquisition node.**
- W&D's low repeat-purchase rate (from `home_services.md`) is partly offset: **customer value = future purchases + referrals + reputation + proof.**

## Hard compliance rules (reject part of the YouTube playbook)
1. **No review gating.** Never do "were you happy? 4–5★ → Google, 1–3 → private form". Every eligible customer gets the same neutral review request.
2. **No incentives for reviews,** ever (no "£25 / 10% off for a review").
3. **No mass review blasts** to thousands of old customers. Sudden spikes can look like manipulation, get reviews removed, and annoy people.
4. **Optimize for more genuine reviews, not for 5 stars.** Negative reviews are operational signal ("salesman vanished after deposit").
5. **Never promise rankings** ("page one in 30 days"). Distance, competition and the algorithm aren't ours to control.
6. **Don't tell customers what to write.** Analyse themes in natural reviews afterwards instead.

## Architecture: three independent workflows
- **Review:** `JOB_COMPLETE` (or `SNAGS_RESOLVED`, test which) → neutral request to all eligible customers → optional neutral reminder → stop.
- **Service recovery:** a separate satisfaction and snag check → unhappy customers get the problem fixed. **This must never decide who gets the review request.**
- **Referral:** after a clear positive moment, "know anyone who might benefit?" Using satisfaction to time the referral ask is fine. Track `referrer_id`, `referred_lead_id`, reward status, booked, sold, revenue and GP, then compare referral CAC and conversion against Google, Meta and reactivation.

**Referral economics:** use a double-sided reward (referrer gets something when a qualifying install completes, friend gets something too), **priced from GP and CAC**. Avoid % discounts on £15k jobs. Prefer fixed values or **upgrades with high perceived value and low marginal cost**. Keep referral rewards completely separate from reviews.

**ICP filter:** don't switch post-sale automation on for installers with bad workmanship or unresolved snags. It just speeds up negative feedback.

## Where it fits
- **The lifecycle becomes a closed loop:** acquire → respond → convert → preserve (show rate) → close (quote follow-up) → recover (dormant) → fulfil → **compound** (review → referral → proof) → new lead.
- **Rollout:** reactivation → fresh-lead and quote recovery → appointments/show rate → review automation (almost free once `JOB_COMPLETE` arrives, and sticky) → referral engine (needs economics and tracking) → case-study and proof capture (photos plus a genuine review, with consent).
- **Pitch it as an outcome:** "make every sale create the next one", not "AI review replies".
- **Velarqo's own growth:** ask happy installers to refer other installers ("know another firm sitting on dead quotes?"). One great first case study gives you proof, data, a testimonial and referrals.
- **Long-term data moat:** referral intelligence. Which projects and areas spawn new jobs (e.g. whole-house installs creating clusters of neighbour enquiries within 90 days), plus AI analysis of real review themes. No unsolicited neighbourhood spam.
- **Don't build any of it before the first pilot.**

## Ratings
| Item | Score |
|---|---|
| Reviews + referrals + proof as a post-sale module | 9 |
| Reviews as a recurring feature | 9 |
| Geographic/customer referral intelligence (long-term) | 9 |
| Referral automation for W&D | 8.5 |
| Reviews as the core offer / reputation agency | 4 |
| Review gating | 0 (policy violation) |
| Incentivised Google reviews | 0 (policy + UK law) |
