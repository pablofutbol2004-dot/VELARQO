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

## Microsoft 365 half (8 of the 16 inboxes), verified 2026-10-10

Decision (10 Oct): 8 inboxes on Google, 8 on a new Microsoft 365 Business
Basic tenant, so one provider's suspension can't stop all sending. The
engine supports both (`provider` field per mailbox, `integrations/email/
outlook.py`, `microsoft_auth.py`). Click-by-click steps: docs/LAUNCH.md,
"Microsoft 365: the second 8 mailboxes".

### App registration and tokens (P: learn.microsoft.com)
- Register in **the new tenant**: Entra ID → App registrations → New
  registration; "Single tenant only"; redirect URI under the **Mobile and
  desktop applications** (public client/native) platform, value
  `http://localhost` (P, quickstart-register-app; the localhost rule and the
  "Allow public client flows" switch under Authentication → Advanced
  settings: P, scenario-desktop-production; port matching for localhost is
  not enforced: S, vendor KB; our code uses `http://localhost:<random port>`,
  the same as MSAL).
- No client secret: authorization code + PKCE, public client. If the token
  exchange says a secret is required, "Allow public client flows" is off.
- Delegated Graph permissions: `Mail.ReadWrite`, `Mail.Send`, `User.Read`,
  `offline_access`. `Mail.ReadWrite` because createReply/draft edits need
  it (P, message-createreply). "Grant admin consent for <tenant>" on the
  API permissions page avoids per-user consent prompts (P).
- Refresh tokens: rotated on use, 90-day inactivity expiry for public
  clients (S: general Entra token-lifetime docs, not re-read today). Code
  stores the rotated token in .env each time; run the engine from one
  machine per mailbox.

### Threading on Graph (P: learn.microsoft.com message resource)
- Custom headers on a new message may only start with `x-`, so In-Reply-To
  can't be set directly. A follow-up is `POST /me/messages/{id}/createReply`
  → PATCH subject/body/toRecipients → `POST .../send`; Exchange writes
  In-Reply-To/References and keeps the conversationId (P for the API; that
  the recipient's client threads it is the normal RFC 5322 behaviour, S).
- Message ids change when an item moves Drafts → Sent Items unless every
  request sends `Prefer: IdType="ImmutableId"` (P). The code does.
- One Q&A thread reports Graph giving an *external* reply a new
  conversationId despite correct headers (S). The engine also matches
  replies by sender address and company domain, so that doesn't lose a
  reply.

### DNS Microsoft needs per custom domain (P: learn.microsoft.com)
- MX `<domain-with-dashes>.mail.protection.outlook.com` priority 0; SPF
  `v=spf1 include:spf.protection.outlook.com -all`; CNAME `autodiscover` →
  `autodiscover.outlook.com`; DMARC as for Google. (P, admin centre domain
  wizard shows exact values.)
- DKIM: Defender portal → Email authentication settings → DKIM tab → domain
  → Create DKIM keys → publish two CNAMEs `selector1._domainkey` and
  `selector2._domainkey` → values like
  `selector1-<domain-with-dashes>._domainkey.<tenant>.<r|n>-v1.dkim.mail.microsoft`
  (newer tenants) or `..._domainkey.<tenant>.onmicrosoft.com` (older) → then
  enable signing (P, email-authentication-dkim-configure, updated Aug 2026).
  No 24-72 h wait like Google's.

### Instantly warm-up for Microsoft (P: help.instantly.ai 9201836)
- Email Accounts → Add new → Connect existing accounts → Office 365 /
  Outlook → confirm SMTP enabled → Microsoft sign-in → tick "Consent on
  behalf of your organization" (needs an admin role; S for the role list).
- Prerequisite: **Authenticated SMTP** and **IMAP** enabled per mailbox:
  admin centre → Users → Active users → user → Mail → Manage email apps (P,
  authenticated-client-smtp-submission, Sep 2026). If **Security defaults**
  is on, SMTP AUTH is off and the box is greyed out: disable security
  defaults and put MFA on per user instead (P, same page). Judgement: do it;
  warm-up needs it, and per-user MFA keeps the risk the same.

### Limits (P: Exchange Online service description, not re-read today → S)
- 10,000 recipients/mailbox/day, 30 messages/minute. Irrelevant at our caps.
- Graph throttling is per-tenant and unpublished in detail; the client
  retries on 429/503 with Retry-After, capped at 60 s.

Sources read today: learn.microsoft.com/graph/api/resources/message,
learn.microsoft.com/entra/identity-platform/quickstart-register-app,
learn.microsoft.com/defender-office-365/email-authentication-dkim-configure,
learn.microsoft.com/exchange/.../authenticated-client-smtp-submission,
help.instantly.ai/en/articles/9201836, learn.microsoft.com/graph/api/message-createreply.
