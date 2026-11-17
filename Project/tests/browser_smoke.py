"""Optional Chromium end-to-end check; requires Playwright as a testing tool."""
from pathlib import Path
from playwright.sync_api import sync_playwright


def main():
    root = Path(__file__).resolve().parents[1]
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True, args=["--no-sandbox"])
        page = browser.new_page(viewport={"width": 1600, "height": 1300})
        errors = []
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.goto("http://127.0.0.1:8765")
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Analysis ready')")
        assert page.locator(".photo").count() == 7
        assert not page.locator("#advanced").evaluate("el => el.open")
        assert not page.locator("#measurements").evaluate("el => el.open")
        assert page.locator("#threshold").is_visible()
        assert not page.locator("#minimum").is_visible()
        assert not page.locator("#histogram").is_visible()
        page.locator("#advanced > summary").click()
        assert page.locator("#minimum").is_visible()
        assert page.locator("#minimum").input_value() == "93"
        page.locator("#advanced > summary").click()
        page.locator("#measurements > summary").click()
        assert page.locator("#histogram").is_visible()
        assert page.locator("#results").is_visible()
        page.locator("#measurements > summary").click()
        initial = page.locator("#thresholdNumber").input_value()
        page.locator("h1").click()
        page.keyboard.press("+")
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Analysis ready')")
        assert int(page.locator("#thresholdNumber").input_value()) == int(initial) + 5
        page.locator("#next").click()
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Analysis ready')")
        page.locator("#previous").click()
        assert int(page.locator("#thresholdNumber").input_value()) == int(initial) + 5
        page.wait_for_function("current().result && document.querySelector('#viewer').dataset.ready === 'true'")
        box = page.locator("#viewer").bounding_box()
        page.mouse.move(box["x"]+box["width"]*.2,box["y"]+box["height"]*.2)
        page.mouse.down()
        page.mouse.move(box["x"]+box["width"]*.8,box["y"]+box["height"]*.8,steps=10)
        page.mouse.up()
        page.wait_for_function("document.querySelector('#roiLabel').textContent.includes('original pixels')")
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Analysis ready')")
        assert "original pixels" in page.locator("#roiLabel").inner_text()
        page.locator('[data-view="mask_numbered"]').click()
        page.locator("#save").click()
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Saved to')", timeout=30000)
        assert page.locator("#saveState").inner_text() == "Saved"
        page.locator("#reset").click()
        page.wait_for_function("document.querySelector('#status').textContent.startsWith('Analysis ready')")
        assert page.locator("#roiLabel").inner_text() == "ROI: full image"
        page.screenshot(path=str(root / "dokumentasi/web_dashboard.png"), full_page=True)
        page.set_viewport_size({"width":390,"height":844})
        assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
        assert not errors, errors
        print("Browser PASS: collapsed details, expandable controls and measurements, photos, keyboard, settings retention, scaled ROI, mask tab, save, reset, mobile width; no JS errors")
        browser.close()


if __name__ == "__main__":
    main()