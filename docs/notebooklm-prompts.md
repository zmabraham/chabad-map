# Chabad Map — NotebookLM Extraction Prompt Library

A set of prompts for pulling structured data out of Chabad history seforim using NotebookLM. Designed to produce JSON conforming to the v0.1 data spec.

## Workflow overview

NotebookLM works per-notebook with uploaded sources. You can't run one giant prompt across everything — you'll work in passes:

1. **Setup pass:** Upload sources to a NotebookLM notebook. Use one notebook per major source set (e.g., one notebook for *Beis Rebbi*, one for *Sefer HaToldos Admur HaZaken*, one for *Igros Kodesh Vol 1-5*). This keeps citations clean.
2. **Discovery pass:** Identify every named person mentioned in the source. Build a master id list.
3. **Extraction pass:** Pull structured person records in small batches (3-5 at a time).
4. **Story pass:** Extract sippurim and link them to the persons already in your dataset.
5. **Event & letter pass:** Pull events and correspondence as separate sweeps.
6. **Validation pass:** Use NotebookLM to cross-check claims against multiple sources.

Each prompt below is self-contained and can be pasted directly into NotebookLM's chat.

A practical note on output size: NotebookLM truncates long responses. Always request small batches and use "continue" to extend. Don't ask for "all persons in this book" — ask for "the next 5 persons starting with X."

---

## Prompt 1 — System/role primer (paste at start of each session)

Paste this once at the start of a session so subsequent prompts inherit the framing.

```
You are a research assistant helping to build a structured historical database 
of figures connected to the Chabad-Lubavitch chassidic movement. You will be 
asked to extract biographical data, stories, events, and correspondence from 
the sources I have uploaded to this notebook.

GROUND RULES:
1. Only state facts that appear in the uploaded sources. Never use your prior 
   knowledge of Chabad history to fill gaps. If a fact is not in the sources, 
   the field is null.
2. For every factual claim in your output, cite the specific source and page 
   number where it appears. Use NotebookLM's standard inline citation.
3. When sources disagree, note both versions and which source supports each.
4. Hebrew dates are primary. Always include the Hebrew date if the source 
   provides one, even if you can convert to Gregorian.
5. Mark uncertainty honestly. Use "circa": true for approximate dates. Use 
   confidence_level "fragmentary" for figures with thin documentation.
6. When asked for JSON, output ONLY valid JSON — no preamble, no explanation, 
   no markdown code fences unless explicitly requested.
7. Use the id slugs I provide. Never invent new ids for persons that already 
   have an established id in my system. If a person is mentioned but you 
   don't have an id for them, flag them in a "new_persons_detected" array.

Confirm you understand by replying "Ready" and listing the sources currently 
in this notebook.
```

---

## Prompt 2 — Discovery pass

Use this to build an initial roster of every named person in a source. Run on each uploaded book.

```
DISCOVERY TASK: List every named individual mentioned in the uploaded sources 
who is connected to Chabad history (Rebbes, family members, chassidim, 
contemporaries, scholars, opponents, government officials).

For each person, output a row with these fields, separated by ` | `:
- proposed_id (kebab-case English, e.g., "hillel-paritcher")
- display_name_en (how they are most commonly referred to in English)
- display_name_he (Hebrew form as it appears in the source)
- generation (1-7 Chabad generation, or "pre-chabad" / "contemporary" / "unknown")
- one_line_identifier (e.g., "Rav of Paritch", "Son of Mitteler Rebbe", 
  "Maskil opponent")
- source_pages (where they appear)

Output as a plain text table. Do NOT include duplicates — if a person appears 
with multiple name spellings, list once with all spellings comma-separated 
under display_name_en.

Process the sources in order. Give me the FIRST 25 persons you encounter. 
Then stop and wait for me to say "continue" before giving the next 25.
```

After running this on all sources, dedupe the list by hand (or with another prompt — see Prompt 8) and assign canonical ids. This id list is the input for the next prompt.

---

## Prompt 3 — Person extraction (batch)

The workhorse prompt. Pulls full structured records.

