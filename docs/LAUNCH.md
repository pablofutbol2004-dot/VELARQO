# Launch checklist: first cold emails

Built and tested: the send engine (`outreach/send_engine/`) and its CLI
(`python -m pipelines.outbound`). About 4,800 emailable Ltd companies (windows
and doors, plus roofing) are in `outreach_queue`, on company addresses, ranked
by priority. First send: about **25 Oct 2026**.

The slowest step is inbox warm-up (2-3 weeks). It started on 4 Oct, so the
4 current mailboxes are ready by then. The extra 12 mailboxes (see below) warm
up later and join the send as they're ready.

## Done

1. **Sending domains:** `getvelarqo.com` and `velarqohq.com` (never send cold
   email from `velarqo.com` itself, so the website and hello@ stay safe).
2. **Google Workspace, 4 mailboxes** across those two domains.
3. **DNS** (SPF, DKIM, DMARC) on both sending domains.
4. **Warm-up in Instantly** on all 4 mailboxes since 2026-10-04. Instantly is
   used for warm-up only; our own engine does the sending. Keep it running
   after the first send.

## You (Pablo) — needs your card or your Google login

5. **Google Cloud OAuth client** (free, about 10 minutes): new project →
   enable Gmail API → OAuth consent screen **Internal** → credentials →
   "Desktop app". Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`
   (use `scripts/set_secret.py`, never paste them into chat).
6. **Website identity, before the first email:** your full legal name and
   address on velarqo.com (and the NIF once you're registered). Spanish law
   and a sceptical installer both expect to see who is behind the emails.
   Send Claude the details and it edits the site. (Deploy is manual:
   `npx wrangler deploy`.)
- **Later, not needed for the very first send:** buy 6 more domains and
  create 12 more mailboxes (16 in total), then connect them to Instantly for
  warm-up. Claude does the DNS. This is for more parallel tests. Decided
  10 Oct: **8 on Google, 8 on Microsoft 365**, so one provider suspending us
  can't stop all sending. The Microsoft half is the section
  "Microsoft 365: the second 8 mailboxes" below.

## Me (Claude) — once the OAuth client exists

7. `config/mailboxes.json` from `config/mailboxes.example.json` (each entry
   says `"provider": "gmail"` or `"outlook"`), start at `daily_cap: 10` per
   mailbox and raise it weekly (10 → 20 → 30) while bounces stay under 3%.
8. `python -m pipelines.outbound authorize-mailbox <email>` for each mailbox
   (opens Google or Microsoft sign-in, depending on the mailbox's provider;
   the token goes into `.env`, never into chat). It checks that the token
   really belongs to that mailbox before saving anything.
9. `python -m pipelines.outbound test-send <your gmail> --mailbox <email>
   --with-follow-up`: check both emails land in the inbox, not spam, and that
   the second one sits under the first (threading).
   `python -m pipelines.outbound status --check-mailboxes` signs in to every
   mailbox and reports which tokens are missing or wrong.
10. Schedule `scripts/outbound_tick.cmd` every 15 minutes. **For now this is
    Windows Task Scheduler on your PC; later the VPS** (Pablo hasn't bought it
    yet), so sending doesn't depend on your PC being on. Each tick sends up
    to 2 emails per mailbox, and only one tick may run at a time. It only
    sends Mon-Fri, 08:30-17:00 UK time, and only when the kill switch is on.

## Microsoft 365: the second 8 mailboxes (from ~31 Oct)

The engine treats a Microsoft mailbox exactly like a Google one: same
`mailboxes.json`, same `authorize-mailbox`, `test-send`, `status`, `run`,
same reply/bounce/complaint handling and kill switch. The code is
`integrations/email/outlook.py` (Microsoft Graph) and
`integrations/email/microsoft_auth.py`. Follow-ups are sent as *replies* to
the first email, so they thread in the recipient's inbox the way Gmail's do.

Everything below was written from Microsoft's own pages on 10 Oct 2026
(links in `docs/knowledge/web_research/2026-10-10_inbox_setup.md`). Screens
change; if a name doesn't match, look for the nearest one.

### A. You (Pablo): tenant, domains, users (about 1 hour, plus DNS waits)

1. **Buy Microsoft 365 Business Basic** at microsoft.com → "Microsoft 365
   Business Basic" → Buy now, for **8 users**. Use a *new* account (this
   creates a fresh tenant such as `velarqo.onmicrosoft.com`). Pick the
   annual plan only if the price difference matters; monthly can be cancelled.
2. **Add the 4 Microsoft sending domains** (the ones not on Google):
   admin.microsoft.com → **Settings → Domains → Add domain** → type the
   domain → verify with the **TXT record** Microsoft shows (Claude adds it at
   the registrar / Cloudflare) → on the next screen choose **"Let me add the
   DNS records myself"** / Exchange only, and give Claude the values. Claude
   adds, per domain:
   - MX: `<domain-with-dashes>.mail.protection.outlook.com`, priority 0
     (Microsoft shows the exact host).
   - TXT (SPF): `v=spf1 include:spf.protection.outlook.com -all`
   - CNAME `autodiscover` → `autodiscover.outlook.com`
   - TXT `_dmarc`: `v=DMARC1; p=none; rua=mailto:dmarc@velarqo.com`
3. **DKIM** (can be done straight away on Microsoft, no 24-72 h wait):
   security.microsoft.com → **Email & collaboration → Policies & rules →
   Threat policies → Email authentication settings → DKIM tab** → click the
   domain → **Create DKIM keys** → copy the two CNAME values (`selector1`
   and `selector2`; they end in `...dkim.mail.microsoft` or
   `...onmicrosoft.com`) → Claude publishes both CNAMEs → come back and set
   **"Sign messages for this domain with DKIM signatures"** to **Enabled**.
   If it says the CNAMEs aren't found, wait an hour and retry.
4. **Create the 8 users**: admin.microsoft.com → **Users → Active users →
   Add a user**. Person-style names, 2 per domain, unique passwords, assign a
   Business Basic licence, and set the username to the sending domain (not
   `onmicrosoft.com`). Sign in to each once at outlook.office.com and set the
   display name, a photo and a plain signature.
5. **Per user, allow Instantly's protocols**: Users → Active users → the
   user → **Mail → Manage email apps** → tick **Authenticated SMTP** and
   **IMAP** → Save. If the box is greyed out, **Security defaults** is on:
   entra.microsoft.com → **Entra ID → Overview → Properties → Manage
   security defaults → Disabled**. (Microsoft recommends leaving security
   defaults on; we trade it for Instantly warm-up and switch MFA on per user
   instead: entra.microsoft.com → Users → the user → Authentication methods.)

### B. You (Pablo): the app the engine signs in with (10 minutes, once)

6. entra.microsoft.com → **Entra ID → App registrations → New registration**.
   - Name: `Velarqo sender`.
   - Supported account types: **Single tenant only** (accounts in this
     organizational directory only).
   - Redirect URI: platform **Public client/native (mobile & desktop)**,
     value `http://localhost`.
   - **Register**.
