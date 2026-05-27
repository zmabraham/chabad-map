"""Extract per-person journey arrays from the master timeline events.

Reads:
  - scripts/event_index.json   (person_id -> list of event refs)
  - scripts/events_source.json (full events corpus)
  - data/places.json           (place lookup)
  - stories/{event_id}.md      (optional, full body)

Writes:
  - scripts/journey_patch.json
  - scripts/journey_extraction_report.md
"""

import json
import os
import re
import sys
from collections import Counter, defaultdict

ROOT = r"C:\Users\rabbi\OneDrive\Desktop\chabad-map\chabad-map"
STORIES_DIR = r"C:\Users\rabbi\AppData\Local\Temp\mtc\public\stories"

# --- 1. Load data ---
with open(os.path.join(ROOT, "scripts", "event_index.json"), encoding="utf-8") as f:
    EVENT_INDEX = json.load(f)
with open(os.path.join(ROOT, "scripts", "events_source.json"), encoding="utf-8") as f:
    EVENTS_LIST = json.load(f)
with open(os.path.join(ROOT, "data", "places.json"), encoding="utf-8") as f:
    PLACES = json.load(f)
with open(os.path.join(ROOT, "data", "persons.json"), encoding="utf-8") as f:
    PERSONS = json.load(f)

EVENTS_BY_ID = {e["id"]: e for e in EVENTS_LIST}
PERSONS_BY_ID = {p["id"]: p for p in PERSONS}

# --- 2. Place name patterns ---
# Build a list of (regex, place_id) ordered with longer/more specific first.
# We use word boundaries.

# Manual aliases / variants -> place_id. The base name_en (stripped of parens) is added automatically.
EXTRA_ALIASES = {
    "mezhibuzh": ["Medzhibozh", "Mezibuz", "Medzhybizh"],
    "anipoli": ["Hannopil", "Annopol", "Anipol", "Anipoli"],
    "vilna": ["Vilnius", "Vilna"],
    "lubavitch": ["Lyubavichi", "Lubavitch"],
    "petersburg": ["St. Petersburg", "Saint Petersburg", "Petersburg", "St Petersburg"],
    "leningrad": ["Leningrad"],
    "new-york": ["770", "Crown Heights", "Brooklyn", "Eastern Parkway", "New York City"],
    "berditchev": ["Berdychiv", "Berditchov"],
    "hadiach": ["Haditch", "Hadiach"],
    "homel": ["Gomel", "Homel"],
    "kapust": ["Kopys", "Kopust", "Kapust"],
    "niezhin": ["Nizhyn", "Niezhin", "Nezhin"],
    "avritch": ["Ovruch", "Avritch"],
    "bobruisk": ["Babruisk", "Bobruisk"],
    "paritch": ["Parichi", "Paritch"],
    "yekaterinoslav": ["Dnipro", "Dnipropetrovsk", "Yekaterinoslav"],
    "nikolaev": ["Mykolaiv", "Nikolayev", "Nikolaev"],
    "alma-ata": ["Almaty", "Alma-Ata", "Alma Ata"],
    "lviv": ["Lwow", "Lvov", "Lviv", "Lemberg"],
    "tzfat": ["Safed", "Tsfat", "Tzfas", "Tzfat"],
    "kfar-chabad": ["Kfar Chabad"],
    "nachlat-har-chabad": ["Kiryat Malachi", "Nachlat Har Chabad"],
    "nevel": ["Nevel"],
    "chashnik": ["Chashniki", "Chashnik"],
    "yanovitch": ["Yanavichy", "Yanovich", "Yanovitch"],
    "tiberias": ["Teveria", "Tiberias", "Tveria"],
    "kremenchug": ["Kremenchuk", "Kremenchug"],
    "kharkov": ["Kharkiv", "Kharkov"],
    "kishinev": ["Chisinau", "Kishinev"],
    "ludmir": ["Volodymyr-Volynskyi", "Ludmir", "Vladimir-Volynsky"],
    "kletzk": ["Kletsk", "Kletzk"],
    "borisov": ["Barysaw", "Borisov"],
    "pohar": ["Pogar", "Pohar"],
    "rakshik": ["Rokiskis", "Rakshik"],
    "kazimirov": ["Kazimirovo", "Kazimirov"],
    "beshankovich": ["Beshankovichy", "Beshankovich"],
    "mezritch": ["Mezhirichi", "Mezritch", "Mezeritch", "Mezhirich"],
    "smilovitz": ["Smilavichy", "Smilovitz"],
    "krichev": ["Krychaw", "Krichev"],
    "smilyan": ["Smila", "Smilyan"],
    "yakshitz": ["Yakshitsy", "Yakshitz"],
    "zuravitz": ["Zhuravichi", "Zuravitz"],
    "krasnaluki": ["Krasnoluki", "Krasnaluki"],
    "repka": ["Ripky", "Repka"],
    "rogatchov": ["Rahachow", "Rogatchov", "Rogachev"],
    "prohovitch": ["Pohrebyshche", "Prohovitch", "Pohrebishche"],
    "podobranka": ["Poddobryanka", "Podobranka"],
    "chortkov": ["Chortkiv", "Chortkov"],
    "lizhensk": ["Lezajsk", "Lizhensk"],
    "nikolsburg": ["Mikulov", "Nikolsburg"],
    "polonne": ["Polonnoye", "Polonne"],
    "ula": ["Ula"],
    "disna": ["Dzisna", "Disna"],
    "krislava": ["Kraslava", "Krislava"],
    "ruzhin": ["Ruzhyn", "Ruzhin"],
    "fastov": ["Fastiv", "Fastov"],
    "shvintzian": ["Svencionys", "Shvintzian", "Svintsyan"],
    "koretz": ["Korets", "Koretz", "Korzec"],
    "zlotchov": ["Zolochiv", "Zlotchov", "Zloczow"],
    "kobilnik": ["Narach", "Kobilnik"],
    "sadigura": ["Sadhora", "Sadigura"],
    "klimovitch": ["Klimavichy", "Klimovitch", "Klimovichi"],
    "strashelye": ["Starasel'lye", "Strashelye", "Strashelya"],
    "gzhatsk": ["Gagarin", "Gzhatsk"],
    "kurenets": ["Kurenyets", "Kurenets"],
    "rostov": ["Rostov-on-Don", "Rostov on Don", "Rostov"],
    "new-york": ["770", "Crown Heights", "Brooklyn", "Eastern Parkway", "New York City", "New York"],
}

