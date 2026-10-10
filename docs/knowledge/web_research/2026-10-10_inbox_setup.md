# 16-inbox setup: verified practice (web research, 2026-10-10)

Tags: P primary (Google/Instantly docs), S secondary, V vendor folklore.

## Limits and risks
- Paid Workspace: 2,000 msgs/user/day, 3,000 unique recipients (2,000 external); trial: 500/day, no rise until the domain has paid $100 cumulatively (up to 75 days) (P: knowledge.workspace.google.com gmail-sending-limits).
- Gmail API: messages.send = 100 quota units, ~60 sends/min/user; no separate daily cap (P: developers.google.com gmail quota).
- No Google statement on lower limits for new accounts, bulk-created users, or secondary domains vs separate tenants: all V. One tenant for 8 domains is normal; the risk is one suspension hitting all. Later, put a few domains in a second tenant.
- Google's Acceptable Use Policy bans using Workspace for unsolicited bulk commercial email (P, archived versions seen; check live text). Suspensions in late 2025 mostly hit cheap/free/.edu volume senders (V, Salesforge).
- If a trial ends without a valid payment method, Google suspends all users (S).

## Domains and DNS
- .com vs .co.uk: either; reputation and auth matter more (S, Suped 2026-08). Lookalikes (try/get/use + brand) are Instantly's own recommendation (P, 2025-09); person-name inboxes, 2-3 per domain, no numbers. 301-redirect each lookalike to velarqo.com (judgement).
- Google sender rules (P, support.google.com/a/answer/81126): SPF or DKIM, TLS, PTR; bulk (>5,000/day) needs SPF+DKIM+DMARC. Spam rate <0.10%, never 0.30%.
- DKIM 2048-bit; can only be generated 24-72 h after Gmail is enabled, up to 48 h to work (P). DMARC p=none with rua; tighten later (S/V).

## Warm-up and caps
- Instantly new-account settings: warm-up limit 10, increase 1/day, reply rate 30%, slow warm-up ON (P).
- Instantly ramp (P, 2025-10): days 1-3 warm-up only; days 4-7 10→18 cold/day; days 8-14 20→28; day 15+ cap 30. Minimum 14 days warm-up, 21-28 safer. Keep warm-up on forever. Pause if bounces >1%, complaints near 0.3%, seed placement <80%.
- Cold cap per inbox, 5 sources: Instantly 30 (P); MailReach 10-30 new, 50-100 warmed (V); Woodpecker 100-150, week 1 20-30 (V); community 15-20, never >25 (S/V); Smartlead start 10-15, +5/day (P for Smartlead). Use 20-30 → 16 inboxes ≈ 320-480/day.

## Hygiene and monitoring
- Gmail API scopes: gmail.send is "sensitive", readonly/modify "restricted"; request the minimum (P).
- Step 1 plain text, no images, no links, no open/click tracking (S/V). Photo, name, signature, 2FA on each inbox.
- Postmaster Tools needs ~200+/day to Gmail to show data (S), so rely on seed tests: Mail-Tester, MXToolbox, GlockApps free, GMass seed list. Act at 0.10% spam, stop at 0.30%, >1% bounces, <80% placement.

## Tonight checklist (10 Oct)
1. Buy 6 domains (.com or .co.uk, WHOIS privacy on).
2. Admin console → add each as secondary domain, verify by TXT.
3. Google MX + SPF `v=spf1 include:_spf.google.com ~all`.
4. Create 12 users (person-style names, unique passwords).
5. 2FA, sign in once each, add photo/name/signature.
6. Don't generate DKIM yet (24-72 h wait). Set a reminder for 11-13 Oct.
7. DMARC p=none with rua on each domain.
8. 11-13 Oct: DKIM 2048 per domain, check with MXToolbox.
9. Authorise the OAuth app per mailbox, narrowest scope.
10. Connect all to Instantly: limit 10, increase 1, reply 30%, slow warm-up ON.
11. 301 redirects to velarqo.com; custom tracking domain if tracking is ever used.
12. Add domains to Postmaster Tools.
13. Seed test + blacklist check 22-24 Oct.

Earliest cold sends from a 10 Oct start: 24 Oct (14-day minimum), 31 Oct safer (21 days). Start at 10/inbox/day, +2/day while placement and bounces hold.
