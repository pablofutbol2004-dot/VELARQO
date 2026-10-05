-- Counts paid-API calls per day so code can refuse to go past the free
-- allowance (Google Places: ~1,000 free Enterprise calls per month).

create table if not exists public.api_usage (
  day date not null,
  api text not null,
  calls integer not null default 0,
  primary key (day, api)
);

alter table public.api_usage enable row level security;
revoke all on public.api_usage from anon, authenticated;
grant select, insert, update on public.api_usage to velarqo_loader;
create policy api_usage_loader on public.api_usage for all to velarqo_loader using (true) with check (true);
