"""Independent browser assertions. Run only inside the reviewed container."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import sys
from pathlib import Path
import threading
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from torque_reporting import Reporter
from playwright.sync_api import sync_playwright, expect

def main():
    server = ThreadingHTTPServer(("127.0.0.1",0),
                                partial(SimpleHTTPRequestHandler,directory="/workspace/site"))
    thread = threading.Thread(target=server.serve_forever,daemon=True)
    thread.start()
    passed = 0
    reporter = Reporter()
    kind = None
    stage = "launch-browser"
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(chromium_sandbox=True)
            with reporter.case("reduced-motion-paused"):
                stage = "check-reduced-motion"
                base = f"http://127.0.0.1:{server.server_port}/"
                # Separate contexts prevent state leaking between motion preferences.
                reduced = browser.new_context(reduced_motion="reduce")
                page = reduced.new_page()
                page.goto(base,wait_until="domcontentloaded")
                video = page.locator("#reel")
                video.scroll_into_view_if_needed()
                page.wait_for_function("document.querySelector('#reel').readyState >= 2")
                page.wait_for_timeout(1000)
                assert video.evaluate("(v) => v.paused"), "Reduced-motion autoplay must remain paused"
                passed += 1
            with reporter.case("manual-play"):
                stage = "check-manual-play"
                page.locator("#reel-btn").click()
                expect(video).to_have_js_property("paused",False,timeout=5000)
                passed += 1
            reduced.close()
            with reporter.case("normal-autoplay"):
                stage = "check-normal-autoplay"
                normal = browser.new_context(reduced_motion="no-preference")
                page = normal.new_page()
                page.goto(base,wait_until="domcontentloaded")
                page.locator("#reel").scroll_into_view_if_needed()
                expect(page.locator("#reel")).to_have_js_property("paused",False,timeout=5000)
                passed += 1
            normal.close()
            browser.close()
    except AssertionError as exc:
        kind = "assertion"
        print(str(exc))
    except Exception as exc:
        kind = "infrastructure"
        print("Browser acceptance infrastructure failed: "+type(exc).__name__)
        # The isolated container receives no credentials; keep browser stderr bounded.
        print("Stage: "+stage)
        print(str(exc)[:6000])
    finally:
        server.shutdown()
        server.server_close()
    print("TORQUE_TEST_RESULT="+json.dumps({"failure_kind":kind,"assertions_passed":passed,"cases":reporter.cases}))
    return 0 if kind is None and passed == 3 else 1

if __name__ == "__main__":
    sys.exit(main())
