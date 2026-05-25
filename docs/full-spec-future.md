# Chabad Historical Map — Data Specification

Version 0.1 — design document for the canonical data model.

## Design principles

A few decisions that shape everything below:

1. **Sources are mandatory, not optional.** Every fact — every date, place, relationship — carries a source reference. A claim with no source is a `needs_research` flag, not a fact.
2. **Hebrew dates are first-class.** Yahrzeits are observed by Hebrew date; many figures' Gregorian dates are unknown or reconstructed. The Hebrew date is often the *real* date; the Gregorian is the conversion.
3. **Uncertainty is data.** "Circa 1780," "between Tishrei and Kislev," "year unknown but during the Mitteler Rebbe's nesius" — all common, all need to be representable without forcing false precision.
4. **Names are not strings.** A single person can be known by 5+ names across Hebrew, Yiddish, English transliterations, work titles, place designations, and acronyms. The schema treats names as structured objects.
5. **Relationships are entities, not fields.** A father-son relationship has its own metadata (sources, notes, certainty). Don't bury it in a `father_id` column on the person.
6. **Notability is a graded field, not a boolean.** A tier-1 figure (the Rebbe) and a tier-5 figure (a chossid mentioned once in a sippur) both belong in the database, but with very different display and indexing treatment.
7. **Branches matter.** Chabad-Lubavitch is the main line, but Kapust, Liadi, Avritch, Niezhin, and Strashelye are part of the story. Don't hardcode "Lubavitch" as the only path.

## Entity overview

Eight entities. Person is the hub; everything else attaches to it.

| Entity | Purpose |
|---|---|
| `person` | Individual humans — Rebbes, family, chassidim, contemporaries |
| `place` | Geographic locations, with period and modern names |
| `relationship` | Typed, directional or symmetric link between two persons |
| `event` | Dated occurrence at a place involving one or more persons |
| `work` | Written work: sefer, maamar, sicha, kuntres, reshima |
| `letter` | Correspondence — a specialized work type, but networked enough to warrant its own entity |
| `story` | A sippur/account, with source attribution, mentioning persons and places |
| `source` | Bibliographic reference (book, archive, oral, web) |

---

## 1. `person`

The central entity. Designed to handle anyone from the Alter Rebbe down to a chossid mentioned in one story.

