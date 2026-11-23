-- Multi-country readiness (owner 2026-11-23: "we should be ready but turn off for now").
-- Each market carries its own display config; only active markets are offered to visitors.
alter table markets add column if not exists ui jsonb not null default '{}';

update markets set ui = '{
  "symbol": "S$", "center": [1.3521, 103.8198], "zoom": 11, "transit_word": "MRT",
  "property_types": [["true", "HDB"], ["false", "Condo"]],
  "stay_note_true": "HDB rules: minimum {n}-month stay applies.",
  "stay_note_false": "Condo listing — minimum {n} months.",
  "min_stay_true": 6, "min_stay_false": 3,
  "price_max": 3000, "price_step": 50
}' where id = 'sg';

insert into markets (id, name, currency, languages, transit_lines, legal_notices, active, ui) values
 ('th', 'Thailand', 'THB', '{en,my,th}',
  '{"SUK": {"name": "BTS Sukhumvit", "color": "#7fbf3f"},
    "SIL": {"name": "BTS Silom", "color": "#00703c"},
    "BLU": {"name": "MRT Blue", "color": "#1e4f9c"},
    "PUR": {"name": "MRT Purple", "color": "#6e3f98"},
    "YEL": {"name": "MRT Yellow", "color": "#e6b800"},
    "PNK": {"name": "MRT Pink", "color": "#e85fa5"},
    "ARL": {"name": "Airport Rail Link", "color": "#c8102e"}}',
  '{"deposit_warning": true}', false,
  '{"symbol": "฿", "center": [13.7563, 100.5018], "zoom": 11, "transit_word": "BTS/MRT",
    "property_types": [["true", "Apartment"], ["false", "House"]],
    "stay_note_true": "", "stay_note_false": "", "min_stay_true": 0, "min_stay_false": 0,
    "price_max": 30000, "price_step": 500}'),
 ('mm', 'Myanmar', 'MMK', '{en,my}', '{}',
  '{"deposit_warning": true}', false,
  '{"symbol": "K", "center": [16.8409, 96.1735], "zoom": 11, "transit_word": "",
    "property_types": [["true", "Apartment"], ["false", "House"]],
    "stay_note_true": "", "stay_note_false": "", "min_stay_true": 0, "min_stay_false": 0,
    "price_max": 2000000, "price_step": 50000}')
on conflict (id) do nothing;

-- read-only, non-sensitive market config for the site (active flag decides what visitors see)
create or replace view public_markets with (security_invoker = false) as
  select id, name, currency, languages, transit_lines, active, ui from markets;
grant select on public_markets to anon, authenticated;

-- posting into a switched-off market is refused at the database, whatever the client does
create or replace function enforce_active_market() returns trigger
language plpgsql security definer set search_path = public as $$
begin
  if auth.role() is distinct from 'authenticated' then return new; end if;   -- admin/service path
  if not exists (select 1 from markets where id = new.market_id and active) then
    raise exception 'this country is not open on RoomKaki yet';
  end if;
  return new;
end $$;
drop trigger if exists trg_active_market on listings;
create trigger trg_active_market before insert on listings
  for each row execute function enforce_active_market();
