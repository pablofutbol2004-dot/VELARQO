-- Second review of the pilot delivery code (2026-10-11).
-- credit_reversal: a credited no-show who later rebooks/attends is charged
--   again (agreement: a rebook is still one booked survey).
-- booked_at: when the survey a line refers to was booked, so the weekly cap
--   is applied per ISO week of the booking, not per invoice run.

alter table public.invoice_lines drop constraint invoice_lines_kind_check;
alter table public.invoice_lines add constraint invoice_lines_kind_check
  check (kind in ('booked', 'no_show_credit', 'credit_reversal'));
alter table public.invoice_lines add column booked_at timestamptz;