def base_name(name_en):
    # "Anipoli (Hannopil)" -> "Anipoli"
    return re.sub(r"\s*\([^)]*\)\s*", "", name_en).strip()

# Build (alias_regex, place_id) list. Longer aliases first.
def build_place_patterns():
    pairs = []  # (alias_string, place_id)
    for p in PLACES:
        pid = p["id"]
        base = base_name(p["name_en"])
        pairs.append((base, pid))
        # If name has parens variant
        m = re.search(r"\(([^)]+)\)", p["name_en"])
        if m:
            for v in re.split(r"[/,]", m.group(1)):
                v = v.strip()
                if v:
                    pairs.append((v, pid))
        for alias in EXTRA_ALIASES.get(pid, []):
            pairs.append((alias, pid))
    # Dedupe and sort by length desc
    seen = set()
    out = []
    for alias, pid in pairs:
        key = (alias.lower(), pid)
        if key in seen:
            continue
        seen.add(key)
        out.append((alias, pid))
    out.sort(key=lambda x: -len(x[0]))
    # Compile regexes
    compiled = []
    for alias, pid in out:
        # Use word-boundary; for 770 we want digit boundary which \b handles
        # For multi-word phrases use raw escape
        pattern = r"\b" + re.escape(alias) + r"\b"
        compiled.append((re.compile(pattern, re.IGNORECASE), alias, pid))
    return compiled

PLACE_PATTERNS = build_place_patterns()

def find_places_in_text(text):
    """Return list of place_ids found in text, in order, deduped."""
    if not text:
        return []
    found = []
    seen = set()
    # We track character positions to avoid double-matching the same span
    masked = list(text)
    for regex, alias, pid in PLACE_PATTERNS:
        for m in regex.finditer(text):
            # Skip if span already masked (i.e. matched by a longer alias)
            if any(c == "\0" for c in masked[m.start():m.end()]):
                continue
            for i in range(m.start(), m.end()):
                masked[i] = "\0"
            if pid not in seen:
                seen.add(pid)
                found.append(pid)
    return found

