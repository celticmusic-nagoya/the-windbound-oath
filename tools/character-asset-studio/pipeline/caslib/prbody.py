"""Idempotent Draft PR body sections.

A section is wrapped in
    <!-- cas:summary:begin key=KEY -->
    ...
    <!-- cas:summary:end key=KEY -->
merge() replaces the section with the same KEY, appends it if absent, and reports 'unchanged' when the body
would not change — so re-sending the same QA result never duplicates the PR body.

The v0.5 marker `<!-- cas-pipeline-summary -->` (no end marker; its section ran to the end of the body) is
recognised and converted in place to key=legacy-v0.5, keeping its text unchanged.
"""
import re

LEGACY = "<!-- cas-pipeline-summary -->"
LEGACY_KEY = "legacy-v0.5"
KEY_RE = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def begin(key):
    return f"<!-- cas:summary:begin key={key} -->"


def end(key):
    return f"<!-- cas:summary:end key={key} -->"


def _block(key, content):
    return f"{begin(key)}\n{content.strip()}\n{end(key)}"


def convert_legacy(body):
    """Wrap a v0.5 legacy section (marker .. end of body) in begin/end markers. No other text changes."""
    if LEGACY not in body or begin(LEGACY_KEY) in body:
        return body, False
    i = body.index(LEGACY)
    head, tail = body[:i], body[i + len(LEGACY):]
    return head.rstrip() + "\n\n" + _block(LEGACY_KEY, tail) + "\n", True


def sections(body):
    return re.findall(r"<!-- cas:summary:begin key=([A-Za-z0-9._-]+) -->", body)


def merge(body, key, content):
    """Return (new_body, action) with action in {'appended', 'replaced', 'unchanged'} (+ '+legacy-converted')."""
    if not KEY_RE.match(key):
        raise ValueError(f"invalid section key: {key!r}")
    body = body or ""
    body, converted = convert_legacy(body)
    b, e = begin(key), end(key)
    if body.count(b) > 1 or body.count(e) > 1:
        raise ValueError(f"PR body has duplicate markers for key={key}; refusing to guess which one to keep")
    new_block = _block(key, content)
    if b in body:
        if e not in body or body.index(e) < body.index(b):
            raise ValueError(f"PR body has an unterminated section key={key}")
        s, t = body.index(b), body.index(e) + len(e)
        new = body[:s] + new_block + body[t:]
        action = "unchanged" if new == body else "replaced"
    else:
        new = body.rstrip() + "\n\n" + new_block + "\n"
        action = "appended"
    if converted:
        action += "+legacy-converted"
    return new, action
