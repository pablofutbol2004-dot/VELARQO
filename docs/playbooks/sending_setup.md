# Sending setup: domains, inboxes, warm-up (about 1 hour)

Side: **Velarqo** (our own cold email). Launch = warm-up start + 21 days
(`truth/velarqo/launch.yaml`).

## 1. Domains (10 min, ~€30/year)

Buy at Porkbun, Cloudflare Registrar or Namecheap (cheap, simple DNS):

| Domain | Use |
|---|---|
| `getvelarqo.com` | sending |
| `velarqohq.com` | sending |
| `velarqo.co.uk` | **main brand** (website, real replies later), only if `velarqo.com` isn't yours. Never send cold email from it. |

Checked 2026-09-30 by DNS: all three had no DNS records (very likely free).

## 2. Google Workspace (20 min, ~€7-8 per inbox per month)

1. Sign up for **Business Starter** with `getvelarqo.com` as the primary domain.
2. Admin console → Domains → add `velarqohq.com` as a **secondary domain** (not an alias).
3. Create 6 users, all your real name, e.g.:
   - `pablo@getvelarqo.com`, `pablo.v@getvelarqo.com`, `p.v@getvelarqo.com`
   - the same three on `velarqohq.com`
4. Give each a profile photo (the same real photo). It helps trust and deliverability.

## 3. DNS records for EACH sending domain (15 min)

| Type | Host | Value |
|---|---|---|
| MX | @ | `smtp.google.com` (priority 1) |
| TXT (SPF) | @ | `v=spf1 include:_spf.google.com ~all` |
| TXT (DKIM) | `google._domainkey` | generate in Admin console → Apps → Google Workspace → Gmail → Authenticate email → Generate new record (2048-bit), paste it, then click **Start authentication** |
| TXT (DMARC) | `_dmarc` | `v=DMARC1; p=none; rua=mailto:pablo@getvelarqo.com` |
| Redirect | @ and www | forward to the main site (velarqo.co.uk or velarqo.com) |

Tell Claude when done: it checks every record from its side.

## 4. Smartlead (10 min, ~€34/month)

1. Sign up for **Basic**.
2. In Google Admin: Security → API controls → allow Smartlead (or enable
   IMAP + app access as Smartlead's guide says) so the inboxes can connect.
3. Connect all 6 inboxes (Google OAuth).
4. For each inbox turn **warm-up on**: start ~5/day, increase ~3/day, max ~40,
   reply rate ~30%. Leave it running.
5. Don't send any campaign yet.

## 5. Then

- Write the warm-up start date into `truth/velarqo/launch.yaml` (`warmup_started`).
- Don't use the inboxes for anything else; don't send cold email before launch day.
