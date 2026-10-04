-- Send engine: everything needed to send cold email safely and stop
-- immediately when something goes wrong.
--
-- * messages.idempotency_key (campaign:company:step) makes a double send
--   impossible even if a run is repeated or two runs overlap.
-- * 'sending' is claimed in its own transaction before the provider call;
--   a crash mid-send leaves the row in 'sending' (never retried
--   automatically) rather than risking a second email.
-- * campaigns.status gates which campaigns may send at all; send_controls
--   is the global kill switch (starts OFF).
-- * replies.category drives suppression and the human review queue.
-- * call/sample/pilot events record the rest of the funnel so tests (copy,
--   offer, price) are judged on downstream outcomes, not just replies.

alter table public.messages drop constraint messages_status_check;
alter table public.messages add constraint messages_status_check
  check (status in ('queued', 'sending', 'sent', 'failed', 'skipped', 'cancelled'));

alter table public.messages
  add column idempotency_key text,
  add column mailbox text,
  add column rfc_message_id text,
  add column skip_reason text,
  add column bounced_at timestamptz;

create unique index messages_idempotency_idx on public.messages (idempotency_key) where idempotency_key is not null;
create index messages_due_idx on public.messages (scheduled_for) where status = 'queued';
create index messages_mailbox_sent_idx on public.messages (mailbox, sent_at) where status = 'sent';

alter table public.campaigns
  add column status text not null default 'draft' check (status in ('draft', 'active', 'paused', 'done'));

create table public.send_controls (
  id boolean primary key default true check (id),
  sending_enabled boolean not null default false,
  paused_reason text,
  updated_at timestamptz not null default now()
);
insert into public.send_controls default values;

alter table public.replies
  add column mailbox text,
  add column category text,
  add column needs_human boolean not null default false,
  add column handled_at timestamptz,
  -- set by a human when the automatic category was wrong; results use it first
  add column human_category text;
create unique index replies_provider_message_idx on public.replies (mailbox, provider_message_id)
  where provider_message_id is not null;
create index replies_needs_human_idx on public.replies (received_at) where needs_human and handled_at is null;

alter table public.events drop constraint events_type_check;
alter table public.events add constraint events_type_check check (type in (
  'sourced', 'enriched', 'scored', 'queued', 'sent', 'bounced', 'opened', 'replied',
  'unsubscribed', 'appointment_booked', 'quote_sent', 'won', 'lost', 'note',
  'skipped', 'failed', 'suppressed', 'paused',
  -- Velarqo's own sales funnel after a reply (payload carries test arms, e.g. price quoted)
  'call_booked', 'call_held', 'sample_received', 'pilot_signed'
));

alter table public.send_controls enable row level security;
grant select, insert, update, delete on public.send_controls to velarqo_loader;
create policy loader_full_access on public.send_controls for all to velarqo_loader using (true) with check (true);
