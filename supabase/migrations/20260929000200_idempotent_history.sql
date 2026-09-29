-- Re-running the pipeline must add history, not duplicate it:
-- one snapshot per (company, url, fetch time), one score per (company, ICP version).
alter table public.website_snapshots
  add constraint website_snapshots_unique_fetch unique (company_id, url, fetched_at);

alter table public.score_history
  add constraint score_history_unique_version unique (company_id, icp_version);
