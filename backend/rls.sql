-- RoomKaki RLS + public read view + photo storage. Safe to re-run.

-- Ensure RLS on (auto-RLS already enabled these; explicit for clarity)
alter table profiles         enable row level security;
alter table listings         enable row level security;
alter table listing_photos   enable row level security;
alter table contact_reveals  enable row level security;
alter table reports          enable row level security;
alter table favorites        enable row level security;

-- PROFILES: a user sees and manages only their own row
drop policy if exists p_profile_self_sel on profiles;
create policy p_profile_self_sel on profiles for select using (auth.uid() = id);
drop policy if exists p_profile_self_ins on profiles;
create policy p_profile_self_ins on profiles for insert with check (auth.uid() = id);
drop policy if exists p_profile_self_upd on profiles;
create policy p_profile_self_upd on profiles for update using (auth.uid() = id);

-- LISTINGS: owners manage their own; NO public policy on the base table
-- (contact_phone must never leak — public reads go through the view below)
drop policy if exists p_listing_owner_sel on listings;
create policy p_listing_owner_sel on listings for select using (auth.uid() = poster_id);
drop policy if exists p_listing_owner_ins on listings;
create policy p_listing_owner_ins on listings for insert with check (auth.uid() = poster_id);
drop policy if exists p_listing_owner_upd on listings;
create policy p_listing_owner_upd on listings for update using (auth.uid() = poster_id);

-- PHOTOS: owner manages photos of their own listings
drop policy if exists p_photo_owner_all on listing_photos;
create policy p_photo_owner_all on listing_photos for all
  using (exists (select 1 from listings l where l.id = listing_id and l.poster_id = auth.uid()))
  with check (exists (select 1 from listings l where l.id = listing_id and l.poster_id = auth.uid()));

-- REPORTS: any authenticated user may file a report; reads are admin-only (no select policy)
drop policy if exists p_report_ins on reports;
create policy p_report_ins on reports for insert to authenticated with check (true);

-- FAVORITES: a user manages only their own favorites
drop policy if exists p_fav_self on favorites;
create policy p_fav_self on favorites for all using (auth.uid() = profile_id) with check (auth.uid() = profile_id);

-- CONTACT REVEALS: a user may log their own reveal
drop policy if exists p_reveal_ins on contact_reveals;
create policy p_reveal_ins on contact_reveals for insert to authenticated with check (auth.uid() = seeker_id);

-- MODERATION GATE: RLS alone can't stop an owner from POSTing/ PATCHing status='live'
-- (their insert/update policy is row-scoped, not column-scoped). This trigger makes
-- 'live' reachable ONLY by an admin (service_role / dashboard). End users may create,
-- edit, pause and remove their own listings, but never self-approve to public.
create or replace function enforce_listing_moderation()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if auth.role() is distinct from 'authenticated' then return new; end if;  -- admin/service bypass
  if tg_op = 'INSERT' then
    new.status := 'pending';                       -- nothing enters public on creation
  elsif tg_op = 'UPDATE' and new.status = 'live' and old.status is distinct from 'live' then
    new.status := old.status;                      -- refuse self-publish; edits to an already-live row keep it live
  end if;
  return new;
end $$;
drop trigger if exists trg_listing_moderation on listings;
create trigger trg_listing_moderation before insert or update on listings
  for each row execute function enforce_listing_moderation();

-- PUBLIC READ VIEW: live listings WITHOUT contact_phone. Anon-safe.
create or replace view public_listings
with (security_invoker = false) as
  select id, market_id, poster_id, room_type, price_month, title, description,
         title_i18n, description_i18n, is_hdb, transit_line, station, walk_minutes,
         area, lat, lng, gender_pref, couple_ok, cooking_ok, aircon, wifi,
         available_from, listed_by_owner, created_at
  from listings
  where status = 'live';
grant select on public_listings to anon, authenticated;

-- PUBLIC PHOTOS: photo rows for LIVE listings only (the file bytes are already public in the
-- listing-photos bucket; this exposes the storage_path so the client can build the URL).
create or replace view public_listing_photos
with (security_invoker = false) as
  select p.listing_id, p.storage_path, p.position
  from listing_photos p join listings l on l.id = p.listing_id
  where l.status = 'live';
grant select on public_listing_photos to anon, authenticated;

-- reveal_contact: security-definer RPC — logs the reveal, then returns the phone.
create or replace function reveal_contact(p_listing_id bigint)
returns text language plpgsql security definer set search_path = public as $$
declare v_phone text;
begin
  if auth.uid() is null then raise exception 'must be signed in'; end if;
  insert into contact_reveals (listing_id, seeker_id)
    values (p_listing_id, auth.uid())
    on conflict (listing_id, seeker_id) do nothing;
  select contact_phone into v_phone from listings where id = p_listing_id and status = 'live';
  return v_phone;
end $$;
grant execute on function reveal_contact(bigint) to authenticated;

-- PHOTO STORAGE bucket (public read; authed users upload under their own folder)
insert into storage.buckets (id, name, public)
  values ('listing-photos', 'listing-photos', true)
  on conflict (id) do nothing;

drop policy if exists p_photos_public_read on storage.objects;
create policy p_photos_public_read on storage.objects for select
  using (bucket_id = 'listing-photos');
drop policy if exists p_photos_authed_write on storage.objects;
create policy p_photos_authed_write on storage.objects for insert to authenticated
  with check (bucket_id = 'listing-photos' and (storage.foldername(name))[1] = auth.uid()::text);
