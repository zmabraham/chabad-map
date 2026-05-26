"""Split bN_v1.json / bN_v2.json (each containing multiple JSON arrays with
stray markdown fences) into per-batch files b{NUM}_v{V}.json starting at NUM=5.

Use when a file dropped into scripts/incoming/ contains more than one array.
"""
import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8")

FENCE = chr(0x60) * 3  # ```


def extract_arrays(text: str) -> list:
    decoder = json.JSONDecoder()
    arrays = []
    pos = 0
    while pos < len(text):
        while pos < len(text):
            ch = text[pos]
            if ch.isspace():
                pos += 1
                continue
            if text[pos:pos + 3] == FENCE:
                nl = text.find("\n", pos)
                pos = nl + 1 if nl >= 0 else len(text)
                continue
            break
        if pos >= len(text):
            break
        try:
            obj, end = decoder.raw_decode(text[pos:])
        except json.JSONDecodeError as e:
            print(f"  parse error at offset {pos}: {e}", file=sys.stderr)
            break
        arrays.append(obj)
        pos += end
    return arrays


INCOMING = Path("scripts/incoming")
START = 5  # First new batch number
removed = []
for src_name in ("bN_v1.json", "bN_v2.json"):
    src = INCOMING / src_name
    if not src.exists():
        continue
    text = src.read_text(encoding="utf-8")
    arrays = extract_arrays(text)
    v_label = "v1" if src_name.endswith("v1.json") else "v2"
    print(f"{src}: {len(arrays)} arrays found")
    for i, arr in enumerate(arrays):
        n = START + i
        out = INCOMING / f"b{n}_{v_label}.json"
        out.write_text(
            json.dumps(arr, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        first = arr[0].get("common_name", "?") if arr else "?"
        last = arr[-1].get("common_name", "?") if arr else "?"
        print(f'  -> {out.name}: {len(arr)} entries (first="{first}", last="{last}")')
    removed.append(str(src))
    os.remove(src)

for r in removed:
    print(f"removed {r}")
