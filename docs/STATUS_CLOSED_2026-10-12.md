# Velarqo: closed 12 Oct 2026

Pablo decided to stop Velarqo before the first send. Nothing was ever emailed to a prospect.

## What was switched off
- Windows scheduled tasks disabled: daily backup, daily free data, daily Places lookup, daily website refresh.
- Docker container `velarqo-postgres` stopped, with its restart policy set to `no`. The data is kept in the volume.
- Last database backup: `velarqo_20261012_161608.dump` (169 MB), made by `scripts/backup_db.py`.
- Pablo cancels the paid services himself: Google Workspace, Instantly, domain auto-renewals, and any Google Cloud billing or keys.

## What exists if it's ever restarted
- **Last plan:** US estimate recovery for remodelers, window/door firms and roofers (`docs/PLAN_US_2026-10.md`), with cold email v1 in `docs/COLD_EMAIL_US_V1.md`.
- **Send engine** with UK (PECR) and US (CAN-SPAM) markets, US time-zone windows and the US footer (commit 1276ce8).
- **US list:** 2,219 checked contractors with emails from their own sites, in `data/us/us_prospects_final.csv` (local only, not in git). It's rebuilt by `data/us/build_final.py`, from the free WA/OR licence data plus Codex and Grokbot web research.
- **Research:** `docs/knowledge/` (YouTube reviews, web research, ChatGPT handoffs) and `docs/LEARNINGS.md`.

## To restart
1. `docker update --restart=unless-stopped velarqo-postgres && docker start velarqo-postgres`.
2. Re-enable the scheduled tasks, if wanted.
3. Re-create the sending inboxes. Warm-up takes 2-3 weeks.
4. Re-check the list (emails go stale within months).
