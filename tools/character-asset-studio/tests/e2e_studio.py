#!/usr/bin/env python3
"""Browser E2E for Character Asset Studio v0.2 (Playwright, headless Chromium).

Usage (from the repository root):  python3 tools/character-asset-studio/tests/e2e_studio.py [OUT_DIR]
Serves the repository root on a free localhost port, runs the checks at 390x844 (mobile emulation, touch)
and 1440x900 (desktop), writes screenshots + e2e_report.json to OUT_DIR. Read-only on repository files.
"""
import hashlib, io, json, os, socket, subprocess, sys, time
from pathlib import Path
from PIL import Image
from playwright.sync_api import sync_playwright

ROOT = Path(__file__).resolve().parents[3]
STUDIO = "tools/character-asset-studio/"
OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / STUDIO / "qa"
OUT.mkdir(parents=True, exist_ok=True)


def free_port():
    s = socket.socket(); s.bind(("127.0.0.1", 0)); p = s.getsockname()[1]; s.close(); return p


def run_viewport(p, base, name, vp, mobile):
    rows = []
    def rec(check, ok, detail=""):
        rows.append({"viewport": name, "check": check, "result": "PASS" if ok else "FAIL", "detail": str(detail)})
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport=vp, device_scale_factor=2 if mobile else 1, is_mobile=mobile, has_touch=mobile, accept_downloads=True)
    page = ctx.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("dialog", lambda d: (errors.append("dialog: " + d.message), d.dismiss()))
    page.goto(base + STUDIO + "index.html")
    page.wait_for_selector("body[data-ready='1']", timeout=15000)
    rec("presets loaded", page.locator("#preset option").count() == 6, page.locator("#preset option").count())
    rec("constraints rendered (front)", page.locator("#constraints input[type=checkbox]").count() >= 6, page.locator("#constraints input[type=checkbox]").count())
    ov = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    rec("no horizontal overflow", ov, page.evaluate("[document.documentElement.scrollWidth, window.innerWidth]"))

    # demo candidates + view switching
    page.click("#loadDemo"); page.wait_for_function("document.querySelectorAll('#layers .layeritem').length >= 1", timeout=15000)
    nonblank = {}
    for v in ("front", "back", "left", "right"):
        page.select_option("#view", v)
        label = page.locator("#layers .layeritem span").first.inner_text()
        px = page.evaluate("""() => { const c = document.getElementById('canvas'); const x = c.getContext('2d');
            const d = x.getImageData(500, 600, 200, 400).data; let n = 0; for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i]-233)+Math.abs(d[i+1]-237)+Math.abs(d[i+2]-241) > 60) n++; return n; }""")
        nonblank[v] = px
        rec(f"view {v}: candidate shown and labelled non-canonical", f"morwen_{v}_candidate.png" in label and "[候補]" in label and px > 5000, f"{label} / painted px {px}")
    page.screenshot(path=str(OUT / f"{name}_01_demo_right.png"), full_page=False)

    # canonical read-only view with SHA check
    page.click("#loadCanon"); page.wait_for_function("document.getElementById('qa').innerText.includes('正本照合')", timeout=20000)
    txt = page.inner_text("#qa")
    rec("canonical 4 views SHA-256 match MANIFEST", txt.count("SHA一致") == 4 and "不一致" not in txt, txt)

    # 6 frames: put the left candidate into frames 1..5 of the front view, then play
    page.select_option("#view", "front")
    demo = str(ROOT / STUDIO / "demo/morwen_left_candidate.png")
    for f in range(1, 6):
        page.fill("#frameInput", str(f)); page.dispatch_event("#frameInput", "change")
        page.set_input_files("#file", demo)
        page.wait_for_function(f"document.getElementById('frameLabel').innerText.startsWith('{f} /') && document.querySelectorAll('#layers .layeritem').length >= 1")
    page.fill("#frameInput", "0"); page.dispatch_event("#frameInput", "change")
    page.fill("#fps", "12")
    seen = set()
    page.click("#play")
    t0 = time.time()
    while time.time() - t0 < 1.6:
        seen.add(page.inner_text("#frameLabel").split(" /")[0]); time.sleep(0.04)
    page.click("#play")
    rec(">= 6 frames inspectable via playback", len({s for s in seen if s.isdigit() and int(s) <= 5}) >= 6, sorted(seen, key=lambda s: int(s) if s.isdigit() else 99))
    page.fill("#frameInput", "0"); page.dispatch_event("#frameInput", "change")

    # landmark drag (ground 600,1540 -> 650,1500) with pointer events
    box = page.locator("#canvas").bounding_box()
    sx, sy = box["width"] / 1200, box["height"] / 1600
    page.locator("#canvas").scroll_into_view_if_needed(); box = page.locator("#canvas").bounding_box()
    x0, y0 = box["x"] + 600 * sx, box["y"] + 1540 * sy
    x1, y1 = box["x"] + 650 * sx, box["y"] + 1500 * sy
    page.mouse.move(x0, y0); page.mouse.down(); page.mouse.move((x0 + x1) / 2, (y0 + y1) / 2, steps=4); page.mouse.move(x1, y1, steps=4); page.mouse.up()
    coord = page.inner_text("#lmCoord")
    rec("landmark drag updates coordinates", page.inner_text("#lmName") == "ground" and "manual_edit" in coord, coord)
    page.select_option("#lmConfidence", "medium")

    # spec export determinism + import round trip
    def download(btn):
        with page.expect_download() as d:
            page.click(btn)
        return Path(d.value.path()).read_bytes()
    s1, s2 = download("#exportSpec"), download("#exportSpec")
    spec = json.loads(s1)
    g = spec["landmarks"]["front"]["ground"]
    rec("spec JSON deterministic", s1 == s2, hashlib.sha256(s1).hexdigest()[:16])
    rec("spec v2.0 records drag + confidence", spec["schemaVersion"] == "2.0" and g["source"] == "manual_edit" and g["confidence"] == "medium" and abs(g["px"][0] - 650) <= 4 and abs(g["px"][1] - 1500) <= 4, g)
    rec("spec marks assets canonical/non-canonical", any(a["canonical"] for a in spec["assets"]) and any(not a["canonical"] for a in spec["assets"]) and spec["status"] == "candidate_not_canonical", len(spec["assets"]))
    tmp = OUT / f"{name}_spec_roundtrip.json"; tmp.write_bytes(s1)
    page.evaluate("() => { }")
    page.set_input_files("#importSpec", str(tmp))
    page.wait_for_function("document.getElementById('qa').innerText.includes('素体仕様を読み込みました')")
    s3 = download("#exportSpec")
    rec("spec import -> export round trip identical", s3 == s1, "")
    tmp.unlink()

    # composite (clean, transparent) vs guide PNG
    comp = Image.open(io.BytesIO(download("#exportComposite"))); guide = Image.open(io.BytesIO(download("#guide")))
    ca = comp.convert("RGBA"); ga = guide.convert("RGBA")
    rec("composite PNG 1200x1600 RGBA with alpha 0 corners", comp.size == (1200, 1600) and ca.getpixel((2, 2))[3] == 0 and ca.getpixel((1197, 2))[3] == 0, (comp.size, comp.mode, ca.getpixel((2, 2))))
    cpx = sum(1 for a in ca.getchannel("A").tobytes() if a > 0)
    rec("composite excludes read-only canonical layer but keeps candidate", cpx > 50000, cpx)
    rec("guide PNG differs from clean composite (opaque background + guides)", guide.size == (1200, 1600) and ga.getpixel((2, 2))[3] == 255, ga.getpixel((2, 2)))

    # QA run + JSON
    page.click("#runQA")
    qa = json.loads(download("#exportQA"))
    checks = {c["name"]: c["status"] for c in qa["checks"]}
    rec("QA JSON: canonical SHA PASS, anatomy NOT_RUN, checklist NOT_RUN", checks.get("canonical_sha256") == "PASS" and checks.get("anatomy_and_design") == "NOT_RUN" and all(m["status"] == "NOT_RUN" for m in qa["manualChecklist"]), checks)
    rec("QA flags RGB canon as not transparent (expected FAIL item)", checks.get("real_transparency") == "FAIL", checks.get("real_transparency"))
    page.screenshot(path=str(OUT / f"{name}_02_qa.png"), full_page=True)

    # preset switch (future presets, normalised anchors)
    page.select_option("#preset", "HD_FIELD_1024x1280")
    dims = page.evaluate("[document.getElementById('canvas').width, document.getElementById('canvas').height]")
    rec("preset switch resizes canvas (1024x1280)", dims == [1024, 1280], dims)
    s4 = json.loads(download("#exportSpec"))
    rec("normalised anchor converts to new canvas", s4["canvas"] == {"width": 1024, "height": 1280} and s4["landmarks"]["back"]["ground"]["px"] == [512, 1232], s4["landmarks"]["back"]["ground"]["px"])
    page.screenshot(path=str(OUT / f"{name}_03_preset_hd.png"), full_page=False)
    rec("no console/page errors or alert dialogs", not errors, errors[:5])
    browser.close()
    return rows


def main():
    port = free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    rows = []
    try:
        with sync_playwright() as p:
            rows += run_viewport(p, f"http://127.0.0.1:{port}/", "mobile390", {"width": 390, "height": 844}, True)
            rows += run_viewport(p, f"http://127.0.0.1:{port}/", "desktop1440", {"width": 1440, "height": 900}, False)
    finally:
        srv.terminate()
    fails = [r for r in rows if r["result"] != "PASS"]
    rep = {"tool": "Character Asset Studio v0.2", "runner": "Playwright headless Chromium (emulated viewports)", "result": "FAIL" if fails else "PASS",
           "checks": len(rows), "fail_count": len(fails), "rows": rows,
           "not_run": ["Android real device", "iOS Safari", "real touch-screen drag (emulated pointer only)"]}
    (OUT / "e2e_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("result", "checks", "fail_count")}))
    for r in rows:
        if r["result"] != "PASS": print("FAIL", r["viewport"], r["check"], r["detail"][:300])
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
