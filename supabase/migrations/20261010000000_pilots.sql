-- Client pilots (docs/delivery/WORKFLOW.md): one pilot per signed agreement,
-- one row per homeowner, an event log, explicit approvals, weekly invoices.
-- Homeowner personal data lives here only while a pilot runs (deleted 30 days
-- after it ends, per the DPA); raw export files stay in clients/ (gitignored).

create table public.pilots (
  id text primary key,                                   -- <client_slug>-<yyyymm>-<n>
  client_slug text not null,
  company_id uuid references public.companies(id),
  vertical text not null,
  state text not null default 'draft' check (state in (
    'draft', 'sample_received', 'audited', 'agreement_signed', 'data_received',
    'eligibility_frozen', 'messages_approved', 'canary_ready', 'canary_running',
    'canary_reviewed', 'live', 'paused', 'completed', 'cancelled')),
  price_per_booked_gbp numeric,                          -- from the signed agreement only
  holdout_fraction numeric not null default 0.15 check (holdout_fraction >= 0 and holdout_fraction < 0.5),
  service_postcode_areas text[] not null default '{}',   -- e.g. {LS, BD, HG}; empty = no area filter
  rules_version text,
  frozen_at timestamptz,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);

create table public.pilot_approvals (
  id bigserial primary key,
  pilot_id text not null references public.pilots(id),
  gate text not null check (gate in ('agreement', 'messages', 'canary_go', 'go_live', 'resume')),
  decision text not null check (decision in ('approved', 'rejected')),
  actor text not null,
  details jsonb not null default '{}',                   -- e.g. message texts + hash, signed PDF paths
  decided_at timestamptz not null default now()
);

create table public.pilot_homeowners (
  pilot_id text not null references public.pilots(id),
  homeowner_key text not null,
  source_record_id text,
  name text, phone text, email text, postcode text,
  quote_date date, product text, quote_value numeric, quote_status text, lead_source text,
  state text not null default 'imported' check (state in (
    'imported', 'excluded', 'eligible', 'holdout', 'treatment', 'queued', 'pushing', 'push_failed',
    'enrolled', 'replied', 'booked', 'attended', 'no_show', 'requoted', 'won', 'lost',
    'no_response', 'opted_out')),
  exclusion_reason text,
  arm text check (arm in ('treatment', 'holdout')),
  stratum text,
  wave_id text,
  ghl_contact_id text,
  push_error text,
  raw jsonb not null default '{}',
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  primary key (pilot_id, homeowner_key),
  -- The comparison group is never contacted: no wave, never a contact state.
  constraint holdout_never_contacted check (
    arm is distinct from 'holdout' or (wave_id is null and state in ('holdout', 'opted_out')))
);
create index pilot_homeowners_state on public.pilot_homeowners (pilot_id, state);

create table public.pilot_events (
  id bigserial primary key,
  pilot_id text not null references public.pilots(id),
  homeowner_key text,
  run_id uuid,
  type text not null,
  source_event_id text unique,                           -- e.g. GHL webhook id: duplicates are ignored
  payload jsonb not null default '{}',
  created_at timestamptz not null default now()
);
create index pilot_events_pilot on public.pilot_events (pilot_id, created_at);

create table public.invoices (
  id bigserial primary key,
  pilot_id text not null references public.pilots(id),
  iso_week text not null,                                -- e.g. 2026-W44
  status text not null default 'draft' check (status in ('draft', 'sent', 'paid', 'void')),
  total_gbp numeric not null default 0,
  created_at timestamptz not null default now(),
  unique (pilot_id, iso_week)
);

create table public.invoice_lines (
  id bigserial primary key,
  invoice_id bigint not null references public.invoices(id),
  pilot_id text not null references public.pilots(id),
  homeowner_key text not null,
  booking_ref text not null,
  kind text not null check (kind in ('booked', 'no_show_credit')),
  amount_gbp numeric not null,
  unique (pilot_id, homeowner_key, booking_ref, kind)    -- one charge and at most one credit per booking
);

do $$
declare t text;
begin
  foreach t in array array['pilots', 'pilot_approvals', 'pilot_homeowners', 'pilot_events', 'invoices', 'invoice_lines'] loop
    execute format('alter table public.%I enable row level security', t);
    execute format('revoke all on public.%I from anon, authenticated', t);
    execute format('grant select, insert, update, delete on public.%I to velarqo_loader', t);
    execute format('create policy loader_full_access on public.%I for all to velarqo_loader using (true) with check (true)', t);
  end loop;
end $$;
grant usage, select on all sequences in schema public to velarqo_loader;
