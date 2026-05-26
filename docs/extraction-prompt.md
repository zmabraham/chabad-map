# NotebookLM Extraction Prompts — Current App Schema

Prompts for pulling new person and place entries out of Chabad history sources via NotebookLM, formatted to drop directly into `data/persons.json` and `data/places.json`.

Targets **today's app schema** (see `entry-schema.md`), not the future v0.1 expansion (`notebooklm-prompts.md`).

## Workflow at a glance

1. **Generate the "known IDs" block.** Run `python scripts/known_ids.py > known.txt`. This produces the deduplication context: every existing person and place ID with their canonical names. Paste this into each NotebookLM session so the model reuses existing IDs instead of coining new ones for figures already in the dataset.
2. **Run the system primer** (Prompt 0) once at the start of each NotebookLM session.
3. **Run the discovery pass** (Prompt 1) to enumerate everyone mentioned in the uploaded source.
4. **Run the extraction pass** (Prompt 2) in batches of 3–5 persons.
5. **Save the JSON output to `scripts/new_entries.json`.**
6. **Run `python scripts/merge_new_entries.py scripts/new_entries.json`** — fuzzy-matches against the existing dataset, flags duplicates, produces a clean patch.
7. **Review the patch, then splice the cleared entries into `data/persons.json` and `data/places.json`.**

## Output shape

NotebookLM should return a single JSON object with two arrays — one for new persons, one for new places it had to propose along the way:

```jsonc
{
  "persons": [ /* Person records per entry-schema.md */ ],
  "places":  [ /* Place records for any place_id used above that doesn't appear in the known places list */ ]
}
```

The merge script expects exactly this shape.

---

## Prompt 0 — System primer (paste once at session start)

```
You are a research assistant helping extend a structured historical database of
figures and places connected to the Chabad-Lubavitch chassidic movement.

GROUND RULES:
1. Only state facts that appear in the sources uploaded to this notebook. Never
   use prior knowledge to fill gaps. If a fact is not in the sources, the field
   is null.
2. When sources disagree, prefer the more chassidic-historical authoritative
   source (Beis Rebbi, Sefer HaToldos, the Rebbe's sichos, Igros Kodesh) over
   secondary literature. Note disagreements in the bio if material.
3. Output is JSON only — no preamble, no explanation, no markdown fences around
   the JSON. Plain valid JSON, parseable directly.
4. Years are Gregorian integers. If a source gives only a Hebrew year, convert
   it to Gregorian using the standard year + 3760/3761 mapping (Tishrei-based);
   if uncertain across that boundary, prefer the later year. Put a note in the
   bio if the Hebrew year is the primary source.
5. NEVER invent an ID for someone already in the KNOWN PERSONS list below. If
   you find them mentioned in this source, reuse the existing ID and only
   extract fields that are MISSING or in addition. Same rule for places.
6. For new persons not in the known list, propose a kebab-case ID following the
   pattern of existing IDs (e.g., "reb-firstname-lastname" or
   "rabbi-firstname-place" for figures named after their seat).
7. For new places, only propose if you have BOTH a coordinate (verified from
   Wikipedia or a reliable source) AND a modern country. Otherwise, omit the
   place_id field and describe the location in the bio for human follow-up.

KNOWN PERSONS (use these exact IDs; do not duplicate):
[PASTE the persons section from `scripts/known_ids.py` output here]

KNOWN PLACES (use these exact IDs; do not duplicate):
[PASTE the places section from `scripts/known_ids.py` output here]

Reply "Ready" when you have read this and the uploaded sources, then list the
sources you see.
```

---

## Prompt 1 — Discovery pass

Use to enumerate every named individual in the uploaded source before extracting full records.

```
DISCOVERY PASS

List every named individual mentioned in the uploaded sources who is connected
to Chabad history (Rebbes, family, chassidim, mashpi'im, contemporaries,
opponents, government officials they interacted with).

For each, output ONE row as plain text:

  proposed_id | common_name_en | name_he | generation_guess | one_line_who_they_are

where:
- proposed_id is kebab-case; if the person is already in the KNOWN PERSONS list,
  use the existing id verbatim and prefix the row with "[KNOWN]".
- generation_guess is 0-7 per the schema, or "?" if unclear.
- one_line_who_they_are is under 15 words.

Process the sources in narrative order. Give me the FIRST 20 rows, then stop and
wait for "continue" before giving the next 20.

Do NOT include duplicates. If a person appears under multiple spellings, list
once with all spellings comma-separated under common_name_en.
```

When the discovery list is complete, manually skim it for obvious duplicates against the known list, then feed the new entries into Prompt 2 in batches.

---

## Prompt 2 — Person extraction (batch)

