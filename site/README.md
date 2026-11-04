# THE WINDBOUND OATH — Official Website (`site/`)

WEBSITE-REBUILD-01. A standalone static site, separate from the game (repository root).
Published path on GitHub Pages: `/the-windbound-oath/site/` (game stays at `/the-windbound-oath/`).

## Structure
| Path | Role |
|---|---|
| `index.html` | 8 sections: HERO / NEWS / STORY / SYSTEM / CHARACTERS / GALLERY / PLAY GAME / FOOTER |
| `css/site.css` | Design tokens (CSS variables) + layout. Breakpoints: ≤1024px tablet, ≤768px smartphone (base 390px) |
| `js/site.js` | Mobile menu, news rendering, gallery lightbox (`<dialog>`, ←/→/Esc) |
| `data/news.json` | News list. Edit this file only; items are sorted by date automatically |
| `img/` | Web derivatives only (lossless WebP, downscaled, alpha/aspect kept). `IMAGE_REPORT.json` lists source → output sizes and source SHA-256 |
| `img/screenshots/candidates/` | Real gameplay captures awaiting director approval (not linked yet) |
| `tools/build_images.py` | Rebuilds `img/` from the official originals (read-only) |
| `tools/qa_site.js` | Playwright QA (overflow, images, CLS, nav, lightbox, keyboard, console) |

No framework, no build step. The game's HTML/CSS/JS and original assets are not modified.

## Update news
Add an item to `data/news.json`: `{ "date": "YYYY-MM-DD", "category": "DEVELOPMENT|ART|FIX", "title": "…" }`.

## Rebuild images
```
python3 site/tools/build_images.py
```

## Pending director approval
- STORY introduction text (`data-status="pending-approval"`)
- Emma profile text
- Gameplay screenshots for GALLERY; held CGs (CG02, CG04, CG05) and the Goblin Raider are not included

## Figma (Phase 3)
Sections are flat flex/grid containers with `gap` (→ Auto Layout), tokens in `:root` (→ Figma variables),
and real text/images (no baked-in text), so each section maps to one Auto Layout frame.
