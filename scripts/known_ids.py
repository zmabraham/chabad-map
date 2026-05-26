"""Generate the "known IDs" block to paste into the NotebookLM extraction prompt.

Reads the current persons.json and places.json and prints a structured
reference block so the model can self-deduplicate by reusing existing IDs.

Run before each NotebookLM session so the context reflects the latest dataset.

Usage:
    python scripts/known_ids.py                # prints to stdout
    python scripts/known_ids.py > known.txt    # save to a file to paste from
"""
import json
import sys
from pathlib import Path

# Windows consoles default to cp1252; force UTF-8 so Hebrew prints correctly.
sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
persons = json.loads((ROOT / "data" / "persons.json").read_text(encoding="utf-8"))
places = json.loads((ROOT / "data" / "places.json").read_text(encoding="utf-8"))


def person_label(p: dict) -> str:
    he = f" / {p['name_he']}" if p.get("name_he") else ""
    years = ""
    by, dy = p.get("birth_year"), p.get("death_year")
    if by or dy:
        years = f" ({by or '?'}–{dy or '?'})"
    return f"  {p['id']}: {p['common_name']}{he}{years}"


def place_label(pl: dict) -> str:
    he = f" / {pl['name_he']}" if pl.get("name_he") else ""
    return f"  {pl['id']}: {pl['name_en']}{he} — {pl['modern_country']}"


print(f"# Known person IDs ({len(persons)} entries — reuse these; never coin a new ID for someone in this list)")
for p in sorted(persons, key=lambda x: (x["generation"], x["id"])):
    print(person_label(p))

print()
print(f"# Known place IDs ({len(places)} entries — reuse these; never coin a new ID for a place in this list)")
for pl in sorted(places, key=lambda x: x["id"]):
    print(place_label(pl))