```json
{
  "id": "hillel-paritcher",
  "slug": "hillel-paritcher",
  "schema_version": "0.1",

  "names": {
    "display_he": "ר' הלל פאריטשער",
    "display_en": "Reb Hillel Paritcher",
    "display_yi": "רב הלל פאריטשער",
    "formal_he": "הרב הלל בן הרב מאיר הלוי מפאריטש",
    "formal_en": "Harav Hillel ben Harav Meir HaLevi of Paritch",
    "given_he": "הלל",
    "given_en": "Hillel",
    "patronymic_he": "בן מאיר",
    "family_name": null,
    "place_designation": "Paritcher",
    "work_designation": null,
    "honorifics": ["Reb", "Harav", "HaChossid"],
    "acronym": null,
    "aliases": [
      { "name": "Hillel of Paritch", "language": "en", "type": "common" },
      { "name": "Reb Hillel", "language": "en", "type": "short" },
      { "name": "ר' הלל מפאריטש", "language": "he", "type": "common" }
    ],
    "sort_key": "Hillel Paritcher"
  },

  "gender": "male",

  "vitals": {
    "birth": {
      "hebrew_date": { "year": 5555, "month": "Tishrei", "day": null },
      "gregorian_date": { "year": 1795, "month": null, "day": null, "precision": "year" },
      "circa": true,
      "place_id": "khmilnyk",
      "source_ids": ["beis-rebbi-p123"]
    },
    "death": {
      "hebrew_date": { "year": 5624, "month": "Av", "day": 11 },
      "gregorian_date": { "year": 1864, "month": 8, "day": 13, "precision": "day" },
      "circa": false,
      "place_id": "kherson",
      "cause": null,
      "source_ids": ["sefer-hatoldos-maharash-p45"]
    },
    "burial": {
      "place_id": "kherson-cemetery",
      "ohel": false,
      "source_ids": ["sefer-hatoldos-maharash-p45"]
    },
    "yahrzeit": { "hebrew_month": "Av", "hebrew_day": 11 }
  },

  "era": {
    "generation": 3,
    "active_during_nesius_of": ["alter-rebbe", "mitteler-rebbe", "tzemach-tzedek", "maharash"],
    "primary_rebbe_id": "tzemach-tzedek",
    "branch": "chabad-lubavitch"
  },

  "roles": [
    {
      "type": "mashpia",
      "start_date": { "hebrew_year": 5586 },
      "end_date": { "hebrew_year": 5624 },
      "place_id": "babroisk",
      "notes": "Famous mashpia in Babroisk region",
      "source_ids": ["beis-rebbi-p124"]
    },
    {
      "type": "talmid",
      "of_person_id": "alter-rebbe",
      "start_date": { "hebrew_year": 5566 },
      "notes": "Famously sought out the Alter Rebbe as a young illui",
      "source_ids": ["sippurei-chassidim-zevin-vol1-p78"]
    }
  ],

  "places_lived": [
    {
      "place_id": "khmilnyk",
      "start_date": { "year_he": 5555 },
      "end_date": { "year_he": 5566 },
      "role": "youth",
      "source_ids": ["beis-rebbi-p123"]
    },
    {
      "place_id": "paritch",
      "start_date": { "year_he": 5570 },
      "end_date": { "year_he": 5605 },
      "role": "rav",
      "source_ids": ["beis-rebbi-p124"]
    },
    {
      "place_id": "babroisk",
      "start_date": { "year_he": 5605 },
      "end_date": { "year_he": 5624 },
      "role": "mashpia",
      "source_ids": ["beis-rebbi-p125"]
    }
  ],

  "notability": {
    "tier": 2,
    "rationale": "Major mashpia of the third generation; subject of many sippurim; author of Pelach HaRimon"
  },

  "bio": {
    "claim_to_fame_en": "Legendary mashpia and Talmudic genius who famously interrupted the Alter Rebbe's tish as a young man to ask his question.",
    "claim_to_fame_he": "...",
    "short_en": "...",
    "medium_en": "...",
    "long_en_md": "...",
    "long_he_md": "..."
  },

  "media": {
    "portrait": null,
    "images": [],
    "documents": []
  },

  "content_links": {
    "works_authored": ["pelach-harimon", "likutei-biurim"],
    "letters_sent": [],
    "letters_received": [],
    "mentioned_in_works": [
      { "work_id": "igrot-kodesh-maharash-vol1", "location": "letter 23" }
    ],
    "appears_in_stories": ["alter-rebbe-tish-interruption", "hillel-rebbe-meeting"],
    "yechidus_records": [
      { "rebbe_id": "alter-rebbe", "year_he": 5566, "place_id": "liadi", "source_ids": ["..."] }
    ]
  },

  "tags": ["mashpia", "third-generation", "talmid-chacham", "author", "pre-war"],

  "metadata": {
    "created_at": "2026-05-25",
    "last_updated": "2026-05-25",
    "last_reviewed_by": "...",
    "confidence_level": "well-documented",
    "needs_research_flags": ["birth_year_uncertain"],
    "contributors": []
  }
}
```

### Field-by-field notes

**`id` and `slug`.** Use kebab-case English. Stable. Never change them — anything that links to a person uses this. If the name changes, the id doesn't.

**`names.display_*`.** This is what shows on the map pin and node label. Pick what the Chabad world actually calls them — "the Tzemach Tzedek" not "R' Menachem Mendel Schneersohn (3rd)." Use intuition; this is the human-facing string.

**`names.formal_*`.** Full Harav X ben Y of Z form. Used on the person's detail page header.

