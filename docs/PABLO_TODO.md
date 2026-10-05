# Pablo's to-do list (things only you can do)

Claude keeps this list up to date. Each item says why it matters and when
it's needed. Tell Claude when one is done.

## Soon: needed before the first real email (~26 Oct)

- [ ] **Buy 6 more domains** on Cloudflare: tryvelarqo.com, usevelarqo.com,
  hellovelarqo.com, teamvelarqo.com, joinvelarqo.com, meetvelarqo.com.
  Claude does all DNS + redirects. *Why:* 16 mailboxes = faster tests.
- [ ] **Create 12 mailboxes** in Google Admin (pablo@ and pablo.garcia@ on each
  new domain), log into each once (mail.google.com), then connect each in
  Instantly. Claude turns on warm-up.
- [ ] **Google Cloud OAuth client** (free, ~10 min): needed so the sending
  engine can send and read replies through Gmail. Steps in `docs/LAUNCH.md`
  item 5. Put the ID and secret in `.env` via `scripts/set_secret.py`.
- [ ] **Google Calendar booking page** "15-min call with Pablo" (free, in
  Workspace). *Why:* replies need a link to book a call.

## Before the first pilot

- [ ] **Your full name on velarqo.com** (Claude edits the site; you just
  confirm the name to show).
- [ ] **Pilot agreement + data processing agreement**: Claude drafts, a
  lawyer/gestor checks.

## Before the first invoice

- [ ] **Register as autónomo** in Spain (alta Hacienda + RETA) with a gestor.
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
