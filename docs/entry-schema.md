# Entry Schema — for Adding New Persons and Places

This is the canonical schema the live app consumes today. Use it for every new contribution to `data/persons.json` and `data/places.json`.

For the more elaborate future schema (relationships, events, letters, stories, sources, etc.) see `full-spec-future.md`. **Do not use that schema for new contributions today** — the app cannot read it. Extending the schema is a separate, deliberate decision.

---

## Person record

```jsonc
{
  "id": "kebab-case-slug",                  // required, unique, permanent
  "name_en": "Rabbi Full Formal Name",      // required
  "name_he": "רבי שם מלא",                 // required
  "common_name": "Reb Short Name",          // required — shown on map and lists
  "generation": 3,                          // required — integer 0-7 (see table below)
  "birth_year": 1795,                       // integer Gregorian, or null
  "death_year": 1864,                       // integer Gregorian, or null
  "birth_place_id": "khmilnik",             // must match an id in places.json, or null
  "death_place_id": "kherson",              // must match an id in places.json, or null
  "role": "Mashpia",                        // required — one of the controlled values below
  "bio": "Two to five sentences. Self-contained.",   // required, faithful to sources
  "primary_place_id": "paritch",            // optional — see "Primary place" below
  "journey": [                              // optional — see "Journey" below
    { "year": 1795, "place_id": "khmilnik", "event": "Born" },
    { "year": 1810, "place_id": "paritch",  "event": "Appointed Rav" }
  ],
  "chabadpedia_url": "https://chabadpedia.co.il/...",   // optional
  "photo_url": "https://chabadpedia.co.il/images/..."   // optional
}
```

### Field reference

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Kebab-case slug. Pattern: `^[a-z0-9]+(-[a-z0-9]+)*$`. Never reuse, never change once published. |
| `name_en` | yes | Full formal English: "Rabbi Schneur Zalman of Liadi", "Rebbetzin Chana Schneerson". Keep titles ("Rabbi", "Reb", "Rebbetzin") attached. |
| `name_he` | yes | Full Hebrew name as it appears in standard Chabad sources. Use traditional spelling, not modern Israeli. |
| `common_name` | yes | The 1-4 word name actually used in conversation: "Alter Rebbe", "Tzemach Tzedek", "Reb Hillel Paritcher". Shown as the map pin label and on every list. |
| `generation` | yes | See generation table. Use the figure's *primary* era of activity. |
| `birth_year` | nullable | Gregorian integer. `null` if unknown — don't guess. Don't put quoted strings or "c. 1780" — if uncertain, leave `null` and note in bio. |
| `death_year` | nullable | Same. |
| `birth_place_id` | nullable | Must resolve to an entry in `places.json`. If the place doesn't exist yet, add the place first (see Place record below). |
| `death_place_id` | nullable | Same. |
| `role` | yes | One of the controlled values below. |
| `bio` | yes | 2-5 sentences. Render-faithful prose — no markdown, no editorializing. The app shows this verbatim. |
| `primary_place_id` | optional | The "where they are based" pin location. When omitted, the app derives it as `death_place_id ?? birth_place_id`. **Set this explicitly** for figures named after a place where they served but did not die (e.g., "Reb Hillel of Paritch" → `paritch`, not Kherson where he died). |
| `journey` | optional | Ordered list of life events. See "Journey" below. When empty/omitted, the app synthesizes a 2-step fallback from birth/death. |
| `chabadpedia_url` | optional | Page URL on chabadpedia.co.il. Rendered as a "More on Chabadpedia" link. |
| `photo_url` | optional | Direct URL to a primary biographical image. Currently Chabadpedia-hosted; verify licensing if used at scale. |

### Controlled values: `generation`

| Value | Era | Years |
|---|---|---|
| `0` | Pre-Chabad (Baal Shem Tov, Maggid of Mezeritch and their immediate circle) | pre-1772 |
| `1` | Alter Rebbe | 1745–1812 |
| `2` | Mitteler Rebbe | 1773–1827 |
| `3` | Tzemach Tzedek | 1789–1866 |
| `4` | Maharash | 1834–1882 |
| `5` | Rashab | 1860–1920 |
| `6` | Rayatz | 1880–1950 |
| `7` | The Rebbe | 1902–1994 |

Use the peak of their activity, not their birth date. Reb Hillel Paritcher lived through generations 1–4; his peak was the Tzemach Tzedek era, so he's generation 3.

### Controlled values: `role`

Use one of these exact strings (case sensitive — the app filters and labels on them):

- `Rebbe`
- `Rebbetzin`
- `Son of Rebbe`
- `Family` (other family members)
- `Mashpia`
- `Chossid`
- `Pre-Chabad Teacher`

If a figure genuinely doesn't fit any of these, **add a value to this list** in a PR with a one-line justification — don't introduce a one-off role string in `persons.json`.

### Primary place

The app pins each person at one location and lets the year-range slider filter who's shown. The default rule is:

