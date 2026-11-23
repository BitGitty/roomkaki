-- Landlord tool: views per listing for the signed-in poster only (from the /ev/open/<id> events).
create index if not exists pageviews_path on pageviews (path) where site = 'roomkaki';
create or replace function my_listing_views()
returns table (listing_id bigint, views bigint, views_7d bigint)
language sql security definer set search_path = public as $$
  select l.id,
         count(p.*) filter (where p.path is not null),
         count(p.*) filter (where p.ts > now() - interval '7 days')
  from listings l
  left join pageviews p on p.site = 'roomkaki' and p.path = '/ev/open/' || l.id
  where l.poster_id = auth.uid()
  group by l.id
$$;
revoke all on function my_listing_views() from public;
grant execute on function my_listing_views() to authenticated;
