-- The app login (velarqo_loader) may add to the free-allowance counter and the
-- opt-out list, but never delete or rewrite them: a script bug or a stray
-- command must not reset the Places spend lock or "forget" an opt-out.
-- (Deleting a suppression on request is an admin action, done by hand.)

revoke delete on public.api_usage from velarqo_loader;
revoke delete, update on public.suppressions from velarqo_loader;
