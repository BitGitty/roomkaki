-- Anti-scraping (owner 2026-11-23: "we should be blocking bots and scraper on our web too"):
-- phone reveals are capped per account (20/day, existing) AND per network address (40/day), so making many
-- accounts from one connection doesn't bypass the cap. IP is stored only as a salted hash.
alter table contact_reveals add column if not exists ip_hash text;
create index if not exists contact_reveals_ip_ts on contact_reveals (ip_hash, created_at);

create or replace function reveal_contact(p_listing_id bigint)
returns text language plpgsql security definer set search_path = public as $$
declare v_phone text; v_user int; v_ip int; v_ip_hash text;
begin
  if auth.uid() is null then raise exception 'must be signed in'; end if;
  v_ip_hash := md5('rk-reveal-2026:' || split_part(coalesce(nullif(current_setting('request.headers', true), '')::json->>'x-forwarded-for', ''), ',', 1));
  select count(*) into v_user from contact_reveals where seeker_id = auth.uid() and created_at > now() - interval '24 hours';
  if v_user >= 20 then raise exception 'daily contact limit reached — try again tomorrow'; end if;
  select count(*) into v_ip from contact_reveals where ip_hash = v_ip_hash and created_at > now() - interval '24 hours';
  if v_ip >= 40 then raise exception 'too many contact requests from this network — try again tomorrow'; end if;
  insert into contact_reveals (listing_id, seeker_id, ip_hash)
    values (p_listing_id, auth.uid(), v_ip_hash)
    on conflict (listing_id, seeker_id) do nothing;
  select contact_phone into v_phone from listings where id = p_listing_id and status = 'live';
  return v_phone;
end $$;
grant execute on function reveal_contact(bigint) to authenticated;
