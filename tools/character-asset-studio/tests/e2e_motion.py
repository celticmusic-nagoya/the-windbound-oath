#!/usr/bin/env python3
"""Browser E2E for the v0.3 Motion Reference Studio (Playwright, headless Chromium).

Usage (repository root):  python3 tools/character-asset-studio/tests/e2e_motion.py [OUT_DIR] [--real-video PATH]
* Generates a synthetic H.264 MP4 with ffmpeg at test time (frame index encoded as grey level, lossless),
  so frame stepping can be verified exactly. No third-party video is committed or required.
* --real-video PATH (optional): additionally loads a real reference video together with the committed
  motion/grid_overlay_walk.reference.json and checks the SHA-256 match. Screenshots of real videos are written
  to a temporary directory only (never to OUT_DIR), so no third-party pixels end up in the repository.
"""
import hashlib, json, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_studio import ROOT, STUDIO, free_port  # noqa: E402

args = [a for a in sys.argv[1:]]
REAL = None
if "--real-video" in args:
    i = args.index("--real-video"); REAL = Path(args[i + 1]); del args[i:i + 2]
EXTRA = []
while "--extra-video" in args:
    i = args.index("--extra-video"); EXTRA.append(Path(args[i + 1])); del args[i:i + 2]
OUT = Path(args[0]) if args else ROOT / STUDIO / "qa"
OUT.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="motion_e2e_"))
FPS, NFRAMES = 25, 100


def make_video():
    p = TMP / "synthetic_frame_index.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", f"nullsrc=size=320x240:rate={FPS}:duration={NFRAMES / FPS}",
                    "-vf", "geq=lum='20+2*N':cb=128:cr=128,format=yuv420p", "-c:v", "libx264", "-qp", "0", "-pix_fmt", "yuv420p", str(p)], check=True)
    return p


def lum_frame(page):
    """Grey level at the centre of the video box -> frame index."""
    v = page.evaluate("""() => { const c = document.getElementById('mvCanvas'), x = c.getContext('2d');
        const b = MotionStudio.vbox; const d = x.getImageData(Math.round(b.x + b.w * 0.5), Math.round(b.y + b.h * 0.5), 1, 1).data; return d[0]; }""")
    return round(((v * 219 / 255 + 16) - 20) / 2), v  # limited-range YUV -> RGB


