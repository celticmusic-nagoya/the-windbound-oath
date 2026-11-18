#!/usr/bin/env python3
"""Read-only, deterministic pull-request diff report; no AI API or code execution."""
import argparse
import os
from pathlib import Path
import subprocess

MAX_FILES = 100
MAX_PATH_CHARS = 240
SOURCE_SUFFIXES = {".js", ".mjs", ".cjs", ".py", ".html", ".css", ".json"}
SENSITIVE_MARKERS = (".env", ".pem", ".key", "credentials", "secret", "token")


def changed_files(base, head):
    raw = subprocess.check_output([
        "git", "diff", "--name-status", "-z", "--find-renames",
        base, head, "--"
    ])
    parts = raw.split(b"\0")
    result = []
    i = 0
    while i < len(parts) and parts[i]:
        status = os.fsdecode(parts[i])
        i += 1
        if status.startswith(("R", "C")):
            if i + 1 >= len(parts):
                raise ValueError("Malformed rename/copy diff")
            i += 1  # Skip previous path
        if i >= len(parts):
            raise ValueError("Malformed diff")
        path = os.fsdecode(parts[i])
        i += 1
        result.append((status, path))
    return result


def summarize(files):
    lines = ["# PR change review (read-only)", "",
             "Automated inventory only. This is not an AI code review or an approval.", ""]
    source = [(s, p) for s, p in files if Path(p).suffix.lower() in SOURCE_SUFFIXES]
    lines += [f"- Changed files: **{len(files)}**",
              f"- Source/config files: **{len(source)}**", ""]
    if len(files) > MAX_FILES:
        lines.append(f"- Display truncated to {MAX_FILES} files; review the full diff on GitHub.")
    lines += ["| Change | File | Review note |", "|---|---|---|"]
    for status, path in files[:MAX_FILES]:
        lower = path.lower()
        note = ("Check for credentials or private data" if any(x in lower for x in SENSITIVE_MARKERS)
                else "Review behavior and regressions" if Path(path).suffix.lower() in SOURCE_SUFFIXES
                else "Verify asset provenance and compatibility")
        safe_path = path[:MAX_PATH_CHARS].replace("|", "\\|").replace("\n", " ").replace("\r", " ").replace("`", "'")
        lines.append(f"| {status[:8]} | `{safe_path}` | {note} |")
    if not files:
        lines.append("| — | No changed files | Check selected base/head refs |")
    lines += ["", "## Manual gates", "",
              "- [ ] Confirm canon/design locks and source provenance",
              "- [ ] Review gameplay regression and mobile impact",
              "- [ ] Verify relevant existing automated tests",
              "- [ ] Confirm no secrets or unexpected generated assets",
              "", "No files were modified and no approval is implied."]
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", required=True)
    parser.add_argument("--head", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()
    report = summarize(changed_files(args.base, args.head))
    Path(args.output).write_text(report, encoding="utf-8")
    print(f"Review report written: {args.output}")


if __name__ == "__main__":
    main()
