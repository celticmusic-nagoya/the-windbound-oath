"""Same-camera photo material comparison; no external textures at runtime."""
import base64
import hashlib
import json
import statistics
from pathlib import Path
from playwright.sync_api import sync_playwright

out = Path("photo-comparison")
out.mkdir(exist_ok=True)
results = {}
with sync_playwright() as p:
    browser = p.chromium.launch(args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--no-sandbox"])
    for mode in (0, 1):
        page = browser.new_page(viewport={"width":960,"height":560}, device_scale_factor=1)
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        page.on("console", lambda m: errors.append(m.text) if m.type == "error" else None)
        page.on("response", lambda r: errors.append(str(r.status)+" "+r.url) if r.status >= 400 else None)
        page.goto(f"http://127.0.0.1:8765/dev/windwaiting-cliff/?qa&fixed-water&wind=0&photo={mode}")
        page.wait_for_function("window.cliffQA?.frameTimes.length >= 16", timeout=180000)
        state = page.evaluate("cliffQA")
        png = base64.b64decode(page.evaluate("cliffCapture()").split(",",1)[1])
        (out / f"photo-{mode}.png").write_bytes(png)
        assert not errors, errors
        results[str(mode)] = {k:state[k] for k in ("position","camera","groundHeight","triangles","drawCalls")}
        results[str(mode)].update(sha256=hashlib.sha256(png).hexdigest(), median_frame_ms=statistics.median(state["frameTimes"][-12:]))
        page.close()
    browser.close()
for k in ("position","camera","groundHeight","triangles","drawCalls"):
    assert results["0"][k] == results["1"][k], k
assert results["0"]["sha256"] != results["1"]["sha256"], "photo candidate has no visible effect"
(out/"comparison.json").write_text(json.dumps(results,indent=2)+"\n")
