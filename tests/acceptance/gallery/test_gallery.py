"""Behavioral browser tests of the real gallery with fixture I/O; no GPU required."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
from playwright.sync_api import sync_playwright, expect

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args):pass


def main(workspace='/workspace'):
    passed=0;kind=None;failures=[];server=None
    try:
        with tempfile.TemporaryDirectory(prefix='gallery-harness-') as output:
            subprocess.run(['node',str(Path(__file__).with_name('build-harness.cjs')),workspace,output],check=True,timeout=30)
            server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=output))
            threading.Thread(target=server.serve_forever,daemon=True).start()
            with sync_playwright() as pw:
                options={'chromium_sandbox':True}
                if os.getenv('TORQUE_TEST_BROWSER'):options['executable_path']=os.environ['TORQUE_TEST_BROWSER']
                browser=pw.chromium.launch(**options)
                page=browser.new_page(viewport={'width':1000,'height':700})
                page.set_default_timeout(5000)
                page.on('pageerror',lambda error: print('Harness browser error: '+str(error)[:500]))
                def reset():
                    page.goto(f'http://127.0.0.1:{server.server_port}/')
                    expect(page.locator('.card')).to_have_count(2)
                    page.mouse.move(0,0)
                def events(kind):return page.evaluate('(kind)=>window.fixture.events.filter(e=>e[0]===kind)',kind)
                def tab_to_card():
                    for _ in range(20):
                        page.keyboard.press('Tab')
                        if page.locator('.card').first.evaluate('(e)=>e===document.activeElement'):return
                    raise AssertionError('Tab never reaches a gallery card')
                def cards():
                    for key in ('Enter','Space'):
                        reset();tab_to_card();page.keyboard.press(key)
                        page.wait_for_function("window.fixture.events.some(e=>e[0]==='open')")
                        assert events('open')==[['open','one']],key+' must open the focused card exactly once'
                def actions():
                    reset();tab_to_card()
                    expect(page.locator('.card-actions').first).to_be_visible()
                    buttons=page.locator('.card').first.locator('button')
                    expect(buttons).to_have_count(2)
                    for button in buttons.all():assert (button.get_attribute('aria-label') or '').strip(),'Missing action aria-label'
                    page.keyboard.press('Tab');expect(buttons.nth(0)).to_be_focused()
                    page.keyboard.press('Enter')
                    page.wait_for_function("window.fixture.events.some(e=>e[0]==='favorite')")
                    assert events('favorite')==[['favorite','one',True]] and not events('open')
                    page.keyboard.press('Tab');expect(buttons.nth(1)).to_be_focused()
                    page.evaluate('window.fixture.confirm=false');page.keyboard.press('Enter')
                    page.wait_for_timeout(100);expect(page.locator('.card')).to_have_count(2)
                    assert not events('delete') and not events('open')
                    page.evaluate('window.fixture.confirm=true');page.keyboard.press('Space')
                    expect(page.locator('.card')).to_have_count(1)
                    assert events('delete')==[['delete','one']] and not events('open')
                def alt():
                    reset()
                    for image in page.locator('.card img').all():
                        value=(image.get_attribute('alt') or '').strip()
                        assert len(value)>=3 and value.lower() in image.locator('..').get_attribute('title').lower(),'Alt text must describe the prompt'
                def mouse():
                    reset();page.locator('.card').first.click(position={'x':10,'y':10})
                    assert events('open')==[['open','one']]
                    reset();card=page.locator('.card').first;card.hover()
                    card.locator('button').nth(0).click();page.wait_for_function("window.fixture.events.some(e=>e[0]==='favorite')")
                    assert events('favorite')==[['favorite','one',True]] and not events('open')
                    card.locator('button').nth(1).click();expect(page.locator('.card')).to_have_count(1)
                    assert events('delete')==[['delete','one']] and not events('open')
                reset()  # A failure to mount fixture images is infrastructure, not a reproduced bug.
                for name,check in [('card-keyboard',cards),('action-keyboard',actions),('thumbnail-alt',alt),('mouse-regression',mouse)]:
                    try:check();passed+=1
                    except (AssertionError,TimeoutError) as exc:
                        failures.append(name);print(name+': '+str(exc)[:700])
                    except Exception as exc:
                        # Playwright assertions/timeouts have their own exception types.
                        from playwright.sync_api import Error
                        if isinstance(exc,Error):failures.append(name);print(name+': '+str(exc)[:700])
                        else:raise
                browser.close()
                kind='assertion' if failures else None
    except Exception as exc:
        kind='infrastructure'
        print('Gallery acceptance infrastructure failed: '+type(exc).__name__)
    finally:
        if server:server.shutdown();server.server_close()
    print('Failed checks: '+', '.join(failures))
    print('TORQUE_TEST_RESULT='+json.dumps({'failure_kind':kind,'assertions_passed':passed}))
    return 0 if kind is None and passed==4 else 1


if __name__=='__main__':sys.exit(main(sys.argv[1] if len(sys.argv)>1 else '/workspace'))
