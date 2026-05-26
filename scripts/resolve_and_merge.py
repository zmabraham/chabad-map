"""Resolve user-supplied name-based extraction batches into merge-ready records.

Input: paired batch files (v1 + v2) per group, each with place NAMES (not IDs).
Pipeline:
  1. Pair-merge v1 + v2 by index (fill nulls, prefer richer journey).
  2. Cross-group dedupe via common_name fuzzy match (groups can overlap).
  3. Resolve place names -> place_ids via PLACE_ALIASES + places.json lookup.
  4. Generate kebab-case person IDs.
  5. Match against existing persons.json (action: patch vs create).
  6. Output scripts/new_entries.json (merge_new_entries.py-compatible format).
  7. Surface unresolved place names for manual geocoding.

Usage: python scripts/resolve_and_merge.py
"""
from __future__ import annotations

import json
import re
import sys
import unicodedata
from collections import Counter
from difflib import SequenceMatcher
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")
ROOT = Path(__file__).resolve().parent.parent
PERSONS_PATH = ROOT / "data" / "persons.json"
PLACES_PATH = ROOT / "data" / "places.json"
OUTPUT_PATH = ROOT / "scripts" / "new_entries.json"
UNRESOLVED_PATH = ROOT / "scripts" / "unresolved_places.md"

# Paired batches: (v1, v2). Each is loaded fresh; pair-merge by index.
BATCHES = [
    (ROOT / "scripts" / "incoming.json",          ROOT / "scripts" / "incoming_b2.json"),
    (ROOT / "scripts" / "incoming" / "b2_v1.json", ROOT / "scripts" / "incoming" / "b2_v2.json"),
    (ROOT / "scripts" / "incoming" / "b3_v1.json", ROOT / "scripts" / "incoming" / "b3_v2.json"),
    (ROOT / "scripts" / "incoming" / "b4_v1.json", ROOT / "scripts" / "incoming" / "b4_v2.json"),
]

# Manual place-name aliases. Anything not here gets fuzzy-matched against places.json.
PLACE_ALIASES = {
    "mezhibuzh": "mezhibuzh", "medzhybizh": "mezhibuzh",
    "kopust": "kapust", "kopys": "kapust",
    "ovruch": "avritch", "avritch": "avritch",
    "nezhin": "niezhin", "niezhin": "niezhin",
    "homil": "homel", "homel": "homel", "gomel": "homel",
    "nikolayev": "nikolaev", "nikolaev": "nikolaev",
    "alma ata": "alma-ata", "alma-ata": "alma-ata", "almaty": "alma-ata",
    "haditch": "hadiach", "hadiach": "hadiach", "hadiatch": "hadiach",
    "babinovitch": "babinovich", "babinovich": "babinovich",
    "lvov": "lviv", "lviv": "lviv",
    "lieple": "lepli", "lepel": "lepli",
    "new york": "new-york", "brooklyn": "new-york", "crown heights": "new-york",
    "tel aviv": "tel-aviv", "tel-aviv": "tel-aviv",
    "bnei brak": "bnei-brak", "bnei-brak": "bnei-brak",
    "kfar chabad": "kfar-chabad",
    "leningrad": "leningrad", "saint petersburg": "petersburg", "st. petersburg": "petersburg",
    "petersburg": "petersburg",
}
# Place names that are too vague to map to a coordinate.
VAGUE_PLACES = {
    "holy land", "soviet union", "russia", "united states", "us", "usa", "america",
    "israel", "europe", "eastern europe", "poland", "ukraine", "belarus", "lithuania",
    "latvia", "germany", "white russia", "kazakhstan", "georgia",
}


# ---- Helpers --------------------------------------------------------------