7. On the app's **Overview** page copy **Application (client) ID** and
   **Directory (tenant) ID** into `.env` with
   `.venv\Scripts\python.exe scripts\set_secret.py MS_CLIENT_ID` and the
   same for `MS_TENANT_ID` (never paste them into chat). There is no client
   secret: this is a desktop app.
8. **Authentication** (left menu) → scroll to **Advanced settings → Allow
   public client flows → Yes** → Save.
9. **API permissions → Add a permission → Microsoft Graph → Delegated
   permissions** → tick `Mail.ReadWrite`, `Mail.Send`, `User.Read`,
   `offline_access` → **Add permissions** → **Grant admin consent for
   <tenant>** → Yes. Every row should now say "Granted for ...".
   (`Mail.ReadWrite` rather than `Mail.Read`: a threaded follow-up is a
   draft reply that the engine edits before sending.)

### C. Me (Claude), once A and B are done

10. Add the 8 mailboxes to `config/mailboxes.json` with
    `"provider": "outlook"`, `daily_cap: 10`, `enabled: true`.
11. `python -m pipelines.outbound authorize-mailbox <email>` for each: a
    Microsoft sign-in page opens, sign in **as that mailbox** (use a private
    window if another Microsoft account is signed in), accept. The refresh
    token is stored in `.env` as `OUTLOOK_REFRESH_TOKEN_<EMAIL>`. Microsoft
    rotates these tokens; the engine saves the new one automatically, so
    **only one machine may run the engine** for a given mailbox (PC *or*
    VPS, not both) or they invalidate each other's tokens.
