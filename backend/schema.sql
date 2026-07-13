-- RoomKaki P1 schema (Supabase Postgres)
-- Trust v1 = verification signals + report SLA. No numeric trust scores (see MASTER_PLAN).

create table profiles (
  id uuid primary key references auth.users on delete cascade,
  display_name text not null check (char_length(display_name) between 2 and 60),
  phone_verified_at timestamptz,          -- set by OTP flow; NULL = unverified
  is_owner_claimed boolean default false, -- self-declared owner vs agent; shown transparently
  preferred_lang text not null default 'en' check (preferred_lang in ('en','my')),
  created_at timestamptz not null default now(),
  banned_at timestamptz
);

create table markets (                    -- config-not-code: one row per market
  id text primary key,                    -- 'sg'
  name text not null,                     -- 'Singapore'
  currency text not null,                 -- 'SGD'
  languages text[] not null,              -- {'en','my'}
  transit_lines jsonb not null,           -- {"EW":{"name":"East West","color":"#009645"},...}
  legal_notices jsonb not null,           -- {"hdb_min_stay_months":6,"condo_min_stay_months":3,...}
  active boolean not null default false
);

create table listings (
  id bigint generated always as identity primary key,
  market_id text not null references markets default 'sg',
  poster_id uuid not null references profiles,
  status text not null default 'pending'  -- moderation gate: nothing public without review
    check (status in ('pending','live','paused','rejected','removed','expired')),
  room_type text not null check (room_type in ('common','single','master','studio','whole_unit')),
  price_month integer not null check (price_month between 100 and 20000),
  title text not null check (char_length(title) between 8 and 100),
  description text not null check (char_length(description) <= 3000),
  title_i18n jsonb not null default '{}',        -- {"my": "..."} AI-translated, per market languages
  description_i18n jsonb not null default '{}',
  is_hdb boolean not null default true,          -- drives min-stay legal notice
  transit_line text,                             -- 'EW' — validated against market config in app layer
  station text,
  walk_minutes smallint check (walk_minutes between 0 and 60),
  area text not null,
  lat double precision, lng double precision,
  gender_pref text not null default 'any' check (gender_pref in ('any','female','male')),
  couple_ok boolean not null default false,
  cooking_ok boolean not null default false,
  aircon boolean not null default false,
  wifi boolean not null default true,
  available_from date,
  listed_by_owner boolean not null default false, -- mirrors poster claim at time of posting
  contact_phone text not null,                    -- revealed only via logged contact_reveals
  dedup_hash text,                                -- normalized text+price+area hash for duplicate detection
  created_at timestamptz not null default now(),
  updated_at timestamptz not null default now(),
  expires_at timestamptz not null default now() + interval '45 days'  -- stale listings auto-expire
);
create index on listings (market_id, status, price_month);
create index on listings (transit_line, station) where status = 'live';
create index on listings (dedup_hash);

create table listing_photos (
  id bigint generated always as identity primary key,
  listing_id bigint not null references listings on delete cascade,
  storage_path text not null,             -- Supabase Storage; EXIF stripped client-side
  position smallint not null default 0,
  moderation text not null default 'pending' check (moderation in ('pending','ok','rejected'))
);

create table contact_reveals (            -- Loop 2: every contact is logged on-platform
  id bigint generated always as identity primary key,
  listing_id bigint not null references listings,
  seeker_id uuid not null references profiles,
  created_at timestamptz not null default now(),
  unique (listing_id, seeker_id)          -- one reveal per seeker per listing; re-views free
);

create table reports (                    -- scam/report flow, <48h SLA
  id bigint generated always as identity primary key,
  listing_id bigint references listings,
  reported_profile uuid references profiles,
  reporter_id uuid references profiles,   -- nullable: anonymous reports allowed
  reason text not null check (reason in ('scam','fake_photos','already_rented','wrong_info','abusive','other')),
  detail text check (char_length(detail) <= 2000),
  status text not null default 'open' check (status in ('open','reviewing','actioned','dismissed')),
  created_at timestamptz not null default now(),
  resolved_at timestamptz
);
create index on reports (status, created_at);

create table favorites (
  profile_id uuid references profiles,
  listing_id bigint references listings on delete cascade,
  created_at timestamptz not null default now(),
  primary key (profile_id, listing_id)
);

create table moderation_log (             -- every admin action auditable
  id bigint generated always as identity primary key,
  actor text not null,                    -- 'auto' | admin uuid
  listing_id bigint, report_id bigint, profile_id uuid,
  action text not null,
  note text,
  created_at timestamptz not null default now()
);

-- RLS sketch (enforced in migration files):
--   listings: SELECT where status='live' for anon; owners see own any-status.
--   contact_phone: never selectable directly; exposed only via a security-definer
--     RPC reveal_contact(listing_id) that inserts into contact_reveals first.
--   reports: INSERT for authed; SELECT admin-only.
--   profiles: phone numbers never public; display_name + verification badges only.

insert into markets (id, name, currency, languages, transit_lines, legal_notices, active) values (
  'sg', 'Singapore', 'SGD', '{en,my}',
  '{"EW":{"name":"East West","color":"#009645"},"NS":{"name":"North South","color":"#d42e12"},"NE":{"name":"North East","color":"#9900aa"},"CC":{"name":"Circle","color":"#fa9e0d"},"DT":{"name":"Downtown","color":"#005ec4"},"TE":{"name":"Thomson-East Coast","color":"#9D5B25"}}',
  '{"hdb_min_stay_months":6,"condo_min_stay_months":3,"deposit_warning":true}',
  true
);
