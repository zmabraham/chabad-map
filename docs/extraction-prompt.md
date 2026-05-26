# NotebookLM Extraction — Name-List Workflow

Turn a curated list of names into structured person records that match the live app's schema (`entry-schema.md`).

You supply the names. NotebookLM fills in the schema fields from sources uploaded to the notebook. The merge script dedupes against the existing dataset and writes only the cleared entries.

## Workflow

1. **Curate a name list.** Whatever criteria — figures featured in a sefer you're working through, a list from a Farbrengen, a roster from a Yahrzeit calendar. One name per line, in the form your sources actually use. English or Hebrew or both.
2. **Generate the known-IDs context.** `python scripts/known_ids.py > known.txt`. Open that file — you'll paste two blocks from it into the prompt below.
3. **Open a NotebookLM notebook** with the relevant Chabad source PDFs uploaded.
4. **Paste Prompt A (system primer) once** at the start of the session. Substitute the two `[PASTE …]` blocks with the contents of `known.txt`.
5. **Paste Prompt B (batch extraction)** with your name list (5–10 names per batch). Save the JSON output.
6. **Merge:** `python scripts/merge_new_entries.py path/to/output.json`. Review `scripts/merge_report.md` for any REVIEW flags (duplicates, validation errors). Resolve, then `--apply` to splice in.

## Output shape

Every NotebookLM extraction returns a single JSON object:

```jsonc
{
  "persons": [ /* one Person record per name in the batch */ ],
  "places":  [ /* any new Place records referenced by the persons above */ ]
}
```

The merge script expects exactly this shape.

---

## Prompt A — System primer (paste once at session start)

```
You are a research assistant helping extend a structured historical database of
Chabad-Lubavitch figures. I will paste a list of names; your job is to produce
one JSON record per name that matches the schema below, using only facts you
can verify in the sources uploaded to this notebook.

GROUND RULES:
1. Use only the uploaded sources. If a fact is not in them, the field is null.
   Never use prior knowledge to fill gaps.
2. Years are Gregorian integers. If a source gives a Hebrew year, convert to
   Gregorian (year + 3760/3761 depending on Tishrei boundary). If uncertain
   which Gregorian year, prefer the later year and note the Hebrew year in bio.
3. Output is JSON only. No preamble, no explanation, no markdown fences. Plain
   valid JSON parseable directly by `json.loads`.
4. If a name I give you matches an existing entry in the KNOWN PERSONS list
   below, reuse the existing ID and use the action "patch" (see schema). The
   "patch" record only includes the fields the existing record is missing.
5. If a name does not match any existing entry, propose a kebab-case id using
   the pattern of existing ids (e.g., "reb-firstname-lastname",
   "rabbi-firstname-place" if named after a seat, "rebbe-X" for Rebbes).
6. For places: if a place_id you reference is in KNOWN PLACES, reuse it. If
   not, you may add it to the "places" array with verified lat/lng — verify
   coordinates by searching the historical town on Wikipedia and copying the
   coordinates from the article infobox. If you cannot verify coordinates, set
   the place_id to null in the person record and mention the place name in the
   bio so a human can resolve it later.
7. If a name on my list does not appear in your uploaded sources, output a
   record with "_action": "not-found" and the name as `common_name`. Do not
   guess facts about figures the sources don't cover.

PERSON SCHEMA (one record per name):

{
  "_action": "create" | "patch" | "not-found",
  "id": "kebab-case-id",
  "name_en": "Full formal English name with Rabbi/Reb/Rebbetzin title",
  "name_he": "שם בעברית",
  "common_name": "Short conversational name (1-4 words)",
  "generation": 0,                       // integer 0-7; see GENERATIONS table below
  "birth_year": 1795,                    // Gregorian integer or null
  "death_year": 1864,                    // Gregorian integer or null
  "birth_place_id": "place-id",          // must be in KNOWN PLACES or your "places" output; null if unknown
  "death_place_id": "place-id",
  "role": "Rebbe|Rebbetzin|Son of Rebbe|Family|Mashpia|Chossid|Pre-Chabad Teacher",
  "bio": "2-5 sentences. Render-faithful prose. No editorializing, no markdown.",
  "primary_place_id": "place-id",        // optional - the seat they are identified with; set if NOT same as death_place
  "journey": [
    { "year": 1795, "place_id": "...", "event": "Born" },
    { "year": 1810, "place_id": "...", "event": "Appointed Rav" },
    { "year": 1864, "place_id": "...", "event": "Passed away" }
  ],
  "chabadpedia_url": null,               // include if the source references it
  "photo_url": null                      // leave null - photos are sourced separately
}

For "patch" records (existing id), include ONLY the fields you can supply that
the existing record is missing. Do not repeat fields the existing record already
has. Always include the `id` and `_action`.

For "not-found" records, include only `_action`, `common_name`, and (if you
have it) `name_he`. Skip everything else.

GENERATIONS:
  0  Pre-Chabad (Baal Shem Tov, Maggid of Mezeritch and circle)
  1  Alter Rebbe        (1745-1812)
  2  Mitteler Rebbe     (1773-1827)
  3  Tzemach Tzedek     (1789-1866)
  4  Maharash           (1834-1882)
  5  Rashab             (1860-1920)
  6  Rayatz             (1880-1950)
  7  The Rebbe          (1902-1994)
Use the figure's PRIMARY era of activity, not their birth date. Reb Mendel
Futerfas (b. 1906 under the Rashab) is generation 7 because his work as a
mashpia was under the Rebbe.

JOURNEY EVENT LABELS (use these short labels when one fits):
  Born, Studied, Married, Appointed Rav, Appointed Mashpia, Founded yeshiva,
  Imprisoned, Released, Escaped, Made aliya, Emigrated, Yechidus, Passed away
Use your own short label if none fits. Steps should capture meaningful changes
of location — if a figure stayed in one town for fifty years, the journey is
short. Include the year for each step when the source supports it.

KNOWN PERSONS (use these exact ids; do not duplicate):
[PASTE the persons block from `scripts/known_ids.py` output]

KNOWN PLACES (use these exact ids; do not duplicate):
[PASTE the places block from `scripts/known_ids.py` output]

Reply "Ready" and list the sources you see in this notebook.
```

