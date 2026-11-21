"""Compare the PR #421 candidate and isolate the old road material multiplier."""
import argparse
import base64
import json
from pathlib import Path

from playwright.sync_api import sync_playwright


def run(browser, url, out, mode):
    page = browser.new_page(viewport={"width": 960, "height": 560}, device_scale_factor=1)
    errors = []
    page.on("pageerror", lambda error: errors.append(str(error)))
    page.on("console", lambda message: errors.append(message.text) if message.type == "error" else None)

    if mode == "vertex-color-off":
        def remove_vertex_color(route):
            response = route.fetch()
            source = response.text()
            needle = "for (const material of road) {"
            assert source.count(needle) == 1
            route.fulfill(response=response, body=source.replace(needle, needle + "\n    material.vertexColors = false;"))
        page.route("**/surface.mjs", remove_vertex_color)

    hero = int(mode == "hero-cliff")
    headland = int(mode == "headland")
    blueprint = int(mode == "blueprint")
    cliff_v2 = int(mode == "cliff-v2")
    cliff_v3 = int(mode == "cliff-v3")
    cliff_v3d = int(mode == "cliff-v3d")
    composition = int(mode not in ("baseline", "vertex-color-off"))
    mode_query = f"composition={composition}&hero-cliff={hero}&headland={headland}&cliff-blueprint={blueprint}&cliff-v2={cliff_v2}&cliff-v3={cliff_v3}&cliff-v3d={cliff_v3d}"
    page.goto(f"{url}/dev/windwaiting-cliff/?qa&fixed-water&wind=0&photo=1&vista=1&{mode_query}",
              wait_until="domcontentloaded")
    try:
        page.wait_for_function("window.cliffQA?.frameTimes.length > 3", timeout=90_000)
    except Exception:
        print(f"{mode}: {errors}", flush=True)
        raise

    def frame(filename=None):
        png = base64.b64decode(page.evaluate("cliffCapture()").split(",", 1)[1])
        if filename:
            (out / filename).write_bytes(png)
        return png

    stopped = frame(f"{mode}-photo-spawn.png")
    state = page.evaluate("cliffQA")
    result = {key: state[key] for key in ("position", "camera", "groundHeight", "triangles", "drawCalls")}
    if composition:
        assert stopped == frame()
        page.get_by_role("button", name="風を戻す").click()
        page.wait_for_function("cliffQA.wind > 0")
        assert frame(f"{mode}-photo-wind.png") != frame()
        page.get_by_role("button", name="風を止める").click()
        page.wait_for_function("cliffQA.wind === 0")
        assert stopped == frame()
        page.locator("canvas").focus()
        page.keyboard.down("w")
        try:
            page.wait_for_function(
                "p => Math.hypot(p[0]-cliffQA.position[0],p[2]-cliffQA.position[2]) > 1.5",
                arg=state["position"], timeout=75_000,
            )
        finally:
            page.keyboard.up("w")
        moved = page.evaluate("cliffQA")
        assert abs(moved["position"][1] - moved["groundHeight"]) < .0001
        result["movement"] = moved["position"]
        result["movement_ground_error_bu"] = abs(moved["position"][1] - moved["groundHeight"])
        result["wind"] = "animated frames differ and stopped pose matches original PNG"
        frame(f"{mode}-photo-traversal.png")
    assert not errors, errors
    page.close()
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("base_url")
    parser.add_argument("output", type=Path)
    parser.add_argument("--chromium", default="/usr/bin/chromium")
    args = parser.parse_args()
    args.output.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path=args.chromium, args=[
            "--disable-dev-shm-usage", "--enable-unsafe-swiftshader", "--use-angle=swiftshader", "--no-sandbox",
        ])
        results = {mode: run(browser, args.base_url, args.output, mode)
                   for mode in ("baseline", "vertex-color-off", "candidate", "hero-cliff", "headland", "blueprint", "cliff-v2", "cliff-v3", "cliff-v3d")}
        browser.close()
    for key in ("position", "camera", "groundHeight"):
        assert len({json.dumps(result[key]) for result in results.values()}) == 1, key
    for key in ("triangles", "drawCalls"):
        assert results["baseline"][key] == results["vertex-color-off"][key], key
    assert results["candidate"]["triangles"] <= results["baseline"]["triangles"]
    assert results["hero-cliff"]["triangles"] == results["candidate"]["triangles"]
    assert 0 < results["headland"]["triangles"] - results["hero-cliff"]["triangles"] < 1000
    assert results["blueprint"]["triangles"] <= results["headland"]["triangles"] + 1000
    assert results["cliff-v2"]["triangles"] <= results["blueprint"]["triangles"] + 3000
    assert results["cliff-v3"]["triangles"] <= results["cliff-v2"]["triangles"] + 3000
    assert results["cliff-v3d"]["triangles"] <= results["cliff-v3"]["triangles"] + 3000
    (args.output / "webgl-photo-qa.json").write_text(json.dumps(results, indent=2) + "\n")


if __name__ == "__main__":
    main()
