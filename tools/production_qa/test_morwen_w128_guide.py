"""Credential-free synthetic tests for W128 G2 guide guards (positive and negative controls)."""
import hashlib
import json
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import morwen_w128_guide as w  # noqa: E402
import morwen_w128_trial as t  # noqa: E402

BG, WIRE, BLUE, STRAND = (232, 232, 232), (194, 217, 65), (30, 120, 230), (90, 60, 100)
REG = {"center_px": [511.5, 385.5], "scale": 1.28, "jacket_mae": 2.0}
S = REG["scale"] * 29 / 51


def bp_point(x, y):
    return [(x - 511.5) / S + 212.5, (y - 385.5) / S + 125]


def screen(rx, g2_selected=True, brush=True, g1_selected=False, cy=370):
    a = np.full((768, 1024, 3), BG, np.uint8)
    a[450:560, 450:575] = (30, 35, 60)
    yy, xx = np.mgrid[0:768, 0:1024]
    inside = ((xx - 511.5) / rx) ** 2 + ((yy - cy) / 58) ** 2 <= 1
    grid = (np.rint(xx - 511.5).astype(int) % 6 == 0) | (np.rint(yy - cy).astype(int) % 6 == 0)
    a[inside & grid] = WIRE
    if g2_selected:
        a[335:355, 51:85] = BLUE
    if g1_selected:
        a[270:290, 51:85] = BLUE
    if brush:
        a[125:150, 351:379] = BLUE
    return a


def write(tmp, name, arr):
    p = Path(tmp) / name
    Image.fromarray(arr).save(p)
    return p


def rows(tmp, png, labels=("Freehand Group 1", "Freehand Group 2")):
    d = {"screen_px": [1024, 768], "screenshot_sha256": hashlib.sha256(Path(png).read_bytes()).hexdigest(),
         "rows": [{"label": l, "x": 160, "y": 280 + 65 * i} for i, l in enumerate(labels)]}
    p = Path(tmp) / (Path(png).stem + "-rows.json")
    p.write_text(json.dumps(d))
    return p


def blueprint(tmp):
    lanes = {f"F0{i}": [bp_point(511.5, 322), bp_point(511.5, 345), bp_point(511.5, 365)] for i in range(2, 6)}
    lanes["F06"] = [bp_point(520, 322), bp_point(536, 345), bp_point(540, 368)]   # right flank
    lanes["F01"] = [bp_point(503, 322), bp_point(487, 345), bp_point(483, 368)]   # left flank
    p = Path(tmp) / "bp.json"
    p.write_text(json.dumps({"schema": "morwen_hair_blueprint_w92_v1",
                             "view_lanes": {"front": [{"id": k, "points_px": v} for k, v in lanes.items()]}}))
    return p


def reg(tmp, png):
    p = Path(tmp) / "reg.json"
    p.write_text(json.dumps(dict(REG, screenshot_sha256=hashlib.sha256(Path(png).read_bytes()).hexdigest())))
    return p


def run_guide(tmp, arr, name="g.png", labels=None):
    png = write(tmp, name, arr)
    rw = rows(tmp, png, labels) if labels else rows(tmp, png)
    out = Path(tmp) / (name + ".json")
    w.guide(png, rw, reg(tmp, png), blueprint(tmp), out)
    return json.loads(out.read_text())


def expect_error(fn, msg):
    try:
        fn()
    except ValueError as e:
        assert msg in str(e), e
    else:
        raise AssertionError("expected failure: " + msg)


def test_wide_guide_draws_flanks(tmp):
    d = run_guide(tmp, screen(rx=40))
    assert d["draw"] == ["F06", "F01"], d["draw"]
    assert d["lanes"]["F06"]["worst_signed_distance_px"] <= w.DRAW_LIMIT


def test_narrow_guide_refuses(tmp):
    d = run_guide(tmp, screen(rx=24))
    assert d["draw"] == [] and d["lanes"]["F06"]["worst_signed_distance_px"] > w.DRAW_LIMIT


