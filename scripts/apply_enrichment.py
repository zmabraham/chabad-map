"""Apply Chabadpedia enrichment to persons.json + emit report.

Run from repo root or scripts dir; uses paths relative to this file.

Rules:
  - Never overwrite non-null existing values; only fill nulls.
  - Add chabadpedia_url (always for matched persons) and photo_url fields.
  - Map Hebrew place names to existing place IDs by name_he/name_en match.
  - Don't add new places; null and report unmatched.
  - Validate before write.
"""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
PERSONS_PATH = ROOT / "data" / "persons.json"
PLACES_PATH = ROOT / "data" / "places.json"
URLS_PATH = HERE / "chabadpedia_urls.json"
ENRICH_PATH = HERE / "enrich_data.json"
REPORT_PATH = HERE / "enrichment_report.md"

# Manual additional place-name aliases (Hebrew->existing place id)
# Built by checking what's in places.json against what Chabadpedia uses.
PLACE_ALIASES = {
    # exact matches via name_he in places.json
    "ניו יורק": "new-york",
    "תל אביב": "tel-aviv",
    "ירושלים": "jerusalem",
    "כפר חב\"ד": "kfar-chabad",
    "חברון": "hebron",
    "בני ברק": "bnei-brak",
    "לוד": "lod",
    "ויטבסק": "vitebsk",
    "וויטעבסק": "vitebsk",
    "ליובאוויטש": "lubavitch",
    "ליאדי": "liadi",
    "האדיטש": "hadiach",
    "ליאזנא": "liozna",
    "שקלוב": "shklov",
    "שקלאוו": "shklov",
    "סמרקנד": "samarkand",
    "ריגה": "riga",
    "ריגא": "riga",
    "ורשה": "warsaw",
    "ווארשא": "warsaw",
    "חרסון": "kherson",
    "כערסאן": "kherson",
    "אלמא אטא": "alma-ata",
    "וילנא": "vilna",
    "ווילנא": "vilna",
    "פאריטש": "paritch",
    "באברויסק": "bobruisk",
    "בוברויסק": "bobruisk",
    "בברויסק": "bobruisk",
    "לוקימא": None,
    "ניקולייב": "nikolaev",
    "ניקאלאיעוו": "nikolaev",
    "האמיל": "homel",
    "האמלי": "homel",
    "הומיל": "homel",
    "נחלת הר חב\"ד": "nachlat-har-chabad",
    "נעוועל": "nevel",
    "קאפוסט": "kapust",
    "יקטרינוסלב": "yekaterinoslav",
    "יעקאטערינאסלאוו": "yekaterinoslav",
    "דנייפרופטרובסק": "yekaterinoslav",  # Soviet name for Yekaterinoslav
    "מוסקבה": "moscow",
    "מאסקווא": "moscow",
    "לונדון": None,  # no london in places.json
    "צפת": "tzfat",
    "ראשון לציון": None,  # not in places.json
    "טבריה": None,  # not in places.json
    "פוקינג": None,
    "ולדיווסטוק": None,
    "פלעשניץ": None,
    "מאליאט": None,
    "מוהילוב": "mohilev",
    "מאהליעוו": "mohilev",
    "ז'יטומיר": None,
    "צ'רקאס": None,
    "אוסווס": None,
    "קרמנצ'וג": None,
    "ז'עמבין": None,
    "דיסנה": None,
    "מאיור": None,
    "קריסלבה": "krislava",
    "קרעסלאווא": "krislava",
    "רוגוצ'וב": None,
    "רוגצ'וב": None,
    "רודניא": None,
    "קורניץ": None,
    "שצעדרין": "shchedrin",
    "שטשעדרין": "shchedrin",
    "קזחסטן": None,  # country, not a city
    "שומיאץ": None,
    "וויעזנא": None,
    "חומץ": None,
    "סמילוביץ'": None,
    "ז'לובין": None,
    "קזמירוב": None,
    "פוצ'עפ": None,
    "זוראוויטש": None,
    "הורודוק": None,
    "פודוברנקה": None,
    "סוליש": None,
    "פינסק": None,
    "קלצק": None,
    "ליעפלי": "lepli",
    "לעפלי": "lepli",
    "רעגזנעוואטע": None,
}