def run_viewport(p, base, name, vp, mobile, vid):
    rows = []
    def rec(check, ok, detail=""):
        rows.append({"viewport": name, "check": check, "result": "PASS" if ok else "FAIL", "detail": str(detail)})
    browser = p.chromium.launch()
    ctx = browser.new_context(viewport=vp, device_scale_factor=2 if mobile else 1, is_mobile=mobile, has_touch=mobile, accept_downloads=True)
    page = ctx.new_page(); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
    page.on("dialog", lambda d: (errors.append("dialog: " + d.message), d.dismiss()))
    page.goto(base + STUDIO + "index.html"); page.wait_for_selector("body[data-ready='1']", timeout=15000)
    rec("v0.3 panel present, v0.2 controls intact", page.locator("#motionPanel").count() == 1 and page.locator("#runQA").count() == 1 and page.locator("#exportSpec").count() == 1, "")

    def download(btn):
        with page.expect_download() as d:
            page.click(btn)
        return Path(d.value.path()).read_bytes()

    # 1. load + frame stepping
    page.set_input_files("#mvFile", str(vid)); page.wait_for_selector("body[data-mv-ready='1']", timeout=20000)
    sha = hashlib.sha256(vid.read_bytes()).hexdigest()
    st = page.inner_text("#mvStatus")
    rec("MP4 loads; SHA-256 computed in browser", sha[:12] in st and "100コマ" in st, st)
    page.locator("#mvCanvas").scroll_into_view_if_needed()
    f, v = lum_frame(page); rec("frame 0 displayed", f == 0 and page.inner_text("#mvFrameLabel") == "0 / 99", (f, v))
    def wait_label(n): page.wait_for_function(f"document.getElementById('mvFrameLabel').innerText === '{n} / 99'", timeout=8000); time.sleep(0.15)
    for _ in range(5): page.click("#mvNext")
    wait_label(5); f, v = lum_frame(page); rec("+1 x5 -> exact frame 5", f == 5, (f, v))
    page.click("#mvPrev"); wait_label(4); f, v = lum_frame(page); rec("-1 -> exact frame 4", f == 4, (f, v))
    page.click("#mvNext10"); wait_label(14); f, v = lum_frame(page); rec("+10 -> exact frame 14", f == 14, (f, v))
    page.evaluate("() => { const s = document.getElementById('mvSlider'); s.value = 50; s.dispatchEvent(new Event('input')); }")
    wait_label(50); f, v = lum_frame(page); rec("slider seek -> exact frame 50", f == 50, (f, v))
    page.click("#mvPlay"); time.sleep(0.9); page.click("#mvPlay"); time.sleep(0.5)
    lab = int(page.inner_text("#mvFrameLabel").split(" /")[0]); f, v = lum_frame(page)
    rec("play then pause advances and lands on a whole frame", lab > 50 and f == lab, (lab, f, v))

    # 2. comparison with the sprite
    page.click("#loadDemo"); page.wait_for_function("document.querySelectorAll('#layers .layeritem').length >= 1", timeout=15000)
    page.select_option("#view", "right"); time.sleep(0.2)
    spec_before = download("#exportSpec")  # baseline after loading the sprite; motion work must not change it
    count = """() => { const c = document.getElementById('mvCanvas'), x = c.getContext('2d'), d = x.getImageData(c.width/2+2, 0, c.width/2-2, c.height).data;
        let n = 0; for (let i = 0; i < d.length; i += 4) if (Math.abs(d[i]-10)+Math.abs(d[i+1]-16)+Math.abs(d[i+2]-24) > 40) n++; return n; }"""
    side_px = page.evaluate(count)
    rec("side-by-side: sprite painted in right half", side_px > 15000, side_px)
    page.select_option("#mvMode", "overlay"); time.sleep(0.2)
    f, v = lum_frame(page)
    ov = page.evaluate("() => { const c = document.getElementById('mvCanvas'); const d = c.getContext('2d').getImageData(c.width/2-60, c.height*0.4, 120, 200).data; let n=0; for (let i=0;i<d.length;i+=4) if (Math.abs(d[i]-d[i+2])>25) n++; return n; }")
    rec("overlay: sprite drawn over the video frame (coloured pixels over grey)", ov > 2000, ov)
    page.select_option("#mvMode", "side")
    page.screenshot(path=str(OUT / f"motion_{name}_01_compare.png"), full_page=False)

    # 3. phases (frames 10A 35B 60A 85B + passing 22)
    def to(n):
        page.evaluate(f"() => {{ const s = document.getElementById('mvSlider'); s.value = {n}; s.dispatchEvent(new Event('input')); }}"); wait_label(n)
    for fr, side in ((10, "A"), (35, "B"), (60, "A"), (85, "B")):
        to(fr); page.select_option("#mvPhase", "contact"); page.select_option("#mvSide", side); page.click("#mvAddPhase")
    to(22); page.select_option("#mvPhase", "passing"); page.select_option("#mvSide", "A"); page.click("#mvAddPhase")
    ph = page.evaluate("MotionStudio.ref.phases.map(p => [p.frame, p.phase, p.side])")
    rec("phases registered and sorted", ph == [[10, "contact", "A"], [22, "passing", "A"], [35, "contact", "B"], [60, "contact", "A"], [85, "contact", "B"]], ph)
    rec("cycles derived from same-side contacts", page.locator("#mvCycle option").count() == 2 and "F10→F60" in page.locator("#mvCycle option").first.inner_text(), page.locator("#mvCycle option").first.inner_text())

    # C. leg-spread extrema are separate markers; contacts are unverified candidates until confirmed by eye
    to(40); page.select_option("#mvPhase", "leg_spread_max"); page.click("#mvAddPhase")
    cand = page.evaluate("[MotionStudio.ref.candidates.map(c => [c.frame, c.kind]), MotionStudio.ref.phases.length]")
    rec("C: leg-spread maximum stored as analysis marker, not as contact", cand == [[[40, "leg_spread_max"]], 5], cand)
    badges = page.locator("#mvPhaseList .mvbadge.cand").count()
    rec("C: registered contacts shown as 候補（未確定）", badges == 4, badges)
    to(10); page.click("#mvConfirm")
    conf = page.evaluate("MotionStudio.ref.phases.filter(p => p.verification === 'visual_confirmed').map(p => p.frame)")
    rec("C: visual confirmation is an explicit per-contact action", conf == [10] and page.locator("#mvPhaseList .mvbadge.ok").count() == 1, conf)
    page.click("#mvConfirm"); page.click("#mvConfirm")   # toggle off and on again
    rec("C: confirmation can be toggled", page.evaluate("MotionStudio.ref.phases.filter(p => p.verification).length") == 1, "")

    # 4. joint anchors via tap/click on the video, trajectory
    page.select_option("#mvJoint", "hip"); page.locator("#mvCanvas").scroll_into_view_if_needed()
    pts = {10: (0.30, 0.50), 20: (0.45, 0.48), 30: (0.60, 0.50)}
    for fr, (nx, ny) in pts.items():
        to(fr)
        box = page.locator("#mvCanvas").bounding_box(); cw = page.evaluate("MotionStudio.cv.width"); s = box["width"] / cw
        vb = page.evaluate("MotionStudio.vbox")
        x = box["x"] + (vb["x"] + nx * vb["w"]) * s; y = box["y"] + (vb["y"] + ny * vb["h"]) * s
        if mobile: page.touchscreen.tap(x, y)
        else: page.mouse.click(x, y)
        time.sleep(0.1)
    traj = page.evaluate("MotionCore.trajectory(MotionStudio.ref, 'hip')")
    ok = len(traj) == 3 and all(abs(t[1] - pts[t[0]][0]) < 0.02 and abs(t[2] - pts[t[0]][1]) < 0.02 for t in traj)
    rec("anchor recorded per frame at tapped position", ok, traj)
    to(15)
    ghost = page.evaluate("MotionCore.anchorAt(MotionStudio.ref, 'hip', 15)")
    rec("interpolated (ghost) anchor between keys", ghost is not None and abs(ghost[0] - 0.375) < 0.02, ghost)
    trail = page.evaluate("""() => { const c = document.getElementById('mvCanvas'), d = c.getContext('2d').getImageData(0, 0, c.width/2, c.height).data;
        let n = 0; for (let i = 0; i < d.length; i += 4) if (d[i+1] > 200 && d[i] > 90 && d[i] < 150 && d[i+2] > 120 && d[i+2] < 190) n++; return n; }""")
    rec("trajectory polyline drawn", trail > 30, trail)
    page.screenshot(path=str(OUT / f"motion_{name}_02_anchors.png"), full_page=False)

    # D1. 12-frame comparison with only one registered sprite frame -> 未登録 shown, counts explicit
    def build(n):
        page.select_option("#mvCount", str(n)); page.click("#mvBuildCycle")
        page.wait_for_function(f"document.getElementById('mvCycleGrid').dataset.count === '{n}'", timeout=30000)
    purple = """(i) => { const c = document.querySelectorAll('#mvCycleGrid canvas')[i], d = c.getContext('2d').getImageData(0, 200, 200, 200).data;
        let n = 0; for (let k = 0; k < d.length; k += 4) if (d[k+2] > d[k+1] + 30 && d[k] > d[k+1] + 15) n++; return n; }"""
    build(12)
    g = page.evaluate("Object.assign({}, document.getElementById('mvCycleGrid').dataset)")
    info = page.inner_text("#mvCycleInfo")
    rec("D1: 1 registered / 11 未登録 in 12-frame comparison", g["registered"] == "1" and g["missing"] == "11" and g["reused"] == "0", g)
    rec("D1: counts stated (登録済み 1/12, 比較枠 12)", "比較枠 12" in info and "登録済みスプライト 1 / 12" in info and "未登録 11 枠" in info, info)
    caps = page.locator("#mvCycleGrid figcaption").all_inner_texts()
    rec("D1: missing cells captioned 未登録", sum("未登録" in c for c in caps) == 11, caps[:3])
    px = [page.evaluate(purple, i) for i in range(12)]
    rec("D1: sprite drawn only in the registered cell (no auto-fill)", px[0] > 800 and all(v == 0 for v in px[1:]), px)
    page.locator("#mvCycleInfo").scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / f"motion_{name}_03_cycle12_missing.png"), full_page=False)
    # reuse preview: opt-in, labelled 仮表示, never counted as registered
    page.check("#mvReuse"); build(12)
    g = page.evaluate("Object.assign({}, document.getElementById('mvCycleGrid').dataset)")
    caps = page.locator("#mvCycleGrid figcaption").all_inner_texts()
    src = page.evaluate("[...document.querySelectorAll('#mvCycleGrid .mvcell')].map(c => c.dataset.state + ':' + c.dataset.sourceFrame)")
    rec("D1: reuse preview labelled 仮表示 (11 cells reuse f0)", g["reused"] == "11" and g["registered"] == "1" and sum("仮表示" in c for c in caps) == 11 and all(x == "reused:0" for x in src[1:]), src[:4])
    rec("D1: reuse notice explains it is not animation material", "アニメーション素材ではありません" in page.inner_text("#mvCycleInfo"), page.inner_text("#mvCycleInfo"))
    rec("D1: reuse does not register frames in the studio", page.evaluate("MotionStudio.registeredFrames()") == [0], page.evaluate("MotionStudio.registeredFrames()"))
    page.screenshot(path=str(OUT / f"motion_{name}_04_cycle12_reuse.png"), full_page=False)
    page.uncheck("#mvReuse")

    rec("phases/anchors/reuse leave BASE_BODY_SPEC unchanged", download("#exportSpec") == spec_before, "")
    # D2. register all 12 frames (distinct images cycle right/front/back/left) -> 6/8/12 show the right frames
    files = ["right", "front", "back", "left"]
    for f in range(1, 12):
        page.fill("#frameInput", str(f)); page.dispatch_event("#frameInput", "change")
        page.set_input_files("#file", str(ROOT / STUDIO / f"demo/morwen_{files[f % 4]}_candidate.png"))
        page.wait_for_function(f"MotionStudio.registeredFrames().includes({f})", timeout=15000)
    page.fill("#frameInput", "0"); page.dispatch_event("#frameInput", "change")
    fp = """(i) => { const c = document.querySelectorAll('#mvCycleGrid canvas')[i], d = c.getContext('2d').getImageData(0, 200, 200, 200).data;
        let h = 2166136261; for (let k = 0; k < d.length; k += 16) { h ^= d[k] + 3 * d[k+1] + 7 * d[k+2]; h = Math.imul(h, 16777619) >>> 0; } return h; }"""
    for n in (6, 8, 12):
        build(n)
        cells = page.evaluate("[...document.querySelectorAll('#mvCycleGrid .mvcell')].map(c => [c.dataset.state, Number(c.dataset.spriteFrame), Number(c.dataset.sourceFrame)])")
        exp = [page.evaluate(f"MotionCore.spriteFrameFor({i}, {n}, 12)") for i in range(n)]
        okmap = all(c[0] == "registered" and c[1] == e and c[2] == e for c, e in zip(cells, exp)) and len(cells) == n
        hashes = [page.evaluate(fp, i) for i in range(n)]
        groups = {}
        for i, e in enumerate(exp): groups.setdefault(files[e % 4], set()).add(hashes[i])
        distinct = len({next(iter(v)) for v in groups.values()}) == len(groups)
        same = all(len(v) == 1 for v in groups.values())
        caps = page.locator("#mvCycleGrid figcaption").all_inner_texts()
        vf = [int(c.split("動画F")[1].split(" ")[0]) for c in caps]
        info = page.inner_text("#mvCycleInfo")
        rec(f"D2: {n}-frame comparison: every cell shows its registered sprite frame", okmap and same and distinct and "登録済みスプライト 12 / 12" in info and f"未登録 0 枠" in info,
            {"frames": [c[1] for c in cells], "images": [files[e % 4] for e in exp], "same_image_identical": same, "different_images_differ": distinct})
        rec(f"D2: {n}-frame comparison sampled evenly (F10..F60)", vf == page.evaluate(f"MotionCore.sampleCycle(10, 60, {n})"), vf)
    page.locator("#mvCycleInfo").scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / f"motion_{name}_05_cycle12_all.png"), full_page=False)

    spec_before = download("#exportSpec")  # re-baseline: frames 1-11 were added through the studio's own layer input
    # B / D3. comparison view: fit, aspect, independent scales, ground alignment
    page.click("#mvResetView"); to(10)
    geo = page.evaluate("({cw: MotionStudio.cv.width, ch: MotionStudio.cv.height, v: MotionStudio.vbox, s: MotionStudio.sbox})")
    half_w, ch = geo["cw"] / 2, geo["ch"]
    v, sb = geo["v"], geo["s"]
    rec("B: video fitted to its half (touches width or height, aspect 4:3 kept)", (abs(v["w"] - half_w) < 1 or abs(v["h"] - ch) < 1) and abs(v["w"] / v["h"] - 4 / 3) < 0.01, v)
    rec("B: sprite cropped to content and fitted (touches width or height)", abs(sb["w"] - half_w) < 1 or abs(sb["h"] - ch) < 1, sb)
    page.evaluate("() => { const e = document.getElementById('mvVScale'); e.value = 200; e.dispatchEvent(new Event('input')); }")
    g2 = page.evaluate("({v: MotionStudio.vbox, s: MotionStudio.sbox})")
    rec("B: video scale independent of sprite", abs(g2["v"]["w"] - 2 * v["w"]) < 1 and g2["s"] == sb, [g2["v"]["w"], v["w"]])
    page.evaluate("() => { const e = document.getElementById('mvVScale'); e.value = 100; e.dispatchEvent(new Event('input')); const s = document.getElementById('mvScale'); s.value = 70; s.dispatchEvent(new Event('input')); }")
    g3 = page.evaluate("({v: MotionStudio.vbox, s: MotionStudio.sbox})")
    rec("B: sprite scale independent of video", g3["v"] == v and abs(g3["s"]["h"] - 0.7 * sb["h"]) < 1, [g3["s"]["h"], sb["h"]])
    page.evaluate("() => { const e = document.getElementById('mvVGround'); e.value = 80; e.dispatchEvent(new Event('input')); }")
    page.click("#mvAlignGround")
    gy = page.evaluate("[MotionStudio.vGroundY, MotionStudio.sGroundY]")
    rec("B: 足元を揃える aligns sprite ground to video foot line", abs(gy[0] - gy[1]) <= 1.5, gy)
    rec("B: alignment changes display only (BASE_BODY_SPEC unchanged)", download("#exportSpec") == spec_before, "")
    cvb = page.locator("#mvCanvas").bounding_box()
    rec("D3: comparison canvas legible size", cvb["height"] >= (250 if mobile else 400) and cvb["width"] >= (320 if mobile else 700), cvb)
    page.locator("#mvCanvas").scroll_into_view_if_needed()
    page.screenshot(path=str(OUT / f"motion_{name}_06_compare_aligned.png"), full_page=False)
    page.click("#mvResetView")

    # 6. JSON export / import
    j1, j2 = download("#mvExport"), download("#mvExport")
    js = json.loads(j1)
    rec("motion JSON deterministic", j1 == j2, hashlib.sha256(j1).hexdigest()[:16])
    rec("motion JSON: UNAPPROVED_REFERENCE, autoApply false, video SHA, no pixels",
        js["status"] == "UNAPPROVED_REFERENCE" and js["autoApply"] is False and js["video"]["sha256"] == sha and b"base64" not in j1 and b"data:image" not in j1 and len(js["phases"]) == 5, js["derived"])
    forged = dict(js); forged["status"] = "APPROVED"; forged["autoApply"] = True
    fp = TMP / f"{name}_forged.json"; fp.write_text(json.dumps(forged))
    page.set_input_files("#mvImport", str(fp)); page.wait_for_function("document.getElementById('mvStatus').innerText.includes('適用')")
    j3 = download("#mvExport")
    rec("import round trip identical; status cannot be upgraded", j3 == j1, "")
    wrong = dict(js); wrong["video"] = dict(js["video"], sha256="0" * 64); wrong["phases"] = []
    wp = TMP / f"{name}_wrong.json"; wp.write_text(json.dumps(wrong))
    page.set_input_files("#mvImport", str(wp)); page.wait_for_function("document.getElementById('mvStatus').innerText.includes('一致しません')")
    rec("JSON for a different video is refused (SHA mismatch)", len(page.evaluate("MotionStudio.ref.phases")) == 5, page.inner_text("#mvStatus"))
    page.click("#mvLoadRepoRef"); page.wait_for_function("document.getElementById('mvStatus').innerText.includes('一致しません')")
    rec("bundled Grid Overlay JSON not applied to an unrelated video", len(page.evaluate("MotionStudio.ref.phases")) == 5, "")

    # 7. studio data untouched by motion work
    spec_after = download("#exportSpec")
    rec("BASE_BODY_SPEC export unchanged by motion data (no auto-apply)", spec_before == spec_after, hashlib.sha256(spec_after).hexdigest()[:16])

    # 8. layout / touch
    ov = page.evaluate("document.documentElement.scrollWidth <= window.innerWidth + 1")
    rec("no horizontal overflow", ov, page.evaluate("[document.documentElement.scrollWidth, window.innerWidth]"))
    if mobile:
        small = page.evaluate("""() => [...document.querySelectorAll('#motionPanel button, #motionPanel .upload, #motionPanel select')]
            .filter(e => e.offsetParent && e.getBoundingClientRect().height < 44).map(e => e.id || e.textContent.trim().slice(0, 12))""")
        rec("mobile: motion controls >= 44px tall", not small, small)
    rec("no console/page errors or alert dialogs", not errors, errors[:5])
    browser.close()
    return rows


