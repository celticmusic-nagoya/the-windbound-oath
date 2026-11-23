"""Oracle tests for g1_eval: the source itself must PASS every criterion it supplies; a shifted/shrunk candidate and
moved locks must FAIL; missing inputs stay NOT_RUN (never PASS). Needs SRC_DIR with the verified originals."""
import json
import os
import shutil
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import g1_eval as G  # noqa: E402
from observed_locks_l0 import VIEWS  # noqa: E402

SRC = Path(os.environ.get("TWO_L0_SRC", "/tmp/l0/src"))
BP = json.loads((HERE / "morwen_hair_l0_blueprint_v1.json").read_text())


def cand_from_source(tmp, shift=0, scale=1.0, move=0):
    c = {"views": {}}
    for v, (f, _) in VIEWS.items():
        im = Image.open(SRC / f)
        if shift or scale != 1.0:
            w, h = im.size
            im = im.resize((int(w * scale), int(h * scale)))
            canvas = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            canvas.paste(im, (shift, 0))
            im = canvas
        im.save(tmp / f"{v}.png")
        locks = {lid: [[x + move, y] for x, y in L["views"][v]["points_px"]]
                 for lid, L in BP["locks"].items() if v in L["views"]}
        pts = {k: p["xy_px"] for k, p in BP["points"].items() if p["view"] == v}
        c["views"][v] = {"render": f"{v}.png", "locks": locks, "points": pts}
    return c


def run(**kw):
    tmp = Path(tempfile.mkdtemp())
    try:
        return G.evaluate(BP, cand_from_source(tmp, **kw), tmp)
    finally:
        shutil.rmtree(tmp)


def test_identity_passes():
    r = run()
    assert r["status"] == "PASS", r["counts"]


def test_shift_fails_silhouette():
    r = run(shift=20)
    assert any(k.startswith("silhouette") and c["status"] == "FAIL" for k, c in r["criteria"].items())


def test_shrink_fails_silhouette():
    r = run(scale=0.9)
    assert r["status"] == "FAIL"


def test_moved_locks_fail():
    r = run(move=8)
    assert any(k.startswith("lock_") and c["status"] == "FAIL" for k, c in r["criteria"].items())


def test_missing_is_not_run():
    r = G.evaluate(BP, {"views": {}}, Path("."))
    assert r["status"] == "NOT_RUN" and r["counts"]["PASS"] == 0


if __name__ == "__main__":
    for n, f in list(globals().items()):
        if n.startswith("test_"):
            f()
            print("ok", n)
