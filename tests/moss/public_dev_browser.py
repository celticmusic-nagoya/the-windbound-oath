"""Live deployment smoke test; does not alter existing user saves."""
import hashlib
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

PUBLIC = "https://celticmusic-nagoya.github.io/the-windbound-oath/"
DEV = "https://raw.githack.com/celticmusic-nagoya/the-windbound-oath/main/index.html"
EXPECTED = hashlib.sha256(Path("js/runtime-environment.js").read_bytes()).hexdigest()
OUT = Path("browser-dev-qa")
OUT.mkdir(exist_ok=True)
errors = []
results = []

with sync_playwright() as p:
    browser = p.chromium.launch(headless=True)
    for device, viewport, mobile in [
        ("desktop", {"width": 1440, "height": 900}, False),
        ("mobile-emulation", {"width": 390, "height": 844}, True),
    ]:
        for channel, url, enabled in [
            ("public", PUBLIC + "?dev=1&title=0&legacyVillage=1&height25d=1&perf=1&motiontest=1", False),
            ("development", DEV, True),
        ]:
            name = device + "-" + channel
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile)
            page = context.new_page()
            errors_js = []
            page.on("pageerror", lambda e: errors_js.append(str(e)))
            try:
                with page.expect_response(lambda r: "/js/runtime-environment.js" in r.url, timeout=60000) as response:
                    document = page.goto(url, wait_until="domcontentloaded", timeout=90000)
                assert document and document.ok, f"HTML status {document.status if document else None}"
                env = response.value
                assert env.ok, f"environment script status {env.status}"
                actual = hashlib.sha256(env.body()).hexdigest()
                assert actual == EXPECTED, f"stale/deviant environment script {actual} != {EXPECTED}"
                page.wait_for_function("typeof window.WINDBOUND_DEV === 'boolean' && !!window.TitleScreen", timeout=60000)
                assert page.evaluate("window.WINDBOUND_DEV") is enabled
                expect(page.locator("#title-screen")).to_be_visible(timeout=30000)
                expect(page.locator('[data-loading-action="new-game"]')).to_be_enabled()
                page.locator('[data-loading-action="new-game"]').click()
                expect(page.locator("#title-screen")).to_be_hidden(timeout=60000)
                if enabled:
                    expect(page.locator("#devBtn")).to_be_visible(timeout=90000)
                    expect(page.locator("#devBuildIndicator")).to_be_visible()
                    page.locator("#devBtn").click(timeout=60000)
                    expect(page.locator("#devPanel")).to_be_visible()
                    expect(page.locator("#devInstantKill")).to_be_visible()
                    expect(page.locator("#devForceCritical")).to_be_visible()
                    assert page.evaluate("typeof window.MotionTest?.open === 'function'")
                    page.locator("#devClose").click()
                else:
                    for selector in ["#devBtn", "#devPanel", "#devBuildIndicator", ".dev-only-command", "#height25dBadge"]:
                        assert page.locator(selector).evaluate_all("(els) => els.every(e => getComputedStyle(e).display === 'none' || getComputedStyle(e).visibility === 'hidden')"), selector
                    assert page.evaluate("typeof window.MotionTest === 'undefined' && devJump('opening') === false && BattleCritical.force() === false")
                    assert page.evaluate("PrologueCombat.instantKill('normal') === false")
                assert not errors_js, f"page errors: {errors_js}"
                results.append({"case": name, "status": "PASS", "script_sha256": actual, "url": page.url})
            except Exception as e:
                errors.append(name + ": " + str(e))
                results.append({"case": name, "status": "FAIL", "error": str(e), "page_errors": errors_js, "url": page.url})
            finally:
                try:
                    page.screenshot(path=str(OUT / (name + ".png")), timeout=10000)
                except Exception as e:
                    print("Screenshot unavailable:", e)
                context.close()
                (OUT / "results.json").write_text(json.dumps(results, indent=2), encoding="utf-8")
    browser.close()

print(json.dumps(results, indent=2))
assert not errors, "\n".join(errors)
