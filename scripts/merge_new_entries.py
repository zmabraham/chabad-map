"""Dedup-check and merge a batch of new entries (e.g. NotebookLM output) into
the existing persons.json / places.json dataset.

The script never auto-overwrites. It produces:
  - scripts/merge_report.md   (human-readable, every flag explained)
  - scripts/merge_patch.json  (the cleared-for-merge additions and patches)

Run with `--apply` to splice the patch into data/{persons,places}.json after
you have reviewed the report.

Usage:
    python scripts/merge_new_entries.py path/to/new_entries.json
    python scripts/merge_new_entries.py path/to/new_entries.json --apply

Input file format (the NotebookLM extraction prompt produces this shape):
    {
      "persons": [ Person records ],
      "places":  [ Place records ]
    }

Person records may optionally carry an "_action" field with values "create" or
"patch". A "patch" record reuses an existing id and fills only the nullable
fields the existing record lacks. A "create" record proposes a new id.
"""
from __future__ import annotations

import argparse
import json
import math
import sys
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
PERSONS_PATH = ROOT / "data" / "persons.json"
PLACES_PATH = ROOT / "data" / "places.json"
REPORT_PATH = ROOT / "scripts" / "merge_report.md"
PATCH_PATH = ROOT / "scripts" / "merge_patch.json"

# Tunables --------------------------------------------------------------------

NAME_SIM_FLAG = 0.82          # similarity at/above this triggers a duplicate flag
NAME_SIM_STRONG = 0.92        # near-certain duplicate
PLACE_PROXIMITY_KM = 5.0      # places within this distance are suspect even if names differ

# Normalization ---------------------------------------------------------------

HEBREW_DIACRITICS = "".join(chr(c) for c in range(0x0591, 0x05C8))  # nikud + cantillation


def strip_hebrew_marks(s: str) -> str:
    return "".join(ch for ch in s if ch not in HEBREW_DIACRITICS)


