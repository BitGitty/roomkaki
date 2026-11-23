-- RoomKaki Studio extra panel: room actions (opens, out-clicks, alerts, searches) + most-opened rooms.
-- Same owner-key check as studio_data (studio_keys).
create or replace function studio_room_actions(p_site text, p_key text, p_days int default 28)
returns json language plpgsql security definer set search_path = public as $$
declare ok boolean; d int := least(greatest(coalesce(p_days, 28), 1), 365);
begin
  select exists(select 1 from studio_keys where site = p_site and key_hash = encode(sha256(convert_to(p_key, 'UTF8')), 'hex')) into ok;
  if not ok then return null; end if;
  return json_build_object(
    'actions', (select coalesce(json_agg(x order by x.n desc), '[]') from (
        select kind, count(*) n from site_events where site = p_site and ts > now() - make_interval(days => d)
        group by kind) x),
    'rooms', (select coalesce(json_agg(y order by y.opens desc), '[]') from (
        select e.label::bigint id, l.title, count(*) opens from site_events e
        join listings l on l.id = e.label::bigint
        where e.site = p_site and e.kind = 'open' and e.label ~ '^[0-9]+$' and e.ts > now() - make_interval(days => d)
        group by e.label, l.title order by count(*) desc limit 10) y));
end $$;
revoke all on function studio_room_actions(text, text, int) from public;
grant execute on function studio_room_actions(text, text, int) to anon;
