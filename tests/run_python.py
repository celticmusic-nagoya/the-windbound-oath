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
path = sys.argv[1]
sys.argv = sys.argv[1:]
sys.path.insert(0, os.path.dirname(os.path.abspath(path)))
runpy.run_path(path, run_name='__main__')
