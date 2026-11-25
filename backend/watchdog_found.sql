-- Watchdog jobs that used to need a chat session: list live FOUND listings, remove one whose source died.
create or replace function job_found_listings(p_secret text)
returns table (id bigint, source_url text) language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  return query select l.id, l.source_url from listings l where l.status = 'live' and l.source_url is not null;
end $$;

create or replace function job_remove_found(p_secret text, p_id bigint)
returns boolean language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  update listings set status = 'removed' where id = p_id and source_url is not null and status = 'live';  -- found only
  return found;
end $$;
revoke all on function job_found_listings(text), job_remove_found(text, bigint) from public;
grant execute on function job_found_listings(text), job_remove_found(text, bigint) to anon;