# A word looks like a place mention if it's "in/from/to <CapWord>" but didn't match anything.
LOCATION_HINT_RE = re.compile(r"\b(?:in|from|to|at|near|of|near to|toward)\s+([A-Z][a-zA-ZÀ-ſ'’\-]{3,30})\b")
# Common false-positives to ignore
LOC_STOPWORDS = {
    "The", "Rabbi", "Rebbe", "Rebbetzin", "Reb", "Russia", "Russian", "Ukraine", "Ukrainian",
    "Poland", "Polish", "Belarus", "Lithuania", "Lithuanian", "Israel", "Israeli", "America",
    "American", "Europe", "European", "Soviet", "USSR", "Empire", "Czarist", "Czar", "Tzarist",
    "G-d", "God", "Hashem", "Torah", "Talmud", "Chassidim", "Chassidut", "Chassidus", "Chabad",
    "Lubavitch", "Jewish", "Jews", "Russia", "Yiddish", "Hebrew",
    "Mr", "Mrs", "Dr", "Cheshvan", "Tishrei", "Kislev", "Tevet", "Shevat", "Adar", "Nissan", "Iyar",
    "Sivan", "Tammuz", "Av", "Elul", "Sukkot", "Sukkos", "Pesach", "Shavuot", "Shavuos",
    "Rosh", "Hashanah", "Hashana", "Yom", "Kippur", "Purim", "Chanukah", "Hanukkah", "Tishabav",
    "Shabbat", "Shabbos", "Shabbat", "Hosafot",
    "January", "February", "March", "April", "May", "June", "July", "August", "September",
    "October", "November", "December",
    "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday",
    "He", "She", "It", "They", "We", "I", "His", "Her", "Their", "Our", "My",
    "When", "Where", "Who", "What", "Why", "How", "Which", "There", "Then", "Now",
    "Maamar", "Sicha", "Sichos", "Maamarim", "Hayom", "Yom", "Sefer", "Sefarim",
    "Schneersohn", "Schneerson", "Yitzchak", "Menachem", "Mendel", "Yosef", "Yehuda",
    "Shmuel", "Shalom", "DovBer", "Dovber", "Moshe", "Levi", "Avraham", "Yisrael",
    "Chaya", "Mushka", "Mussia", "Rivka", "Sarah", "Devora", "Esther", "Leah",
    "Maggid", "Mezeritch", "Anipoli",  # we already match these via aliases; safe to ignore
}
def collect_unresolved_location_hints(text, found_ids, counter):
    if not text:
        return
    # If text contains any matched place_ids, skip the brute scan? No — there could be others alongside.
    for m in LOCATION_HINT_RE.finditer(text):
        word = m.group(1)
        if word in LOC_STOPWORDS:
            continue
        # If find_places_in_text catches this word, skip
        if find_places_in_text(word):
            continue
        counter[word] += 1