def normalize_he(s: str) -> str:
    if s is None:
        return ""
    # strip Hebrew quotes/marks and common decorations
    out = s.strip()
    # remove trailing punctuation
    return out


def map_place(he: str, places_by_he: dict, places_by_id: dict):
    if not he:
        return None, "empty"
    he = normalize_he(he)
    if he in PLACE_ALIASES:
        pid = PLACE_ALIASES[he]
        if pid is None:
            return None, "no_existing_place"
        if pid in places_by_id:
            return pid, "alias_match"
        return None, "alias_invalid"
    # try direct name_he match
    if he in places_by_he:
        return places_by_he[he], "name_he_match"
    return None, "no_match"


def main():
    persons = json.loads(PERSONS_PATH.read_text(encoding="utf-8"))
    places = json.loads(PLACES_PATH.read_text(encoding="utf-8"))
    urls = json.loads(URLS_PATH.read_text(encoding="utf-8"))
    enrich = json.loads(ENRICH_PATH.read_text(encoding="utf-8"))

    original_count = len(persons)
    place_ids = {p["id"] for p in places}
    places_by_he = {p["name_he"]: p["id"] for p in places}
    places_by_id = {p["id"]: p for p in places}
    persons_by_id = {p["id"]: p for p in persons}

    # Capture original non-null values for verification later
    originals = {}
    for p in persons:
        originals[p["id"]] = {
            "birth_year": p.get("birth_year"),
            "death_year": p.get("death_year"),
            "birth_place_id": p.get("birth_place_id"),
            "death_place_id": p.get("death_place_id"),
        }

    report_lines = []
    counts = {
        "matched": 0,
        "filled_birth_year": 0,
        "filled_death_year": 0,
        "filled_birth_place": 0,
        "filled_death_place": 0,
        "photos_added": 0,
        "fetch_fail": 0,
        "no_person_match": 0,
        "no_info": 0,
    }
    unmatched_places = {}  # he -> [person_id, ...]
    no_person_match_urls = []
    person_lines = []

    for idx_str, entry in enrich["entries"].items():
        person_id = entry.get("person_id")
        url = entry["url"]
        status = entry.get("fetch_status")
        url_name = urls["entries"][int(idx_str)]["name"]

        if status == "fail":
            counts["fetch_fail"] += 1
            person_lines.append(f"- `{person_id or url_name}`: fetch failed ({url})")
            continue
        if status == "no_person_match":
            counts["no_person_match"] += 1
            no_person_match_urls.append((url_name, url))
            continue
        if person_id is None:
            counts["no_person_match"] += 1
            no_person_match_urls.append((url_name, url))
            continue

        person = persons_by_id.get(person_id)
        if person is None:
            person_lines.append(f"- `{person_id}`: ERROR — person_id not found in persons.json")
            continue

        counts["matched"] += 1
        filled = []

        # chabadpedia_url always
        if "chabadpedia_url" not in person or person.get("chabadpedia_url") in (None, ""):
            person["chabadpedia_url"] = url
            filled.append("chabadpedia_url")

        if status == "noinfo":
            counts["no_info"] += 1
            person_lines.append(f"- `{person_id}`: no extractable data; added chabadpedia_url only")
            continue

        # Years
        by = entry.get("birth_year")
        dy = entry.get("death_year")
        if by is not None and person.get("birth_year") is None:
            person["birth_year"] = by
            counts["filled_birth_year"] += 1
            filled.append(f"birth_year={by}")
        if dy is not None and person.get("death_year") is None:
            person["death_year"] = dy
            counts["filled_death_year"] += 1
            filled.append(f"death_year={dy}")

        # Places
        bp_he = entry.get("birth_place_he")
        dp_he = entry.get("death_place_he")
        if bp_he and person.get("birth_place_id") is None:
            pid, reason = map_place(bp_he, places_by_he, places_by_id)
            if pid:
                person["birth_place_id"] = pid
                counts["filled_birth_place"] += 1
                filled.append(f"birth_place_id={pid}")
            else:
                unmatched_places.setdefault(bp_he, []).append(f"{person_id} (birth)")
        if dp_he and person.get("death_place_id") is None:
            pid, reason = map_place(dp_he, places_by_he, places_by_id)
            if pid:
                person["death_place_id"] = pid
                counts["filled_death_place"] += 1
                filled.append(f"death_place_id={pid}")
            else:
                unmatched_places.setdefault(dp_he, []).append(f"{person_id} (death)")

        # Photo
        photo = entry.get("photo_url")
        if photo:
            if not photo.startswith("http"):
                photo = "https://chabadpedia.co.il" + photo
            if "photo_url" not in person or person.get("photo_url") in (None, ""):
                person["photo_url"] = photo
                counts["photos_added"] += 1
                filled.append("photo_url")
        else:
            if "photo_url" not in person:
                person["photo_url"] = None

        person_lines.append(f"- `{person_id}`: filled {', '.join(filled) if filled else '(nothing new)'}")

    # Validate
    errors = []
    if len(persons) != original_count:
        errors.append(f"Person count changed: {original_count} -> {len(persons)}")
    for p in persons:
        orig = originals.get(p["id"])
        if not orig:
            errors.append(f"Unknown id appeared: {p['id']}")
            continue
        for field in ("birth_year", "death_year", "birth_place_id", "death_place_id"):
            orig_val = orig[field]
            new_val = p.get(field)
            if orig_val is not None and new_val != orig_val:
                errors.append(f"{p['id']}: {field} non-null original {orig_val!r} was overwritten to {new_val!r}")
        for field in ("birth_place_id", "death_place_id"):
            v = p.get(field)
            if v is not None and v not in place_ids:
                errors.append(f"{p['id']}: {field}={v!r} not in places.json")

    # Try to parse via json.dumps round-trip
    try:
        out_text = json.dumps(persons, ensure_ascii=False, indent=2) + "\n"
        json.loads(out_text)
    except Exception as e:
        errors.append(f"JSON serialization failed: {e}")

    # Write report
    report = []
    report.append("# Chabadpedia Enrichment Report\n")
    report.append(f"- Total URL entries: {len(enrich['entries'])}")
    report.append(f"- Matched persons: {counts['matched']}")
    report.append(f"- Fetch failures: {counts['fetch_fail']}")
    report.append(f"- No-info pages: {counts['no_info']}")
    report.append(f"- URLs with no person match: {counts['no_person_match']}")
    report.append(f"- Filled birth_year: {counts['filled_birth_year']}")
    report.append(f"- Filled death_year: {counts['filled_death_year']}")
    report.append(f"- Filled birth_place_id: {counts['filled_birth_place']}")
    report.append(f"- Filled death_place_id: {counts['filled_death_place']}")
    report.append(f"- Photos added: {counts['photos_added']}")
    report.append("")
    report.append("## Per-person")
    report.append("")
    report.extend(person_lines)
    report.append("")
    report.append("## URLs with no person match")
    report.append("")
    if no_person_match_urls:
        for n, u in no_person_match_urls:
            report.append(f"- {n} — {u}")
    else:
        report.append("(none)")
    report.append("")
    report.append("## Unmatched Hebrew places")
    report.append("")
    report.append("These Hebrew place names appeared on Chabadpedia but do not exist in places.json.")
    report.append("Decide whether to add them (will require lat/lng).")
    report.append("")
    if unmatched_places:
        for he, refs in sorted(unmatched_places.items()):
            report.append(f"- `{he}` (mentioned by: {', '.join(refs)})")
    else:
        report.append("(none)")
    report.append("")

    if errors:
        report.append("## VALIDATION ERRORS — file NOT written")
        report.append("")
        for e in errors:
            report.append(f"- {e}")
        report.append("")
        REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
        print("VALIDATION FAILED. See report. persons.json NOT modified.")
        for e in errors:
            print("  ", e)
        return 1

    # Write persons.json
    PERSONS_PATH.write_text(out_text, encoding="utf-8")
    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")

    # Stdout summary
    print(f"Persons enriched: {counts['matched']}")
    print(f"Filled birth_year={counts['filled_birth_year']}, death_year={counts['filled_death_year']}")
    print(f"Filled birth_place={counts['filled_birth_place']}, death_place={counts['filled_death_place']}")
    print(f"Photos added: {counts['photos_added']}")
    print(f"Fetch failures: {counts['fetch_fail']}, No-info: {counts['no_info']}, No-match URLs: {counts['no_person_match']}")
    print(f"Unmatched place names: {len(unmatched_places)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
