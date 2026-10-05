-- Town-by-town Places searches already run, so the daily sweep never repeats
-- one. Only counts are kept, never Google's results.

create table if not exists public.places_sweep (
  query text primary key,
  town text not null,
  done_at timestamptz not null default now(),
  results integer not null default 0,
  matched integer not null default 0
);

alter table public.places_sweep enable row level security;
revoke all on public.places_sweep from anon, authenticated;
grant select, insert, update on public.places_sweep to velarqo_loader;
create policy places_sweep_loader on public.places_sweep for all to velarqo_loader using (true) with check (true);