**`names.work_designation`.** For people known by their sefer: "Tzemach Tzedek" → `work_designation: "Tzemach Tzedek"`. For the Mitteler Rebbe, it's the title "Mitteler Rebbe" itself rather than a work. Use `acronym` for things like "Maharash," "Rashab," "Rayatz."

**`names.aliases`.** The catch-all. Include every spelling variant you've seen — "Schneersohn," "Schneerson," "Shneuri," etc. The search index should hit on any of these.

**`vitals.*.hebrew_date`.** Hebrew year is Anno Mundi (e.g., 5555). Hebrew months: `Tishrei`, `Cheshvan`, `Kislev`, `Tevet`, `Shevat`, `Adar`, `Adar Aleph`, `Adar Beis`, `Nisan`, `Iyar`, `Sivan`, `Tammuz`, `Av`, `Elul`. Day is 1-30, null if unknown.

**`vitals.*.gregorian_date.precision`.** One of `day`, `month`, `year`, `decade`, `century`. Lets you render "1795" vs "August 13, 1864" appropriately.

**`vitals.*.circa`.** Boolean. If true, render with "c." prefix.

**`vitals.yahrzeit`.** Stored separately even though it duplicates death. Reason: for many minor figures, the yahrzeit is the *only* date known. Also lets you build a "yahrzeit today" feature.

**`era.generation`.** Integer 1-7+, indicating which Rebbe's era they primarily belonged to. 1 = Alter Rebbe, 7 = the Rebbe, 8 = post-Gimmel Tammuz. Use the *peak* of their activity if they span generations.

**`era.active_during_nesius_of`.** Array of rebbe ids whose tenure they lived through. Hillel Paritcher lived through four nesius'n; this is how you express that.

**`era.branch`.** Important. Values: `chabad-lubavitch`, `chabad-kapust`, `chabad-liadi` (R' Moshe), `chabad-strashelye`, `chabad-avritch`, `chabad-niezhin`, `pre-chabad`, `non-chabad`. The `non-chabad` value is for contemporary rabbis they corresponded with (e.g., Reb Levi Yitzchak Berditchever, the Maggid of Mezeritch's other talmidim, etc.).

**`roles`.** Array because people fill multiple roles across their lives, and often simultaneously. Common types: `rebbe`, `rebbetzin`, `son-of-rebbe`, `mashpia`, `chozer`, `mazkir` (secretary), `gabbai`, `rav` (of a town), `rosh-yeshiva`, `mashgiach`, `melamed`, `shochet`, `talmid`, `chossid`, `askan`, `businessman`, `shliach`, `meshulach`, `oved` (in the chassidic-avodah sense).

**`places_lived`.** Time-stamped residency. This is what powers the map — you can show where someone was at any given year. The `role` field here is the role they had in that specific place (e.g., `rav` of Paritch, `mashpia` in Babroisk).

**`notability.tier`.** 1-5 scale:
- **1**: The seven Rebbes. Always rendered, always indexed.
- **2**: Rebbeim's wives, sons, principal mashpi'im, the most famous chassidim (Hillel Paritcher, Reb Aizik Homiler, Reb Mendel Futerfas, etc.), Rebbe's parents.
- **3**: Major chassidim, prominent shluchim of historical significance, known authors of chassidic seforim.
- **4**: Named figures who appear in multiple sources/stories.
- **5**: Figures mentioned in passing in a single story. Included for completeness, displayed only on filtered views.

**`bio.claim_to_fame_*`.** One sentence. Shows in map tooltip and search results. Make it specific and memorable, not generic ("a great chossid").

**`bio.long_*_md`.** Markdown. Allows formatting, links to other persons (`[Alter Rebbe](/person/alter-rebbe)`), works, places.

**`content_links.yechidus_records`.** Specific to Chabad — private audiences with a Rebbe. Often the only "event" attaching a minor figure to a Rebbe.

**`metadata.confidence_level`.** Values: `well-documented` (multiple solid sources), `documented` (one good source), `partial` (basic facts confirmed, details thin), `fragmentary` (name and one detail), `legendary` (appears in oral tradition without firm sourcing).

---

## 2. `place`