def test_selection_and_brush_guards(tmp):
    expect_error(lambda: run_guide(tmp, screen(40, g2_selected=False), "a.png"), "G2 selection")
    expect_error(lambda: run_guide(tmp, screen(40, brush=False), "b.png"), "brush inactive")
    expect_error(lambda: run_guide(tmp, screen(40, g1_selected=True), "c.png"), "G1 still selected")
    expect_error(lambda: run_guide(tmp, screen(40), "d.png", labels=("Freehand Group 1",)), "expected exactly G1 and new G2")


def test_points_spacing_and_eligibility(tmp):
    run_guide(tmp, screen(40))
    gj = Path(tmp) / "g.png.json"
    w.points(gj, "F06")
    expect_error(lambda: w.points(gj, "F03"), "lane not eligible")


def test_completion_and_labels(tmp):
    before = screen(40)
    b = write(tmp, "before.png", before)
    bpf = blueprint(tmp)
    r = Path(tmp) / "r.json"
    r.write_text(json.dumps(REG))
    path, _, _ = w.lane_path(json.loads(bpf.read_text()), "F06", REG)
    def drawn(frac, name):
        a = before.copy()
        for x, y in path[:max(1, int(len(path) * frac))]:
            a[round(y) - 2:round(y) + 3, round(x) - 2:round(x) + 3] = STRAND
        return write(tmp, name, a)
    assert w.complete(b, drawn(1.0, "full.png"), r, bpf, "F06", Path(tmp) / "c1.json") == "COMPLETE"
    assert w.complete(b, drawn(0.5, "half.png"), r, bpf, "F06", Path(tmp) / "c2.json") == "TRUNCATED"
    tb, ta = Path(tmp) / "b.txt", Path(tmp) / "a.txt"
    tb.write_text("Hair 1 | Hair 2 | Freehand Group 2")
    ta.write_text("Hair 1 | Hair 2 | Freehand Group 2 | Hair 1")
    w.newlabel(tb, ta)
    ta.write_text("Hair 1 | Freehand Group 2 | Hair 3")
    expect_error(lambda: w.newlabel(tb, ta), "existing hair label disappeared")


def test_preservation_name_filter(tmp):
    ok = ["W128-g2-brush.png", "W128-F06-completion.json", "W125-save-poll-03.png", "W110-save-return.txt"]
    bad = ["W128-x.vroid", "../W128-a.png", "W110-F06-after.png", "W125-save-poll-3.png", "secret.txt"]
    assert all(t.NAME.fullmatch(n) for n in ok)
    assert not any(t.NAME.fullmatch(n) for n in bad)


def test_w129_eye_hidden_shown_handle(tmp):
    base = screen(40)
    base[274:300, 255:300] = (255, 255, 255)        # white G1 row (row y=280, eye y=288)
    base[286:291, 269:282] = (150, 150, 150)        # G1 eye icon
    with_g1 = base.copy()
    with_g1[318:380, 480:545] = (80, 48, 80)        # G1 fringe strands
    png = write(tmp, "sel.png", with_g1)
    rw = rows(tmp, png)
    w.eye(png, rw, "1")
    expect_error(lambda: w.eye(png, rw, "2"), "eye row is selected")
    hid = write(tmp, "hid.png", base)
    w.hidden(png, hid)
    expect_error(lambda: w.hidden(png, png), "not hidden")
    w.shown(png, hid, hid, png)
    expect_error(lambda: w.shown(png, hid, hid, hid), "not restored")
    # crown handle: white 3x3 core with green ring at the W108 left position, select tool active
    h = base.copy()
    h[125:150, 351:379] = BG
    h[125:150, 315:348] = BLUE
    h[326:339, 492:505] = (40, 200, 40)
    h[331:334, 497:500] = (255, 255, 255)
    hp = write(tmp, "h.png", h)
    hr = rows(tmp, hp)
    rp = Path(tmp) / "hreg.json"
    rp.write_text(json.dumps(dict(REG, screenshot_sha256=hashlib.sha256(hp.read_bytes()).hexdigest())))
    w.handle(hp, hr, rp, "left")
    expect_error(lambda: w.handle(hp, hr, rp, "right"), "crown control point not visible")


