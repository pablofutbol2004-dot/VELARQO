# Client pilot workflow: export → homeowner messages → bookings → invoice

Design for delivery pieces 3-12 in `README.md`, written before building so
nothing that touches real homeowners or money is improvised. Our database is
the record of truth; GoHighLevel (GHL) does the homeowner sending, replies
and booking calendar.

## 1. Identity

| Thing | ID | Rule |
|---|---|---|
| Pilot | `pilot_id` = `<client_slug>-<yyyymm>-<n>` | One per agreement. Every event carries it (correlation ID). |
| Wave | `wave_id` = `<pilot_id>-w<n>` | A batch of homeowners released together (canary = w1). |
| Homeowner | `homeowner_key` = sha256(`client_slug` + their own record ID, or + normalised phone/email if no ID) | Stable across re-exports, so the same person is never imported twice. |
| Run | `run_id` (uuid) per script/webhook execution | Logged on every event, so "what ran" is answerable. |

## 2. Pilot states (one row per pilot)

```
draft → sample_received → audited → agreement_signed → data_received
      → eligibility_frozen → messages_approved → canary_ready
      → canary_running → canary_reviewed → live ⇄ paused → completed
any state → cancelled
```

Gates are explicit **approval** records (who, when, what exactly, decision):

| Gate | Approver | What is stored |
|---|---|---|
| agreement_signed | installer + Pablo | signed PDFs (pilot terms + DPA) path, version, date |
| messages_approved | installer | exact text of every message + its hash; any edit = new approval |
| canary_ready → canary_running | Pablo | eligibility counts, holdout counts, test send to own phone done |
| canary_reviewed → live | Pablo | canary results vs stop conditions; written yes/no |
| paused → live | Pablo | which stop condition fired, what changed |

Nothing moves past a gate without its approval row. Code checks the state
before every side effect, not just at the start.

## 3. Homeowner states (one row per homeowner per pilot)

```
imported → excluded(reason)                       [terminal]
imported → eligible → holdout                     [never contacted; terminal for sending]
imported → eligible → treatment → queued(wave) → pushing → enrolled
        → replied → booked → attended | no_show → requoted → won | lost
        → no_response (sequence finished)          [terminal]
any contactable state → opted_out                 [terminal, overrides everything]
```

Rules: states only move forward (a late webhook can't move `won` back to
`replied`); `opted_out` beats everything; `holdout` can never be queued
(enforced by a database check, not only the code).

## 4. Steps and side effects

