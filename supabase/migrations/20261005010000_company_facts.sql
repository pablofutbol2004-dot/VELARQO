-- Raw facts per company per free source (Companies House API endpoints,
-- later others), refreshed by a daily job. One row per (company, source);
-- the payload is kept whole so new signals can be derived later without
-- re-fetching. company_signals turns the payloads into usable columns.

create table public.company_facts (
  company_id uuid not null references public.companies (id) on delete cascade,
  source text not null,
  payload jsonb not null,
  fetched_at timestamptz not null default now(),
  primary key (company_id, source)
);
create index company_facts_fetched_idx on public.company_facts (source, fetched_at);

alter table public.company_facts enable row level security;
grant select, insert, update, delete on public.company_facts to velarqo_loader;
create policy loader_full_access on public.company_facts for all to velarqo_loader using (true) with check (true);

create view public.company_signals with (security_invoker = true) as
select
  c.id as company_id,
  p.payload->>'company_status' as ch_status,
  coalesce((p.payload->'accounts'->>'overdue')::boolean, false) as accounts_overdue,
  coalesce((p.payload->'confirmation_statement'->>'overdue')::boolean, false) as confirmation_overdue,
  p.payload->'accounts'->'last_accounts'->>'type' as last_accounts_type,
  (p.payload->'accounts'->'last_accounts'->>'made_up_to')::date as last_accounts_made_up_to,
  coalesce((p.payload->>'has_insolvency_history')::boolean, false)
    or i.payload is not null and jsonb_array_length(coalesce(i.payload->'cases', '[]')) > 0 as insolvency,
  coalesce((p.payload->>'has_charges')::boolean, false) as has_charges,
  (select count(*) from jsonb_array_elements(coalesce(ch.payload->'items', '[]')) x
     where x->>'status' = 'outstanding') as charges_outstanding,
  (select count(*) from jsonb_array_elements(coalesce(psc.payload->'items', '[]')) x
     where x->>'ceased_on' is null) as active_psc_count,
  (select string_agg(x->>'name', '; ') from jsonb_array_elements(coalesce(psc.payload->'items', '[]')) x
     where x->>'ceased_on' is null and x->>'kind' like 'individual%') as psc_names,
  (select max((x->>'notified_on')::date) from jsonb_array_elements(coalesce(psc.payload->'items', '[]')) x
     where x->>'ceased_on' is null) as newest_psc_since,
  (select max((x->>'appointed_on')::date) from jsonb_array_elements(coalesce(o.payload->'items', '[]')) x
     where x->>'officer_role' = 'director' and x->>'resigned_on' is null) as newest_director_since,
  (select min((x->>'appointed_on')::date) from jsonb_array_elements(coalesce(o.payload->'items', '[]')) x
     where x->>'officer_role' = 'director' and x->>'resigned_on' is null) as longest_director_since,
  (select count(*) from jsonb_array_elements(coalesce(f.payload->'items', '[]')) x
     where (x->>'date')::date > current_date - 365) as filings_last_year,
  greatest(p.fetched_at, o.fetched_at) as fetched_at
from public.companies c
left join public.company_facts p on p.company_id = c.id and p.source = 'ch_profile'
left join public.company_facts o on o.company_id = c.id and o.source = 'ch_officers'
left join public.company_facts psc on psc.company_id = c.id and psc.source = 'ch_psc'
left join public.company_facts ch on ch.company_id = c.id and ch.source = 'ch_charges'
left join public.company_facts f on f.company_id = c.id and f.source = 'ch_filings'
left join public.company_facts i on i.company_id = c.id and i.source = 'ch_insolvency'
where p.payload is not null;

revoke all on public.company_signals from anon, authenticated;
grant select on public.company_signals to velarqo_loader;
