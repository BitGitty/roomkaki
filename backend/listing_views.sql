-- Landlord tool: views per listing for the signed-in poster only.
-- Counts "open" events from track.js (site_events) plus the older /ev/open/<id> page-view rows (before 2026-11-23).
create index if not exists pageviews_path on pageviews (path) where site = 'roomkaki';
create index if not exists site_events_open on site_events (site, kind, label);
create or replace function my_listing_views()
returns table (listing_id bigint, views bigint, views_7d bigint)
language sql security definer set search_path = public as $$
  with ev as (
    select label::bigint as lid, ts from site_events
     where site = 'roomkaki' and kind = 'open' and label ~ '^[0-9]+$'
    union all
    select substring(path from '^/ev/open/([0-9]+)$')::bigint, ts from pageviews
     where site = 'roomkaki' and path ~ '^/ev/open/[0-9]+$')
  select l.id, count(ev.lid), count(ev.lid) filter (where ev.ts > now() - interval '7 days')
  from listings l left join ev on ev.lid = l.id
  where l.poster_id = auth.uid()
  group by l.id
$$;
revoke all on function my_listing_views() from public;
grant execute on function my_listing_views() to authenticated;
