# Chabad Map — Essential Spec

The smallest schema that supports the three views: geographical map, timeline, and person pages.

## What this builds

- **Map view:** pins for birth and death places of each person. Click a pin → see who's there.
- **Timeline view:** horizontal bars showing each person's lifespan. Scrub, filter, click a bar → see the person.
- **Person view:** name, dates, places, short bio.

Two entities. That's the whole data model.

---

## Entity 1: `person`

```json
{
  "id": "alter-rebbe",
  "name_en": "Rabbi Schneur Zalman of Liadi",
  "name_he": "רבי שניאור זלמן מליאדי",
  "common_name": "Alter Rebbe",
  "generation": 1,
  "birth_year": 1745,
  "death_year": 1812,
  "birth_place_id": "liozna",
  "death_place_id": "piena",
  "role": "Rebbe",
  "bio": "Founder of Chabad chassidus. Born in Liozna; became a leading disciple of the Maggid of Mezeritch. Established Chabad as a distinct intellectual stream of chassidus and authored Tanya and Shulchan Aruch HaRav. Imprisoned by the Czarist government in 1798 and 1800; his release on Yud-Tes Kislev is celebrated as the 'Rosh Hashanah of Chassidus.' Died in 1812 while fleeing Napoleon's advance."
}
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `id` | string | Kebab-case slug. Permanent identifier. |
| `name_en` | string | Full formal English name. |
| `name_he` | string | Full Hebrew name. |
| `common_name` | string | How they're typically referred to ("Alter Rebbe," "Tzemach Tzedek," "Reb Hillel"). Used as the map pin label. |
| `generation` | integer | `0` for pre-Chabad teachers (Baal Shem Tov, Maggid), `1`-`7` for the seven Rebbes' eras. Used for filtering and color-coding. |
| `birth_year` | integer or null | Gregorian year. Drives the timeline. |
| `death_year` | integer or null | Gregorian year. Drives the timeline. |
| `birth_place_id` | string or null | Reference to `place.id`. Drives a map pin. |
| `death_place_id` | string or null | Reference to `place.id`. Drives a map pin. If same as birth, only one pin renders. |
| `role` | string | Short label: `Rebbe`, `Rebbetzin`, `Son of Rebbe`, `Mashpia`, `Chossid`, `Family`, `Pre-Chabad Teacher`. |
| `bio` | string | 2-5 sentences. Self-contained — anything worth knowing goes here. |

---

## Entity 2: `place`

```json
{
  "id": "liadi",
  "name_en": "Liadi",
  "name_he": "ליאדי",
  "lat": 54.5897,
  "lng": 30.9897,
  "modern_country": "Belarus"
}
```

### Field reference

| Field | Type | Notes |
|---|---|---|
| `id` | string | Kebab-case slug. Prefer the historical chassidic name. |
| `name_en` | string | English display name. |
| `name_he` | string | Hebrew display name. |
| `lat` / `lng` | number | Decimal degrees. |
| `modern_country` | string | For user orientation. |

---

## Suggested starter dataset

~25 persons, ~20 places. Should fit in a single afternoon of careful entry.

**Persons (~25):**
- Seven Rebbes: Alter Rebbe, Mitteler Rebbe, Tzemach Tzedek, Maharash, Rashab, Rayatz, the Rebbe
- Wives: Rebbetzin Chaya Mushka (Rebbe), Rebbetzin Shterna Sarah (Rashab), Rebbetzin Chana (Rebbe's mother), Rebbetzin Rivka (Maharash's wife)
- Rebbe's father: Rabbi Levi Yitzchak Schneerson
- Pre-Chabad anchors: Baal Shem Tov, Maggid of Mezeritch
- A few major chassidim: Reb Hillel Paritcher, Reb Aizik Homiler, Reb Mendel Futerfas, Reb Shmuel Munkes, Reb Pinchas Reizes
- Tzemach Tzedek's other sons (the dynasty branches): Maharil of Kapust, R' Yisrael Noach of Niezhin, R' Yosef Yitzchak of Avritch

**Places (~20):**
- Mezhibuzh, Mezeritch, Liozna, Liadi, Piena, Lubavitch, Kapust, Niezhin, Avritch, Haditch, Rostov, Yekaterinoslav, Nikolaev, Riga, Otwock, Warsaw, Paris, Marseilles, Brooklyn (Crown Heights)

---

## What this gets you

A working product that says something meaningful:

- The map shows the geographic story — early Chabad rooted in modern-day Belarus and Ukraine, the 20th century pulling everything west and across the Atlantic.
- The timeline shows the dynasty — seven overlapping lifespans spanning 1745 to 1994, with the seventh stretching toward the present.
- The pre-Chabad anchors (Baal Shem Tov, Maggid) provide context, and the Tzemach Tzedek's sons let you see the branching without needing a lineage tree to display it (just put them all in the dataset; the map will cluster them geographically and the timeline will line them up by era).

That's a satisfying first product. Ship it, see what people want next, then expand.

---

## Growth path

When you outgrow this:

| Add when you need... | Change |
|---|---|
| Migration paths (more than two places) | Add `places_lived` array with year ranges. Keep `birth_place_id` and `death_place_id` as derived. |
| Family tree | Add `father_id`, `mother_id`, `spouse_id` fields. |
| Teacher chains | Add `teacher_id` field. |
| Stories | Add the `story` entity from the MVP spec. |
| Hebrew dates / yahrzeits | Add `hebrew_birth` / `hebrew_death` objects. |
| Photos | Add `image_url`. |
| Source citations | Add `source` string field, then later structured sources. |

Every one of these is additive — nothing in this schema gets thrown out when you grow.