def normalize_latin(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s.lower().strip()


def name_similarity(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    # Try Hebrew vs Hebrew (strip nikud), latin vs latin (strip diacritics+lower)
    if any(0x0590 <= ord(c) <= 0x05FF for c in a) and any(0x0590 <= ord(c) <= 0x05FF for c in b):
        return SequenceMatcher(None, strip_hebrew_marks(a), strip_hebrew_marks(b)).ratio()
    return SequenceMatcher(None, normalize_latin(a), normalize_latin(b)).ratio()


def haversine_km(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    r = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlam = math.radians(lng2 - lng1)
    a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlam / 2) ** 2
    return 2 * r * math.asin(math.sqrt(a))

# Matching --------------------------------------------------------------------

def find_person_candidates(new_p: dict, existing: list[dict]) -> list[tuple[float, dict, str]]:
    """Return [(score, existing_person, reason), ...] sorted by score desc."""
    hits = []
    new_names = [new_p.get("name_en", ""), new_p.get("common_name", ""), new_p.get("name_he", "")]
    for ex in existing:
        best = 0.0
        best_reason = ""
        for nn in new_names:
            for ef in ("name_en", "common_name", "name_he"):
                s = name_similarity(nn, ex.get(ef, ""))
                if s > best:
                    best = s
                    best_reason = f'"{nn}" ~ "{ex[ef]}" ({s:.2f})'
        if best >= NAME_SIM_FLAG:
            hits.append((best, ex, best_reason))
    hits.sort(key=lambda x: -x[0])
    return hits


def find_place_candidates(new_pl: dict, existing: list[dict]) -> list[tuple[float, dict, str]]:
    hits = []
    new_names = [new_pl.get("name_en", ""), new_pl.get("name_he", "")]
    nlat, nlng = new_pl.get("lat"), new_pl.get("lng")
    for ex in existing:
        best = 0.0
        best_reason = ""
        for nn in new_names:
            for ef in ("name_en", "name_he"):
                s = name_similarity(nn, ex.get(ef, ""))
                if s > best:
                    best = s
                    best_reason = f'"{nn}" ~ "{ex[ef]}" ({s:.2f})'
        if nlat is not None and nlng is not None and ex.get("lat") is not None:
            km = haversine_km(nlat, nlng, ex["lat"], ex["lng"])
            if km <= PLACE_PROXIMITY_KM:
                proximity_score = 1.0 - (km / PLACE_PROXIMITY_KM) * 0.2  # 0.8-1.0 for proximity hits
                if proximity_score > best:
                    best = proximity_score
                    best_reason = f'coords {km:.1f}km from "{ex["name_en"]}"'
        if best >= NAME_SIM_FLAG:
            hits.append((best, ex, best_reason))
    hits.sort(key=lambda x: -x[0])
    return hits

# Validation ------------------------------------------------------------------

REQUIRED_PERSON = {"id", "name_en", "name_he", "common_name", "generation", "role", "bio"}
REQUIRED_PLACE = {"id", "name_en", "name_he", "lat", "lng", "modern_country"}
VALID_ROLES = {"Rebbe", "Rebbetzin", "Son of Rebbe", "Family", "Mashpia", "Chossid", "Pre-Chabad Teacher"}


def validate_person(p: dict, place_ids: set[str]) -> list[str]:
    errs = []
    missing = REQUIRED_PERSON - p.keys()
    if missing:
        errs.append(f"missing fields: {sorted(missing)}")
    if "generation" in p and p["generation"] not in range(8):
        errs.append(f"generation out of range: {p['generation']}")
    if "role" in p and p["role"] not in VALID_ROLES:
        errs.append(f"role not in controlled list: {p['role']!r}")
    for field in ("birth_place_id", "death_place_id", "primary_place_id"):
        v = p.get(field)
        if v and v not in place_ids:
            errs.append(f"{field}={v} does not resolve")
    for i, step in enumerate(p.get("journey") or []):
        if "place_id" not in step or step["place_id"] not in place_ids:
            errs.append(f"journey[{i}].place_id={step.get('place_id')!r} does not resolve")
    return errs


def validate_place(pl: dict) -> list[str]:
    errs = []
    missing = REQUIRED_PLACE - pl.keys()
    if missing:
        errs.append(f"missing fields: {sorted(missing)}")
    lat, lng = pl.get("lat"), pl.get("lng")
    if isinstance(lat, (int, float)) and not -90 <= lat <= 90:
        errs.append(f"lat out of range: {lat}")
    if isinstance(lng, (int, float)) and not -180 <= lng <= 180:
        errs.append(f"lng out of range: {lng}")
    return errs

# Patch application ------------------------------------------------------------

def fill_nulls(existing: dict, patch: dict, fields: list[str]) -> list[str]:
    """Fill only fields where existing has null/missing and patch has a real value.
    Returns the list of fields actually filled."""
    filled = []
    for f in fields:
        if f not in patch:
            continue
        new_v = patch[f]
        if new_v in (None, "", []):
            continue
        cur_v = existing.get(f)
        if cur_v in (None, "", []):
            existing[f] = new_v
            filled.append(f)
    return filled


PATCHABLE_PERSON_FIELDS = [
    "birth_year",
    "death_year",
    "birth_place_id",
    "death_place_id",
    "primary_place_id",
    "journey",
    "chabadpedia_url",
    "photo_url",
]

# Main ------------------------------------------------------------------------

def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("input", type=Path, help="JSON file with {persons:[...], places:[...]}")
    ap.add_argument("--apply", action="store_true", help="Splice the cleared patch into data/")
    args = ap.parse_args()

    if not args.input.exists():
        print(f"Input not found: {args.input}", file=sys.stderr)
        return 2

    input_data = json.loads(args.input.read_text(encoding="utf-8"))
    new_persons = input_data.get("persons") or []
    new_places = input_data.get("places") or []

    persons = json.loads(PERSONS_PATH.read_text(encoding="utf-8"))
    places = json.loads(PLACES_PATH.read_text(encoding="utf-8"))
    person_by_id = {p["id"]: p for p in persons}
    place_by_id = {pl["id"]: pl for pl in places}
    place_ids = set(place_by_id)

    # Provisional place_ids after this batch — include new places so person validation passes
    provisional_place_ids = set(place_ids)
    for pl in new_places:
        if pl.get("id"):
            provisional_place_ids.add(pl["id"])

    report = ["# Merge Report", ""]
    cleared_persons: list[dict] = []
    cleared_places: list[dict] = []
    patches_to_apply: list[tuple[dict, dict]] = []  # (existing_record, patch_record)

    # ----- Places ------------------------------------------------------------
    report.append(f"## Places ({len(new_places)} proposed)")
    if not new_places:
        report.append("_None._")
    for pl in new_places:
        errs = validate_place(pl)
        pid = pl.get("id", "?")
        line_header = f"### `{pid}` — {pl.get('name_en', '?')}"
        notes = []
        if errs:
            notes.append(f"❌ validation errors: {errs}")
        if pid in place_by_id:
            notes.append(f"❌ ID collision with existing `{pid}` — already in places.json")
        cands = find_place_candidates(pl, places) if not errs and pid not in place_by_id else []
        for score, ex, reason in cands[:3]:
            severity = "🔴 likely-duplicate" if score >= NAME_SIM_STRONG else "🟡 possible-duplicate"
            notes.append(f"{severity} of `{ex['id']}` ({ex['name_en']}) — {reason}")
        verdict = "CLEARED" if not notes else "REVIEW"
        report.append(line_header)
        report.append(f"- verdict: **{verdict}**")
        for n in notes:
            report.append(f"- {n}")
        if verdict == "CLEARED":
            cleared_places.append({k: v for k, v in pl.items() if not k.startswith("_")})
        report.append("")

    # ----- Persons -----------------------------------------------------------
    report.append(f"## Persons ({len(new_persons)} proposed)")
    if not new_persons:
        report.append("_None._")
    not_found_count = 0
    for p in new_persons:
        action = p.get("_action", "create")
        pid = p.get("id", "?")
        line_header = f"### `{pid}` — {p.get('common_name') or p.get('name_en', '?')}  _(action: {action})_"

        if action == "not-found":
            not_found_count += 1
            report.append(f"### {p.get('common_name') or p.get('name_he') or '?'}  _(action: not-found)_")
            report.append("- verdict: **SKIPPED** — NotebookLM could not locate this name in the uploaded sources. Try a different source or a different spelling.")
            report.append("")
            continue

        if action == "patch":
            if pid not in person_by_id:
                report.append(line_header)
                report.append(f"- verdict: **REVIEW**")
                report.append(f"- ❌ patch target `{pid}` does not exist in persons.json")
                report.append("")
                continue
            existing = person_by_id[pid]
            # Snapshot what would change without mutating yet
            preview = dict(existing)
            filled = fill_nulls(preview, p, PATCHABLE_PERSON_FIELDS)
            errs = validate_person(preview, provisional_place_ids)
            if not filled:
                report.append(line_header)
                report.append(f"- verdict: **SKIPPED** — patch adds no new info")
                report.append("")
                continue
            verdict = "CLEARED" if not errs else "REVIEW"
            report.append(line_header)
            report.append(f"- verdict: **{verdict}**")
            report.append(f"- would fill: {filled}")
            for e in errs:
                report.append(f"- ❌ {e}")
            report.append("")
            if verdict == "CLEARED":
                patches_to_apply.append((existing, p))
            continue

        # action == "create"
        notes = []
        errs = validate_person(p, provisional_place_ids)
        if errs:
            notes.append(f"❌ validation errors: {errs}")
        if pid in person_by_id:
            notes.append(f"❌ ID collision with existing `{pid}` — already in persons.json")
        force_create = bool(p.get("_force_create"))
        cands = (
            find_person_candidates(p, persons)
            if not errs and pid not in person_by_id and not force_create
            else []
        )
        for score, ex, reason in cands[:3]:
            severity = "🔴 likely-duplicate" if score >= NAME_SIM_STRONG else "🟡 possible-duplicate"
            notes.append(
                f"{severity} of `{ex['id']}` ({ex['common_name']}) — {reason}"
            )
        verdict = "CLEARED" if not notes else "REVIEW"
        report.append(line_header)
        report.append(f"- verdict: **{verdict}**")
        for n in notes:
            report.append(f"- {n}")
        if verdict == "CLEARED":
            cleared_persons.append({k: v for k, v in p.items() if not k.startswith("_")})
        report.append("")

    # ----- Summary -----------------------------------------------------------
    summary = [
        "## Summary",
        f"- New persons cleared: {len(cleared_persons)} / {len(new_persons)}",
        f"- Person patches cleared: {len(patches_to_apply)}",
        f"- Not found in sources: {not_found_count}",
        f"- New places cleared: {len(cleared_places)} / {len(new_places)}",
        "",
        "Run again with `--apply` to splice cleared entries into the dataset.",
        "Resolve the REVIEW items in the input file (rename the id, merge by hand, or drop the duplicate) before re-running.",
        "",
    ]
    report = summary + report

    REPORT_PATH.write_text("\n".join(report), encoding="utf-8")
    patch = {
        "persons": cleared_persons,
        "places": cleared_places,
        "patches": [
            {"id": ex["id"], "fill": {k: pat[k] for k in PATCHABLE_PERSON_FIELDS if k in pat}}
            for ex, pat in patches_to_apply
        ],
    }
    PATCH_PATH.write_text(json.dumps(patch, ensure_ascii=False, indent=2), encoding="utf-8")

    print(f"Report: {REPORT_PATH}")
    print(f"Patch:  {PATCH_PATH}")
    print(
        f"Persons cleared: {len(cleared_persons)} | Patches: {len(patches_to_apply)} | "
        f"Places cleared: {len(cleared_places)}"
    )

    if not args.apply:
        return 0

    # Apply
    persons.extend(cleared_persons)
    for ex, pat in patches_to_apply:
        fill_nulls(ex, pat, PATCHABLE_PERSON_FIELDS)
    places.extend(cleared_places)

    PERSONS_PATH.write_text(json.dumps(persons, ensure_ascii=False, indent=2), encoding="utf-8")
    PLACES_PATH.write_text(json.dumps(places, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"Applied. persons.json now has {len(persons)} entries, places.json has {len(places)} entries.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