# --- 3. Event classification ---
BORN_PAT = re.compile(r"\b(birth(\s+of)?|born|was born|is born)\b", re.IGNORECASE)
DEATH_PAT = re.compile(r"\b(passed away|passing|yahrzeit|died|histalkus|funeral|burial|interred)\b", re.IGNORECASE)
MARRIED_PAT = re.compile(r"\b(married|wedding|chasunah|engagement|engaged)\b", re.IGNORECASE)
APPOINTED_RAV_PAT = re.compile(r"\b(appointed (as )?rav|became rav|named rav|elected rav|served as rav|crowned|accepts the leadership|accepts leadership|becomes the .*rebbe|became rebbe|assumed leadership|nasi)\b", re.IGNORECASE)
APPOINTED_MASHPIA_PAT = re.compile(r"\bmashpia\b", re.IGNORECASE)
FOUNDED_PAT = re.compile(r"\b(founded|established|opened|inaugurat\w+|set up|formed)\b.*\b(yeshiva|tomchei tmimim|chabad house|community|school|kollel)\b", re.IGNORECASE)
ARRESTED_PAT = re.compile(r"\b(arrested|imprisoned|arrest|imprisonment|jailed)\b", re.IGNORECASE)
RELEASED_PAT = re.compile(r"\b(released|freedom|freed|liberation|liberated|yud[ -]?tes kislev|yud[ -]?gimmel kislev)\b", re.IGNORECASE)
ESCAPED_PAT = re.compile(r"\b(escaped|fled|flight|smuggled out)\b", re.IGNORECASE)
ALIYA_PAT = re.compile(r"\b(made aliya|aliyah|immigrat\w+ to (eretz yisrael|israel|the holy land)|arriv\w+ in (jerusalem|tzfat|hebron|tiberias))\b", re.IGNORECASE)
EMIGRATE_PAT = re.compile(r"\b(emigrat\w+|immigrat\w+ to (america|the united states|the us)|arriv\w+ in (america|new york))\b", re.IGNORECASE)
YECHIDUS_PAT = re.compile(r"\byechidus\b", re.IGNORECASE)
TRAVEL_PAT = re.compile(r"\b(traveled|travelled|journey to|set out for|moved to|relocated|arriv\w+ in|came to|departed for)\b", re.IGNORECASE)
EXILE_PAT = re.compile(r"\b(exile|exiled|banish\w+|deport\w+)\b", re.IGNORECASE)
ESCAPED_FROM_RUSSIA_PAT = re.compile(r"\bgreat escape\b|\bexodus from russia\b", re.IGNORECASE)
SETTLED_PAT = re.compile(r"\b(settled in|made his home in|established his court in|moved his court to)\b", re.IGNORECASE)
STUDY_PAT = re.compile(r"\b(studied (at|in|under)|learned (at|in|under)|attended .{0,30}yeshiva|entered the yeshiva)\b", re.IGNORECASE)

def classify_event(text):
    """Return event label string or None to skip."""
    if not text:
        return None
    if DEATH_PAT.search(text):
        return "Passed away"
    if BORN_PAT.search(text):
        return "Born"
    if MARRIED_PAT.search(text):
        return "Married"
    if RELEASED_PAT.search(text):
        return "Released"
    if ARRESTED_PAT.search(text):
        return "Imprisoned"
    if ESCAPED_FROM_RUSSIA_PAT.search(text):
        return "Escaped Russia"
    if ESCAPED_PAT.search(text):
        return "Escaped"
    if ALIYA_PAT.search(text):
        return "Made aliya"
    if EMIGRATE_PAT.search(text):
        return "Emigrated"
    if FOUNDED_PAT.search(text):
        return "Founded yeshiva"
    if APPOINTED_RAV_PAT.search(text):
        return "Appointed Rav"
    if APPOINTED_MASHPIA_PAT.search(text):
        return "Appointed Mashpia"
    if YECHIDUS_PAT.search(text):
        return "Yechidus"
    if EXILE_PAT.search(text):
        return "Exiled"
    if SETTLED_PAT.search(text):
        return "Settled"
    if STUDY_PAT.search(text):
        return "Studied"
    if TRAVEL_PAT.search(text):
        return "Traveled"
    return None

# --- 4. Get story body for an event ---
def get_story_text(event):
    """Get the full story text for an event, combining title/summary/body."""
    title = event.get("title_en") or ""
    summary = event.get("summary_en") or ""
    body = event.get("story_body") or ""
    if not body:
        # Try loading from md file
        eid = event["id"]
        path = os.path.join(STORIES_DIR, f"{eid}.md")
        if os.path.exists(path):
            try:
                with open(path, encoding="utf-8") as f:
                    body = f.read()
            except Exception:
                pass
    return f"{title}\n{summary}\n{body}"

# --- Patterns that suggest the event is NOT about this person's actual life moment
# (e.g., yahrzeit commemorations, retellings, later citations) ---
COMMEMORATION_PAT = re.compile(
    r"\b(yahrzeit|hilula|hilulah|anniversary|commemorat\w*|retold|in honor of|annual|each year|every year|in memory of|memorial|on the occasion of|tribute)\b",
    re.IGNORECASE,
)
TEACHING_PAT = re.compile(
    r"\b(delivered a (maamar|sicha|talk|discourse)|maamar|sicha|farbrengen|published|wrote a letter|in a letter|teaching|class on|edition of|reprint|the work .* by|booklet|essay)\b",
    re.IGNORECASE,
)

