"""Optional deterministic live-camera browser check; no physical camera required."""
from pathlib import Path
import tempfile
import threading

import cv2
import numpy as np
from playwright.sync_api import sync_playwright

from web_app import create_server


def main():
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        image = np.zeros((120, 160, 3), np.uint8)
        cv2.rectangle(image, (20, 20), (40, 40), (255, 255, 255), -1)
        cv2.imwrite(str(root / "photo.png"), image)
        server = create_server(root, root / "exports", 0)
        thread = threading.Thread(target=server.serve_forever, daemon=True)
        thread.start()
        try:
            with sync_playwright() as playwright:
                browser = playwright.chromium.launch(executable_path="/usr/bin/chromium", headless=True,
                                                     args=["--no-sandbox"])
                page = browser.new_page(viewport={"width": 1400, "height": 1100})
                errors = []
                page.on("pageerror", lambda error: errors.append(str(error)))
                page.add_init_script("""window.denyCamera=false; window.streams=[];
                    navigator.mediaDevices.getUserMedia=async()=>{
                        if(window.denyCamera)throw new DOMException('Permission denied','NotAllowedError');
                        const c=document.createElement('canvas');c.width=160;c.height=120;
                        const x=c.getContext('2d');x.fillStyle='black';x.fillRect(0,0,160,120);
                        x.fillStyle='white';x.fillRect(20,20,21,21);
                        const stream=c.captureStream(10);window.streams.push(stream);return stream;
                    };""")
                page.goto(f"http://127.0.0.1:{server.server_port}")
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('Analysis ready')")

                def check_immediate_adjustment(endpoint):
                    page.locator("h1").click()
                    page.wait_for_function("!photoBusy && !cameraBusy")
                    page.evaluate("""endpoint=>{
                        window.analysisCalls=[];window.releaseAnalysis=null;
                        const original=window.fetch;
                        window.fetch=async(path,options)=>{
                            if(path===endpoint){
                                window.analysisCalls.push(JSON.parse(options.body));
                                if(window.analysisCalls.length===1)
                                    await new Promise(resolve=>window.releaseAnalysis=resolve);
                            }
                            return original(path,options);
                        };
                        window.restoreFetch=()=>window.fetch=original;
                    }""", endpoint)
                    previous_count = page.locator("#count").inner_text()
                    previous_rows = page.locator("#results").inner_html()
                    initial_threshold = int(page.locator("#thresholdNumber").input_value())
                    page.evaluate("document.dispatchEvent(new KeyboardEvent('keydown',{key:'+'}))")
                    assert page.evaluate("window.analysisCalls.length") == 1, "Analysis must start in the input handler, without a timer"
                    for key in ("+", "+", "-"):
                        page.keyboard.press(key)
                    assert int(page.locator("#thresholdNumber").input_value()) == initial_threshold + 10
                    assert page.evaluate("window.analysisCalls.length") == 1, "Do not queue parallel requests"
                    assert page.locator("#count").inner_text() == previous_count
                    assert page.locator("#results").inner_html() == previous_rows
                    assert page.locator("#saveState").inner_text() == "Not saved / changed"
                    assert "pending" not in page.locator("body").inner_text().lower()
                    assert page.locator("#save").is_disabled()
                    page.keyboard.press("s")
                    assert page.locator("#save").is_disabled()
                    page.evaluate("window.releaseAnalysis()")
                    page.wait_for_function("current().pending === false && !document.querySelector('#save').disabled")
                    calls = page.evaluate("window.analysisCalls")
                    assert calls[-1]["threshold"] == initial_threshold + 10
                    if endpoint == "/api/analyze":
                        assert len(calls) == 2, "Only process the active request and latest settings"
                    page.evaluate("window.restoreFetch()")

                check_immediate_adjustment("/api/analyze")
                page.locator("#cameraStart").click()
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('Live detection')")
                assert page.locator("#count").inner_text() == "1"
                assert page.locator("#filename").inner_text().startswith("Live camera")
                page.wait_for_function("document.querySelector('#viewer').dataset.ready==='true'")
                check_immediate_adjustment("/api/camera/analyze")
                page.locator("#thresholdNumber").fill("255")
                page.locator("#thresholdNumber").press("Tab")
                page.wait_for_function("document.querySelector('#count').textContent==='0'")
                page.locator("#thresholdNumber").fill("127")
                page.locator("#thresholdNumber").press("Tab")
                page.wait_for_function("document.querySelector('#count').textContent==='1'")
                page.locator('[data-view="original"]').click()
                page.wait_for_function("document.querySelector('#viewer').dataset.ready==='true'")
                box = page.locator("#viewer").bounding_box()
                page.mouse.move(box["x"] + box["width"] * .05, box["y"] + box["height"] * .05)
                page.mouse.down()
                page.mouse.move(box["x"] + box["width"] * .6, box["y"] + box["height"] * .6, steps=5)
                page.mouse.up()
                page.wait_for_function("current().result && current().params.roi !== null && current().pending === false")
                page.locator("#save").click()
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('Saved camera snapshot')")
                assert len(list((root / "exports/camera").glob("*/original.png"))) == 1
                page.locator("#cameraStop").click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('photo') || document.querySelector('#status').textContent.startsWith('Analysis ready')")
                assert page.evaluate("window.streams.every(s=>s.getTracks().every(t=>t.readyState==='ended'))")
                page.locator("#cameraStart").click()
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('Live detection')")
                page.locator(".photo").click()
                page.wait_for_function("document.querySelector('#filename').textContent==='photo.png'")
                assert page.evaluate("window.streams.every(s=>s.getTracks().every(t=>t.readyState==='ended'))")
                page.evaluate("window.denyCamera=true")
                page.locator("#cameraStart").click()
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('Cannot start camera')")
                assert page.locator("#cameraStart").is_enabled()
                server.photos = []
                page.reload()
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('No photos found')")
                page.evaluate("window.denyCamera=false")
                page.locator("#cameraStart").click()
                page.wait_for_function("document.querySelector('#status').textContent.startsWith('Live detection')")
                assert page.locator("#count").inner_text() == "1"
                page.locator("#cameraStop").click()
                assert page.evaluate("window.streams.every(s=>s.getTracks().every(t=>t.readyState==='ended'))")
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth<=window.innerWidth")
                assert not errors, errors
                browser.close()
                print("Camera browser PASS: immediate photo/camera adjustments, latest-settings processing without request backlog, stable results, save protection, live counts, ROI, snapshot, stop/restart, permission denial, empty library, mobile width")
        finally:
            server.shutdown()
            server.server_close()
            thread.join()


if __name__ == "__main__":
    main()