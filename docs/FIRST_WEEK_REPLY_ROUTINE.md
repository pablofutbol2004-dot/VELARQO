# First week of replies: the routine (from ~25 Oct 2026)

One page. The bet in `docs/HARD_TO_FAIL_PLAN.md` fails on "replies but no
calls", and the fix is reply speed: **every reply answered within the
hour, 08:30-17:00 UK, Monday to Friday.** This page is how.

## 0. Before the first send (15 minutes, once)

1. Pick a push channel (free, no account needed for ntfy):
   - **ntfy**: install the ntfy app on your phone, subscribe to a long random
     topic name (it's a password: anyone who knows it can read your alerts), then
     `python scripts/set_secret.py NTFY_TOPIC` and paste the same name.
   - or **Telegram**: make a bot with @BotFather, message it once, read your
     chat id from `https://api.telegram.org/bot<token>/getUpdates`, then
     `set_secret.py TELEGRAM_BOT_TOKEN` and `set_secret.py TELEGRAM_CHAT_ID`.
2. Email copy: `python scripts/set_secret.py VELARQO_ALERT_EMAIL` with your
   Gmail address. It is sent from the first mailbox in `config/mailboxes.json`
   (or the one in `VELARQO_ALERT_MAILBOX`), so it needs a token.
3. `python -m pipelines.outbound alert-test`: a sample alert must reach the
   phone and the inbox. If it doesn't, nothing else on this page works.
4. Schedule `scripts\daily_scoreboard.cmd` at 20:05 in Task Scheduler (the
   15-minute tick also sends the summary if it runs after 20:00; both
   dedupe, so you get it once).

## 1. What pings you

The 15-minute tick reads every mailbox, classifies each reply, and pings
(push + email) for anything that needs a person **now**:

| Ping | What it means | Within the hour |
|---|---|---|
| **POSITIVE** / wants a call / asks how much / wants info / said yes | A live lead | Reply or ring (section 2) |
| **READ IT**: GDPR question | "Where did you get my email?" | Answer by hand, honestly |
| **READ IT**: wrong person / forwarded / left | Someone else is the contact | Email the named person |
| **READ IT**: already follow up / later / mixed / question | A conversation, not a no | Answer what they asked |
| **COMPLAINT (sending paused)** | Spam accusation, ICO, legal, deletion request | Read it, don't argue; see section 4 |
| unmatched reply | We can't tie it to an email we sent | Find the thread in the mailbox |

What does **not** ping: "not interested" and opt-outs (already suppressed;
they are in the `replies` list and the 20:00 summary) and automatic
notices (bounces, out-of-office, helpdesk acks). Nothing is ever
suppressed as "not interested" when the reply also asks a question or
mentions GDPR: those always come to you.

Each alert carries: the reply text, the company (phone, website), what
they were sent and which test arm, earlier replies, the **price arm to
quote** on a call, and the playbook reply to send (from
`docs/SALES_PLAYBOOK.md` section 1). Edit it; never paste it blind.

## 2. The hour: what to do

1. Open the alert. Read the whole reply, not the label.
2. Reply **in the same thread, from the same mailbox**, plain text, short.
   Goal of every reply: a 15-20 minute call. If they gave a number, ring it
   instead of writing.
3. Before any call: `python -m pipelines.outbound call-sheet <their email>`.
   Ask the `docs/PRICING.md` questions before saying the price.
4. Log it the moment you're done (this is the scoreboard's only source):
   ```bash
   python -m pipelines.outbound handled <reply id>
   ```
   ```bash
   python -m pipelines.outbound outcome <email> call_booked
   ```
   then `call_held --reaction ok|hesitant|objected --note "..."`,
   `sample_received`, `pilot_signed`, or `lost --note "..."`.
5. If the automatic label was wrong, correct it so the test results use
   your label: `handled <id> --as positive|unknown|not_interested|...`.

Not in hours (evenings, weekends): the alert still arrives; answer first
thing at 08:30. Don't send cold replies at 23:00.

## 3. The day

- **08:30**: `python -m pipelines.outbound status` (a mailbox with a
  problem doesn't send) and `replies` (anything waiting from overnight).
- **During the day**: answer pings within the hour. Nothing else about
  outreach needs you; the tick sends, follows up and stops by itself.
- **20:00**: the scoreboard lands on your phone:
  `sent / bounces / replies / positive / calls / samples / pilots` today and
  cumulative, per arm and per step, plus "waiting for you" and whether
  sending is on. Same thing any time: `python -m pipelines.outbound scoreboard`
  (`--csv` saves `data/scoreboard_<day>.csv`).
- **Friday only**: `results cold_offer_v1`. Read the rules in
  `docs/TESTING_PLAN.md` before changing anything. Mid-week panic goes in
  `parking.md`.

## 4. When something is wrong

- **COMPLAINT**: sending is paused for every mailbox. Read the reply. If it
  is a deletion or subject access request, answer it within a month (the
  legitimate interests assessment and the wording are in `docs/legal/`).
  `handled <id>`, then `sending on` only once you're sure the rest of the
  list is fine. One complaint is a signal, not a disaster; three in a week
  means the copy or the list is wrong.
- **Bounce rate** above 5% pauses sending by itself. Above 3%, check the
  list source before the next cohort.
- **No pings for two days while emails go out**: run `alert-test`. Then
  `status` for mailbox problems, and `replies` in case alerts are failing
  (a failed alert is retried on the next two ticks, then left in the list;
  `outbound_problems` shows "alerting failed").
- **A positive reply you can't answer today**: reply with one line saying
  when you will ("Thanks, I'll ring you tomorrow between 10 and 12"). A
  short honest reply beats a perfect late one.

## 5. Where things live

| | |
|---|---|
| Reply templates, call script, objections | `docs/SALES_PLAYBOOK.md` |
| "Send me info" email | `docs/delivery/01_send_info_email.md` |
| Classifier and its test set | `outreach/reply_classifier/classify.py`, `tests/fixtures/installer_replies.json` |
| Alerts (channels, what pings, suggested replies) | `outreach/alerts/` |
| Scoreboard | `reporting/scoreboard.py` |
| What was already alerted | table `alert_log` |
