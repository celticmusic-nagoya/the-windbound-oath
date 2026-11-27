"""Fail-closed public gallery boundary. Existing public records are immutable here."""
import argparse
import json
import pathlib
import re

def index(manifest):
    rows = manifest["entries"]
    by_sha = {}
    for row in rows:
        sha = row["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", sha) or sha in by_sha:
            raise ValueError("invalid or duplicate gallery SHA")
        by_sha[sha] = row
    return by_sha

def approved_candidates(history, staged, approvals):
    old = index(history)
    candidates = index(staged)
    allowed = {}
    for receipt in approvals["entries"]:
        sha = receipt["sha256"]
        if not re.fullmatch(r"[0-9a-f]{64}", sha) or sha in allowed:
            raise ValueError("invalid or duplicate publication receipt")
        if not isinstance(receipt.get("approval_ref"), str) or not receipt["approval_ref"].strip():
            raise ValueError("missing explicit publication approval reference")
        if not re.fullmatch(r"[0-9a-f]{40}", receipt["head"]):
            raise ValueError("invalid approved source HEAD")
        allowed[sha] = receipt
    selected = []
    for sha, row in candidates.items():
        if sha in old or sha not in allowed:
            continue
        receipt = allowed[sha]
        if row.get("stage", "").endswith("/ preview only"):
            raise ValueError("preview-only record cannot enter public gallery")
        for key in ("head", "name", "path", "run_id", "artifact_id", "source_path"):
            if row.get(key) != receipt.get(key):
                raise ValueError("approved source provenance mismatch: " + key)
        selected.append(row)
    return {"version": 1, "entries": selected}

def verify(history, approved, final):
    old, new, actual = map(index, (history, approved, final))
    if old.keys() & new.keys():
        raise ValueError("approved delta overlaps history")
    if actual != {**old, **new}:
        raise ValueError("public delta differs from approved records or alters history")
    return len(old), len(new)

def read(path):
    return json.loads(pathlib.Path(path).read_text())

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["filter", "verify"])
    parser.add_argument("history")
    parser.add_argument("candidate")
    parser.add_argument("third")
    parser.add_argument("output", nargs="?")
    a = parser.parse_args()
    if a.mode == "filter":
        delta = approved_candidates(read(a.history), read(a.candidate), read(a.third))
        if not a.output:
            parser.error("filter requires output")
        pathlib.Path(a.output).write_text(json.dumps(delta, ensure_ascii=False, indent=2) + "\n")
        print("Approved public delta:", len(delta["entries"]))
    else:
        old, new = verify(read(a.history), read(a.candidate), read(a.third))
        print("Public boundary verified: historical", old, "approved additions", new)

if __name__ == "__main__":
    main()