```
PERSON EXTRACTION TASK

I will give you a list of persons by id and name. For each one, extract a 
complete JSON record from the uploaded sources following the schema below.

SCHEMA (fields with * are required; others are null if not in sources):

{
  "id": "*",                          // use exactly the id I provide
  "names": {
    "display_he": "",                  // primary Hebrew form
    "display_en": "*",                 // primary English form  
    "display_yi": "",                  // Yiddish if attested
    "formal_he": "",                   // full "Harav X ben Y of Z" form
    "formal_en": "",
    "given_he": "*",
    "given_en": "*",
    "patronymic_he": "",
    "patronymic_en": "",
    "family_name": "",
    "place_designation": "",           // e.g., "Paritcher"
    "work_designation": "",            // e.g., "Tzemach Tzedek"
    "honorifics": [],                  // ["Reb", "Harav", "HaChossid", etc.]
    "acronym": "",                     // e.g., "Maharash", "Rashab"
    "aliases": [
      { "name": "", "language": "en|he|yi", "type": "common|short|variant" }
    ]
  },
  "gender": "male|female",
  "vitals": {
    "birth": {
      "hebrew_date": { "year": null, "month": null, "day": null },
      "gregorian_date": { "year": null, "month": null, "day": null, "precision": "day|month|year|decade|century" },
      "circa": false,
      "place_id": null,                // use known place id if exists, else propose
      "source_citation": ""            // page number from sources
    },
    "death": { /* same structure */ },
    "burial": { "place_id": null, "ohel": false, "source_citation": "" },
    "yahrzeit": { "hebrew_month": null, "hebrew_day": null }
  },
  "era": {
    "generation": null,                // 1-7
    "active_during_nesius_of": [],     // array of rebbe ids
    "primary_rebbe_id": null,
    "branch": "chabad-lubavitch|chabad-kapust|chabad-liadi|chabad-strashelye|chabad-avritch|chabad-niezhin|pre-chabad|non-chabad"
  },
  "roles": [
    {
      "type": "",                      // mashpia, chozer, rav, mazkir, talmid, chossid, etc.
      "of_person_id": null,            // if role is "chozer of X", "talmid of Y"
      "start_date": { "hebrew_year": null, "gregorian_year": null },
      "end_date": { "hebrew_year": null, "gregorian_year": null },
      "place_id": null,
      "notes": "",
      "source_citation": ""
    }
  ],
  "places_lived": [
    {
      "place_id": null,
      "start_date": { "hebrew_year": null },
      "end_date": { "hebrew_year": null },
      "role": "",
      "source_citation": ""
    }
  ],
  "relationships_extracted": [
    {
      "type": "father-son|mother-son|spouses|teacher-student|rebbe-chossid|mashpia-mekabel|siblings|father-in-law-son-in-law|chozer-of|gabbai-of",
      "from_person": "id or name if id unknown",
      "to_person": "id or name if id unknown",
      "directional": true,
      "source_citation": ""
    }
  ],
  "notability_tier": null,             // 1=Rebbe, 2=rebbe-family/major-chossid, 3=notable, 4=named-figure, 5=mentioned-in-passing
  "bio": {
    "claim_to_fame_en": "",            // ONE sentence — what makes them historically significant per the sources
    "short_en": "",                    // 2-3 sentence summary
    "medium_en_md": "",                // 1-2 paragraphs, markdown, with inline source citations
  },
  "content_links": {
    "works_authored_titles": [],       // titles of seforim/maamarim attributed to them
    "yechidus_records": [
      { "rebbe_id": null, "year_he": null, "place_id": null, "source_citation": "" }
    ]
  },
  "tags": [],
  "metadata": {
    "confidence_level": "well-documented|documented|partial|fragmentary|legendary",
    "needs_research_flags": [],        // ["birth_year_uncertain", "no_death_date", etc.]
    "new_persons_detected": [],        // any persons mentioned in this record who don't have ids yet
    "new_places_detected": []          // same for places
  }
}

EXTRACTION RULES:
- Output an array of JSON objects, one per requested person.
- If a field is not supported by the sources, set it to null (not "unknown" 
  or empty string unless the schema specifies empty string).
- Every fact-bearing field needs a source_citation indicating the page(s) 
  where it appears in the uploaded sources.
- For relationships, give "to_person" / "from_person" as ids if known; if 
  unknown, give the name as it appears in the source and add the name to 
  "new_persons_detected".
- The claim_to_fame_en must be a single sentence that captures what the 
  sources emphasize about this person's significance. Avoid generic praise.
- Output ONLY the JSON array. No preamble, no explanation, no markdown fences.

PERSONS TO EXTRACT (batch of 3):

1. id: alter-rebbe — Rabbi Schneur Zalman of Liadi (אדמו"ר הזקן)
2. id: mitteler-rebbe — Rabbi Dovber Schneuri (אדמו"ר האמצעי)
3. id: tzemach-tzedek — Rabbi Menachem Mendel Schneersohn (צמח צדק)

KNOWN PERSON IDS (use these for any references):
[paste your current id list here, e.g.:]
- alter-rebbe, mitteler-rebbe, tzemach-tzedek, maharash, rashab, rayatz, rebbe
- rebbetzin-chaya-mushka, levik-schneerson, rebbetzin-chana
- hillel-paritcher, aizik-homiler, mendel-futerfas
- ...

KNOWN PLACE IDS:
- liadi, liozna, lubavitch, mezeritch, rostov, riga, otwock, warsaw, paris, 
  marseille, new-york, crown-heights, 770
- ...

Begin.
```

