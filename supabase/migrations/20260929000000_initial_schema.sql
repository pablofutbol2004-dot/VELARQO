-- Velarqo core schema: lead universe, campaigns, sent messages + outcomes,
-- and suppression list. RLS is on with no policies on purpose: nothing is
-- readable/writable with the public (anon) key - only backend scripts
-- using the service-role key or a direct DB connection.

create table public.companies (
  id uuid primary key default gen_random_uuid(),
  vertical text not null,
  -- stable identity across re-runs: "ch:<company_number>", "osm:<type>/<id>",
  -- or "name:<match_name>|<postcode district>"; upserts key on this
  source_key text not null,
  display_name text not null,
  legal_name text,
  match_name text,
  company_number text,
  osm_ids text[] not null default '{}',
  sources text[] not null default '{}',
  sic_codes text[] not null default '{}',
  accounts_category text,
  company_category text,
  incorporation_date date,
  brand text,
  website text,
  email text,
  email_source text,
  phone text,
  address text,
  city text,
  postcode text,
  registered_postcode text,
  lat double precision,
  lon double precision,
  website_status text,
  website_title text,
  emails_found text[] not null default '{}',
  enriched_at timestamptz,
  icp_score numeric(5, 1),
  tier text check (tier in ('A', 'B', 'C', 'reject')),
  vertical_fit numeric(4, 3),
  score_reasons text[] not null default '{}',
  merge_confidence text,
  first_seen_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  unique (vertical, source_key),
  unique (vertical, company_number)
);

create index companies_vertical_tier_idx on public.companies (vertical, tier);
create index companies_email_idx on public.companies (lower(email)) where email is not null;
create index companies_postcode_idx on public.companies (postcode);
create index companies_match_name_idx on public.companies (match_name);

create table public.campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  vertical text not null,
  -- snapshot of the ICP/templates used, so results stay attributable
  settings jsonb not null default '{}',
  created_at timestamptz not null default now()
);

create table public.messages (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references public.campaigns (id) on delete restrict,
  company_id uuid not null references public.companies (id) on delete restrict,
  to_email text not null,
  variant_index integer,
  subject text,
  body text,
  channel text not null default 'email',
  provider text,
  provider_message_id text,
  provider_thread_id text,
  status text not null default 'queued' check (status in ('queued', 'sent', 'failed', 'skipped')),
  scheduled_for timestamptz,
  sent_at timestamptz,
  replied_at timestamptz,
  reply_sentiment text check (reply_sentiment in ('positive', 'maybe', 'negative')),
  appointment_at timestamptz,
  quote_value numeric(12, 2),
  sale_closed boolean not null default false,
  revenue numeric(12, 2),
  created_at timestamptz not null default now()
);

create index messages_campaign_idx on public.messages (campaign_id);
create index messages_company_idx on public.messages (company_id);
create index messages_thread_idx on public.messages (provider_thread_id) where provider_thread_id is not null;

create table public.suppressions (
  id uuid primary key default gen_random_uuid(),
  email text,
  domain text,
  reason text not null check (reason in ('unsubscribed', 'bounced', 'complained', 'dnd', 'manual')),
  source text,
  created_at timestamptz not null default now(),
  check (email is not null or domain is not null)
);

create unique index suppressions_email_idx on public.suppressions (lower(email)) where email is not null;
create unique index suppressions_domain_idx on public.suppressions (lower(domain)) where domain is not null;

create function public.set_updated_at() returns trigger
language plpgsql
set search_path = ''
as $$
begin
  new.updated_at = now();
  return new;
end;
$$;

create trigger companies_set_updated_at
before update on public.companies
for each row execute function public.set_updated_at();

alter table public.companies enable row level security;
alter table public.campaigns enable row level security;
alter table public.messages enable row level security;
alter table public.suppressions enable row level security;
