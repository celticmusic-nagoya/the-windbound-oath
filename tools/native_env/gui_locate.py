#!/usr/bin/env python3
"""State-gated GUI step for X11 apps (Xvfb): screenshot -> OCR label locator -> click -> postcondition.

Each step captures the screen, locates a label with tesseract (exact normalised word sequence, optional region),
clicks its centre (or a calibrated offset), then waits for a postcondition label (or a file) with bounded attempts.
On failure it records the screenshot and OCR words; on a missing label it scrolls a bounded number of times inside
the given region before giving up. Every step is appended to a JSON-lines ledger (evidence / reusable mapping).
Usage: gui_locate.py step --display :91 --ledger L.jsonl --shots DIR --name ID --label "Send now" [--region x0,y0,x1,y1]
                         [--scroll-at x,y] [--expect "Blender: sent 1"] [--expect-file PATH] [--offset dx,dy] [--type TEXT]
       gui_locate.py click --display :91 --at x,y ...   (calibrated coordinate, same postcondition gate)
"""
import argparse
import csv
import io
import json
import os
import subprocess
import time
from pathlib import Path


def sh(*a, env=None, **k):
    return subprocess.run(list(a), check=True, capture_output=True, env=env, **k)


def shot(disp, path):
    sh("import", "-display", disp, "-window", "root", str(path))
    return path


VARIANTS = ([], ["-colorspace", "Gray", "-negate", "-level", "20%,80%"], ["-colorspace", "Gray", "-threshold", "60%", "-negate"])


def ocr(path, region=None):
    """OCR in three contrast variants (dark UI, light-on-colour buttons); returns one word list per variant."""
    x0, y0, x1, y1 = region or (0, 0, 0, 0)
    geo = ["-crop", f"{x1 - x0}x{y1 - y0}+{x0}+{y0}", "+repage"] if region else []
    out_lists = []
    for k, v in enumerate(VARIANTS):
        img = f"{path}.v{k}.png"
        sh("convert", str(path), *geo, "-resize", "200%", *v, img)
        out = sh("tesseract", img, "-", "--psm", "11", "tsv").stdout.decode("utf-8", "replace")
        words = []
        for r in csv.DictReader(io.StringIO(out), delimiter="\t", quoting=csv.QUOTE_NONE):
            t = (r.get("text") or "").strip()
            if t and float(r.get("conf") or -1) > 30:
                words.append({"t": t, "x": x0 + int(r["left"]) / 2, "y": y0 + int(r["top"]) / 2,
                              "w": int(r["width"]) / 2, "h": int(r["height"]) / 2,
                              "line": (r["block_num"], r["par_num"], r["line_num"])})
        out_lists.append(words)
    return out_lists


def norm(s):
    return "".join(ch for ch in s.lower() if ch.isalnum())


def find(variants, label):
    hits = []
    for words in variants:
        for h in find_one(words, label):
            if all(abs(h["cx"] - o["cx"]) > 8 or abs(h["cy"] - o["cy"]) > 8 for o in hits):
                hits.append(h)
    return hits