def test_w130_crown_lift(tmp):
    a = screen(30, cy=384)
    a[125:150, 351:379] = BG
    a[125:150, 315:348] = BLUE
    for (x, y) in [(500, 352), (511, 353), (523, 352), (490, 358), (532, 358), (484, 368), (538, 368),
                   (481, 380), (541, 380), (481, 395), (541, 395), (511, 375), (511, 395)]:
        a[y - 7:y + 8, x - 7:x + 8] = (40, 200, 40)
        a[y - 2:y + 3, x - 2:x + 3] = (255, 255, 255)
    png = write(tmp, "c.png", a)
    rw = rows(tmp, png)
    rg = reg(tmp, png)
    w.guide(png, rw, rg, blueprint(tmp), Path(tmp) / "g.json", "select")
    w.crown(png, rw, rg, Path(tmp) / "g.json", Path(tmp) / "c.json")
    c = json.loads((Path(tmp) / "c.json").read_text())
    assert all(abs(u - v) <= 0.5 for p, q in zip(c["crown_row"], [[500, 352], [511, 353], [523, 352]]) for u, v in zip(p, q)) and 0 < c["lift_px"] <= 27 * 1.0
    assert all(abs(d[3] * 768 - (d[1] * 768 - c["lift_px"])) < 0.01 for d in c["drags"])
    expect_error(lambda: w.guide(png, rw, rg, blueprint(tmp), Path(tmp) / "g2.json", "brush"), "brush inactive")


def test_w131_shoulder(tmp):
    a = screen(40)
    a[125:150, 351:379] = BG
    a[125:150, 315:348] = BLUE
    pts = [(500, 300), (511, 299), (523, 300), (484, 318), (539, 318), (476, 335), (547, 335),
           (472, 360), (551, 360), (511, 330), (511, 360), (472, 390), (551, 390)]
    for (x, y) in pts:
        a[y - 7:y + 8, x - 7:x + 8] = (40, 200, 40)
        a[y - 2:y + 3, x - 2:x + 3] = (255, 255, 255)
    png = write(tmp, "s.png", a)
    rw, rg = rows(tmp, png), reg(tmp, png)
    gj = Path(tmp) / "g.json"
    w.guide(png, rw, rg, blueprint(tmp), gj, "select")
    g = json.loads(gj.read_text())
    g["lanes"]["F01"]["body_deficit_px"] = 2.3      # simulate the W130 flank deficits
    g["lanes"]["F06"]["body_deficit_px"] = -5.0      # right side already supported
    for l in g["lanes"]:
        g["lanes"][l]["root_deficit_px"] = -6.0
    gj.write_text(json.dumps(g))
    expect_error(lambda: w.crown(png, rw, rg, gj, Path(tmp) / "c.json"), "no crown lift needed")
    w.shoulder(png, rw, rg, gj, Path(tmp) / "s.json")
    sd = json.loads((Path(tmp) / "s.json").read_text())
    assert sd["sides"]["right"]["move"] == 0 and len(sd["drags"]) == 1
    assert sd["sides"]["left"]["point"] == [484.0, 318.0] and sd["sides"]["left"]["target"][0] < 484 and sd["sides"]["left"]["target"][1] < 318


def test_w132_plan(tmp):
    g = {"lanes": {l: {"root_deficit_px": -2.0, "body_deficit_px": -3.0} for l in w.LANES}}
    p = Path(tmp) / "g.json"
    def run(mod):
        d = json.loads(json.dumps(g)); mod(d); p.write_text(json.dumps(d))
        import io, contextlib
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            w.plan(p)
        return buf.getvalue().strip()
    assert run(lambda d: None) == "none"
    assert run(lambda d: d["lanes"]["F03"].update(root_deficit_px=0.4)) == "crown"
    assert run(lambda d: d["lanes"]["F01"].update(body_deficit_px=2.2)) == "shoulder"   # W131 state
    assert run(lambda d: d["lanes"]["F03"].update(body_deficit_px=5.0)) == "none"       # center lane body is not a flank target


def main():
    tests = [v for k, v in globals().items() if k.startswith("test_")]
    for fn in tests:
        with tempfile.TemporaryDirectory() as tmp:
            fn(tmp)
        print("PASS", fn.__name__)
    print(f"{len(tests)}/{len(tests)} PASS")


if __name__ == "__main__":
    main()
