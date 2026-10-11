# Pablo's to-do list (things only you can do)

Claude keeps this list up to date. Each item says why it matters and when
it's needed. Tell Claude when one is done.

## Tomorrow (11 Oct): Microsoft 365 tenant, 8 inboxes

Claude does all DNS; you do the clicks. Paste every record Microsoft shows
into the chat and Claude adds it in Cloudflare.

1. **Create the tenant:** microsoft.com/microsoft-365/business → Business
   Basic → Buy now (not the trial: lower sending limits). Admin email = your
   Gmail, tenant name e.g. `velarqo.onmicrosoft.com`, 8 licences (~£5 each).
2. **Add the domains** at admin.microsoft.com → Settings → Domains → Add
   domain: `usevelarqo.com`, `hellovelarqo.com`, `meetvelarqo.com`. For
   each: paste the TXT verification record (`MS=ms...`) to Claude → Verify
   → choose "I'll add the DNS records myself" → paste the MX / Autodiscover
   CNAME / SPF page to Claude.
3. **Create 8 users** (Users → Active users → Add a user): Pablo Garcia,
   `pablo` / `pablo.garcia` / `pablo.g` at usevelarqo (3), hellovelarqo (3),
   meetvelarqo (2); assign Business Basic; set passwords.
4. **DKIM:** security.microsoft.com → Email & collaboration → Policies &
   rules → Threat policies → DKIM → each domain → Create DKIM keys → paste
   the two CNAMEs (selector1/selector2) to Claude → Enable. Claude adds
   DMARC `p=none` for each domain.
5. **Each inbox once:** sign in at outlook.office.com, set up MFA
   (Authenticator app), add photo, name, signature.
6. **Instantly:** Add account → Microsoft 365 → sign in with each mailbox.
   Tell Claude when the 8 are in; warm-up gets set by API (limit 10,
   +1/day, 30%, slow warm-up on, campaign limit 1).

Warm-up from ~11 Oct → cold sends from ~25 Oct at the earliest, 1 Nov safer.

## Open items (as of 10 Oct evening)

- [ ] Google Admin → Apps → Google Workspace → Gmail → Authenticate email →
      tryvelarqo.com → **Start authentication** (DNS is live).
- [ ] Sign into the 4 new Google inboxes once: 2FA, photo, name, signature
      (pablo.g@getvelarqo.com, pablo.g@velarqohq.com, pablo@tryvelarqo.com,
      pablo.garcia@tryvelarqo.com). Warm-up is already running.
- [ ] **Roll the Cloudflare API token** (dash.cloudflare.com → My Profile →
      API Tokens → the DNS token → Roll); it passed through chat. Delete the
      R2 token created by mistake. Give Claude the new value via
      `notepad D:elarqo\.cf_token.txt` (paste, save, close, say "saved").
- [ ] Photo for the website; confirm "Pablo Garcia" as the public name.
- [ ] UK phone number for the site and signature (~£5/month): yes or no.
- [ ] Google Cloud OAuth client (docs/LAUNCH.md step 5), so the engine can
      send through the inboxes.
- [ ] Approve or edit the v2 cold email (`docs/COLD_EMAIL_V2.md`).
- [ ] Tell Claude the heavy uni weeks (exams, entregas) until June, so the
      floor rules are pre-set.
- [ ] Read and sign the LIA (`docs/legal/LIA_cold_email.md`).

## Before the first real email (25 Oct)

- [ ] **Google Cloud OAuth client** (free, ~10 min): needed so the sending
  engine can send and read replies through Gmail. Steps in `docs/LAUNCH.md`
  item 5. Put the ID and secret in `.env` via `scripts/set_secret.py`.
  After that Claude does `config/mailboxes.json`, `authorize-mailbox`,
  `test-send` and the 15-minute schedule.
- [ ] **Your full legal identity on velarqo.com:** full name, address, and
  the NIF once you're registered. Claude edits the site; you send the
  details. *Why:* Spanish law expects it on commercial emails, and a
  sceptical installer will look. Needed before the first cold email, not
  just before the first pilot.
- [ ] **Read and agree the legitimate interests assessment (LIA)** (draft: `docs/legal/LIA_cold_email.md`) for cold emailing
  named directors. Claude can draft it; you read and agree it. *Why:* UK
  GDPR needs it written down, and the legal checklist in
  `.claude/skills/velarqo-outreach/SKILL.md` (item 3) requires it. None
  exists yet.
- [ ] **Google Calendar booking page** "15-min call with Pablo" (free, in
  Workspace). *Why:* replies need a link to book a call.
- [ ] **Copy the daily database backup off your PC**, regularly. The backup
  (`scripts/backup_db.py`) keeps the last 14 in `data/backups`, but they're
  on the same PC as the database. Copy the newest to an external drive or
  cloud storage.

## For more tests (soon, not blocking the first send)

- [ ] **Approve the letter test** (`docs/LETTERS.md`): read the sample
  (`docs/letters/sample_letter.pdf`), send Claude your surname, UK number,
  legal address line and photo, then order 50 letters on Stannp (about
  £44 + VAT) the same week as the first email batch. Also add a Cloudflare
  Email Routing rule `post@velarqo.com` -> your Gmail so letter replies
  are counted separately. *Why:* a cheap channel nobody else uses; the
  list, letter and PDFs are ready.

- [ ] **Buy 6 more domains** on Cloudflare: tryvelarqo.com, usevelarqo.com,
  hellovelarqo.com, teamvelarqo.com, joinvelarqo.com, meetvelarqo.com.
  Claude does all DNS + redirects. *Why:* 16 mailboxes = faster tests.
- [ ] **Create 12 mailboxes** in Google Admin (pablo@ and pablo.garcia@ on each
  new domain), log into each once (mail.google.com), then connect each in
  Instantly. Claude turns on warm-up.
- [ ] **Buy a VPS** when you're ready to pay for it. It will host the
  database, the sending engine and the webhook server, so sending doesn't
  depend on your PC being on. Until then everything runs on your PC.

## Before the first pilot

- [ ] **Register as autónomo** in Spain (alta Hacienda + RETA) with a gestor.
  Confirm the timing with the gestor, but plan for it before the first
  pilot starts, not only before the first invoice.
- [ ] **UK lawyer review** of the pilot agreement (`docs/delivery/04`), the
  data processing agreement (`docs/delivery/05`) and the privacy page. Both
  documents are drafts. Ask the lawyer one specific question too: is
  recording opt-outs at the point the installer collected the data enough
  for the PECR soft opt-in, or do we need more?
- [ ] **GoHighLevel:** start the free trial when the first sample arrives;
  pay when the first pilot is agreed (Claude will remind you).

## Before the first invoice

- [ ] **Ask the gestor:** VAT on services to UK businesses, invoice format.
- [ ] **Bank account that takes GBP** (e.g. Wise).

## Optional / later

- [x] **Google Places API** (done 5 Oct 2026). Key "velarqo-places" in the
  Default Gemini Project, restricted to Places. Free allowance only: Google
  quota caps text search and place details at 32/day each, and our code stops
  at 30/day / 950 a month. Runs daily at 10:15.
- [ ] **UK Ltd company**: only once clients are paying; ask the gestor about
  Spanish tax residency first.

## Done

- [x] Sending domains getvelarqo.com + velarqohq.com, 4 mailboxes, DNS, warm-up (2026-10-04)
- [x] Instantly API key, Companies House API key (2026-10-04)
- [x] Database moved to local Docker Postgres (Supabase kept as a frozen backup)
