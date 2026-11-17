-- Found listings (2026-11-17): temporary supply bootstrap. Rooms found on PUBLIC posts elsewhere,
-- listed with a link to the original post instead of republishing the landlord's phone number.
-- Removed as organic supply arrives; cron re-checks source links and removes stale ones.
alter table listings add column if not exists source_url text;

create or replace view public_listings
with (security_invoker = false) as
  select id, market_id, poster_id, room_type, price_month, title, description,
         title_i18n, description_i18n, is_hdb, transit_line, station, walk_minutes,
         area, lat, lng, gender_pref, couple_ok, cooking_ok, aircon, wifi,
         available_from, listed_by_owner, created_at, source_url
  from listings
  where status = 'live';
grant select on public_listings to anon, authenticated;
