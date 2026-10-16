# test-only: run existing engine tests with BL-01 Loading bypassed (they start battles directly and assume an immediate start)
try:
    from playwright.sync_api import Page
    _g = Page.goto
    def goto(self, *a, **k):
        try: self.context.add_init_script("window.WINDBOUND_NO_BATTLE_LOADING=true")
        except Exception: pass
        return _g(self, *a, **k)
    Page.goto = goto
except Exception:
    pass