After running, validate the JSON, add ids for `new_persons_detected`, then run the next batch with the updated id list.

---

## Prompt 4 — Story / sippur extraction

The Chabad world is dense with stories. They're often the primary source of detail for lesser-known figures. This prompt extracts them as discrete entities.

```
STORY EXTRACTION TASK

Find every sippur (story, anecdote, historical narrative) in the uploaded 
sources and extract each one as a JSON record per the schema below.

A "story" qualifies if:
- It describes a specific event or incident
- It involves at least one named person
- It is narrated as a discrete unit (not just a biographical aside)

For each story, extract:

{
  "id": "",                            // generate a descriptive slug, e.g., 
                                       // "alter-rebbe-tish-hillel-interruption"
  "title_en": "",                      // 5-10 word descriptive title
  "title_he": "",                      // Hebrew version of title if natural
  "summary_en": "",                    // 2-4 sentence retelling of the story
  "summary_he": "",                    // Hebrew retelling
  "full_text_excerpt": "",             // a short direct quote from the source 
                                       // (under 50 words) if available
  "approximate_date": {
    "hebrew_year": null,
    "gregorian_year": null,
    "circa": true,
    "rebbe_era": null,                 // which Rebbe was nasi when this 
                                       // happened (id)
    "date_basis": ""                   // how the date is established 
                                       // (e.g., "before Alter Rebbe's arrest")
  },
  "place_ids": [],                     // all locations involved
  "new_places_detected": [],
  "persons_mentioned": [
    {
      "person_id": null,               // if you know the id, use it
      "person_name_as_appears": "",    // the exact name string from the source
      "role_in_story": "protagonist|rebbe|antagonist|witness|messenger|family|other",
      "notes": ""                      // anything specific about their part
    }
  ],
  "new_persons_detected": [],
  "themes": [],                        // chassidic themes: bittul, ahavas-yisrael, 
                                       // emunah, mesiras-nefesh, hashgacha-pratis, 
                                       // chiddush-baTorah, kabbalas-ol, etc.
  "story_type": "yechidus|farbrengen|miracle|teaching|encounter|historical-event|family|prison|escape|other",
  "moral_or_point": "",                // what the source presents as the takeaway
  "source_citation": "",               // page and source
  "source_certainty": "well-attested|attested|oral-tradition|disputed",
  "told_by": "",                       // if the story is attributed to a specific 
                                       // narrator (e.g., "told by the Rebbe in 
                                       // Sicha of Yud Shevat 5712")
  "related_story_ids": [],             // if this story has variants or parallels
  "needs_research_flags": []
}

EXTRACTION RULES:
- Each story is its own JSON object. Output an array.
- For persons_mentioned, list everyone named in the story — protagonists, 
  bystanders, those referenced in passing.
- If a story exists in multiple versions across sources, create separate 
  records and link them via related_story_ids.
- The summary_en must be a faithful retelling, not interpretation. Save 
  interpretation for moral_or_point.
- full_text_excerpt is a SHORT direct quotation under 50 words from the source.
- Cite the source page for every story.

PARAMETERS:
- Extract from: [specify source name and page range, e.g., "Beis Rebbi pp. 
  100-150" or "Likutei Sippurim Perlow chapter 3"]
- Batch size: 5 stories per response. Stop after 5 and wait for "continue".

KNOWN PERSON IDS:
[paste list]

KNOWN PLACE IDS:
[paste list]

Begin extraction.
```

