-- Lightweight first-party pageview analytics (RoomKaki + RightsAtlas share one table).
create table if not exists pageviews (
  id bigint generated always as identity primary key,
  site text not null,
  path text,
  referrer text,
  ts timestamptz not null default now()
);
create index if not exists pageviews_site_ts on pageviews (site, ts);

-- anon-callable, security-definer: the browser beacon calls this; no direct table access.
create or replace function track_view(p_site text, p_path text default null, p_ref text default null)
returns void
language plpgsql
security definer
set search_path = public
as $$
begin
  insert into pageviews (site, path, referrer)
  values (left(coalesce(p_site, '?'), 40), left(p_path, 300), left(nullif(p_ref, ''), 300));
end;
$$;

revoke all on function track_view(text, text, text) from public;
grant execute on function track_view(text, text, text) to anon;

-- keep the table private to clients; only service_role (my queries) reads it.
alter table pageviews enable row level security;
