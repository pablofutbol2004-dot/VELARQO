-- Keep everything: raw source payloads, every website fetch, every scoring
-- run, people, replies and a per-lead event timeline. The companies table
-- stays the "current best view"; these tables are the history behind it,
-- so scoring/ICP changes and experiments can be compared after the fact.

alter table public.companies
  add column score_breakdown jsonb not null default '{}',
  add column icp_version text,
  add column extra jsonb not null default '{}';

-- One row per record per source, exactly as fetched (all OSM tags, all
-- Companies House columns). Re-sourcing updates payload + last_seen_at.
create table public.source_records (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references public.companies (id) on delete set null,
  source text not null check (source in ('osm', 'companies_house', 'manual', 'client_import')),
  source_id text not null,
  payload jsonb not null,
  first_seen_at timestamptz not null default now(),
  last_seen_at timestamptz not null default now(),
  unique (source, source_id)
);
create index source_records_company_idx on public.source_records (company_id);

create table public.website_snapshots (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  url text not null,
  status text not null,
  title text,
  text text,
  emails_found text[] not null default '{}',
  fetched_at timestamptz not null default now()
);
create index website_snapshots_company_idx on public.website_snapshots (company_id, fetched_at desc);

-- icp_version = hash of the ICP config used, so score changes can be
-- attributed to config changes rather than guessed at.
create table public.score_history (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  icp_version text not null,
  score numeric(5, 1),
  tier text,
  vertical_fit numeric(4, 3),
  breakdown jsonb not null default '{}',
  reasons text[] not null default '{}',
  scored_at timestamptz not null default now()
);
create index score_history_company_idx on public.score_history (company_id, scored_at desc);
create index score_history_version_idx on public.score_history (icp_version);

create table public.contacts (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references public.companies (id) on delete cascade,
  full_name text,
  role text,
  email text,
  phone text,
  source text,
  is_primary boolean not null default false,
  created_at timestamptz not null default now()
);
create index contacts_company_idx on public.contacts (company_id);
create unique index contacts_company_email_idx on public.contacts (company_id, lower(email)) where email is not null;

alter table public.messages
  add column contact_id uuid references public.contacts (id) on delete set null,
  add column sequence_step integer not null default 1,
  add column in_reply_to_message_id uuid references public.messages (id) on delete set null;
create index messages_contact_idx on public.messages (contact_id);

create table public.replies (
  id uuid primary key default gen_random_uuid(),
  message_id uuid references public.messages (id) on delete set null,
  company_id uuid references public.companies (id) on delete set null,
  from_email text not null,
  subject text,
  body text,
  sentiment text check (sentiment in ('positive', 'maybe', 'negative')),
  classification jsonb not null default '{}',
  provider_message_id text,
  received_at timestamptz not null default now()
);
create index replies_message_idx on public.replies (message_id);
create index replies_company_idx on public.replies (company_id);

create table public.events (
  id uuid primary key default gen_random_uuid(),
  company_id uuid references public.companies (id) on delete cascade,
  message_id uuid references public.messages (id) on delete set null,
  type text not null check (type in (
    'sourced', 'enriched', 'scored', 'queued', 'sent', 'bounced', 'opened', 'replied',
    'unsubscribed', 'appointment_booked', 'quote_sent', 'won', 'lost', 'note'
  )),
  payload jsonb not null default '{}',
  occurred_at timestamptz not null default now()
);
create index events_company_idx on public.events (company_id, occurred_at desc);
create index events_message_idx on public.events (message_id);
create index events_type_idx on public.events (type, occurred_at desc);

alter table public.source_records enable row level security;
alter table public.website_snapshots enable row level security;
alter table public.score_history enable row level security;
alter table public.contacts enable row level security;
alter table public.replies enable row level security;
alter table public.events enable row level security;

-- security_invoker: the view runs with the caller's rights, so it can't
-- be used to read around RLS via the public API.
create view public.variant_performance
with (security_invoker = true) as
select
  m.campaign_id,
  c.name as campaign_name,
  m.variant_index,
  count(*) filter (where m.status = 'sent') as sent,
  count(m.replied_at) as replies,
  count(*) filter (where m.reply_sentiment = 'positive') as positive_replies,
  count(m.appointment_at) as appointments,
  count(*) filter (where m.sale_closed) as sales,
  coalesce(sum(m.revenue), 0) as revenue,
  round(count(m.replied_at)::numeric / nullif(count(*) filter (where m.status = 'sent'), 0), 4) as reply_rate,
  round(count(m.appointment_at)::numeric / nullif(count(*) filter (where m.status = 'sent'), 0), 4) as appointment_rate
from public.messages m
join public.campaigns c on c.id = m.campaign_id
group by m.campaign_id, c.name, m.variant_index;
