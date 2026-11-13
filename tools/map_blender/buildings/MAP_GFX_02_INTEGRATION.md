# MAP-GFX-02 integration audit (2026-11-13)
- Current main `index.html` uses `renderSystemTab('settings')` and `#systemBody`.
- Existing settings: fullscreen toggle and BGM toggle. Preserve both.
- No existing `js/settings.js` or `js/options.js` was found.
- Existing SAVE_KEY game save must remain separate from graphics preference.
- Proposed integration (NOT APPLIED): load `map_graphics_policy.js` then `map_graphics_settings.js`; create controller using `localStorage`; call `controller.read()`; append UI with `TWOMapGraphicsSettings.mount(body,controller,document)` after existing BGM/fullscreen controls.
- Rendering integration (NOT APPLIED): pass policy to canvas renderers and vegetation scatter; do not scale HTML UI or touch coordinates; never hide interactable/event objects.
- This adapter currently stores preferences and shows controls, but has no effect on game graphics until renderers are connected.
- Status: CODE_COMMITTED; CI and browser QA NOT_RUN. Main/production unchanged.
