# RoomKaki — Master Plan (merged, final)
*"Rent safely." — the trusted room platform for Singapore's communities.
Merged: my proposal (floor: costs/legal/ops/gates) + Analysis 1 "trust platform"
(trust-as-product, loops, config-driven expansion) + Analysis 2 "RoomNest"
(supply incentives, community partnerships, budget honesty) + 10-attack
corrections applied to each. 2026-07-13.
Brand: **RoomKaki** · launch framing: "RoomKaki Singapore — Burmese community beta".
Naming evidence (RDAP 2026-07-13): roomnest.com, nestroom.com, nestlah.com,
shwenest.com, roomatlas.com ALL REGISTERED · roomkaki.com AVAILABLE ·
myannest.com available but hard-codes one community (rejected on both analyses'
own config-not-code principle).*

## Positioning
We do not sell room search. We sell **renting safely**. Every surface communicates:
verified posters, owner/agent transparency, scam education, report-and-response.
Beachhead: Burmese community, all of Singapore (community wedge, NOT geography wedge).

## The three loops every feature must feed
L1 Liquidity: listings → renters → landlords → listings
L2 Trust: reports → faster takedowns → safer feel → more users → more reports
L3 Retention: saved searches/alerts → return visits → faster matches → word of mouth

## Architecture (config-not-code from day 1)
- Market config: {city, languages[], transit system+colors, legal notices, currency}
  — adding Kuala Lumpur or a new community = config + translations, not a rebuild.
- Stack: SvelteKit/Next on Cloudflare Pages · Supabase (Postgres/Auth/Storage, free
  tier) · Firebase phone OTP · Leaflet/OSM · LLM batch translation (me)
- Trust v1 = verification SIGNALS (phone ✓, doc ✓ later) + report SLA. NO numeric
  trust scores until real history exists (defamation-safe by design).
- Contact = logged in-app reveal (feeds L2) with WhatsApp deep-link as secondary.
- AI v1: auto-translation (EN↔MY first), duplicate detection, listing-quality assist.
  AI v2 (post-data): price guidance, NL search, image QA. Never "scam probability"
  labels on named people.
- Moderation: automation-first queue, human budget ≤30 min/day.

## Design system (locked by approved prototype)
Teal `#0d9488` single accent · emerald=trust · amber=warnings · light/dark auto ·
MRT badges in authentic LTA colors · card grid + map toggle · bottom-sheet details ·
safety banner on every listing · HDB min-stay auto-notices · Airbnb-clean, zero ads
on browse surfaces. (Prototype = D:\roomkaki, live filters/map/sheets working.)

## Legal rails (Singapore)
Classifieds venue only (no agency work — CEA boundary) · HDB 6-month minimum
surfaced per listing · PDPA: minimal data, consent, deletion · report-first scam
handling; no public accusations · immigration-status neutral.

## Monetization sequence (trust is never for sale)
M0 (beta→liquidity): everything free.
M1: featured placement + bump-ups (clearly labeled, never affects verification).
M2: services referrals (movers, internet, insurance) + community-business directory.
M3: employer housing packages; data products (rent index) only at volume + PDPA review.

## Roadmap
### P0 — this week (mostly done)
✅ Prototype approved-pending-review · ✅ legal review · ✅ market analysis
☐ roomkaki.com purchase (Cloudflare) · ☐ publish prototype for community feedback
☐ DB schema + market-config format

### P1 — MVP build (3–4 sessions, ~2 weeks calendar)
Auth (phone OTP) · listing CRUD + photo upload (compression, EXIF strip) ·
browse/search/filters/map (prototype UI, real data) · logged contact reveal +
WhatsApp deep-link · report flow + admin moderation queue · EN/MY UI + listing
auto-translation · seed tooling for concierge onboarding.
**Explicitly NOT in MVP:** chat, trust scores, payments, apps, price AI.