# --- 5. Build journey for a single person ---
def build_journey_for_person(person_id, refs):
    """Return list of journey steps (dicts)."""
    person = PERSONS_BY_ID.get(person_id, {})
    person_name = person.get("name_en", "") or ""
    common_name = (person.get("common_name") or "").strip()
    # All name tokens to detect "is this event about THIS person?"
    # Stop-words that match too many people / too common to be discriminative.
    NAME_STOPWORDS = {
        "rabbi", "reb", "rav", "rebbe", "rebbetzin", "schneersohn", "schneerson",
        "menachem", "mendel", "shneur", "zalman", "yosef", "yitzchak", "shalom",
        "dovber", "shmuel", "yehuda", "leib", "moshe", "chaim", "chaya", "mushka",
        "yisrael", "chassidim", "lubavitch", "chabad", "alter", "mitteler",
        "tzemach", "tzedek", "maharash", "rashab", "rayatz", "the",
    }
    name_tokens = set()
    for s in (person_name, common_name):
        if s:
            for tok in re.split(r"[ ,\-'.()]+", s):
                tok = tok.strip().lower()
                if len(tok) >= 4 and tok not in NAME_STOPWORDS:
                    name_tokens.add(tok)
    # If no discriminative tokens remain, fall back to *all* tokens (best effort)
    if not name_tokens:
        for s in (person_name, common_name):
            if s:
                for tok in re.split(r"[ ,\-'.()]+", s):
                    tok = tok.strip().lower()
                    if len(tok) >= 4:
                        name_tokens.add(tok)

    # Birth/death anchors
    birth_year = person.get("birth_year")
    death_year = person.get("death_year")
    birth_place = person.get("birth_place_id")
    death_place = person.get("death_place_id")

    # Score & process candidate events
    candidates = []  # (year, event_label, place_id, significance, event_id)

    # Always add birth/death from persons.json if known
    forced = []
    if birth_year is not None and birth_place:
        forced.append({"year": birth_year, "place_id": birth_place, "event": "Born", "_src": "persons.json", "_sig": 100})
    if death_year is not None and death_place:
        forced.append({"year": death_year, "place_id": death_place, "event": "Passed away", "_src": "persons.json", "_sig": 100})

    # Define lifetime window for filtering
    lifetime_start = (birth_year - 2) if birth_year is not None else None
    lifetime_end = (death_year + 2) if death_year is not None else None

    for ref in refs:
        eid = ref["event_id"]
        event = EVENTS_BY_ID.get(eid)
        if event is None:
            continue
        year = (event.get("date") or {}).get("y")
        if year is None:
            continue

        # Reject events outside the person's lifetime (later commemorations/yahrzeits/discourses *about* them).
        if lifetime_start is not None and year < lifetime_start:
            continue
        if lifetime_end is not None and year > lifetime_end:
            continue

        text = get_story_text(event)
        if not text.strip():
            continue

        title = event.get("title_en") or ""
        summary = event.get("summary_en") or ""
        title_summary = f"{title} {summary}".lower()

        # Skip yahrzeit/commemoration events
        if COMMEMORATION_PAT.search(title_summary):
            # but allow if it's the actual death year and label says Passed away
            if death_year is None or year != death_year:
                continue

        # Require some name discriminator in title/summary — otherwise the event may be
        # only tangentially about this person (matched via tags/related/body mentions).
        has_name_hint = bool(name_tokens) and any(tok in title_summary for tok in name_tokens)

        label = classify_event(text)
        place_ids = find_places_in_text(text)

        # Track unresolved location-hint words for the report
        # (this is global state via closure — we'll handle separately)
        if not place_ids:
            continue

        # Pin Born/Passed away to actual birth/death year only — else demote/skip
        if label == "Born":
            if birth_year is None:
                # No anchor — only trust if the title explicitly says born + the name token matches
                if not has_name_hint or not BORN_PAT.search(title + " " + summary):
                    continue
            elif abs(year - birth_year) > 2:
                continue
        if label == "Passed away":
            if death_year is None:
                if not has_name_hint or not DEATH_PAT.search(title + " " + summary):
                    continue
            elif abs(year - death_year) > 2:
                continue

        # For other labels, if there's no lifetime anchor at all, require a name hint to keep the step.
        if label not in ("Born", "Passed away"):
            if lifetime_start is None and lifetime_end is None and not has_name_hint:
                continue

        # Skip pure teaching/publication events that aren't location-relevant
        if label is None and TEACHING_PAT.search(title_summary):
            continue

        # Use the most prominent place mentioned. For Born/Passed-away, prefer the person's known birth/death place if it matches.
        place_id = place_ids[0]
        if label == "Born" and birth_place and birth_place in place_ids:
            place_id = birth_place
        if label == "Passed away" and death_place and death_place in place_ids:
            place_id = death_place

        # For "moved to" / "traveled to" events: pick the place that follows the verb if possible.
        if label in ("Traveled", "Settled", "Studied", "Made aliya", "Emigrated", "Escaped Russia", "Escaped"):
            m = re.search(r"\b(?:to|in|at|toward|towards|for|arrived in|moved to|fled to|settled in)\s+([A-Z][\w\-'’ ]{2,40})", text)
            if m:
                possible = m.group(1)
                ids = find_places_in_text(possible)
                if ids:
                    place_id = ids[0]

        if label is None:
            continue

        sig = event.get("significance") or 0
        candidates.append({
            "year": year,
            "place_id": place_id,
            "event": label,
            "_sig": sig,
            "_eid": eid,
        })

    # --- Dedupe and consolidate ---
    all_steps = forced + candidates

    # Remove duplicates: same (year, place_id, label) – keep first (which is persons.json forced when applicable)
    seen = set()
    deduped = []
    for s in all_steps:
        key = (s["year"], s["place_id"], s["event"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(s)

    # Collapse "Born" duplicates (different places for the same person's birth) — keep only the persons.json-anchored one if present
    has_anchored_born = any(s["event"] == "Born" and s.get("_src") == "persons.json" for s in deduped)
    if has_anchored_born:
        deduped = [s for s in deduped if not (s["event"] == "Born" and s.get("_src") != "persons.json")]
    has_anchored_death = any(s["event"] == "Passed away" and s.get("_src") == "persons.json" for s in deduped)
    if has_anchored_death:
        deduped = [s for s in deduped if not (s["event"] == "Passed away" and s.get("_src") != "persons.json")]

    # Sort by year
    deduped.sort(key=lambda s: (s["year"], 0 if s["event"] == "Born" else (99 if s["event"] == "Passed away" else 50)))

    # Trim to cap, prioritizing Born/Passed away + highest significance
    must_keep = [s for s in deduped if s["event"] in ("Born", "Passed away")]
    optional = [s for s in deduped if s["event"] not in ("Born", "Passed away")]
    cap = 15
    budget = max(0, cap - len(must_keep))
    # Sort optional by significance desc
    optional_sorted = sorted(optional, key=lambda s: (-(s.get("_sig") or 0), s["year"]))
    chosen_optional = optional_sorted[:budget]
    final = must_keep + chosen_optional
    final.sort(key=lambda s: (s["year"], 0 if s["event"] == "Born" else (99 if s["event"] == "Passed away" else 50)))

    # Remove same place_id appearing repeatedly with same label within ~5 years
    seen_year_label = {}
    pruned = []
    for s in final:
        key = (s["place_id"], s["event"])
        if key in seen_year_label and abs(s["year"] - seen_year_label[key]) <= 5:
            continue
        seen_year_label[key] = s["year"]
        pruned.append(s)
    final = pruned

    cleaned = [{"year": s["year"], "place_id": s["place_id"], "event": s["event"]} for s in final]
    return cleaned

# --- 6. Run for everyone ---
def main():
    patch = {}
    skipped = []
    per_person_stats = []
    place_resolution_counter = Counter()
    unresolved_candidates = Counter()  # text fragments we couldn't resolve (best-effort)

    # Special handling: for the 7 Rebbes we have very high event counts — also cap their event scan
    REBBES = {
        "baal-shem-tov", "maggid-of-mezeritch",
        "alter-rebbe", "mitteler-rebbe", "tzemach-tzedek",
        "maharash", "rashab", "rayatz", "the-rebbe",
    }

    # Also pre-scan all events once to collect unresolved location words for the report
    for event in EVENTS_LIST:
        text = (event.get("title_en") or "") + " " + (event.get("summary_en") or "")
        collect_unresolved_location_hints(text, None, unresolved_candidates)

    for person_id, refs in EVENT_INDEX.items():
        # For very-high count persons, sort refs by significance desc then year to limit work
        if len(refs) > 200:
            refs_sorted = sorted(refs, key=lambda r: (-(EVENTS_BY_ID.get(r["event_id"], {}).get("significance") or 0), r.get("year") or 0))
            refs_to_use = refs_sorted[:400]
        else:
            refs_to_use = refs

        steps = build_journey_for_person(person_id, refs_to_use)
        per_person_stats.append((person_id, len(refs), len(steps)))
        if len(steps) >= 2:
            patch[person_id] = steps
            for s in steps:
                place_resolution_counter[s["place_id"]] += 1
        elif len(steps) == 1:
            # Single-step journeys are still useful if both year & place are present
            patch[person_id] = steps
            for s in steps:
                place_resolution_counter[s["place_id"]] += 1
        else:
            skipped.append((person_id, len(refs), "no clear year+place events"))

    # Write patch
    out_patch = os.path.join(ROOT, "scripts", "journey_patch.json")
    with open(out_patch, "w", encoding="utf-8") as f:
        json.dump(patch, f, ensure_ascii=False, indent=2)

    # Write report
    out_report = os.path.join(ROOT, "scripts", "journey_extraction_report.md")
    per_person_stats.sort(key=lambda x: -x[2])
    total_steps = sum(s[2] for s in per_person_stats)

    lines = []
    lines.append("# Journey Extraction Report")
    lines.append("")
    lines.append(f"- Total persons with events: **{len(EVENT_INDEX)}**")
    lines.append(f"- Persons with journey emitted: **{len(patch)}**")
    lines.append(f"- Persons skipped: **{len(skipped)}**")
    lines.append(f"- Total journey steps emitted: **{total_steps}**")
    lines.append("")
    lines.append("## Top 10 persons by journey-step count")
    lines.append("")
    lines.append("| Person | Events scanned | Steps emitted |")
    lines.append("|---|---:|---:|")
    for pid, nevents, nsteps in per_person_stats[:10]:
        lines.append(f"| {pid} | {nevents} | {nsteps} |")
    lines.append("")
    lines.append("## All persons (step counts)")
    lines.append("")
    lines.append("| Person | Events scanned | Steps emitted |")
    lines.append("|---|---:|---:|")
    for pid, nevents, nsteps in per_person_stats:
        lines.append(f"| {pid} | {nevents} | {nsteps} |")
    lines.append("")
    lines.append("## Skipped persons (no clear year+place events)")
    lines.append("")
    if skipped:
        for pid, n, reason in skipped:
            lines.append(f"- `{pid}` ({n} events) — {reason}")
    else:
        lines.append("_(none)_")
    lines.append("")
    lines.append("## Most-referenced places in the patch")
    lines.append("")
    for pid, c in place_resolution_counter.most_common(30):
        lines.append(f"- `{pid}` — {c}")
    lines.append("")
    lines.append("## Frequently-mentioned location words that did NOT resolve to a place_id")
    lines.append("")
    if unresolved_candidates:
        for word, c in unresolved_candidates.most_common(40):
            if c >= 3:
                lines.append(f"- `{word}` — {c} mentions")
    else:
        lines.append("_(none tracked)_")
    lines.append("")
    lines.append("## Notes")
    lines.append("")
    lines.append("- Year filter: events without a `date.y` are dropped.")
    lines.append("- Place resolution: matches `name_en` (base + parenthetical) plus curated aliases; longest alias wins.")
    lines.append("- Classification heuristic: regex patterns over (title + summary + story body) detect Born/Passed-away/Married/Imprisoned/Released/Escaped/Made aliya/Emigrated/Founded yeshiva/Appointed Rav/Appointed Mashpia/Yechidus/Exiled/Settled/Studied/Traveled.")
    lines.append("- Each person is capped at 15 steps. Born + Passed away (from persons.json when known) are always retained; remaining slots filled by `significance` desc.")
    lines.append("- Steps within 5 years sharing the same (place_id, label) are collapsed to one to avoid spam from repeat references.")

    with open(out_report, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    print(f"Wrote {out_patch}")
    print(f"Wrote {out_report}")
    print(f"Persons with journeys: {len(patch)}")
    print(f"Total steps: {total_steps}")
    print(f"Skipped: {len(skipped)}")

if __name__ == "__main__":
    main()