| # | Step | Side effect | Idempotency | Retry | On crash midway |
|---|---|---|---|---|---|
| 1 | Import export file | DB inserts | unique (`pilot_id`, `homeowner_key`) → re-import is a no-op | none (local) | re-run whole import |
| 2 | Eligibility (won, opt-out, age 3-24 months, area, unknown source, client's do-not-contact list, our suppression) | DB updates | pure function of the frozen data + rules version | none | re-run |
| 3 | Freeze + holdout split | DB updates | deterministic: hash(`homeowner_key`+`pilot_id`) within quote-age strata; frozen once, never re-drawn | none | re-run gives same split |
| 4 | Push wave to GHL (create/update contact) | **remote write** | GHL upsert keyed on `homeowner_key` stored in a custom field; we store `ghl_contact_id` after | 429/5xx/timeout: 3 tries, exponential backoff with jitter (2s, 4s, 8s ± 50%); 4xx validation: no retry, mark homeowner `push_failed` with the error | state `pushing` is written *before* the call; on restart, `pushing` rows are reconciled by looking the contact up in GHL by `homeowner_key` |
| 5 | Enrol in the GHL workflow (add tag `vq-<wave_id>`) | **starts real texts** | tag is per wave; GHL workflow has re-entry **off**, so a repeated tag does not resend | same as 4 | `enrolled` only after GHL confirms; reconcile by reading the contact's tags |
| 6 | Re-check before enrolling | read | opt-out + suppression + pilot state checked *at enrol time*, not only at import | none | n/a |
| 7 | Webhooks in (reply, STOP, booking, outcome) | DB updates | unique GHL event ID → duplicates ignored; out-of-order events can't regress state | GHL retries on our non-200; we return 200 only after commit | event table is the log; replay is safe |
| 8 | STOP / opt-out | DB + GHL DND | idempotent set | as 4 | next enrol re-checks suppression anyway |
| 9 | Weekly invoice | invoice record + PDF | one invoice per (`pilot_id`, ISO week); lines = booked surveys not yet invoiced; marking lines invoiced is in the same transaction as creating the invoice | none (local); sending the invoice email is manual | re-run finds the existing invoice for that week |
| 10 | No-show credit | credit line | one credit per booking; applied on the next invoice | none | idempotent by booking ID |

Billing rule (pricing P1): one charge per **booked survey**; a homeowner
no-show is credited. Price comes from the signed agreement, never from code
defaults.

## 5. Stop conditions (checked after every wave and daily while live)

Proposed thresholds for client 1. **Pablo to confirm before launch**; they
can't be loosened afterwards to make the pilot "pass":

| Signal | Pause if |
|---|---|
| Opt-out/STOP rate | > 8% of contacted homeowners in a wave |
| Complaints (angry reply, "how did you get my number", mention of ICO) | ≥ 2 in a wave, or any mention of ICO/regulator |
| Text delivery failures | > 10% of a wave |
| Wrong-person replies | > 5% of a wave (bad data, not bad copy) |
| Installer can't cover booked surveys | any survey unattended because of the installer |
| Pablo's manual time | > 60 min per 100 homeowners contacted |
| Replies lost or not answered within 1 working hour | any |

A breach moves the pilot to `paused` automatically (no new waves enrolled)
and alerts Pablo. Messages already in flight finish their current step.

## 6. Failure cases, reasoned through

| Case | What happens |
|---|---|
| Same export imported twice | unique key → second import changes nothing |
| Script crashes between "push contact" and "enrol" | homeowner sits in `pushing`/`pushed`; next run reconciles with GHL, then enrols once |
| GHL times out after it actually created the contact | upsert by `homeowner_key` finds it; no duplicate |
| Same webhook delivered 3 times | event ID unique → processed once |
| Booking webhook arrives before the reply webhook | state can only move forward; `booked` stands |
| Malformed export (no dates, merged cells) | audit reports it; nothing becomes `eligible` without a usable date |
| GHL down for a day | waves wait in `queued`; nothing is lost; pilot can be `paused` |
| Homeowner opts out after being queued | enrol-time re-check skips them |
| Client cancels | pilot → `cancelled`; GHL workflow tag removed; data deleted per DPA within 30 days |

## 7. Data kept, and for how long

- Our DB: homeowner name, phone, email, quote date/product/value/status,
  state history. Needed to push to GHL and to prove results.
- Never in git or `data/`; raw export files only under `clients/<slug>/`.
- Deleted 30 days after the pilot ends unless the installer continues
  (DPA wording). Aggregated counts kept.

## 8. What gets built, in order

1. Tables: `pilots`, `pilot_approvals`, `pilot_homeowners`, `pilot_events`,
   `invoices`, `invoice_lines` (one migration).
2. Import + eligibility + freeze/holdout script (reuses `sample_audit`).
3. GHL push/enrol with the reconcile step (extends `integrations/ghl`).
4. Webhook receiver (needs the cloud/VPS, or a tunnel, to be reachable).
5. Stop-condition check + daily status.
6. Weekly invoice.

## 9. Review fixes (2026-10-10) and what must be checked on the real GoHighLevel

An independent review found these; all fixed and covered by tests that
commit for real and read back from a second connection:
- CLI commands ran inside an uncommitted transaction (texts would go out,
  nothing saved). Every command now uses an autocommit connection.
- Our opt-outs (complaints, DND, `pilot optout`) are pushed to GHL as
  do-not-disturb + wave tag removed (`dnd_pending` → `dnd_confirmed`,
  retried by `check`).
- `send-wave` refuses unless the pilot's GHL location matches `.env`;
  events for unknown contacts are stored, not dropped.
- One person = one contactable row (`person_key` = UK mobile or email):
  opt-out / do-not-contact / already-won on any quote excludes all their
  quotes; only their newest eligible quote is kept; holdout and claims are
  checked per person.
- Only UK mobiles count as textable (Excel's `7700900123` and `.0` fixed).
- Re-import re-applies the rules (e.g. a do-not-contact list added later).
- STOP = whole message, or 3 words or fewer containing stop/unsubscribe;
  every other reply is flagged for a human answer.
- Resume returns to the state it was paused from and only new events count.
- Manual time and rates are also checked pilot-wide.
- Billing: survey calendar only; one charge per person; cancellations
  credited only if not rebooked within 14 days; installer-caused misses
  charged; caps and "first N free" applied; direct bookings can be logged.
- Two `send-wave` runs can't overlap (advisory lock); 401/403 stops the run
  without blaming rows; a fast webhook no longer aborts a wave.
- Only needed fields of GHL events are stored; `pilot purge` deletes
  personal data 30 days after a pilot ends.

**Second review fixes (2026-10-11)**, each with a regression test:
1. One person = every row sharing ANY phone or email, even through a chain
   (quote A: phone + email, quote B: same email only). Grouped at every
   import; the claim also refuses a row whose person (person_key, phone or
   email) is opted out / on the do-not-contact list / already won, and never
   claims two rows of one person. `+44 (0)7700 900123` is a valid mobile.
   Installer and webhook opt-outs reach every quote of the person.
2. No double charge: one claimed row per person, invoices one per person
   AND one per GHL contact (safety net). Stop conditions count people.
3. A credited no-show who rebooks or attends is charged again (new line
   kind `credit_reversal`, migration `20261011100000`); a further no-show is
   credited again.
4. Caps: credited no-shows don't use up `max_billable`; the weekly cap counts
   the ISO week the survey was booked (`invoice_lines.booked_at`); free /
   over-cap is decided in booking order; "first N free" counts only people
   actually texted (enrolled or beyond), by claim order.
5. After the GHL upsert, the row and pilot are re-read under lock; the wave
   tag (= texts) is only added if the row is still `pushing` and the pilot
   still sending (`tag_skipped` event otherwise). The contact id is kept so
   the do-not-disturb still reaches GHL.
6. Pending do-not-disturb pushes are retried for every pilot, whatever its
   state (completed/cancelled too). `check` handles each pilot on its own;
   exit 2 if anything paused, 1 if anything failed.
7. STOP classifier: complaint and wrong-person are always recorded, even in
   "STOP ICO" / "Stop. Wrong number"; "Stop by Tuesday?", "Don't stop",
   "stop round" aren't opt-outs; bare "cancel" goes to a person; a STOP from
   someone with a booked survey also asks for a human answer.
8. Personal data: no message body kept for contacts that aren't our
   homeowners; `homeowner_key` is an HMAC with `VELARQO_KEY_SECRET` (generated
   into `.env` on first use if missing — keep it: a new secret means new keys);
   `pilot purge` also unlinks the GHL location.
Also: the webhook server replies 200 before pushing opt-outs (background,
one at a time); after a resume, rates use people contacted since the resume,
and a reply that arrived during the pause still has to be answered;
`log direct_booking` needs a treatment homeowner we messaged within 14 days;
the canary claims at most 30 people across all its waves.

**Verify on the real GoHighLevel before the first homeowner is texted**
(test with your own phone and a dead number at step 8.6):
1. Which webhooks a Private-Integration sub-account actually sends: signed
   (`x-wh-signature`; possibly a newer header) or workflow "Webhook" actions
   (unsigned; we then use `x-velarqo-secret` and define the payload fields
   ourselves). Confirm GHL signs exactly the bytes it sends.
2. Whether GHL retries on 5xx (or only 429), and how long.
3. What SMS STOP does: sets `dnd`, or only `dndSettings.SMS.status`.
4. Whether failed texts produce `OutboundMessage` with status failed.
5. Settings the no-double-text logic relies on: "allow duplicate contacts"
   OFF (and the matching order), workflow re-entry OFF, exit on reply.
   Check the upsert doesn't overwrite the installer's own contact data.
6. Real `appointmentStatus` values, and whether a reschedule is an update
   or cancel + new booking.
7. Manual replies typed in GHL carry `userId` (that's how "answered" is
   detected).
Still open (by design, manual for now): removing GHL tags when a pilot is
cancelled; "one charge per street address" (we do one per person).
