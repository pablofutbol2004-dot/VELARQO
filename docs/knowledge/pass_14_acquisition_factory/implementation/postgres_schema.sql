-- Pass 14 canonical acquisition schema (Postgres/Supabase starting point)
-- Review RLS and retention policies before production.
create extension if not exists pgcrypto;

create table if not exists companies (
  id uuid primary key default gen_random_uuid(),
  company_number text unique,
  legal_name text,
  trading_name text,
  company_type text,
  company_status text,
  registered_postcode text,
  canonical_domain text,
  website_url text,
  phone text,
  icp_pass boolean,
  icp_score numeric,
  icp_reason_codes text[] default '{}',
  current_state text not null default 'DISCOVERED',
  qualification_version text,
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now()
);
create unique index if not exists companies_domain_unique on companies(lower(canonical_domain)) where canonical_domain is not null and canonical_domain <> '';

create table if not exists people (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  full_name text not null,
  job_title text,
  role_category text,
  role_confidence text,
  current_state text default 'ACTIVE',
  created_at timestamptz not null default now()
);

create table if not exists contact_points (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  person_id uuid references people(id) on delete set null,
  contact_type text not null check (contact_type in ('email','phone','generic_email','social','other')),
  contact_value text not null,
  verification_status text default 'not_checked',
  verification_provider text,
  verified_at timestamptz,
  suppressed boolean not null default false,
  suppression_reason text,
  created_at timestamptz not null default now(),
  unique(contact_type, contact_value)
);

create table if not exists source_evidence (
  id uuid primary key default gen_random_uuid(),
  entity_kind text not null,
  entity_id uuid not null,
  field_name text,
  raw_value text,
  source_type text not null,
  source_record_id text,
  source_url text,
  observed_at timestamptz not null default now(),
  confidence text
);

create table if not exists compliance_routes (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id) on delete cascade,
  contact_id uuid references contact_points(id) on delete cascade,
  subscriber_class text,
  entity_type_confidence text,
  personal_data_used boolean,
  lawful_basis_note text,
  privacy_notice_route text,
  opt_out_ready boolean not null default false,
  suppression_checked boolean not null default false,
  send_allowed text not null default 'review' check (send_allowed in ('true','false','review')),
  review_reason text,
  reviewed_at timestamptz,
  unique(company_id, contact_id)
);

create table if not exists suppressions (
  id uuid primary key default gen_random_uuid(),
  scope text not null check (scope in ('company','contact','contact_value','domain')),
  company_id uuid references companies(id),
  contact_id uuid references contact_points(id),
  contact_value text,
  reason text not null,
  source text,
  created_at timestamptz not null default now(),
  expires_at timestamptz
);

create table if not exists campaigns (
  id uuid primary key default gen_random_uuid(),
  name text not null,
  state text not null default 'draft',
  created_at timestamptz not null default now()
);

create table if not exists campaign_members (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id) on delete cascade,
  cohort_id text not null,
  company_id uuid not null references companies(id),
  person_id uuid references people(id),
  contact_id uuid not null references contact_points(id),
  score numeric,
  template_variant text,
  state text not null default 'COHORTED',
  assigned_at timestamptz not null default now(),
  unique(campaign_id, contact_id)
);

create table if not exists send_queue (
  id uuid primary key default gen_random_uuid(),
  campaign_id uuid not null references campaigns(id),
  campaign_member_id uuid not null references campaign_members(id),
  sequence_step int not null,
  scheduled_at timestamptz,
  sender_mailbox text,
  template_version text,
  idempotency_key text not null unique,
  state text not null default 'READY_TO_SEND',
  created_at timestamptz not null default now()
);

create table if not exists send_events (
  id uuid primary key default gen_random_uuid(),
  queue_id uuid not null references send_queue(id),
  event_type text not null,
  event_at timestamptz not null default now(),
  provider text,
  provider_message_id text,
  provider_status text,
  error_code text,
  raw_response_ref text
);

create table if not exists replies (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id),
  contact_id uuid references contact_points(id),
  campaign_id uuid references campaigns(id),
  received_at timestamptz not null default now(),
  reply_class text,
  sentiment text,
  manual_review boolean not null default true,
  conversation_created boolean not null default false,
  suppression_action boolean not null default false,
  notes text
);

create table if not exists enrichment_jobs (
  id uuid primary key default gen_random_uuid(),
  company_id uuid not null references companies(id),
  adapter text not null,
  job_type text not null,
  requested_at timestamptz not null default now(),
  completed_at timestamptz,
  status text not null default 'queued',
  attempts int not null default 0,
  error text,
  raw_response_ref text
);

create index if not exists idx_companies_state on companies(current_state);
create index if not exists idx_contacts_company on contact_points(company_id);
create index if not exists idx_queue_state_time on send_queue(state, scheduled_at);
create index if not exists idx_replies_company on replies(company_id, received_at desc);