def run_real(p, base, path):
    rows = []
    def rec(check, ok, detail=""):
        rows.append({"viewport": "desktop1440_real", "check": check, "result": "PASS" if ok else "FAIL", "detail": str(detail)})
    browser = p.chromium.launch(); page = browser.new_page(viewport={"width": 1440, "height": 900}); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base + STUDIO + "index.html"); page.wait_for_selector("body[data-ready='1']")
    page.click("#mvLoadRepoRef"); page.wait_for_function("document.getElementById('mvStatus').innerText.includes('読み込み済み')")
    page.set_input_files("#mvFile", str(path)); page.wait_for_selector("body[data-mv-ready='1']", timeout=30000)
    st = page.inner_text("#mvStatus")
    rec("real Grid Overlay MP4 (H.264) decodes; SHA matches bundled reference JSON", "参照JSONと一致" in st and "618コマ" in st, st)
    rec("bundled reference applied: 9 contacts, 7 cycles", page.locator("#mvCycle option").count() == 7, page.inner_text("#mvStats"))
    rec("bundled contacts shown as 候補（未確定）, none confirmed", page.locator("#mvPhaseList .mvbadge.cand").count() == 9 and page.locator("#mvPhaseList .mvbadge.ok").count() == 0, page.inner_text("#mvStats"))
    page.evaluate("() => { const s = document.getElementById('mvSlider'); s.value = 85; s.dispatchEvent(new Event('input')); }")
    page.wait_for_function("document.getElementById('mvFrameLabel').innerText === '85 / 617'")
    page.select_option("#mvCount", "8"); page.click("#mvBuildCycle"); page.wait_for_function("document.getElementById('mvCycleGrid').dataset.count === '8'", timeout=30000)
    rec("8-frame comparison on real video", page.locator("#mvCycleGrid .mvcell").count() == 8, "")
    page.screenshot(path=str(TMP / "real_video_not_for_commit.png"), full_page=True)
    rec("no page errors", not errors, errors[:3])
    browser.close()
    return rows