---

## Prompt 5 — Event extraction

Events are dated historical occurrences (arrests, escapes, founding of yeshivas, publications, etc.) — distinct from stories, which are narratives.

```
EVENT EXTRACTION TASK

Identify discrete historical events mentioned in the sources and extract each 
as JSON per the schema below.

An "event" qualifies if:
- It has a date or approximate date
- It has a location
- It is treated as historically significant by the sources (not just routine)
- It is NOT primarily narrative (those are stories — see Prompt 4)

Examples: an arrest, a release, a yeshiva founding, a publication, a move, 
an escape, a yechidus that had historical consequence, a major farbrengen, 
a takanah, a major dispute.

{
  "id": "",
  "title_en": "",
  "title_he": "",
  "date": {
    "hebrew": { "year": null, "month": null, "day": null },
    "gregorian": { "year": null, "month": null, "day": null },
    "precision": "day|month|year"
  },
  "end_date": { /* same — for multi-day events */ },
  "place_ids": [],
  "people": [
    { "person_id": "", "role": "subject|participant|witness|opponent|authority" }
  ],
  "type": "arrest|imprisonment|release|trial|escape|move|yechidus|farbrengen|publication|appointment|takanah|dispute|founding|fire|pogrom|decree|emigration|aliyah|wedding|bris|other",
  "significance": "",                  // why it matters in Chabad history
  "description_md": "",                // 1-3 paragraphs, markdown
  "consequences": [],                  // later events, publications, or 
                                       // developments that flow from this
  "commemorated_as": "",               // if observed annually (e.g., 
                                       // "Yud-Tes Kislev", "Yud-Beis Tammuz", 
                                       // "Yud Shevat")
  "source_citations": [],
  "tags": []
}

Output an array. Batch of 5 events at a time.

PARAMETERS:
- Extract from: [specify source]
- Focus on events: [optional — e.g., "events occurring during the Alter 
  Rebbe's nesius" or "all events 5687-5700"]

KNOWN IDS:
[paste]

Begin.
```

---

## Prompt 6 — Letter / correspondence extraction

For Igros Kodesh volumes specifically. This is the highest-volume entity by far.

```
LETTER EXTRACTION TASK

The source is a volume of Igros Kodesh. Extract each letter as a JSON record.

{
  "id": "",                            // format: letter-{author-id}-{he-year}-{he-month}-{he-day}-{sequence}
                                       // e.g., letter-rayatz-5688-iyar-05-001
  "from_person_id": "",
  "to_person_id": null,                // null if recipient unknown or general 
                                       // ("anash", "to the talmidim")
  "to_general_audience": null,         // if not to a specific person
  "date": {
    "hebrew": { "year": null, "month": null, "day": null },
    "gregorian": { "year": null, "month": null, "day": null }
  },
  "from_place_id": null,
  "to_place_id": null,
  "topic_tags": [],                    // halacha, encouragement, family, 
                                       // chassidus-explanation, organizational, 
                                       // shidduch, condolence, condemnation, 
                                       // refuah, parnasa, hiskashrus, etc.
  "summary_en": "",                    // 2-3 sentences on what the letter is about
  "language": "he|yi|en|ru",
  "publication_reference": {
    "publication": "",                 // e.g., "Igros Kodesh Admur HaRayatz"
    "volume": null,
    "letter_number": null,
    "page": null
  },
  "persons_mentioned_in_body": [],     // ids or names of persons the letter 
                                       // discusses (beyond sender/recipient)
  "places_mentioned_in_body": [],
  "notable_excerpt": "",               // a short quoted passage under 50 
                                       // words if particularly significant
  "tags": []
}

EXTRACTION RULES:
- One record per letter. Output as array.
- If a letter has multiple recipients, the to_person_id is the primary one; 
  list others under persons_mentioned_in_body.
- topic_tags should be the actual subjects of the letter, not generic labels.
- Don't include the full letter body — only summary and short excerpt.

PARAMETERS:
- Source: [Igros Kodesh volume X]
- Letters to extract: [e.g., letters 1-15 or letters from year 5688]
- Batch size: 10 letters per response.

KNOWN IDS:
[paste]

Begin.
```

