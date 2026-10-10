-- What has already been pinged (reply alerts, the 20:00 scoreboard), so a
-- tick that runs every 15 minutes never sends the same alert twice and a
-- failed send is retried a few times, not forever.
--
-- kind 'reply'  ref = replies.id
-- kind 'daily'  ref = the UK date of the summary (YYYY-MM-DD)

create table if not exists public.alert_log (
  id bigserial primary key,
  kind text not null check (kind in ('reply', 'daily', 'test')),
  ref text not null,
  attempts integer not null default 0,
  sent_at timestamptz,
  channels jsonb not null default '[]',
  error text,
  created_at timestamptz not null default now(),
  unique (kind, ref)
);

alter table public.alert_log enable row level security;
revoke all on public.alert_log from anon, authenticated;
grant select, insert, update on public.alert_log to velarqo_loader;
grant usage, select on sequence public.alert_log_id_seq to velarqo_loader;
create policy loader_full_access on public.alert_log for all to velarqo_loader using (true) with check (true);