def slugify(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    s = s.lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def name_sim(a: str, b: str) -> float:
    if not a or not b:
        return 0.0
    if any(0x0590 <= ord(c) <= 0x05FF for c in a) and any(0x0590 <= ord(c) <= 0x05FF for c in b):
        ha = "".join(ch for ch in a if not (0x0591 <= ord(ch) <= 0x05C7))
        hb = "".join(ch for ch in b if not (0x0591 <= ord(ch) <= 0x05C7))
        return SequenceMatcher(None, ha, hb).ratio()
    norm = lambda s: unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()
    return SequenceMatcher(None, norm(a), norm(b)).ratio()


def is_blank(v):
    return v in (None, "", [], {})


# ---- Load existing ---------------------------------------------------------

existing_persons = json.loads(PERSONS_PATH.read_text(encoding="utf-8"))
existing_places = json.loads(PLACES_PATH.read_text(encoding="utf-8"))
place_by_id = {p["id"]: p for p in existing_places}
existing_person_ids = {p["id"] for p in existing_persons}

# Build a place-name lookup (case-insensitive on name_en, with parenthetical aliases split out).
place_name_index = {}
for p in existing_places:
    keys = [p["name_en"]]
    if "(" in p["name_en"]:
        for chunk in re.split(r"[()]", p["name_en"]):
            chunk = chunk.strip()
            if chunk:
                keys.append(chunk)
    for k in keys:
        place_name_index[k.lower()] = p["id"]
    place_name_index[p["name_he"]] = p["id"]


def resolve_place_name(name: str | None, unresolved: Counter) -> str | None:
    """Return a place_id, or None if not resolvable. Records unresolved in counter."""
    if not name:
        return None
    key = name.strip().lower()
    if key in VAGUE_PLACES:
        unresolved[f"VAGUE: {name}"] += 1
        return None
    if key in PLACE_ALIASES:
        return PLACE_ALIASES[key]
    if key in place_name_index:
        return place_name_index[key]
    # Fuzzy match against place name_en
    best_score = 0.0
    best_id = None
    for k, pid in place_name_index.items():
        s = name_sim(name, k)
        if s > best_score:
            best_score = s
            best_id = pid
    if best_score >= 0.90:
        return best_id
    unresolved[name] += 1
    return None


# ---- Pair-merge ------------------------------------------------------------

PERSON_FIELDS = ["name_en", "name_he", "common_name", "generation", "role",
                 "birth_year", "death_year", "birth_place", "death_place",
                 "primary_place", "bio"]


def pair_merge(a: list[dict], b: list[dict]) -> list[dict]:
    if len(a) != len(b):
        print(f"  WARN: pair length mismatch {len(a)} vs {len(b)} — using shorter", file=sys.stderr)
    out = []
    for i in range(min(len(a), len(b))):
        x, y = a[i], b[i]
        merged = {k: x.get(k) for k in PERSON_FIELDS}
        for k in PERSON_FIELDS:
            if is_blank(merged.get(k)) and not is_blank(y.get(k)):
                merged[k] = y[k]
        jx, jy = x.get("journey") or [], y.get("journey") or []
        merged["journey"] = jx if len(jx) >= len(jy) else jy
        out.append(merged)
    return out


# ---- Cross-group merge by name --------------------------------------------

def find_existing_in_combined(entry: dict, combined: list[dict]) -> int:
    """Return index of best match in combined, or -1 if none above threshold."""
    best_score = 0.0
    best_idx = -1
    for i, c in enumerate(combined):
        # Require same generation to avoid merging different figures who share names
        if c.get("generation") != entry.get("generation"):
            continue
        s_cn = name_sim(c.get("common_name", ""), entry.get("common_name", ""))
        s_he = name_sim(c.get("name_he", ""), entry.get("name_he", ""))
        score = max(s_cn, s_he)
        if score > best_score:
            best_score = score
            best_idx = i
    return best_idx if best_score >= 0.88 else -1


def merge_into(target: dict, addition: dict) -> None:
    for k in PERSON_FIELDS:
        if is_blank(target.get(k)) and not is_blank(addition.get(k)):
            target[k] = addition[k]
    if not target.get("journey") and addition.get("journey"):
        target["journey"] = addition["journey"]
    elif addition.get("journey") and len(addition["journey"]) > len(target.get("journey") or []):
        target["journey"] = addition["journey"]


# ---- Load and pair-merge all batches --------------------------------------

print(f"Loading {len(BATCHES)} batch pairs...")
group_merged = []
for v1_path, v2_path in BATCHES:
    if not v1_path.exists() or not v2_path.exists():
        print(f"  SKIP (missing): {v1_path.name} / {v2_path.name}")
        continue
    v1 = json.loads(v1_path.read_text(encoding="utf-8"))
    v2 = json.loads(v2_path.read_text(encoding="utf-8"))
    merged = pair_merge(v1, v2)
    print(f"  {v1_path.parent.name}/{v1_path.name}: {len(v1)} + {len(v2)} -> {len(merged)} merged")
    group_merged.append(merged)

# ---- Cross-group fold ------------------------------------------------------

combined = []
for group in group_merged:
    for entry in group:
        idx = find_existing_in_combined(entry, combined)
        if idx >= 0:
            merge_into(combined[idx], entry)
        else:
            combined.append(dict(entry))

print(f"\nCombined unique figures: {len(combined)}")

# ---- Resolve places --------------------------------------------------------

unresolved = Counter()
for entry in combined:
    for field in ("birth_place", "death_place", "primary_place"):
        name = entry.get(field)
        entry[f"{field}_id"] = resolve_place_name(name, unresolved)
    new_journey = []
    for step in entry.get("journey") or []:
        pid = resolve_place_name(step.get("place"), unresolved)
        new_journey.append({"year": step.get("year"), "place_id": pid, "event": step.get("event", "")})
    entry["journey_resolved"] = new_journey

# ---- Generate IDs and match against existing persons.json -----------------

def find_existing_person(entry: dict) -> dict | None:
    """Look for a strong match against existing persons.json."""
    best_score = 0.0
    best = None
    for p in existing_persons:
        if p.get("generation") != entry.get("generation"):
            continue
        s_cn = name_sim(p.get("common_name", ""), entry.get("common_name", ""))
        s_he = name_sim(p.get("name_he", ""), entry.get("name_he", ""))
        s_en = name_sim(p.get("name_en", ""), entry.get("name_en", ""))
        score = max(s_cn, s_he, s_en)
        if score > best_score:
            best_score = score
            best = p
    return best if best_score >= 0.90 else None


used_ids = set(existing_person_ids)
final_persons = []
for entry in combined:
    match = find_existing_person(entry)
    if match:
        action = "patch"
        pid = match["id"]
    else:
        action = "create"
        pid = slugify(entry.get("common_name") or entry.get("name_en") or "unknown")
        suffix = 2
        while pid in used_ids:
            pid = slugify(entry.get("common_name") or "unknown") + f"-{suffix}"
            suffix += 1
        used_ids.add(pid)

    rec = {
        "_action": action,
        "id": pid,
        "name_en": entry.get("name_en"),
        "name_he": entry.get("name_he"),
        "common_name": entry.get("common_name"),
        "generation": entry.get("generation"),
        "birth_year": entry.get("birth_year"),
        "death_year": entry.get("death_year"),
        "birth_place_id": entry.get("birth_place_id"),
        "death_place_id": entry.get("death_place_id"),
        "primary_place_id": entry.get("primary_place_id"),
        "role": entry.get("role"),
        "bio": entry.get("bio"),
        "journey": [s for s in (entry.get("journey_resolved") or []) if s.get("place_id")],
    }
    # Drop journey if everything was unresolved
    if not rec["journey"]:
        rec["journey"] = []
    final_persons.append(rec)

# ---- Output ----------------------------------------------------------------

OUTPUT_PATH.write_text(
    json.dumps({"persons": final_persons, "places": []}, ensure_ascii=False, indent=2),
    encoding="utf-8",
)

# Write unresolved-places report
report = ["# Unresolved place names from incoming batches", ""]
report.append(f"Total unique unresolved names: {len(unresolved)}")
report.append("")
report.append("These place names appeared in incoming batches but could not be mapped to an existing entry in `places.json`. To use them in the dataset, add corresponding entries to `places.json` (each needs `id`, `name_en`, `name_he`, `lat`, `lng`, `modern_country`).")
report.append("")
report.append("| Place | Mention count |")
report.append("|---|---|")
for name, count in sorted(unresolved.items(), key=lambda x: -x[1]):
    report.append(f"| {name} | {count} |")
UNRESOLVED_PATH.write_text("\n".join(report), encoding="utf-8")

# ---- Summary ---------------------------------------------------------------

n_patch = sum(1 for p in final_persons if p["_action"] == "patch")
n_create = sum(1 for p in final_persons if p["_action"] == "create")
print(f"\nResolved {len(final_persons)} persons:")
print(f"  patch (existing): {n_patch}")
print(f"  create (new):     {n_create}")
print(f"\nUnresolved place names: {len(unresolved)} unique ({sum(unresolved.values())} mentions)")
print(f"\nOutput: {OUTPUT_PATH}")
print(f"Unresolved places report: {UNRESOLVED_PATH}")