---

## Prompt 7 — Place extraction

```
PLACE EXTRACTION TASK

Identify every geographic location mentioned in the sources and extract each 
as JSON.

{
  "id": "",                            // kebab-case, prefer historical name 
                                       // (e.g., "liadi" not "lyady")
  "names": {
    "en_historical": "",               // name as it appears in chassidic sources
    "en_modern": "",                   // current English name
    "he": "",
    "yi": "",
    "ru_historical": "",
    "local_modern": ""                 // current local language
  },
  "modern_country": "",
  "historical_jurisdictions": [
    { "name": "", "start_year": null, "end_year": null }
  ],
  "coordinates": { "lat": null, "lng": null },
                                       // include if known with reasonable 
                                       // certainty; otherwise null
  "type": "shtetl|town|city|village|region|country|cemetery|ohel|building",
  "chabad_significance": "",           // what role it plays in Chabad history
  "period_of_significance": {
    "start_year_he": null,
    "end_year_he": null
  },
  "notable_events_here": [],           // event ids if known, else descriptions
  "associated_persons": [],            // person ids primarily associated 
                                       // (e.g., "rav of", "born in", "died in")
  "source_citations": [],
  "needs_research_flags": []
}

Output array. Batch of 10 places.

For coordinates, use null unless you are confident — do not invent 
coordinates. They can be filled in later from a geocoding service.

Begin extraction.
```

---

## Prompt 8 — Deduplication / canonicalization

Run periodically to catch duplicates that crept in across sources.

```
DEDUPLICATION TASK

I will paste a list of person entries that may contain duplicates 
(same person under different spellings or designations). Your job is to 
identify which entries refer to the same person.

For each suspected duplicate group, output:

{
  "canonical_id": "",                  // which id should win
  "merge_into_canonical": [],          // other ids to merge into it
  "reasoning": "",                     // why you believe these are the same 
                                       // person (cite sources)
  "uncertainty": "high|medium|low",    // your confidence
  "differentiating_facts": []          // if not the same, what distinguishes 
                                       // them (e.g., "different death years")
}

Be conservative. Two figures with similar names but different fathers, 
generations, or cities are likely different people. When uncertain, mark 
"high" uncertainty and leave for human review.

ENTRIES TO REVIEW:
[paste 10-30 entries here]

Begin.
```

---

## Prompt 9 — Cross-source validation

After you have a draft record, use this prompt to check it against additional sources.

```
VALIDATION TASK

I have an existing record for the following person:

[paste full JSON record]

Cross-check every factual claim in this record against the uploaded sources 
in this notebook. For each claim:

- CONFIRMED: claim is supported by an additional source (cite which one)
- CONFLICTING: a source contradicts the claim (cite source and what it says)
- UNSUPPORTED: no source in this notebook addresses this claim
- ADDITIONAL: information in the sources that should be added to the record

Output a structured review:

{
  "person_id": "",
  "confirmed_facts": [
    { "claim": "", "additional_source": "" }
  ],
  "conflicts": [
    { 
      "claim_in_record": "", 
      "conflicting_source": "", 
      "conflicting_claim": "" 
    }
  ],
  "additions": [
    { "field": "", "new_value": "", "source": "" }
  ],
  "overall_assessment": "consistent|minor-revisions-needed|major-conflicts"
}

Begin.
```

---

## Prompt 10 — Story-to-entity linking

After you have both person records and story records extracted, run this to verify and strengthen the cross-links.