def run_extra(p, base, path, fps):
    rows = []
    def rec(check, ok, detail=""):
        rows.append({"viewport": "desktop1440_extra", "check": f"{path.name[:40]}: {check}", "result": "PASS" if ok else "FAIL", "detail": str(detail)})
    browser = p.chromium.launch(); page = browser.new_page(viewport={"width": 1440, "height": 900}); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base + STUDIO + "index.html"); page.wait_for_selector("body[data-ready='1']")
    page.fill("#mvFps", str(fps)); page.select_option("#mvRegion", "full")
    page.set_input_files("#mvFile", str(path)); page.wait_for_selector("body[data-mv-ready='1']", timeout=30000)
    total = page.inner_text("#mvFrameLabel").split("/ ")[1]
    page.click("#mvNext"); page.wait_for_function("document.getElementById('mvFrameLabel').innerText.startsWith('1 /')")
    rec("decodes and steps one frame", True, f"last frame {total}")
    rec("no page errors", not errors, errors[:3])
    browser.close()
    return rows


def main():
    vid = make_video()
    port = free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0); rows = []
    base = f"http://127.0.0.1:{port}/"
    try:
        with sync_playwright() as p:
            rows += run_viewport(p, base, "mobile390", {"width": 390, "height": 844}, True, vid)
            rows += run_viewport(p, base, "desktop1440", {"width": 1440, "height": 900}, False, vid)
            if REAL: rows += run_real(p, base, REAL)
            for e in EXTRA:
                fps = subprocess.run(["ffprobe", "-v", "error", "-select_streams", "v:0", "-show_entries", "stream=r_frame_rate", "-of", "csv=p=0", str(e)], capture_output=True, text=True).stdout.strip()
                n, d = (fps.split("/") + ["1"])[:2]
                rows += run_extra(p, base, e, round(float(n) / float(d), 3))
    finally:
        srv.terminate()
    fails = [r for r in rows if r["result"] != "PASS"]
    rep = {"tool": "Character Asset Studio v0.4 Motion Reference", "runner": "Playwright headless Chromium (emulated viewports)",
           "video": "synthetic H.264 generated by ffmpeg at test time (lossless, frame index as grey level); not committed",
           "real_video_check": "RUN (screenshots kept outside the repository)" if REAL else "NOT_RUN",
           "extra_videos": [e.name for e in EXTRA],
           "result": "FAIL" if fails else "PASS", "checks": len(rows), "fail_count": len(fails), "rows": rows,
           "not_run": ["Android real device", "iOS Safari", "real touch-screen (emulated touch only)"]}
    (OUT / "e2e_motion_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({k: rep[k] for k in ("result", "checks", "fail_count")}))
    for r in rows:
        if r["result"] != "PASS": print("FAIL", r["viewport"], r["check"], r["detail"][:300])
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