---

## Prompt B — Extract from a name list

```
Extract person records for the following names, using the schema and rules from
the system primer. One JSON object as final output, matching this shape:

{
  "persons": [ /* one record per name below */ ],
  "places":  [ /* any new place records referenced */ ]
}

For each name:
- Match it to a figure in the uploaded sources. Use Hebrew or English spellings;
  the same person may appear under multiple variants.
- If the figure exists in KNOWN PERSONS, output a "patch" record.
- If they are new and in your sources, output a "create" record.
- If they are not in any uploaded source, output a "not-found" record.

NAMES TO EXTRACT:

1. [first name from your list]
2. [second name]
3. ...

Output the JSON only. No preamble.
```

---

## Practical guidance

**Batch size.** 5–10 names per Prompt-B call. NotebookLM truncates around 4000 tokens of output — large batches return cut-off JSON. If you have 50 names, do them as 5–10 batches and merge the outputs into one file before running `merge_new_entries.py`.

**Format of names.** Be specific. "Rabbi Yitzchak Isaac Epstein of Homel" is unambiguous; "R' Yitzchak Isaac" is not (multiple figures by this name). When ambiguity exists, qualify with a place, a generation, or a relationship: "R' Yitzchak Isaac, talmid of the Alter Rebbe."

**Hebrew names.** NotebookLM handles both languages. If the source is Hebrew, including the Hebrew name on your list improves match rate.

**`patch` records.** These let you re-extract for figures already in the dataset and have NotebookLM fill in only the gaps. Useful when you discover a new source that covers a figure better than the original. The merge script will only fill *null* fields — it never overwrites existing data.

**`not-found` records.** Don't silently drop names. If NotebookLM can't find a name in the sources, the record marker tells you which names need a different source. Treat these as a to-do list, not a failure.

**Verification.** Random-sample three records per batch and check that the cited claims appear in the actual source pages. If you find a hallucination, tighten the primer with: "If you cannot point to a specific page in the uploaded sources that supports a claim, set the field to null."

**Update known-IDs between batches.** After you `--apply` a batch, re-run `python scripts/known_ids.py > known.txt` so the next batch's primer reflects the larger dataset. This is how you prevent slow ID drift over time.

**One source per session.** Run one notebook per major source. Keeps NotebookLM's citation context tight.

**What this won't extract.** Relationship networks, full correspondence lists, story collections — these need the larger v0.1 schema (`full-spec-future.md` + `notebooklm-prompts.md`). The current schema is intentionally lean.