def find_one(words, label):
    want = [norm(w) for w in label.split() if norm(w)]
    hits = []
    for i in range(len(words)):
        seq = words[i:i + len(want)]
        if len(seq) == len(want) and all(norm(a["t"]) == b for a, b in zip(seq, want)) and len({s["line"] for s in seq}) == 1:
            x0, y0 = seq[0]["x"], min(s["y"] for s in seq)
            x1, y1 = seq[-1]["x"] + seq[-1]["w"], max(s["y"] + s["h"] for s in seq)
            line_words = [w["t"] for w in words if w["line"] == seq[0]["line"]]
            hits.append({"cx": (x0 + x1) / 2, "cy": (y0 + y1) / 2, "line": " ".join(line_words)})
    return hits


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("mode", choices=("step", "click", "check"))
    ap.add_argument("--display", required=True)
    ap.add_argument("--ledger", required=True)
    ap.add_argument("--shots", required=True)
    ap.add_argument("--name", required=True)
    ap.add_argument("--label")
    ap.add_argument("--line-excludes", default="", help="reject hits whose OCR line contains this word")
    ap.add_argument("--line-exact", action="store_true", help="the whole OCR line must equal the label (buttons)")
    ap.add_argument("--at")
    ap.add_argument("--region")
    ap.add_argument("--scroll-at")
    ap.add_argument("--offset", default="0,0")
    ap.add_argument("--type")
    ap.add_argument("--expect")
    ap.add_argument("--expect-region")
    ap.add_argument("--expect-file")
    ap.add_argument("--timeout", type=float, default=20)
    a = ap.parse_args()
    env = dict(os.environ, DISPLAY=a.display)
    shots = Path(a.shots)
    shots.mkdir(parents=True, exist_ok=True)
    region = [int(v) for v in a.region.split(",")] if a.region else None
    rec = {"name": a.name, "mode": a.mode, "label": a.label, "t": round(time.time(), 2)}
    before = shot(a.display, shots / f"{a.name}_before.png")
    target = None
    if a.mode == "step":
        for attempt in range(6):
            hits = find(ocr(before, region), a.label)
            if a.line_excludes:
                hits = [h for h in hits if a.line_excludes.lower() not in h["line"].lower()]
            if a.line_exact:
                hits = [h for h in hits if norm(h["line"]) == norm(a.label)]
            if len(hits) == 1:
                target = hits[0]
                break
            rec.setdefault("locate_attempts", []).append({"hits": len(hits)})
            if len(hits) > 1:
                break  # ambiguous: never guess
            if a.scroll_at:  # bounded scroll inside the panel, then re-locate
                x, y = a.scroll_at.split(",")
                sh("xdotool", "mousemove", x, y, env=env)
                for _ in range(3):
                    sh("xdotool", "click", "5", env=env)
                time.sleep(0.6)
                before = shot(a.display, shots / f"{a.name}_before_s{attempt}.png")
            else:
                break
        if target is None:
            rec["result"] = "LOCATE_FAIL"
            Path(a.ledger).open("a").write(json.dumps(rec) + "\n")
            raise SystemExit(f"LOCATE_FAIL {a.name}: {a.label}")
        dx, dy = (float(v) for v in a.offset.split(","))
        x, y = int(target["cx"] + dx), int(target["cy"] + dy)
        rec["located"] = target
    elif a.mode == "click":
        x, y = (int(v) for v in a.at.split(","))
    if a.mode != "check":
        rec["click"] = [x, y]
        sh("xdotool", "mousemove", str(x), str(y), env=env)
        time.sleep(0.15)
        sh("xdotool", "click", "1", env=env)
        if a.type is not None:
            time.sleep(0.3)
            sh("xdotool", "key", "ctrl+a", env=env)
            sh("xdotool", "type", "--delay", "15", a.type, env=env)
    ok, end = a.expect is None and a.expect_file is None, time.monotonic() + a.timeout
    er = [int(v) for v in a.expect_region.split(",")] if a.expect_region else None
    n = 0
    while not ok and time.monotonic() < end:
        time.sleep(1.0)
        after = shot(a.display, shots / f"{a.name}_after.png")
        n += 1
        ok = True
        if a.expect:
            ok = bool(find(ocr(after, er), a.expect))
        if a.expect_file:
            ok = ok and Path(a.expect_file).exists()
    shot(a.display, shots / f"{a.name}_after.png")
    rec["postcondition_checks"] = n
    rec["result"] = "PASS" if ok else "POSTCONDITION_FAIL"
    Path(a.ledger).open("a").write(json.dumps(rec) + "\n")
    print("TWO_GUI_STEP", json.dumps(rec), flush=True)
    if not ok:
        raise SystemExit(f"POSTCONDITION_FAIL {a.name}")


if __name__ == "__main__":
    main()
