#!/usr/bin/env python3
"""Run an existing test; optionally use an installed Chromium (no assertion changes)."""
import os
import runpy
import sys

executable = os.environ.get('PW_CHROMIUM_EXECUTABLE')
if executable:
    from playwright.sync_api import BrowserType
    original = BrowserType.launch

    def launch(self, *args, **kwargs):
        if self.name == 'chromium':
            kwargs.setdefault('executable_path', executable)
        return original(self, *args, **kwargs)

    BrowserType.launch = launch
# TITLE-01: the game now opens on a title screen. Existing tests start at the game itself, so (like their other URL
# parameters) ?title=0 is added to local index.html URLs that do not name a `title` parameter. No assertion/wait change;
# a test that wants the title passes title=1 (or any title=) explicitly. Disable with WINDBOUND_TITLE_AUTOSKIP=0.
if os.environ.get('WINDBOUND_TITLE_AUTOSKIP', '1') != '0':
    from urllib.parse import urlsplit, urlunsplit, parse_qsl
    from playwright.sync_api import Page
    original_goto = Page.goto

    def goto(self, url, *args, **kwargs):
        try:
            u = urlsplit(url)
            if u.hostname in ('localhost', '127.0.0.1') and u.path in ('/', '/index.html') and 'title' not in dict(parse_qsl(u.query, keep_blank_values=True)):
                url = urlunsplit((u.scheme, u.netloc, u.path, (u.query + '&' if u.query else '') + 'title=0', u.fragment))
        except Exception:
            pass
        return original_goto(self, url, *args, **kwargs)

    Page.goto = goto
path = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
runpy.run_path(path, run_name='__main__')
