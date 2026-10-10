-- Irish CRO open data is a source of raw company records (docs/IRELAND.md).
set lock_timeout = '20s';

alter table public.source_records drop constraint source_records_source_check;
alter table public.source_records add constraint source_records_source_check
  check (source = any (array['osm', 'companies_house', 'cro', 'manual', 'client_import']));
