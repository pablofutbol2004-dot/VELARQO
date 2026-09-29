-- Dedicated least-privilege login for Velarqo's backend scripts (sourcing,
-- enrichment, scoring, sending). Full access to Velarqo's public tables
-- only - no auth schema, no storage, no role management. The password is
-- set out-of-band (a SCRAM verifier generated on the machine that holds
-- the plaintext in its gitignored .env) and is deliberately not in git.
--
-- RLS stays on: this role gets an explicit allow-all policy per table;
-- anon/authenticated (the public API keys) still get nothing.

create role velarqo_loader login noinherit;

grant usage on schema public to velarqo_loader;
grant select, insert, update, delete on all tables in schema public to velarqo_loader;
alter default privileges for role postgres in schema public
  grant select, insert, update, delete on tables to velarqo_loader;

create policy loader_full_access on public.companies for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.campaigns for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.messages for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.suppressions for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.source_records for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.website_snapshots for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.score_history for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.contacts for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.replies for all to velarqo_loader using (true) with check (true);
create policy loader_full_access on public.events for all to velarqo_loader using (true) with check (true);
