#!/usr/bin/env python3
"""Android QA preparation check (emulation only — NOT a real-device QA).

Usage (repository root):  python3 tools/character-asset-studio/tests/android_prep_check.py [OUT_DIR]
Runs headless Chromium with Android Chrome user agents and phone viewports, and measures:
  * how much of the screen the sticky comparison block (canvas + timeline + transport) occupies on narrow screens,
  * whether controls lower in the panel stay reachable/visible (not covered by the sticky block) after scrolling,
  * whether the tool works over an insecure http:// LAN address (crypto.subtle is unavailable there).
Results go to OUT_DIR/android_prep_report.json. Real Android behaviour must still be checked on a device.
"""
import json, subprocess, sys, tempfile, time
from pathlib import Path
from playwright.sync_api import sync_playwright

sys.path.insert(0, str(Path(__file__).resolve().parent))
from e2e_studio import ROOT, STUDIO, free_port  # noqa: E402

OUT = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / STUDIO / "qa"
OUT.mkdir(parents=True, exist_ok=True)
TMP = Path(tempfile.mkdtemp(prefix="android_prep_"))
UA = "Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Mobile Safari/537.36"
# CSS viewports with Chrome's toolbars visible (approximate): small phone, 390 reference, Pixel 7, Pixel 7 landscape.
VIEWPORTS = [("android360x640", 360, 640), ("android390x740", 390, 740), ("pixel7_412x780", 412, 780), ("landscape780x360", 780, 360)]


def make_video():
    p = TMP / "synthetic.mp4"
    subprocess.run(["ffmpeg", "-loglevel", "error", "-y", "-f", "lavfi", "-i", "testsrc2=size=640x360:rate=25:duration=4",
                    "-c:v", "libx264", "-pix_fmt", "yuv420p", str(p)], check=True)
    return p


def measure(p, base, name, w, h, vid):
    b = p.chromium.launch()
    ctx = b.new_context(viewport={"width": w, "height": h}, device_scale_factor=2.625, is_mobile=True, has_touch=True, user_agent=UA, accept_downloads=True)
    page = ctx.new_page(); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(base + STUDIO + "index.html"); page.wait_for_selector("body[data-ready='1']")
    page.click("#loadDemo"); page.wait_for_function("document.querySelectorAll('#layers .layeritem').length >= 1")
    page.set_input_files("#mvFile", str(vid)); page.wait_for_selector("body[data-mv-ready='1']", timeout=20000)
    res = {"viewport": f"{w}x{h}", "errors": errors}
    sticky = page.evaluate("getComputedStyle(document.querySelector('.mvmain')).position")
    res["sticky"] = sticky
    rows = []
    for target in ("#mvAddPhase", "#mvConfirm", "#mvBuildCycle", "#mvExport"):
        page.evaluate(f"document.querySelector('{target}').scrollIntoView({{block: 'center'}})"); time.sleep(0.2)
        r = page.evaluate(f"""() => {{ const e = document.querySelector('{target}'), r = e.getBoundingClientRect();
            const top = document.elementFromPoint(r.left + r.width / 2, r.top + r.height / 2);
            const m = document.querySelector('.mvmain').getBoundingClientRect();
            return {{ visible: r.top >= 0 && r.bottom <= innerHeight, notCovered: top === e || e.contains(top),
                      stickyTop: Math.round(m.top), stickyBottom: Math.round(m.bottom), vh: innerHeight }}; }}""")
        r["target"] = target; rows.append(r)
    res["controls"] = rows
    pinned = [r for r in rows if r["stickyTop"] <= 1 and r["stickyBottom"] > 0]
    res["sticky_share_of_viewport"] = round(max((r["stickyBottom"] - max(0, r["stickyTop"])) / r["vh"] for r in pinned), 3) if pinned else 0
    res["free_height_px_for_controls"] = min((r["vh"] - r["stickyBottom"]) for r in pinned) if pinned else h
    page.evaluate("document.getElementById('mvCanvas').scrollIntoView({block: 'start'})"); time.sleep(0.2)
    cb = page.locator("#mvCanvas").bounding_box(); res["canvas_css"] = [round(cb["width"]), round(cb["height"])]
    res["horizontal_overflow"] = not page.evaluate("document.documentElement.scrollWidth <= innerWidth + 1")
    page.evaluate("document.querySelector('#mvAddPhase').scrollIntoView({block: 'center'})"); time.sleep(0.2)
    page.screenshot(path=str(OUT / f"android_prep_{name}.png"))
    b.close()
    return res


def insecure_context(p, port, vid):
    """http://<LAN-like host> is not a secure context: crypto.subtle (SHA-256) is unavailable."""
    b = p.chromium.launch(args=[f"--host-resolver-rules=MAP studio-lan.test 127.0.0.1"])
    page = b.new_page(viewport={"width": 390, "height": 740}, user_agent=UA); errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.goto(f"http://studio-lan.test:{port}/{STUDIO}index.html"); page.wait_for_selector("body[data-ready='1']")
    secure = page.evaluate("[window.isSecureContext, !!(window.crypto && crypto.subtle)]")
    page.set_input_files("#mvFile", str(vid)); time.sleep(2.5)
    st = page.inner_text("#mvStatus")
    b.close()
    return {"origin": "http://studio-lan.test (insecure, emulates http://192.168.x.x)", "isSecureContext": secure[0], "cryptoSubtle": secure[1],
            "video_load_status": st, "video_loaded": "SHA-256" in st, "errors": errors[:3]}


def main():
    vid = make_video(); port = free_port()
    srv = subprocess.Popen([sys.executable, "-m", "http.server", str(port), "--bind", "127.0.0.1"], cwd=ROOT, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(1.0)
    try:
        with sync_playwright() as p:
            vps = [measure(p, f"http://127.0.0.1:{port}/", n, w, h, vid) for n, w, h in VIEWPORTS]
            ins = insecure_context(p, port, vid)
    finally:
        srv.terminate()
    rep = {"kind": "Android QA preparation (headless Chromium emulation with Android Chrome UA) — NOT real-device QA",
           "real_device": "NOT_RUN", "viewports": vps, "insecure_http_lan": ins}
    (OUT / "android_prep_report.json").write_text(json.dumps(rep, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    for v in vps:
        print(v["viewport"], "sticky", v["sticky"], "share", v["sticky_share_of_viewport"], "free", v["free_height_px_for_controls"],
              "canvas", v["canvas_css"], "covered", [r["target"] for r in v["controls"] if not r["notCovered"]], "overflow", v["horizontal_overflow"], v["errors"][:2])
    print("insecure:", {k: ins[k] for k in ("isSecureContext", "cryptoSubtle", "video_loaded")}, ins["video_load_status"][:80])


if __name__ == "__main__":
    main()
