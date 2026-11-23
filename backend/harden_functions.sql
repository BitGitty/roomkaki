-- Security review 2026-11-23.
-- 1) Supabase grants EXECUTE to anon by default; these must be logged-in only (each already checks auth inside).
revoke execute on function job_ok(text) from anon, authenticated, public;
revoke execute on function my_listing_views() from anon, public;
revoke execute on function reveal_contact(bigint) from anon, public;
revoke execute on function admin_moderate(bigint, text) from anon, public;
revoke execute on function admin_pending() from anon, public;
grant execute on function my_listing_views(), reveal_contact(bigint), admin_moderate(bigint, text), admin_pending() to authenticated;

-- 2) Flood cap on the anonymous tracking writers (shared with RightsAtlas): a bot cannot bloat the database.
--    1,000 writes/minute across all sites is far above real traffic; extra writes are silently dropped.
create or replace function public.track_view3(p_site text, p_path text default null, p_ref text default null,
  p_kind text default null, p_utm text default null, p_visit text default null, p_device text default null,
  p_tz text default null, p_returning boolean default null)
returns bigint language plpgsql security definer set search_path to 'public' as $$
declare v_id bigint;
begin
  if (select count(*) from pageviews where ts > now() - interval '1 minute') > 1000 then return null; end if;
  insert into pageviews (site, path, referrer, kind, utm, visit, device, tz, is_return)
  values (left(coalesce(p_site,'?'),40), left(p_path,300), left(nullif(p_ref,''),300), left(p_kind,20),
          left(nullif(p_utm,''),60), left(p_visit,40), left(p_device,12), left(p_tz,60), p_returning)
  returning id into v_id;
  return v_id;
end $$;

create or replace function public.track_event(p_site text, p_kind text, p_label text default null, p_path text default null)
returns void language plpgsql security definer set search_path to 'public' as $$
begin
  if p_kind not in ('search', 'play_film', 'play_song', 'outbound', 'signup',   -- RightsAtlas
                    'open', 'out', 'alert') then                               -- RoomKaki
    return;
  end if;
  if (select count(*) from site_events where ts > now() - interval '1 minute') > 1000 then return; end if;
  insert into site_events (site, kind, label, path)
  values (left(coalesce(p_site, '?'), 40), p_kind, left(lower(trim(p_label)), 120), left(p_path, 300));
end $$;
create index if not exists pageviews_ts on pageviews (ts);
create index if not exists site_events_ts on site_events (ts);
