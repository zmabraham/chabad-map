"""Index events from master-timeline-chabad against our persons dataset.

For each event in events.json (8K+ events), find which persons in persons.json
are mentioned by name (common_name, name_en, or a substring of name_en).

Output: scripts/event_index.json
  { person_id: [ {event_id, year, title, summary, story_path}, ... ] }

This index is the input for the journey-extraction agent.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

ROOT = Path(__file__).resolve().parent.parent
import os
EVENTS_PATH = Path(os.path.expandvars("%TEMP%/mtc/public/events.json"))
PERSONS_PATH = ROOT / "data" / "persons.json"
OUT_PATH = ROOT / "scripts" / "event_index.json"

if not EVENTS_PATH.exists():
    print(f"events.json not found at {EVENTS_PATH}; clone master-timeline-chabad first", file=sys.stderr)
    sys.exit(2)

persons = json.loads(PERSONS_PATH.read_text(encoding="utf-8"))
events = json.loads(EVENTS_PATH.read_text(encoding="utf-8"))
print(f"Loaded {len(persons)} persons, {len(events)} events")


def name_anchors(p: dict) -> list[str]:
    """Distinctive name fragments that, if matched, strongly imply this person.
    Skip overly generic names like just 'Rebbetzin' or single-word common names
    that appear in too many events.
    """
    out = set()
    cn = (p.get("common_name") or "").strip()
    ne = (p.get("name_en") or "").strip()
    # common_name verbatim (if at least 2 words OR contains a distinctive marker)
    if cn:
        words = cn.split()
        if len(words) >= 2 or any(c.isdigit() for c in cn) or len(cn) > 6:
            out.add(cn)
    # Drop "Rabbi " / "Reb " / "Rebbetzin " prefix from name_en
    stripped = re.sub(r"^(Rabbi|Reb|Rebbetzin|Rabbeinu)\s+", "", ne, flags=re.I)
    if stripped and len(stripped.split()) >= 2:
        out.add(stripped)
    # Distinctive title words ("Tzemach Tzedek", "Maharil of Kapust")
    # Already captured by common_name.
    return [a for a in out if len(a) >= 5]


# Pre-compile regex per person for fast scanning
person_patterns: list[tuple[dict, list[re.Pattern]]] = []
for p in persons:
    anchors = name_anchors(p)
    if not anchors:
        continue
    patterns = [re.compile(r"\b" + re.escape(a) + r"\b", re.IGNORECASE) for a in anchors]
    person_patterns.append((p, patterns))

print(f"Indexing against {len(person_patterns)} persons with distinctive names...")

index: dict[str, list] = {p["id"]: [] for p, _ in person_patterns}

for ev in events:
    title = ev.get("title_en") or ""
    summary = ev.get("summary_en") or ""
    haystack = title + "\n" + summary
    for p, pats in person_patterns:
        if any(pat.search(haystack) for pat in pats):
            year = (ev.get("date") or {}).get("y")
            entry = {
                "event_id": ev["id"],
                "year": year,
                "title": title[:200],
                "summary": summary[:400] if summary != title else None,
                "story_path": ev.get("story_path"),
                "significance": ev.get("significance"),
            }
            index[p["id"]].append(entry)

# Sort each person's events by year (None last)
for pid in index:
    index[pid].sort(key=lambda e: (e["year"] is None, e["year"] or 0))

# Stats
non_empty = {pid: evs for pid, evs in index.items() if evs}
counts = sorted([(len(evs), pid) for pid, evs in non_empty.items()], reverse=True)
print(f"\nPersons with at least 1 event: {len(non_empty)} / {len(persons)}")
print(f"Total event mentions: {sum(len(v) for v in non_empty.values())}")
print("\nTop 20 persons by event count:")
for cnt, pid in counts[:20]:
    p = next(x for x in persons if x["id"] == pid)
    print(f"  {cnt:4}  {pid:35}  {p['common_name']}")

OUT_PATH.write_text(json.dumps(non_empty, ensure_ascii=False, indent=2), encoding="utf-8")
print(f"\nWrote {OUT_PATH} ({OUT_PATH.stat().st_size // 1024} KB)")