```json
{
  "id": "lubavitch",
  "slug": "lubavitch",
  "names": {
    "en": "Lubavitch",
    "he": "ליובאוויטש",
    "yi": "ליובאוויטש",
    "ru_historical": "Любавичи",
    "modern_name_en": "Lyubavichi",
    "modern_country": "Russia",
    "historical_jurisdictions": [
      { "name": "Mogilev Governorate, Russian Empire", "start_year": 1772, "end_year": 1917 },
      { "name": "Smolensk Oblast, USSR", "start_year": 1917, "end_year": 1991 },
      { "name": "Smolensk Oblast, Russia", "start_year": 1991, "end_year": null }
    ]
  },
  "coordinates": { "lat": 54.8395, "lng": 30.9959 },
  "type": "shtetl",
  "significance": {
    "chabad_role": "Seat of the Chabad movement 1813-1915",
    "period_start_he": 5573,
    "period_end_he": 5675
  },
  "notable_for": [
    "Seat of Rebbeim 3-5",
    "Site of major fires (1855, 1888)",
    "Tomim Yeshiva founded here 1897"
  ],
  "source_ids": ["sefer-hatoldos-rashab-p234"]
}
```

**Notes on places.** Many Russian-Empire shtetls have multiple name forms across Hebrew, Yiddish, Russian, and post-Soviet local language. The `modern_name_en` and `modern_country` are what you'd put into a modern mapping API. The historical name is what appears in seforim and is what should display on the map by default. Type values: `shtetl`, `town`, `city`, `village`, `country`, `region`, `building` (e.g., 770), `cemetery`, `ohel`.

---

## 3. `relationship`

Modeled as its own entity rather than a foreign key, because relationships carry metadata.

```json
{
  "id": "rel-12345",
  "type": "father-son",
  "from_person_id": "alter-rebbe",
  "to_person_id": "mitteler-rebbe",
  "directional": true,
  "start_date": null,
  "end_date": null,
  "notes": "",
  "source_ids": ["beis-rebbi-p15"],
  "confidence": "certain"
}
```

### Relationship types

