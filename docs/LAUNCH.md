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
  warm-up. Claude does the DNS. This is for more parallel tests.

## Me (Claude) — once the OAuth client exists

7. `config/mailboxes.json` from `config/mailboxes.example.json`, start at
   `daily_cap: 10` per mailbox and raise it weekly (10 → 20 → 30) while
   bounces stay under 3%.
8. `python -m pipelines.outbound authorize-mailbox <email>` for each mailbox
   (opens Google sign-in; the token goes into `.env`, never into chat). It
   now checks that the token really belongs to that mailbox.
9. `python -m pipelines.outbound test-send <your gmail> --mailbox <email>`:
   check it lands in the inbox, not spam, and threads properly.
10. Schedule `scripts/outbound_tick.cmd` every 15 minutes. **For now this is
    Windows Task Scheduler on your PC; later the VPS** (Pablo hasn't bought it
    yet), so sending doesn't depend on your PC being on. Each tick sends up
    to 2 emails per mailbox, and only one tick may run at a time. It only
    sends Mon-Fri, 08:30-17:00 UK time, and only when the kill switch is on.

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
