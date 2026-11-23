-- Watchdog health numbers (secret-guarded): posts waiting for approval and how long the oldest has waited.
create or replace function job_health(p_secret text)
returns table (pending int, oldest_pending_hours numeric, live int, alerts_active int)
language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  return query select
    (select count(*)::int from listings where status = 'pending'),
    (select round(extract(epoch from now() - min(created_at)) / 3600, 1) from listings where status = 'pending'),
    (select count(*)::int from listings where status = 'live'),
    (select count(*)::int from room_alerts where active and chat_id is not null);
end $$;
revoke all on function job_health(text) from public;
grant execute on function job_health(text) to anon;
