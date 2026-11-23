-- Small key/value memory for the Telegram job (what was already posted to the channel), secret-guarded.
create table if not exists job_state (key text primary key, value text not null, updated_at timestamptz default now());
alter table job_state enable row level security;

create or replace function job_get_state(p_secret text, p_key text) returns text
language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  return (select value from job_state where key = p_key);
end $$;

create or replace function job_set_state(p_secret text, p_key text, p_value text) returns void
language plpgsql security definer set search_path = public as $$
begin
  if not job_ok(p_secret) then raise exception 'denied'; end if;
  insert into job_state (key, value) values (p_key, p_value)
  on conflict (key) do update set value = excluded.value, updated_at = now();
end $$;

revoke all on function job_get_state(text, text), job_set_state(text, text, text) from public;
grant execute on function job_get_state(text, text), job_set_state(text, text, text) to anon;
