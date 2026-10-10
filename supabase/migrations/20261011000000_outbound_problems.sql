-- Per-mailbox problems from outbound ticks (inbox sync or sending failed),
-- shown by `pipelines.outbound status` so a broken mailbox isn't silent.

create table if not exists public.outbound_problems (
  id bigserial primary key,
  mailbox text not null,
  problem text not null,
  created_at timestamptz not null default now()
);
create index if not exists outbound_problems_recent on public.outbound_problems (created_at desc);

alter table public.outbound_problems enable row level security;
revoke all on public.outbound_problems from anon, authenticated;
grant select, insert, delete on public.outbound_problems to velarqo_loader;
grant usage, select on sequence public.outbound_problems_id_seq to velarqo_loader;
create policy loader_full_access on public.outbound_problems for all to velarqo_loader using (true) with check (true);
