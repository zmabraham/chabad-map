"""Helper to accumulate drive crawl results.

Usage:
    python _ingest_drive.py <input_jsonl_or_json> <parent_folder_title>

Or read from stdin: lines of JSON file-objects, with `--parent-title` flag.
We just append/replace per-file entries in _drive_crawl.json.
"""
import json
import sys
import os

STATE = os.path.join(os.path.dirname(__file__), '_drive_crawl.json')


def load():
    with open(STATE, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(state):
    with open(STATE, 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def add_records(items, parent_folder_id=None, parent_folder_title=None):
    state = load()
    existing_ids = {f['id'] for f in state['files']}
    existing_folder_ids = {f['id'] for f in state['folders']}
    added_f = 0
    added_d = 0
    for it in items:
        mime = it.get('mimeType', '')
        if mime == 'application/vnd.google-apps.folder':
            if it['id'] in existing_folder_ids:
                continue
            state['folders'].append({
                'id': it['id'],
                'title': it.get('title'),
                'parent_id': parent_folder_id or it.get('parentId'),
                'parent_title': parent_folder_title,
            })
            existing_folder_ids.add(it['id'])
            added_d += 1
        elif mime.startswith('image/'):
            if it['id'] in existing_ids:
                continue
            state['files'].append({
                'id': it['id'],
                'title': it.get('title'),
                'mime': mime,
                'size': int(it.get('fileSize', 0)) if it.get('fileSize') else 0,
                'parent_id': parent_folder_id or it.get('parentId'),
                'parent_title': parent_folder_title,
            })
            existing_ids.add(it['id'])
            added_f += 1
    save(state)
    print(f'Added {added_f} files, {added_d} folders. Total now: {len(state["files"])} files / {len(state["folders"])} folders')


if __name__ == '__main__':
    # JSON object on stdin with key 'files', plus parent_folder_id and parent_folder_title
    payload = json.load(sys.stdin)
    add_records(payload['files'], payload.get('parent_folder_id'), payload.get('parent_folder_title'))
