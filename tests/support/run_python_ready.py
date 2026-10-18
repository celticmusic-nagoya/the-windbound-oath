#!/usr/bin/env python3
"""Run an unmodified test after the startup opening line has been shown (READY gate).
The opening 「朝の風が窓を揺らしている…」 is spoken by RildeVillage.startOpening 350 ms after the opening map commits.
Tests that start their own conversation after a fixed wait race with it on slow machines (Issue #16 re-QA, CODEX-P2-REQA-20261019).
This runner only waits for that line (goto/reload) -- it changes no assert, no timeout and no test source.
Env: PW_CHROMIUM_EXECUTABLE (optional), LATE_MS (optional, delay the opening by N ms to simulate a slow machine)."""
import os, runpy, sys
from playwright.sync_api import BrowserType, Page
exe = os.environ.get('PW_CHROMIUM_EXECUTABLE'); late = int(os.environ.get('LATE_MS', '0'))
if exe:
    _l = BrowserType.launch
    BrowserType.launch = lambda self, *a, **k: _l(self, *a, **({**k, 'executable_path': k.get('executable_path') or exe} if self.name == 'chromium' else k))
INIT = """(()=>{const L=%d;const st=window.setTimeout;window.setTimeout=function(f,d,...a){if(L&&d===350&&typeof f==='function'&&String(f).includes('\\u671d\\u306e\\u98a8'))d=350+L;return st.call(window,f,d,...a)};
window.__openingSeen=false;const mo=()=>{const m=document.getElementById('msg');if(!m){requestAnimationFrame(mo);return}new MutationObserver(()=>{if((m.textContent||'').includes('\\u671d\\u306e\\u98a8'))window.__openingSeen=true}).observe(m,{childList:true,subtree:true,characterData:true})};mo()})();""" % late
def gate(page):
    page.wait_for_function('window.__openingSeen===true', timeout=60000); page.wait_for_timeout(150)
_goto, _reload = Page.goto, Page.reload
def goto(self, url, *a, **k):
    if not getattr(self, '_ready_init', False): self.add_init_script(INIT); self._ready_init = True
    r = _goto(self, url, *a, **k); gate(self); return r
def reload(self, *a, **k):
    r = _reload(self, *a, **k); gate(self); return r
Page.goto, Page.reload = goto, reload
path = sys.argv[1]; sys.argv = sys.argv[1:]; sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
runpy.run_path(path, run_name='__main__')
