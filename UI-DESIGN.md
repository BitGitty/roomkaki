# RoomKaki — UI design spec (v1 prototype)

## Design principles
1. **Trust-first visual language** — verification badges, owner/agent transparency,
   safety banners are FIRST-CLASS UI elements, not footnotes. Green = verified/owner.
2. **MRT is the mental map** — authentic line colors (EW green, NS red, NE purple,
   CC orange, DT blue, TE brown) as compact badges; station + walk-minutes on every card.
3. **Calm, airy, zero ad clutter** — the anti-ShweRooms: one accent color, generous
   whitespace, cards with soft shadows, no third-party banners ever on browse surfaces.
4. **Mobile-first** — bottom-sheet listing details, thumb-size chips, sticky header;
   desktop gets the same components in a grid.
5. **Bilingual by design** — Burmese title line shown under English on detail view;
   language toggle in header; full UI translation ships with backend.

## System
- Colors: brand teal `#0d9488` · amber accent `#f59e0b` · light `#f7f9f8` / dark
  `#0e1513` auto-switching · MRT line palette (authentic LTA colors)
- Type: system stack, 800-weight display, 15px body
- Components: chip filters (scrollable row) · listing card (photo, price-first,
  MRT badge, tag row, meta) · bottom sheet detail (photo, price, safety banner,
  facts grid, contact reveal, report) · map view (Leaflet/OSM, price popups)
- Voice: plain, warm, safety-conscious ("Find a room you can trust")

## Prototype scope (this build)
Static demo: 10 realistic seed listings · working client-side filters (type, MRT
line, gender, owner-only, max price, text search) · Cards/Map toggle with real
Singapore map · detail sheets with safety + HDB min-stay notices · EN with Burmese
accents. Post flow, auth, payments = backend phase.