**Family** (`directional: true`, from = parent/elder):
- `father-son`, `father-daughter`, `mother-son`, `mother-daughter`
- `grandfather-grandson`, etc.
- `father-in-law-son-in-law` (significant in Chabad — many rebbes married daughters of preceding rebbes' families)

**Family** (`directional: false`):
- `siblings`, `spouses`, `cousins`

**Teacher-student** (`directional: true`, from = teacher):
- `rebbe-chossid` — the formal hiskashrus relationship
- `mashpia-mekabel` — a chassidic mentorship
- `teacher-student` — generic learning
- `chozer-of` — a chozer who memorized/transcribed maamarim
- `gabbai-of`, `mazkir-of`, `meshares-of` — service roles

**Contemporary** (`directional: false`):
- `correspondents` — wrote letters to each other
- `colleagues` — peer rabbis
- `disputants` — known disagreement (e.g., Vilna Gaon and Alter Rebbe)

**Confidence values:** `certain`, `probable`, `disputed`, `legendary`.

---

## 4. `event`

```json
{
  "id": "alter-rebbe-arrest-1798",
  "title_en": "Arrest and imprisonment of the Alter Rebbe",
  "title_he": "מאסר אדמו\"ר הזקן תקנ\"ט",
  "date": {
    "hebrew": { "year": 5559, "month": "Tishrei", "day": 24 },
    "gregorian": { "year": 1798, "month": 10, "day": 4 },
    "precision": "day"
  },
  "end_date": {
    "hebrew": { "year": 5559, "month": "Kislev", "day": 19 }
  },
  "place_ids": ["liozna", "petersburg", "petropavlovsk-fortress"],
  "people": [
    { "person_id": "alter-rebbe", "role": "subject" },
    { "person_id": "mitteler-rebbe", "role": "family-affected" }
  ],
  "type": "imprisonment",
  "significance": "Yud-Tes Kislev — Rosh Hashanah of Chassidus",
  "description_md": "...",
  "source_ids": ["beis-rebbi-p87", "yud-tes-kislev-archive"],
  "tags": ["yud-tes-kislev", "tcheshma", "founding-event"]
}
```

**Event types:** `birth`, `death`, `marriage`, `move`, `imprisonment`, `release`, `appointment`, `publication`, `farbrengen`, `yechidus`, `escape`, `aliyah`, `death-anniversary-event`, `historic-meeting`, `dispute`, `decree`.

---

## 5. `work`

```json
{
  "id": "tanya",
  "slug": "tanya",
  "titles": {
    "en_primary": "Tanya",
    "en_full": "Likutei Amarim — Tanya",
    "he_primary": "תניא",
    "he_full": "לקוטי אמרים תניא"
  },
  "author_id": "alter-rebbe",
  "coauthor_ids": [],
  "type": "sefer",
  "subject_tags": ["chassidus", "foundational", "binyan-haavodah"],
  "composition_period": {
    "start_year_he": 5547,
    "end_year_he": 5556
  },
  "first_published": {
    "year_he": 5557,
    "year_gregorian": 1796,
    "place_id": "slavita"
  },
  "external_links": {
    "sefaria": "https://www.sefaria.org/Tanya",
    "chabad_library": "https://www.chabadlibrary.org/...",
    "hebrewbooks": "..."
  },
  "structure_notes": "Contains five parts: Likutei Amarim, Shaar HaYichud V'HaEmunah, Igeres HaTeshuvah, Igeres HaKodesh, Kuntres Acharon",
  "source_ids": ["..."]
}
```

**Work types:** `sefer`, `maamar`, `sicha`, `kuntres`, `reshima`, `commentary`, `responsum`, `derush`, `niggun`. Yes, niggunim should be in here — many are attributed to specific Rebbes or chassidim and are historically significant.

---

## 6. `letter`

Could be a subtype of `work`, but correspondence networks are central to your map, so it's worth its own entity.

```json
{
  "id": "letter-rayatz-1928-04-15",
  "from_person_id": "rayatz",
  "to_person_id": "levik-schneerson",
  "date": {
    "hebrew": { "year": 5688, "month": "Iyar", "day": 5 },
    "gregorian": { "year": 1928, "month": 4, "day": 25 }
  },
  "from_place_id": "riga",
  "to_place_id": "yekaterinoslav",
  "topic_tags": ["family", "halacha", "encouragement"],
  "summary_en": "...",
  "language": "he",
  "source": {
    "publication": "Igros Kodesh Admur HaRayatz",
    "volume": 1,
    "letter_number": 234,
    "page": 567
  },
  "full_text_available": true,
  "external_link": "..."
}
```

This is what powers a correspondence-network visualization à la HaMapah. With Igros Kodesh fully digitized, you can in principle generate thousands of edges from this entity alone.

---

## 7. `story`

The sippur is a uniquely Chabad genre — historical narratives told for chassidic mussar, often the only source for a minor figure.

```json
{
  "id": "alter-rebbe-tish-hillel-interruption",
  "title_en": "Reb Hillel interrupts the Alter Rebbe's tish",
  "title_he": "ר' הלל קוטע את התיש של אדמו\"ר הזקן",
  "summary_en": "Young Hillel of Paritch travels to meet the Alter Rebbe with a question on a maamar; arrives during a tish and interrupts to ask. The Alter Rebbe answers by saying the maamar over again.",
  "approximate_date": {
    "hebrew_year": 5566,
    "circa": true,
    "rebbe_era": "alter-rebbe"
  },
  "place_id": "liadi",
  "persons_mentioned": [
    { "person_id": "hillel-paritcher", "role": "protagonist" },
    { "person_id": "alter-rebbe", "role": "rebbe" }
  ],
  "themes": ["bittul", "chiddush", "ahavas-yisrael"],
  "source_ids": ["sippurei-chassidim-zevin-vol1-p78", "rebbe-sicha-yud-shevat-5712"],
  "source_certainty": "well-attested",
  "notes": "Told by the Rebbe multiple times with slight variation."
}
```

**`source_certainty`:** `well-attested` (multiple sources, including from Rebbe), `attested` (one published source), `oral-tradition` (told but not published), `disputed`.

Stories are how you populate the bio for tier-4 and tier-5 figures whose entire historical footprint is appearing in one or two sippurim.

---

## 8. `source`

```json
{
  "id": "beis-rebbi",
  "type": "book",
  "title_he": "בית רבי",
  "title_en": "Beis Rebbi",
  "author": "Chaim Meir Heilman",
  "publication_year": 1903,
  "publication_place": "Berdichev",
  "language": "he",
  "online_url": "https://www.hebrewbooks.org/...",
  "is_primary": false,
  "reliability": "high",
  "notes": "Foundational source for early Chabad history; some details contested by later research."
}
```

**Source types:** `book`, `manuscript`, `letter` (when referenced as a source), `archive`, `oral-tradition`, `sicha`, `maamar`, `journal-article`, `website`.

**Reliability values:** `primary` (the figure himself, or contemporary direct), `high` (published by recognized chassidic-historical institution with sourcing), `medium` (published but less verified), `oral` (oral tradition without solid attribution).

A specific *page* reference is a separate construct — use a citation format like `beis-rebbi-p123` as a reference id in `source_ids` fields, OR model citations as their own entity if you want to go strict.

---

## File organization

For a project of this size, store as JSON files split by entity and (for `person`) by tier, so you can lazy-load:

```
/data
  /persons
    tier-1/                  # 7 Rebbes
      alter-rebbe.json
      mitteler-rebbe.json
      ...
    tier-2/                  # ~50-100 files
    tier-3/                  # ~300-500
    tier-4/                  # ~1000+
    tier-5/                  # ~thousands
  /places
    lubavitch.json
    liadi.json
    ...
  /events
  /works
  /letters
  /stories
  /sources
  /relationships
    family.json
    teacher-student.json
    correspondence.json
```

For development, JSON files in Git is fine and gives you version-controlled data with diffs and PRs. Once you're past ~2000 persons, move to a real database (Postgres or Supabase) and treat the JSON files as exports/seeds.

## Indexing and search

Build a derived search index that flattens all name variants, aliases, acronyms, work designations, and place designations into a single searchable string per person. A user typing "Tzemach Tzedek," "Tzemach-Tzedek," "צמח צדק," "Menachem Mendel," or "Reb Mendele" should all land on the same entry. Same logic for places ("Lubavitch," "ליובאוויטש," "Lyubavichi") and works.

## Validation rules

Before any person record is considered "complete":

- Has at least one source in every section that contains factual claims
- Has at least a tier rating, generation, and one role
- Has `confidence_level` set
- Has either a birth or death date (Hebrew is sufficient)
- Has `bio.claim_to_fame_en` (the one-sentence summary)

Below "complete," records can exist with a `needs_research` flag — and that's fine. A skeleton record for a figure mentioned in one story is still useful; it appears in the graph as a stub.

## Open questions to resolve before locking the schema

1. **Patronymic depth.** Some figures are known with three generations of patronymic ("Avraham ben Yehuda ben Shimon"). Should `patronymic` be a single string or a structured chain?
2. **Multi-generation marriages.** When a rebbe's daughter marries a future rebbe (e.g., the Rebbe and Rebbetzin Chaya Mushka), the spouse relationship doubles as a teacher-student link via father-in-law. Encode this as two separate relationships or one composite?
3. **Modern shluchim.** Tens of thousands of contemporary figures with thin individual histories. Do they live in this dataset or a separate, linked one?
4. **Disputed identifications.** Multiple historical "Reb Mendel"s exist. Do we model "candidate identity" as a separate entity, or just put it in notes?
5. **Living people.** Privacy considerations. Recommend: tier-1 only (the Rebbe's surviving family, etc.) and only with documented public sourcing.

---

*This is v0.1 — iterate on it with one real worked example per entity before scaling up.*
