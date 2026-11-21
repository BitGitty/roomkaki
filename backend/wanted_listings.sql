-- Room-wanted posts (owner 2026-11-21: "we should have for both type of audience").
-- 'offer' = room for rent (existing), 'wanted' = someone looking for a room.
-- Wanted posts reuse the same columns: price_month = budget, area = preferred area,
-- room_type = room they want. Same moderation + contact-reveal flow as offers.
alter table listings add column if not exists listing_kind text not null default 'offer'
  check (listing_kind in ('offer', 'wanted'));

create or replace view public_listings
with (security_invoker = false) as
  select id, market_id, poster_id, room_type, price_month, title, description,
         title_i18n, description_i18n, is_hdb, transit_line, station, walk_minutes,
         area, lat, lng, gender_pref, couple_ok, cooking_ok, aircon, wifi,
         available_from, listed_by_owner, created_at, source_url, listing_kind
  from listings
  where status = 'live';
grant select on public_listings to anon, authenticated;