```
primary_place = primary_place_id ?? death_place_id ?? birth_place_id
```

This default works for most Rebbes (their seat is where they died), but it fails for figures defined by an earlier seat — "Reb Hillel of Paritch" should pin at Paritch, not Kherson where he passed away.

**Rule of thumb:** set `primary_place_id` explicitly when the common name contains "of X" or when the figure is more identified with a place that is *not* their death place.

### Journey

An optional ordered list of life events. Each step:

```jsonc
{
  "year": 1810,                  // integer or null if unknown
  "place_id": "paritch",         // must resolve in places.json
  "event": "Appointed Rav"       // short label, sentence case
}
```

Event labels are free-form short strings. Recommended vocabulary so things stay consistent:

| Label | Use for |
|---|---|
| `Born` | Birth |
| `Studied` | Period of formal study at a seat of learning |
| `Married` | Marriage |
| `Appointed Rav` | Took up a rabbinic post |
| `Appointed Mashpia` | Took up a chassidic-mentor post |
| `Founded yeshiva` | Founded a yeshiva |
| `Imprisoned` | Arrest / imprisonment |
| `Released` | Release from imprisonment |
| `Escaped` | Escape from a regime |
| `Made aliya` | Emigrated to Eretz Yisroel |
| `Emigrated` | Other emigration |
| `Yechidus` | Notable yechidus with a Rebbe |
| `Passed away` | Death |

Steps don't need to be exhaustive — record the steps that meaningfully change *where* the person was. If a figure stayed in one town for fifty years and then moved once, that's two steps.

When `journey` is omitted or empty, the app shows `Born → Passed away` derived from `birth_place_id` and `death_place_id`.

---

## Place record

```jsonc
{
  "id": "paritch",                       // required, unique, permanent
  "name_en": "Paritch",                  // required — historical chassidic spelling
  "name_he": "פאריטש",                   // required
  "lat": 52.815,                         // required — decimal degrees
  "lng": 29.430,                         // required — decimal degrees
  "modern_country": "Belarus",           // required
  "significance": "Seat of Reb Hillel from 1810."  // optional but recommended
}
```

### Field reference

| Field | Required | Notes |
|---|---|---|
| `id` | yes | Kebab-case. Prefer the *historical* chassidic name, not the modern one: `liadi` not `lyady`, `liozna` not `lyozno`, `kherson` not `xerson`. |
| `name_en` | yes | The form that appears in Chabad sources. If the modern English name differs, optionally include in parens: `"Anipoli (Hannopil)"`. |
| `name_he` | yes | Hebrew/Yiddish spelling as found in Chabad sources. |
| `lat` / `lng` | yes | Decimal degrees, 4–5 places of precision. Use the historical town center, not a sprawling modern administrative centroid. |
| `modern_country` | yes | Use the current sovereign country. Existing values in dataset: `Austria`, `Belarus`, `France`, `Israel`, `Israel/Palestinian Territories`, `Kazakhstan`, `Latvia`, `Lithuania`, `Poland`, `Russia`, `Ukraine`, `United Kingdom`, `United States`, `Uzbekistan`. Add new countries sparingly. |
| `significance` | optional | One sentence on the place's Chabad-historical role. Rendered in the place panel. |

### Geocoding hints

If you can't find lat/lng with confidence:
- Search the historical name on Wikipedia — most shtetl pages list coordinates
- Cross-check with Google Maps using the modern name
- If you find two candidate locations, prefer the one that matches the country and region given in the source. Do not guess — leave the place out of `places.json` and flag for manual review.

---

## Validation rules

Before adding any new record:

**Persons:**
- `id` does not exist in `persons.json`
- `name_en`, `name_he`, `common_name`, `generation`, `role`, `bio` are all present
- `birth_place_id` / `death_place_id` / `primary_place_id` (if set) each resolve to a real entry in `places.json`
- All journey `place_id` values resolve
- `role` is one of the controlled values
- `generation` is 0–7

**Places:**
- `id` does not exist in `places.json`
- All required fields are present
- `lat` is in [-90, 90], `lng` in [-180, 180]

You can run `python scripts/validate_data.py` after any edit to confirm the dataset is still internally consistent.

---

## Deduplication

This is the biggest risk when adding entries at scale. The same person can appear under multiple spellings; the same shtetl appears under Hebrew, Yiddish, Russian, and modern transliterations. Two layers of defense:

1. **At extraction time** — the NotebookLM prompts in `extraction-prompt.md` include the full list of existing person and place IDs and names, instructing the model to reuse existing IDs rather than coin new ones. Regenerate that list periodically with `python scripts/known_ids.py`.

2. **At merge time** — run `python scripts/merge_new_entries.py path/to/new_entries.json`. It fuzzy-matches every new entry against the existing dataset and writes a report flagging suspected duplicates by name similarity (and lat/lng proximity for places). Review the report; only merge after you've resolved every flag.

Never paste new entries directly into `persons.json` or `places.json` without running the merge check.
