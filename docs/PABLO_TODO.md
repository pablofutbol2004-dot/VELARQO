# Pablo's to-do list (things only you can do)

Claude keeps this list up to date. Each item says why it matters and when
it's needed. Tell Claude when one is done.

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
- [ ] **Write the legitimate interests assessment (LIA)** for cold emailing
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
