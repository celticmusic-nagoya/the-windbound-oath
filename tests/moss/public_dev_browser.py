"""Browser QA of checked-out bytes at delivery-origin fixtures; --live checks actual deployments."""
import hashlib
import json
import mimetypes
import sys
from urllib.parse import urlsplit, unquote
from pathlib import Path
from playwright.sync_api import sync_playwright, expect

PUBLIC = "https://celticmusic-nagoya.github.io/the-windbound-oath/"
DEV = "https://raw.githack.com/celticmusic-nagoya/the-windbound-oath/main/index.html"
EXPECTED = hashlib.sha256(Path("js/runtime-environment.js").read_bytes()).hexdigest()
OUT = Path("browser-dev-qa")
OUT.mkdir(exist_ok=True)
LIVE = "--live" in sys.argv
MODE = "live" if LIVE else "checkout-origin-fixture"
ROOT = Path.cwd().resolve()

# This is an isolated local response fixture, not a proxy to RawGitHack or a bypass of its notice.
# Only repository files are supplied; the browser never contacts either delivery origin in fixture mode.
def checkout_response(route):
    url = urlsplit(route.request.url)
    prefixes = {"raw.githack.com": "/celticmusic-nagoya/the-windbound-oath/main/",
                "celticmusic-nagoya.github.io": "/the-windbound-oath/"}
    prefix = prefixes.get(url.hostname)
    if not prefix or url.scheme != "https" or not url.path.startswith(prefix):
        route.fulfill(status=404, body="Outside checkout fixture")
        return
    relative = unquote(url.path[len(prefix):]) or "index.html"
    file = (ROOT / relative).resolve()
    if not file.is_relative_to(ROOT) or not file.is_file() or ".git" in file.relative_to(ROOT).parts:
        route.fulfill(status=404, body="Not found in checkout fixture")
        return
    mime = {".js": "text/javascript", ".json": "application/json", ".css": "text/css", ".html": "text/html"}.get(file.suffix.lower()) or mimetypes.guess_type(str(file))[0] or "application/octet-stream"
    route.fulfill(status=200, path=str(file), content_type=mime)

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
            name = MODE + "-" + device + "-" + channel
            context = browser.new_context(viewport=viewport, is_mobile=mobile, has_touch=mobile)
            if not LIVE:
                context.route("https://raw.githack.com/**", checkout_response)
                context.route("https://celticmusic-nagoya.github.io/**", checkout_response)
            page = context.new_page()
            errors_js = []
            page.on("pageerror", lambda e: errors_js.append(str(e)))
            try:
                env_responses = []
                page.on("response", lambda r: env_responses.append(r) if "/js/runtime-environment.js" in r.url else None)
                document = page.goto(url, wait_until="domcontentloaded", timeout=90000)
                assert document and document.ok, f"HTML status {document.status if document else None}"
                # Live provider confirmation is a separate manual acceptance step.
                # Do not automate acceptance of an unverified third-party target.
                if LIVE and enabled and "One more step" in page.locator("body").inner_text():
                    raise RuntimeError("BLOCKED: RawGitHack external content notice requires manual confirmation")
                page.wait_for_function("typeof window.WINDBOUND_DEV === 'boolean'", timeout=60000)
                assert env_responses, "no runtime-environment.js response"
                env = env_responses[-1]
                assert env.ok, f"environment script status {env.status}"
                actual = hashlib.sha256(env.body()).hexdigest()
                assert actual == EXPECTED, f"stale/deviant environment script {actual} != {EXPECTED}"
                page.wait_for_function("typeof window.WINDBOUND_DEV === 'boolean' && !!window.TitleScreen", timeout=60000)
                assert page.evaluate("window.WINDBOUND_DEV") is enabled
                expect(page.locator("#title-screen")).to_be_visible(timeout=30000)
                expect(page.locator('[data-loading-action="new-game"]')).to_be_enabled()
                page.locator('[data-loading-action="new-game"]').click()
                expect(page.locator("#title-screen")).to_be_hidden(timeout=60000)
                page.wait_for_function("window.SaveContinue && SaveContinue.phase === 'READY'", timeout=90000)
                page.wait_for_function("!window.LoadingInput?.busy", timeout=90000)
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
                results.append({"case": name, "mode": MODE, "status": "PASS", "script_sha256": actual, "url": page.url})
            except Exception as e:
                errors.append(name + ": " + str(e))
                try:
                    diagnostic = page.evaluate("({title: document.title, text: document.body?.innerText?.slice(0,1200), scripts: Array.from(document.scripts,s=>s.src).filter(Boolean).slice(0,20), dev: typeof window.WINDBOUND_DEV})")
                except Exception:
                    diagnostic = {}
                results.append({"case": name, "mode": MODE, "status": "BLOCKED" if str(e).startswith("BLOCKED:") else "FAIL", "error": str(e), "page_errors": errors_js, "url": page.url, "diagnostic": diagnostic})
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
