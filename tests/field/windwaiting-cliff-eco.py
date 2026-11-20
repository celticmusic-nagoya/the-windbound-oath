"""Compare ECO v1/v2 with one Chromium, camera, viewport and render backend."""
import argparse
import base64
import hashlib
import json
import statistics
from pathlib import Path

from playwright.sync_api import sync_playwright


def capture(page):
    return base64.b64decode(page.evaluate("cliffCapture()").split(",", 1)[1])


def benchmark(browser, base, output, version):
    page = browser.new_page(viewport={"width": 960, "height": 560}, device_scale_factor=1)
    page.bring_to_front()
    issues = []
    page.on("pageerror", lambda error: issues.append(str(error)))
    page.on("console", lambda msg: issues.append(msg.text) if msg.type == "error" else None)
    page.goto(f"{base}/dev/windwaiting-cliff/?qa&fixed-water&wind=0&eco={version}", wait_until="load")
    page.wait_for_function("() => window.cliffQA?.frameTimes.length >= 16", timeout=120_000)
    assert not issues, issues
    state = page.evaluate("window.cliffQA")
    samples = state["frameTimes"][-12:]
    results = {
        "position": state["position"], "camera": state["camera"],
        "ground_height": state["groundHeight"],
        "triangles": state["triangles"], "draw_calls": state["drawCalls"],
        "frame_ms_median": statistics.median(samples),
        "frame_ms_p90": sorted(samples)[10],
        "sample_count": len(samples), "samples_ms": samples,
    }
    png = capture(page)
    (output / f"web-{version}.png").write_bytes(png)
    if version == "v2":
        assert state["wind"] == 0
        quiet_a = capture(page)
        quiet_b = capture(page)
        assert png == quiet_a == quiet_b, "zero wind changed the still scene"
        page.get_by_role("button", name="風を戻す").click(force=True)
        page.wait_for_function("cliffQA.wind > 0")
        windy_a = capture(page)
        windy_b = capture(page)
        assert windy_a != windy_b and windy_a != png, "wind did not move visible vegetation"
        page.get_by_role("button", name="風を止める").click(force=True)
        page.wait_for_function("cliffQA.wind === 0")
        stopped = capture(page)
        assert stopped == png, "wind-stop did not restore exactly the zero pose"
        results["wind"] = {
            "zero_frames_identical": True, "active_frames_differ": True,
            "stop_returns_to_zero_pose": True, "zero_png_sha256": hashlib.sha256(png).hexdigest(),
        }
    assert not issues, issues
    page.close()
    return results


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base")
    parser.add_argument("output", type=Path)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium,
            args=["--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--no-sandbox"])
        versions = {version: benchmark(browser, args.base, args.output, version) for version in ("legacy", "v2")}
        for key in ("position", "camera", "ground_height"):
            assert versions["legacy"][key] == versions["v2"][key], key
        result = {"browser": browser.version, "renderer": "headless SwiftShader", "resolution": [960, 560],
                  "method": "stationary spawn, water frozen, wind zero; discard the first 4 RAF intervals",
                  "results": versions}
        browser.close()
    (args.output / "comparison.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
