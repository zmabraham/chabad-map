# Chabad Historical Map — Project Context

> **You are picking up this project mid-stream.** Read this file in full before doing anything. Most decisions are already made and documented; your job is to build, not to redesign.

## What this is

An interactive web app that shows the geographic, temporal, and biographical history of Chabad-Lubavitch chassidic figures across ~280 years (Baal Shem Tov era to present). Inspired by [theacharonim.com](https://theacharonim.com/) but focused on Chabad specifically.

The product has three views:

1. **Map** — pins for birth and death places of each person, click a pin to see who's there
2. **Timeline** — horizontal lifespan bars, color-coded by generation, filterable, click a bar to see the person
3. **Person page** — name (Hebrew + English), dates, places, bio

That's the entire MVP. **Do not** add lineage trees, family graphs, correspondence networks, stories collections, or anything else from the broader spec. Those are explicitly deferred. The discipline of this project has been ruthless scope reduction; preserve that.

## Status: data is done, app is not

- ✅ Data model designed and frozen for v1 (see `docs/spec.md`)
- ✅ 82 person records and 58 place records seeded (`data/persons.json`, `data/places.json`)
- ✅ Forward-compatible with the larger v0.1 schema in `docs/full-spec-future.md` (for later)
- ❌ No app code exists yet. **You are building it from scratch.**

## Quickstart

Run this first:

```bash
npm create vite@latest app -- --template react-ts
cd app
npm install
npm install maplibre-gl react-map-gl
npm install -D tailwindcss@latest @tailwindcss/postcss postcss autoprefixer
# Tailwind setup per current Tailwind docs
```

Then:

1. Copy `data/persons.json` and `data/places.json` into `app/src/data/`
2. Build the three views (see "Build order" below)
3. Commit early and often

## Stack constraints

- **React + TypeScript + Vite** — fast, no surprises, what the user prefers
- **MapLibre GL JS** (free, no token) for the map. Mapbox is acceptable if MapLibre proves limiting, but MapLibre first.
- **Tailwind** for styling
- **No backend.** Data is static JSON. Import directly.
- **No state management library** for MVP. `useState` and `useReducer` are enough.
- **No router library required.** A simple in-component view-switcher (`'map' | 'timeline' | 'person'`) is fine. Add `react-router` only if it becomes painful.

Reject any urge to install lodash, axios, moment, framer-motion, shadcn, or other framework-style libraries. They are not needed and they bloat the bundle.

## Data model (read `docs/spec.md` for full detail)

Two entities. Eleven fields on person, six on place.

**Person** has: `id`, `name_en`, `name_he`, `common_name`, `generation` (0-7), `birth_year`, `death_year`, `birth_place_id`, `death_place_id`, `role`, `bio`.

**Place** has: `id`, `name_en`, `name_he`, `lat`, `lng`, `modern_country`, `significance`.

Honest data gaps you must handle gracefully:
- **53 of 82 persons have null birth/death years.** They should still appear in search and on person pages but cannot be rendered on the timeline. Either hide them when timeline is active, or render them in a sidebar "undated figures" list. Do not invent dates.
- **12 persons have neither birth_place_id nor death_place_id.** Same treatment: omit from map, keep in search.
- Some persons have the same `birth_place_id` and `death_place_id`. Render one pin in that case, not two overlapping.

## Generation color coding

The timeline and map should color persons by generation. Suggested palette (adjust if needed for accessibility, but keep ordered):

| Gen | Era | Suggested color |
|---|---|---|
| 0 | Pre-Chabad (Baal Shem Tov, Maggid) | slate / neutral |
| 1 | Alter Rebbe (1745-1812) | indigo |
| 2 | Mitteler Rebbe (1773-1827) | blue |
| 3 | Tzemach Tzedek (1789-1866) | teal |
| 4 | Maharash (1834-1882) | emerald |
| 5 | Rashab (1860-1920) | amber |
| 6 | Rayatz (1880-1950) | orange |
| 7 | The Rebbe (1902-1994) | red |

## Build order

Build vertically — one complete view, then the next. Do not scaffold all three half-built.

1. **Load and validate data.** Import the JSONs, log counts, confirm all place references resolve. (They do — but confirm in your dev console.)
2. **Map view (primary).** Render pins for every place that has at least one person born or died there. On pin click, show a side panel listing the persons associated with that place. Default map view: bounds of Eastern Europe + Israel + NYC.
3. **Person page.** When a user clicks a person from the map's side panel, show full details: both names, dates, both places (linked back to map), role, full bio.
4. **Timeline view.** Horizontal scrollable bars from 1700 to 2000+. Each bar = one person's lifespan. Color by generation. Click bar → person page.
5. **View switcher.** Tabs or buttons at top: Map / Timeline. Person page is a modal or detail panel that overlays either view.
6. **Search.** Simple input that filters by `common_name`, `name_en`, `name_he`. Match should be case-insensitive and tolerant of partial matches.

If you ship steps 1-3 first and the user can see something working, that's a win. Don't block on timeline before showing them the map.

## Hebrew handling

- Hebrew text must render right-to-left when displayed alone. Use `dir="rtl"` on Hebrew-only elements.
- Don't auto-detect language — the schema already separates `name_en` and `name_he` fields.
- Search should match against both Hebrew and English names.
- For Hebrew typography, Tailwind's default fonts are inadequate. Add a Hebrew font (Frank Ruhl Libre is a good default — Google Font, free) and use it specifically for Hebrew text via a utility class.

## Tone and sensitivity

- This is a religious-historical project. The figures are revered. Treat names with care: titles like "Reb," "Rabbi," "Rebbetzin" stay attached to names, not stripped.
- The Hebrew calendar matters in Chabad; you don't need to implement it for MVP, but if you display dates, "1812" is acceptable, "January 6, 1812" without the Hebrew equivalent is not preferred. Year-only is the safe default.
- Photographic content is sensitive. Do not insert images from the web. The schema has no `image_url` field for MVP precisely because images need explicit rights clearance.
- Do not editorialize bios. The text in `bio` fields is what the user wrote; render it faithfully, don't paraphrase or shorten programmatically.

## What "done" looks like for the MVP

A user can:

- Open the app and see a map of Eastern Europe + Israel + NYC populated with pins
- Click a pin and see who lived/died there
- Click a person and see their details
- Switch to a timeline view and see lifespans laid out chronologically, color-coded
- Search by name (Hebrew or English) and find anyone in the dataset
- Read each bio in full

Not required for MVP: routing with URLs, mobile-optimized layout (desktop-first is fine), animations beyond defaults, accessibility audit, internationalization framework, build optimization, tests.

## Future-facing (not your job today)

When the MVP ships and the user wants more, the schema can grow into `docs/full-spec-future.md` and the prompts in `docs/notebooklm-prompts.md` can be used to extract more figures from chassidic source books. **Do not pre-build for these.** They have their own design and their own constraints. The MVP schema is genuinely the right starting point.

## Files in this repo

```
/
├── CLAUDE.md                          # This file
├── README.md                          # Brief project intro
├── data/
│   ├── persons.json                   # 82 person records, validated
│   └── places.json                    # 58 place records, validated
├── docs/
│   ├── spec.md                        # The essential spec (MVP schema). Authoritative.
│   ├── full-spec-future.md            # v0.1 spec for when the project grows. Reference only.
│   └── notebooklm-prompts.md          # For extracting more data later. Reference only.
└── app/                               # You will create this directory
    └── (React + Vite + TS app)
```

## A note on working style

The user iterated on this spec four times to get to a minimal version. Don't betray that by over-building. If you find yourself adding a feature "because it might be useful," stop and ask whether the user requested it. If not, don't build it.

When in doubt: simpler.