12. `python -m pipelines.outbound test-send <your gmail> --mailbox <email>
    --with-follow-up` and `status --check-mailboxes`, as for Google.
13. **Instantly warm-up**: Instantly → **Email Accounts → Add new → Connect
    existing accounts → Office 365 / Outlook** → confirm SMTP is enabled →
    sign in as the mailbox → on the permissions page tick **"Consent on
    behalf of your organization"** (you're the admin) → Accept. Then the
    same warm-up settings as Google (limit 10, increase 1/day, reply rate
    30%, slow warm-up on). Microsoft inboxes need the same 14-21 days before
    cold sends: from a 10 Oct start, **24 Oct earliest, 31 Oct safer**.

### Microsoft limits worth knowing

- Exchange Online: 10,000 recipients per mailbox per day and 30 messages a
  minute; our caps (10-30 a day) are nowhere near either.
- Graph API refresh tokens for desktop apps expire after 90 days *without
  use*; a mailbox that sends on weekdays never hits that. If one does
  expire, `status --check-mailboxes` says so and `authorize-mailbox` fixes it.

## Where things live

- **Database:** a local Docker Postgres container, `velarqo-postgres`
  (`deploy/docker-compose.yml`, port 127.0.0.1:5437). Supabase is a frozen
  backup only. Database changes are applied with
  `.venv/Scripts/python.exe scripts/apply_migration.py <file>`.
- **Backup:** `scripts/backup_db.py` runs daily and keeps the last 14 in
  `data/backups`. Copy the newest one off the PC regularly (an external
  drive or cloud storage).
- **Later, on a VPS:** the database, the sending engine and the webhook
  server move there together.

## First batch (day 1 after warm-up)

```bash
python -m pipelines.outbound create-cohort --size 25 --name "Batch 1"
python -m pipelines.outbound review <campaign_id>
python -m pipelines.outbound activate <campaign_id>
python -m pipelines.outbound sending on
```

Read the review CSV before activating, and `cancel` any company that's
obviously wrong (big manufacturer, commercial-only, not a window firm).

## Daily (5 minutes)

- `python -m pipelines.outbound replies`: answer positives the same day
  (`docs/SALES_PLAYBOOK.md` has the reply templates, call script and
  pilot close), then `handled <id>`.
- `python -m pipelines.outbound status`: sends, bounces, anything stuck.

## Before the first email: open items

- Google Cloud OAuth client (step 5), then Claude does steps 7-10.
- Your full legal identity on velarqo.com (step 6).
- A UK lawyer's view on the pilot agreement, DPA and privacy page is needed
  before the first **pilot**, not the first email (see `docs/PABLO_TODO.md`).
- A written legitimate interests assessment (LIA) for emailing named
  directors (item 3 of the legal checklist in
  `.claude/skills/velarqo-outreach/SKILL.md`). None exists yet.

## Automatic safety (no action needed)

- Never emails the same person twice for the same step, even if a run crashes or repeats.
- Opt-outs, "not interested", bounces and complaints are suppressed for good (address and company domain).
- Any reply stops that company's follow-ups. Out-of-office replies don't.
- A complaint, or a bounce rate over 5% (once 20+ emails have gone out), switches all sending off until you turn it back on.
- Only Ltd/LLP companies (UK PECR corporate subscribers) are ever emailed.
- Sequence: first email, follow-up after 3 business days, final one 5 business days later. All three are plain text, under 80 words (signature and opt-out included), and include the opt-out line.
