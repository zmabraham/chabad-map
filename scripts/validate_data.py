"""One-off data sanity check. Not shipped with the app."""
import json
from pathlib import Path
from collections import Counter

root = Path(__file__).resolve().parent.parent
persons = json.loads((root / "data" / "persons.json").read_text(encoding="utf-8"))
places = json.loads((root / "data" / "places.json").read_text(encoding="utf-8"))

place_ids = {p["id"] for p in places}

print(f"persons: {len(persons)}")
print(f"places:  {len(places)}")

null_birth = sum(1 for p in persons if p["birth_year"] is None)
null_death = sum(1 for p in persons if p["death_year"] is None)
both_null = sum(1 for p in persons if p["birth_year"] is None and p["death_year"] is None)
print(f"null birth_year: {null_birth}")
print(f"null death_year: {null_death}")
print(f"both null:       {both_null}")

no_places = sum(1 for p in persons if p["birth_place_id"] is None and p["death_place_id"] is None)
print(f"no places at all: {no_places}")

same_place = sum(
    1 for p in persons
    if p["birth_place_id"] and p["death_place_id"] and p["birth_place_id"] == p["death_place_id"]
)
print(f"birth == death place: {same_place}")

unresolved = []
for p in persons:
    for field in ("birth_place_id", "death_place_id"):
        pid = p.get(field)
        if pid and pid not in place_ids:
            unresolved.append((p["id"], field, pid))
print(f"unresolved place refs: {len(unresolved)}")
for row in unresolved[:20]:
    print("  ", row)

gens = Counter(p["generation"] for p in persons)
print("by generation:", dict(sorted(gens.items())))

referenced_places = set()
for p in persons:
    if p["birth_place_id"]:
        referenced_places.add(p["birth_place_id"])
    if p["death_place_id"]:
        referenced_places.add(p["death_place_id"])
orphan_places = place_ids - referenced_places
print(f"places referenced by someone: {len(referenced_places)}")
print(f"orphan places (defined but unused): {len(orphan_places)}")
for op in sorted(orphan_places):
    print("  ", op)
