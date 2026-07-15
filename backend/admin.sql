-- RoomKaki admin moderation: an is_admin flag + security-definer RPCs so an admin can
-- approve/reject pending listings from the browser. The moderation trigger blocks the
-- 'authenticated' role from setting status='live', so admins are whitelisted through it.
-- Safe to re-run.

alter table profiles add column if not exists is_admin boolean not null default false;

-- make the owner an admin (their auth uid)
update profiles set is_admin = true where id = '5679f37c-9fd1-46a1-a630-88588c91b615';

create or replace function admin_is() returns boolean
  language sql stable security definer set search_path = public as $$
  select coalesce((select is_admin from profiles where id = auth.uid()), false);
$$;

-- let admins (and service_role) bypass the self-publish block; everyone else is still gated
create or replace function enforce_listing_moderation()
returns trigger language plpgsql security definer set search_path = public as $$
begin
  if auth.role() is distinct from 'authenticated' then return new; end if;   -- admin/service bypass
  if coalesce((select is_admin from profiles where id = auth.uid()), false) then return new; end if;
  if tg_op = 'INSERT' then
    new.status := 'pending';
  elsif tg_op = 'UPDATE' and new.status = 'live' and old.status is distinct from 'live' then
    new.status := old.status;
  end if;
  return new;
end $$;

create or replace function admin_pending()
returns setof listings language plpgsql stable security definer set search_path = public as $$
begin
  if not admin_is() then raise exception 'not authorized'; end if;
  return query select * from listings where status = 'pending' order by created_at asc;
end $$;

create or replace function admin_moderate(p_listing_id bigint, p_status text)
returns text language plpgsql security definer set search_path = public as $$
begin
  if not admin_is() then raise exception 'not authorized'; end if;
  if p_status not in ('live', 'rejected', 'removed', 'pending', 'paused') then
    raise exception 'bad status %', p_status; end if;
  update listings set status = p_status, updated_at = now() where id = p_listing_id;
  insert into moderation_log (actor, listing_id, action, note)
    values (auth.uid()::text, p_listing_id, p_status, 'admin panel');
  return p_status;
end $$;

grant execute on function admin_is() to authenticated;
grant execute on function admin_pending() to authenticated;
grant execute on function admin_moderate(bigint, text) to authenticated;
