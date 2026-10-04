# Launch checklist: first cold emails

Built and tested: the send engine (`outreach/send_engine/`) and its CLI
(`python -m pipelines.outbound`). 1,918 installers are in `outreach_queue`
(UK, residential, Ltd/LLP, with an email), ranked by priority.

The slowest step is inbox warm-up (2-3 weeks), so do steps 1-3 today.

## You (Pablo) — needs your card or your Google login

1. **Buy one sending domain** (about £10/yr), e.g. `getvelarqo.com` or
   `velarqo.co.uk`. Never send cold email from `velarqo.com` itself: if the
   sending domain's reputation gets hurt, the website and hello@ stay safe.
   Point it at Cloudflare and redirect its website to velarqo.com.
2. **Google Workspace on that domain, 2 mailboxes** (Business Starter,
   about £6-7 per user/month), e.g. `pablo@` and `p.@`. Same real name on
   both, profile photo, signature matching the emails.
3. **DNS on the sending domain** (Cloudflare): Google MX records; SPF
   `v=spf1 include:_spf.google.com ~all`; DKIM (generate in Google Admin
   → Apps → Gmail → Authenticate email); DMARC
   `v=DMARC1; p=none; rua=mailto:hello@velarqo.com`. Also add the same
   DMARC record to velarqo.com (it has none today).
4. **Warm-up tool** on both mailboxes (Instantly, Lemwarm, Warmbox: roughly
   $15-40/month). Run it 2-3 weeks before the first real send and keep it
   running after. It must keep warm-up emails out of the inbox (they label
   or archive them) so they don't show up as replies.
5. **Google Cloud OAuth client** (free, about 10 minutes): new project →
   enable Gmail API → OAuth consent screen **Internal** → credentials →
   "Desktop app". Put `GOOGLE_CLIENT_ID` and `GOOGLE_CLIENT_SECRET` in `.env`.
6. **Website identity:** your full name (and NIF once registered) on
   velarqo.com. A sceptical installer will check.

## Me (Claude) — once the above exists

7. `config/mailboxes.json` from `config/mailboxes.example.json`, start at
   `daily_cap: 10` per mailbox and raise it weekly (10 → 20 → 30) while
   bounces stay under 3%.
8. `python -m pipelines.outbound authorize-mailbox <email>` for each mailbox
   (opens Google sign-in; the token goes into `.env`, never into chat).
9. `python -m pipelines.outbound test-send <your gmail> --mailbox <email>`:
   check it lands in the inbox, not spam, and threads properly.
10. Schedule `scripts/outbound_tick.cmd` every 15 minutes in Windows Task
    Scheduler. It only sends Mon-Fri, 08:30-17:00 UK time, and only when
    the kill switch is on.

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
  (`docs/knowledge/pass_13_first_10_installers/sales/` has the call
  script and pilot close), then `handled <id>`.
- `python -m pipelines.outbound status`: sends, bounces, anything stuck.

## Automatic safety (no action needed)

- Never emails the same person twice for the same step, even if a run crashes or repeats.
- Opt-outs, "not interested", bounces and complaints are suppressed for good (address and company domain).
- Any reply stops that company's follow-ups. Out-of-office replies don't.
- A complaint, or a bounce rate over 5% (once 20+ emails have gone out), switches all sending off until you turn it back on.
- Only Ltd/LLP companies (UK PECR corporate subscribers) are ever emailed.
- Sequence: first email, follow-up after 3 business days, final one 5 business days later. All three are plain text, under 90 words, and include the opt-out line.