The workhorse prompt. Pulls full structured records ready to merge.

```
PERSON EXTRACTION — BATCH OF 3-5

For each person listed below, output a JSON object matching this exact schema:

{
  "id": "kebab-case-slug",
  "name_en": "Full formal English name with title (Rabbi/Reb/Rebbetzin)",
  "name_he": "שם בעברית",
  "common_name": "Short conversational name (1-4 words)",
  "generation": 0,                       // integer 0-7
  "birth_year": 1795,                    // integer or null
  "death_year": 1864,                    // integer or null
  "birth_place_id": "place-id",          // null if unknown
  "death_place_id": "place-id",          // null if unknown
  "role": "Rebbe|Rebbetzin|Son of Rebbe|Family|Mashpia|Chossid|Pre-Chabad Teacher",
  "bio": "2-5 sentences, faithful to sources, no markdown",
  "primary_place_id": "place-id",        // optional - the seat they are identified with if NOT same as death_place
  "journey": [
    { "year": 1795, "place_id": "...", "event": "Born" },
    { "year": 1810, "place_id": "...", "event": "Studied" },
    { "year": 1812, "place_id": "...", "event": "Appointed Rav" },
    { "year": 1864, "place_id": "...", "event": "Passed away" }
  ]
}

EXTRACTION RULES:
- If a person is in the KNOWN PERSONS list, reuse their id. Output ONLY the
  fields the source provides that are missing or improving on the known record.
  Mark this case by adding "_action": "patch" to that object.
- For new persons, output the full record and "_action": "create".
- All place_ids must either be in KNOWN PLACES or be defined in your "places"
  output array with at minimum: id, name_en, name_he, lat, lng, modern_country.
- Generation: use the figure's PRIMARY era of activity, not their birth date.
  Hillel Paritcher (1795-1864) is generation 3 (Tzemach Tzedek era), not 1.
- Role: pick the single best fit from the controlled list. Wives of Rebbes
  are "Rebbetzin", sons of Rebbes who did not themselves become Rebbe are
  "Son of Rebbe", recognized chassidic mentors are "Mashpia", general followers
  are "Chossid", Baal Shem Tov / Maggid / their circle are "Pre-Chabad Teacher".
- Journey: include 2-10 steps capturing meaningful location changes. Birth and
  death are always included if known. Events should be short labels from this
  vocabulary when possible: Born, Studied, Married, Appointed Rav, Appointed
  Mashpia, Founded yeshiva, Imprisoned, Released, Escaped, Made aliya, Emigrated,
  Yechidus, Passed away. Use your own short label if none fit.
- bio: 2-5 sentences. Render-faithful prose. No editorial praise, no markdown.
  Anything noteworthy about them goes here.
- For each `place_id` you reference that is NOT in KNOWN PLACES, include the
  place in the "places" array of your output with verified lat/lng (search
  Wikipedia for the historical town to confirm). If you cannot verify the
  coordinates, set the place_id to null in the person record and mention the
  location name in the bio for manual follow-up.

OUTPUT a single JSON object:

{
  "persons": [ /* one record per person below */ ],
  "places":  [ /* any new places referenced */ ]
}

PERSONS TO EXTRACT (this batch):

1. (proposed_id from discovery list) — short name — one-line identifier
2. ...
3. ...

Output the JSON only.
```

---

## Practical guidance

**Batch size.** 3–5 persons per Prompt-2 invocation. NotebookLM truncates around 4000 tokens; larger batches return cut-off JSON.

**Hebrew names.** Use the spelling that appears in standard Chabad seforim (Beis Rebbi, Sefer HaToldos), not modern Israeli orthography. The dataset's existing entries follow chassidic-traditional spelling.

**Year of activity vs year of life.** Generation is about *when they did their work*, not when they were born or died. Reb Mendel Futerfas was born in 1906 (under the Rashab, generation 5) but his work as a mashpia was under the Rayatz and the Rebbe — that puts him in generation 7 in our dataset.

**Spot-check 10% of every batch.** Random-sample three records per batch and verify the cited claims appear in the actual source pages. NotebookLM's biggest failure mode is plausible hallucination from training data when sources are thin. If you find one, tighten the primer with: "If you cannot point to a specific page in the uploaded sources that supports a claim, set the field to null."

**One source per session.** Run one notebook per major source (or tight source-set). Keeps citations clean and reduces cross-contamination of facts between books.

**Iteration.** After each merge:
1. Re-run `python scripts/known_ids.py > known.txt`
2. Update the primer with the fresh list
3. Move to the next source

**What this won't extract reliably.** Relationship networks, full correspondence lists, story collections — these require the larger v0.1 schema. Use `notebooklm-prompts.md` if/when you decide to graduate the schema.