```
STORY LINKING TASK

I will paste a story record. Cross-reference it against the uploaded sources 
and the known id list, then:

1. For every person mentioned in the story (named, hinted at, or referenced 
   by title), assign a person_id from the known list. If no matching id 
   exists, propose a new one and flag.
2. For every place mentioned, assign a place_id or propose a new one.
3. Identify the approximate date as precisely as possible, anchoring to:
   - Direct dates in the source
   - The nesius of the Rebbe at the time
   - Reference events ("after the arrest", "before the publication of Tanya")
4. Identify any other stories in the sources that are variants or parallels 
   of this one (related_story_ids).
5. Identify any works, letters, or events the story references.

STORY:
[paste story JSON]

KNOWN IDS:
[paste lists]

Output the updated story JSON with all links populated.

Begin.
```

---

## Practical tips for working with NotebookLM

**Notebook organization.** Use separate notebooks for different source-set themes — early Chabad seforim in one notebook, Igros Kodesh in another, post-war seforim in a third. This keeps NotebookLM's citation context manageable and you can run extraction in parallel.

**Source uploads.** NotebookLM accepts PDFs, Google Docs, websites, and text. For Hebrew seforim, prefer searchable PDF (OCR'd) over scanned image PDFs. HebrewBooks.org PDFs are often searchable; Otzar HaChochma PDFs sometimes need re-OCR. Chabad library texts are usually well-digitized.

**Batch size.** NotebookLM responses get truncated past ~4000 tokens. Always prompt for small batches (3-5 persons, 5 stories, 10 letters) and use "continue" to extend. If output looks cut off mid-JSON, say "continue from where you stopped, do not repeat earlier output."

**Citation extraction.** NotebookLM appends inline citations (e.g., "[1]") that hyperlink to source passages. When you copy the JSON output, those citations come along. Either parse them programmatically into your `source_citations` field, or ask NotebookLM explicitly: "Replace inline footnote citations with explicit source name and page references in the source_citation fields."

**Hebrew text handling.** NotebookLM handles Hebrew well in both input and output. If extraction quality drops, it may be because the PDF text layer is bad — try a different source edition.

**Hallucination risk.** The biggest risk is NotebookLM filling in plausible-sounding facts from its training data rather than the sources. The system prompt above mitigates this, but spot-check: pick 5 random claims from each batch and verify the cited page actually says what's claimed. If hallucinations appear, tighten the system prompt with: "If you cannot find this fact in a specific cited page of the uploaded sources, set the field to null. Do not use prior knowledge."

**Iteration cycle.** A practical cycle for one source book:
1. Run discovery (Prompt 2) — get the roster
2. Dedupe and assign canonical ids (Prompt 8 + manual review)
3. Run person extraction in batches (Prompt 3)
4. Run story extraction (Prompt 4)
5. Run event extraction (Prompt 5)
6. Run letter extraction if applicable (Prompt 6)
7. Spot-check 10% by reading source against record
8. Merge into your master dataset
9. Run validation (Prompt 9) against any new sources

**Reasonable expectation.** A single mid-length sefer (~300 pages) takes roughly 4-8 hours of NotebookLM session work to extract thoroughly. Don't try to do it all in one sitting — accuracy degrades when you're rushing.

---

## What this won't do

NotebookLM is a strong extraction tool but it isn't your final pipeline. Plan for:

- **Manual review.** Every record needs human eyes before it enters the canonical dataset. Especially: birth/death dates, tier assignments, claims about controversial matters (Kapust split, the petira of Rebbeim, etc.).
- **De-anglicization.** NotebookLM tends to over-translate Hebrew/Yiddish to English. You'll want a second pass to restore Hebrew forms where appropriate.
- **Cross-language reconciliation.** A figure named in a Hebrew source and an English source may not be auto-recognized as the same person. Prompt 8 helps but isn't perfect.
- **Igros Kodesh at scale.** The Rebbe's Igros Kodesh alone is 30+ volumes with thousands of letters. NotebookLM works letter-by-letter; for full extraction you may eventually want a dedicated pipeline. Start with Volumes 1-3 to test the workflow before committing.

Use the prompts as a starting point — adjust the schemas and rules as you discover what works for your sources.
