-- Found-listings seed batch 1 (2026-11-17). 5 fresh public posts (Oct-Nov 2026), area-level coords only.
-- Phones NOT copied; renters use "View original post". Poster = owner profile (admin concierge).
insert into listings
  (market_id, poster_id, status, room_type, price_month, title, description,
   is_hdb, transit_line, station, walk_minutes, area, lat, lng,
   gender_pref, couple_ok, cooking_ok, aircon, wifi, listed_by_owner, contact_phone, source_url)
values
  ('sg', '5679f37c-9fd1-46a1-a630-88588c91b615', 'live', 'common', 500,
   'Common room near City Hall MRT, Bain Street',
   'Shared room at Bras Basah Complex near Peninsula Plaza and Chijmes. Male tenant, no cooking. Found on a public listing - tap "View original post" to contact the poster directly.',
   true, 'EW', 'City Hall', 5, 'Bras Basah', 1.2966, 103.8520,
   'male', false, false, false, true, false, 'see original post',
   'https://burmaspaces.com/rooms/6ad8e04b1eca4dd56f6df87e'),

  ('sg', '5679f37c-9fd1-46a1-a630-88588c91b615', 'live', 'common', 520,
   'Common room in Woodlands HDB near Marsiling MRT',
   'Common room at Woodlands St 31, shared washing machine, fridge and WiFi. Female tenants, light cooking only, no overnight guests. Updated 11 Nov 2026, available now. Found on a public listing - tap "View original post" to contact the poster directly.',
   true, 'NS', 'Marsiling', 12, 'Woodlands', 1.4382, 103.7890,
   'female', false, true, false, true, false, 'see original post',
   'https://burmaspaces.com/rooms/6af47a42b73026c106afb776'),

  ('sg', '5679f37c-9fd1-46a1-a630-88588c91b615', 'live', 'common', 500,
   'Common room near Lakeside MRT, Ho Ching Road',
   'Shared room for 2 in a quiet 4-person household, PUB inclusive, aircon. Male tenant, no cooking, no overnight guests. Posted 9 Nov 2026, available now. Found on a public listing - tap "View original post" to contact the poster directly.',
   true, 'EW', 'Lakeside', 8, 'Jurong West', 1.3340, 103.7200,
   'male', false, false, true, true, false, 'see original post',
   'https://burmaspaces.com/rooms/698dc4c80dac2fbd98aed8ab'),

  ('sg', '5679f37c-9fd1-46a1-a630-88588c91b615', 'live', 'common', 520,
   'Furnished common room, 216 Yishun St 21, 5 min to MRT',
   'Fully furnished common room with aircon, WiFi and induction cooking allowed, utilities included. Female only. 5-minute walk to Yishun MRT. Found on a public listing - tap "View original post" to contact the poster directly.',
   true, 'NS', 'Yishun', 5, 'Yishun', 1.4300, 103.8350,
   'female', false, true, true, true, false, 'see original post',
   'https://www.99.co/singapore/rooms/property/216-yishun-street-21-hdb-WHD275yXMPyBaVawv7E24a'),

  ('sg', '5679f37c-9fd1-46a1-a630-88588c91b615', 'live', 'common', 500,
   'Common room bed-space at 54 Geylang Bahru',
   'Bed-space in a shared common room, WiFi included, immediate move-in. Male tenant, no cooking except boiling water. 7-minute walk to Geylang Bahru MRT. Found on a public listing - tap "View original post" to contact the poster directly.',
   true, 'DT', 'Geylang Bahru', 7, 'Geylang Bahru', 1.3210, 103.8710,
   'male', false, false, false, true, false, 'see original post',
   'https://www.99.co/singapore/rooms/property/54-geylang-bahru-hdb-kekBZLbCrpZUs5dtwkEWtb');
