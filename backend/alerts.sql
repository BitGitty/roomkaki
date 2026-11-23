-- Room alerts on Telegram (owner go 2026-11-23: AI-proof repeat traffic).
-- Visitor saves filters -> gets a token -> opens t.me/RoomKakiBot?start=<token> -> the bot job links their chat.
-- The job runs on GitHub with ONLY a random job secret (no DB password leaves Supabase).
create table if not exists room_alerts (
  id bigint generated always as identity primary key,
  token text not null unique default encode(gen_random_bytes(9), 'hex'),
  market_id text not null default 'sg',
  listing_kind text not null default 'offer' check (listing_kind in ('offer', 'wanted')),
  query text check (char_length(query) <= 80),
  max_price integer check (max_price is null or max_price between 1 and 10000000),
  chat_id bigint,
  active boolean not null default true,
  last_listing_id bigint not null default 0,
  ip_hash text,
  created_at timestamptz not null default now()
);
alter table room_alerts enable row level security;          -- no policies: only the RPCs below touch it
create table if not exists job_secrets (name text primary key, secret text not null);
alter table job_secrets enable row level security;

-- visitor: create an alert (anon), max 10 per network per hour
create or replace function create_alert(p_market text, p_kind text, p_query text, p_max_price integer)
returns text language plpgsql security definer set search_path = public as $$
declare v_ip text; v_n int; v_token text; v_start bigint;
begin
  v_ip := md5('rk-alert-2026:' || split_part(coalesce(nullif(current_setting('request.headers', true), '')::json->>'x-forwarded-for', ''), ',', 1));
  select count(*) into v_n from room_alerts where ip_hash = v_ip and created_at > now() - interval '1 hour';
  if v_n >= 10 then raise exception 'too many alerts — try again later'; end if;
  if not exists (select 1 from markets where id = p_market and active) then raise exception 'market not open'; end if;
  select coalesce(max(id), 0) into v_start from listings;      -- only rooms posted AFTER signing up
  insert into room_alerts (market_id, listing_kind, query, max_price, ip_hash, last_listing_id)
  values (p_market, coalesce(p_kind, 'offer'), nullif(left(btrim(p_query), 80), ''), p_max_price, v_ip, v_start)
  returning token into v_token;
  return v_token;
end $$;
revoke all on function create_alert(text, text, text, integer) from public;
grant execute on function create_alert(text, text, text, integer) to anon, authenticated;

-- job helpers: every call must carry the job secret
create or replace function job_ok(p_secret text) returns boolean language sql security definer set search_path = public
as $$ select exists (select 1 from job_secrets where name = 'alerts' and secret = p_secret) $$;

create or replace function job_link_alert(p_secret text, p_token text, p_chat bigint)
returns text language plpgsql security definer set search_path = public as $$
declare v room_alerts;
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  update room_alerts set chat_id = p_chat, active = true where token = p_token returning * into v;
  if v.id is null then return null; end if;
  return coalesce(v.query, 'any area') || ' · ' || v.listing_kind || coalesce(' · max ' || v.max_price, '');
end $$;

create or replace function job_stop_alerts(p_secret text, p_chat bigint)
returns int language plpgsql security definer set search_path = public as $$
declare n int;
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  update room_alerts set active = false where chat_id = p_chat and active;
  get diagnostics n = row_count;
  return n;
end $$;

-- new live listings matching each linked alert (words all present in title/area/station/description)
create or replace function job_alert_matches(p_secret text)
returns table (alert_id bigint, chat_id bigint, listing_id bigint, title text, price integer, area text, station text, kind text)
language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  return query
  select a.id, a.chat_id, l.id, l.title, l.price_month, l.area, l.station, l.listing_kind
  from room_alerts a
  join listings l on l.status = 'live' and l.market_id = a.market_id and l.listing_kind = a.listing_kind
                 and l.id > a.last_listing_id
                 and (a.max_price is null or l.price_month <= a.max_price)
                 and (a.query is null or not exists (
                      select 1 from regexp_split_to_table(lower(a.query), '\s+') w
                      where w <> '' and position(w in lower(l.title || ' ' || l.area || ' ' || coalesce(l.station, '') || ' ' || l.description)) = 0))
  where a.active and a.chat_id is not null
  order by a.id, l.id
  limit 200;
end $$;

create or replace function job_mark_sent(p_secret text, p_alert bigint, p_listing bigint)
returns void language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  update room_alerts set last_listing_id = greatest(last_listing_id, p_listing) where id = p_alert;
end $$;

revoke all on function job_ok(text) from public;
revoke all on function job_link_alert(text, text, bigint), job_stop_alerts(text, bigint),
                 job_alert_matches(text), job_mark_sent(text, bigint, bigint) from public;
grant execute on function job_link_alert(text, text, bigint), job_stop_alerts(text, bigint),
                 job_alert_matches(text), job_mark_sent(text, bigint, bigint) to anon;
