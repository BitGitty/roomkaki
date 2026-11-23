-- Shared with RightsAtlas: add RoomKaki event kinds (open, out, alert) to the allow-list. Existing kinds unchanged.
create or replace function public.track_event(p_site text, p_kind text, p_label text default null, p_path text default null)
returns void language plpgsql security definer set search_path to 'public' as $$
begin
  if p_kind not in ('search', 'play_film', 'play_song', 'outbound', 'signup',   -- RightsAtlas
                    'open', 'out', 'alert') then                               -- RoomKaki (2026-11-23)
    return;
  end if;
  insert into site_events (site, kind, label, path)
  values (left(coalesce(p_site, '?'), 40), p_kind, left(lower(trim(p_label)), 120), left(p_path, 300));
end $$;
