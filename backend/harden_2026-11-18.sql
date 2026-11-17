-- CRUCIBLE fixes 2026-11-18: reveal rate limit + storage bucket restrictions.

-- C5: cap contact reveals at 20 distinct listings per user per day (crucible: unlimited harvesting).
create or replace function reveal_contact(p_listing_id bigint)
returns text language plpgsql security definer set search_path = public as $$
declare v_phone text; v_today int;
begin
  if auth.uid() is null then raise exception 'must be signed in'; end if;
  select count(*) into v_today from contact_reveals
    where seeker_id = auth.uid() and created_at > now() - interval '24 hours';
  if v_today >= 20 then
    raise exception 'daily contact limit reached — try again tomorrow';
  end if;
  insert into contact_reveals (listing_id, seeker_id)
    values (p_listing_id, auth.uid())
    on conflict (listing_id, seeker_id) do nothing;
  select contact_phone into v_phone from listings where id = p_listing_id and status = 'live';
  return v_phone;
end $$;
grant execute on function reveal_contact(bigint) to authenticated;

-- C39 (defensive): photos bucket only accepts images, max 5MB per file.
update storage.buckets
   set allowed_mime_types = array['image/jpeg','image/png','image/webp'],
       file_size_limit = 5242880
 where id = 'listing-photos';
