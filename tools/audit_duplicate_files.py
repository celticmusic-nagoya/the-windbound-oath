#!/usr/bin/env python3
"""Read-only duplicate audit; never deletes files. Usage: python3 tools/audit_duplicate_files.py"""
from collections import defaultdict
from pathlib import Path
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[1]
tracked = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).split(b"\0")
groups = defaultdict(list)
text_paths = []
for raw in tracked:
    if not raw:
        continue
    rel = raw.decode("utf-8", "surrogateescape")
    p = ROOT / rel
    if not p.is_file():
        continue
    data = p.read_bytes()
    groups[hashlib.sha256(data).hexdigest()].append((rel, len(data)))
    if p.suffix.lower() in {".py", ".js", ".cjs", ".mjs", ".json", ".md", ".html", ".yml", ".yaml", ".sh", ".txt", ".css"} and "qa_preview_" not in p.name:
        text_paths.append((rel, data.decode("utf-8", errors="replace")))
results = []
for digest, files in sorted(groups.items()):
    if len(files) < 2:
        continue
    entries = []
    for rel, size in files:
        basename = Path(rel).name
        refs = [name for name, data in text_paths if name != rel and (rel in data or basename in data)]
        protected = (rel.startswith(("assets/companions/", "img/", "data/", ".github/")) or
                     "/masks/" in rel or "/reference" in rel.lower() or "/master/" in rel.lower())
        entries.append({"path": rel, "bytes": size, "referenced_in": refs[:20],
                        "references_truncated": len(refs) > 20,
                        "protected": protected, "decision": "HOLD"})
    results.append({"sha256": digest, "files": entries})
print(json.dumps({"duplicate_groups": len(results), "deletions": 0,
                  "note": "Filename/text reference scan is incomplete. No deletion is automatically authorized.",
                  "groups": results}, ensure_ascii=False, indent=2))