### P2 — Private beta (weeks 3–6)
User seeds 30–50 concierge listings via community network (his commitment ✓) ·
founding-landlord incentives: free featured placement for 3 months + referral
credit (adopted from Analysis 2) · outreach to Burmese associations, temples and
employers as seeding partners (adopted) · owner-initiated "bring your listing"
import tool — the OWNER pastes their own Carousell/FB post and confirms ownership
(NOT scraping; Analysis 2's auto-importer rejected as ToS/consent violation) ·
soft launch in 2–3 Burmese community groups · our video factory produces Burmese
"rent safely in SG" content as the demand pump · weekly KPI review (listings,
contacts, reports — adopted cadence) · iterate weekly.
**Gate G1 (week 6): ≥40 live listings AND ≥15 logged contacts/week AND ≥1 listing
posted organically (no concierge).** Miss → diagnose 2 weeks → pivot or park.

### P3 — Trust v1 + public launch (weeks 7–10)
Verification badge tiers (phone → doc) · reputation HISTORY (response rate,
listing age; still no scores) · duplicate detection · scam-report SLA <48h public
promise · guides/scam-education hub (video embeds) · public launch + press to
community media.

### P4 — Growth loops (months 3–4)
Saved searches + alerts (L3) · SEO area/MRT landing pages (long game, not the
plan's "50% organic in 6mo" fantasy) · referral mechanics · analytics dashboard.
**Gate G2 (month 4): 150+ active listings · 1,000 MAU · ≥25% listing→contact ·
scam reports resolved <48h.**

### P5 — Monetize (month 4+, post-G2): M1 featured listings live.
### P6 — Expansion (month 6+, post-revenue): language pack #2 (Tagalog or Bahasa)
= same city, new community · then city #2 evaluation. **Gate G3 (month 6):
first S$500 cumulative revenue OR 2,500 MAU** → expansion investment.

## Success metrics (honest tier)
North star: **successful contacts per week** (proxy for matches).
6-month realistic: 200–300 active listings · 1,500–2,500 MAU · 25% contact rate ·
<48h report resolution · 40% returning users. (The analysis's 5,000 MAU/6mo and
50% organic share were rejected as fantasy-tier for a single-community launch.)

## Ops & cost
Cash: ~US$10/yr domain · infra $0 at prototype scale, but honest beta budget
(Analysis 2's fair correction): SMS OTP ~S$0.05/send + AI translation ≈
US$10–30/mo once real traffic arrives — still pocket change, planned not denied ·
moderation ≤30 min/day automation-first · all recurring jobs on schedulers (house
pattern) · this is project #5: build slots come after the Aug 9 portfolio review
unless user reprioritizes (he chose: build now — accepted; documentaries/whiteboard
shift ~2 weeks).

## Rejected from Analysis 1 (with reasons)
22-week phased ceremony (solo+AI ships in days) · 200 pre-registered renters
pre-launch (impossible sequencing) · "East Singapore" wedge (contradicts supply
data) · day-1 trust scores (defamation + no data) · scam-probability AI at MVP
(liability) · WhatsApp-primary contact (kills the trust loop) · verified-landlord
subscription (selling trust) · 6-month organic/SEO dominance metrics (contradicts
its own cold-start thesis) · RoomAtlas name (collides with RightsAtlas; domain taken).

## Rejected from Analysis 2 (with reasons)
Carousell/FB auto-importer (ToS violation; "with consent" is hand-waving — replaced
with owner-initiated import) · Trust Score 0–100 at month 2 (same cold-data +
defamation paradox; also "score correlation with rentals" is unmeasurable — rentals
close off-platform) · in-app chat in MVP (Analysis 1 correctly said don't; moderation
burden + empty-inbox cold start) · 50 renter/20 landlord formal interviews weeks 1–2
(solo-founder ceremony; replaced with community-group survey + 5–10 chats during
seeding) · paid Meta/Google ads early (ads to an empty marketplace burn cash; defer
past G1) · $1–2k lawyer + platform liability insurance pre-validation (mis-sequenced;
disclaimers + CEA-safe positioning now, lawyer at monetization gate G2) · Mapbox
("better pricing" is false — Leaflet/OSM is $0) · Vercel + Supabase Pro (house stack
is Cloudflare Pages + Supabase free) · freelance dev/designer + no-code Bubble
(ignores the actual operating model: AI builder already shipping code) · gold "Shwe
nod" branding + ShweNest/MyanNest names (rides ShweRooms' brand = confusion/trademark
risk, and locks to one community) · "10k+ verified users" homepage stat at launch
(fake trust destroys trust) · NPS>40 at month 2 (meaningless sample size) ·
RoomNest/NestRoom/NestLah names (all .coms already registered — verified by RDAP).

## Adopted from Analysis 2
Founding-landlord incentives (free featured 3 months + referral credit) · community-
institution seeding partners (associations, temples, employers) · honest beta budget
line (OTP + AI translation costs) · weekly KPI review cadence · safety/education hub
linked from every page · multi-step post-listing wizard with translation preview ·
"don't measure success as better-ShweRooms-UI" framing (measure trust adoption +
successful contacts).
