"""Run the candidate on a local HTTP server with Playwright and Chromium."""
import argparse
import base64
import json
import math
import statistics
from pathlib import Path

from playwright.sync_api import sync_playwright


def run(browser, base, out, name, viewport, touch=False):
    page = browser.new_page(viewport=viewport, has_touch=touch, is_mobile=touch)
    page.bring_to_front()
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)
    page.goto(base + "/dev/windwaiting-cliff/?qa", wait_until="networkidle")
    page.wait_for_function("window.cliffQA", timeout=60_000)
    start = page.evaluate("cliffQA.position")
    state = page.evaluate("cliffQA")
    assert state["connectedCells"] > 1000 and state["drawCalls"] > 0
    assert abs(start[1] - state["groundHeight"]) < 0.0001
    assert not errors, errors
    image = page.evaluate("cliffCapture()")
    (out / (name + ".png")).write_bytes(base64.b64decode(image.partition(",")[2]))

    if touch:
        candidates = page.evaluate("""async () => {
          const response = await fetch('../../assets/candidates/lind/windwaiting-cliff-playable/navigation.json');
          const d = await response.json();
          return d.levels.map((y, i) => y === null ? null :
            [d.origin[0]+(i%d.width)*d.stride, y, d.origin[1]+Math.floor(i/d.width)*d.stride])
            .filter(p => p && Math.hypot(p[0]-cliffQA.position[0], p[2]-cliffQA.position[2]) > 1.8 &&
              p[0] < cliffQA.position[0] - 1 && p[2] > cliffQA.position[2] + 1)
            .map(p => ({ p, screen: cliffProject(p) }))
            .find(({screen:[x,y]}) => innerWidth*.37 < x && x < innerWidth*.63 &&
                                      innerHeight*.28 < y && y < innerHeight*.57);
        }""")
        assert candidates, "no visible tap target"
        page.touchscreen.tap(*candidates["screen"])
        page.wait_for_function(
            "p => Math.hypot(p[0]-cliffQA.position[0], p[2]-cliffQA.position[2]) > .8",
            arg=start, timeout=60_000,
        )
    else:
        page.keyboard.down("w")
        try:
            page.wait_for_function(
                "p => Math.hypot(p[0]-cliffQA.position[0], p[2]-cliffQA.position[2]) > 1.5",
                arg=start, timeout=60_000,
            )
        finally:
            page.keyboard.up("w")
    moved = page.evaluate("cliffQA")
    assert abs(moved["position"][1] - moved["groundHeight"]) < 0.0001

    yaw = moved["yaw"]
    if not touch:
        x, y = viewport["width"] // 2, viewport["height"] // 2
        page.mouse.move(x, y)
        page.mouse.down()
        page.mouse.move(x + 121, y + 29, steps=5)
        page.mouse.up()
        page.wait_for_function("yaw => Math.abs(cliffQA.yaw-yaw) > .6", arg=yaw)
        turned = page.evaluate("cliffQA")
        assert math.dist(turned["camera"], moved["camera"]) > 1
    page.get_by_role("button", name="出発点へ").click(force=True)
    page.wait_for_function("start => cliffQA.position.every((v, i) => Math.abs(v-start[i]) < .0001)", arg=start)
    assert not errors, errors
    frames = moved["frameTimes"][2:]
    page.close()
    return {"viewport": viewport, "touch_emulated": touch, "source": start,
            "moved": moved["position"], "ground_error_bu": abs(moved["position"][1] - moved["groundHeight"]),
            "draw_calls": moved["drawCalls"], "triangles": moved["triangles"],
            "sample_frames": len(frames), "median_frame_ms": statistics.median(frames) if frames else None,
            "browser_errors": errors}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(
            executable_path=args.chromium,
            args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--no-sandbox"],
        )
        result = {"browser": browser.version, "renderer": "Chromium headless SwiftShader",
                  "desktop": run(browser, args.base_url, args.output, "browser-desktop", {"width": 960, "height": 560}),
                  "mobile": run(browser, args.base_url, args.output, "browser-touch", {"width": 390, "height": 740}, True)}
    (args.output / "browser-qa.json").write_text(json.dumps(result, indent=2) + "\n")


if __name__ == "__main__":
    main()
