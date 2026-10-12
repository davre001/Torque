"""Real website scripts and styles, with fixture media and download/network I/O."""
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import json
import os
from pathlib import Path
import sys
import threading
from playwright.sync_api import sync_playwright, expect, TimeoutError as BrowserTimeout

class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self,*args): pass

def main(workspace='/workspace'):
    server=ThreadingHTTPServer(('127.0.0.1',0),partial(QuietHandler,directory=str(Path(workspace)/'site')))
    threading.Thread(target=server.serve_forever,daemon=True).start()
    passed=0; failures=[]; kind=None
    try:
        with sync_playwright() as pw:
            options={'chromium_sandbox':True}
            if os.getenv('TORQUE_TEST_BROWSER'): options['executable_path']=os.environ['TORQUE_TEST_BROWSER']
            browser=pw.chromium.launch(**options)
            ctx=browser.new_context(viewport={'width':1100,'height':850})
            ctx.add_init_script("""window.mediaCalls=[];
                HTMLMediaElement.prototype.play=function(){window.mediaCalls.push(this.id);return Promise.resolve()};
                HTMLMediaElement.prototype.pause=function(){};""")
            base=f'http://127.0.0.1:{server.server_port}'
            def route(r):
                if r.request.url.split('?')[0] in (base+'/',base+'/assets/style.css'): r.continue_()
                else: r.fulfill(status=200,body='',content_type='text/plain')
            ctx.route('**/*',route)
            page=ctx.new_page();page.set_default_timeout(3000)
            def reset(motion='reduce'):
                page.emulate_media(reduced_motion=motion)
                page.goto(base+'/',wait_until='domcontentloaded')
                expect(page.locator('#tabs .tab')).to_have_count(8)
                page.locator('#cmp').scroll_into_view_if_needed()
                page.wait_for_timeout(1700)
                page.mouse.move(0,0)
            reset()  # Initialization failure is infrastructure, not an acceptance failure.
            cmp=page.locator('#cmp')
            def split(): return cmp.evaluate("e=>parseFloat(e.style.getPropertyValue('--split'))")
            def tab_to_slider():
                page.locator('#tabs .tab').last.focus()
                for _ in range(12):
                    page.keyboard.press('Tab')
                    if cmp.evaluate('e=>e===document.activeElement'): return
                raise AssertionError('Slider is not reachable by Tab')
            def semantic():
                tab_to_slider()
                expect(cmp).to_have_attribute('role','slider')
                assert cmp.get_attribute('aria-label') or cmp.get_attribute('aria-labelledby'), 'Slider needs a label'
                expect(cmp).to_have_attribute('aria-valuemin','0');expect(cmp).to_have_attribute('aria-valuemax','100')
                assert abs(float(cmp.get_attribute('aria-valuenow'))-split())<0.1
            def keyboard():
                tab_to_slider()
                page.keyboard.press('Home');assert split()==0
                page.keyboard.press('ArrowLeft');assert split()==0
                page.keyboard.press('ArrowRight');assert split()==5
                page.keyboard.press('End');assert split()==100
                page.keyboard.press('ArrowRight');assert split()==100
                page.keyboard.press('ArrowLeft');assert split()==95
                assert float(cmp.get_attribute('aria-valuenow'))==95
            def sweep_focus():
                reset('no-preference');page.locator('#tabs .tab').nth(1).click()
                tab_to_slider();page.keyboard.press('Home');page.wait_for_timeout(400)
                assert split()==0, 'Keyboard interaction must stop sweep'
                style=cmp.evaluate("e=>{let s=getComputedStyle(e);return [s.outlineStyle,s.outlineWidth,s.boxShadow]}")
                assert (style[0]!='none' and float(style[1].replace('px',''))>0) or style[2]!='none', 'Focus needs visible styling'
            def descriptions():
                for index in (0,1,2):
                    page.locator('#tabs .tab').nth(index).click()
                    prompt=page.locator('#cmp-prompt').inner_text().strip()
                    mode=page.locator('#cmp-mode').inner_text().strip()
                    for name in ('#cmp-before','#cmp-after'):
                        alt=page.locator(name).get_attribute('alt') or ''
                        assert mode.lower() in alt.lower() and prompt[:40].lower() in alt.lower(), 'Image description lacks selected mode/prompt'
                assert page.locator('#cmp-bg').get_attribute('alt')=='', 'Background remains decorative'
            def regression():
                reset();box=cmp.bounding_box();page.mouse.click(box['x']+box['width']*.25,box['y']+box['height']*.5)
                assert abs(split()-25)<1
                old=page.locator('#cmp-after').get_attribute('src');page.locator('#tabs .tab').nth(1).click()
                assert page.locator('#cmp-after').get_attribute('src')!=old
                page.locator('#reel').scroll_into_view_if_needed();page.wait_for_timeout(300)
                assert page.evaluate("window.mediaCalls.filter(x=>x==='reel').length")==0, 'Reduced-motion autoplay regression'
                page.locator('#reel-btn').click()
                assert page.evaluate("window.mediaCalls.filter(x=>x==='reel').length")==1
                reset('no-preference');page.locator('#reel').scroll_into_view_if_needed();page.wait_for_timeout(400)
                assert page.evaluate("window.mediaCalls.includes('reel')"), 'Normal autoplay regression'
            for name,test in [('slider-semantics',semantic),('slider-keys',keyboard),('sweep-and-focus',sweep_focus),('image-descriptions',descriptions),('pointer-tabs-motion',regression)]:
                reset()
                try: test();passed+=1
                except (AssertionError,BrowserTimeout,TypeError,ValueError) as exc:
                    failures.append(name+': '+str(exc)[:800])
            browser.close()
            kind='assertion' if failures else None
    except Exception as exc:
        kind='infrastructure';failures.append(type(exc).__name__+': '+str(exc)[:800])
    finally: server.shutdown();server.server_close()
    for failure in failures: print(failure)
    print('TORQUE_TEST_RESULT='+json.dumps({'failure_kind':kind,'assertions_passed':passed}))
    return 0 if kind is None and passed==5 else 1

if __name__=='__main__': sys.exit(main(sys.argv[1] if len(sys.argv)>1 else '/workspace'))
