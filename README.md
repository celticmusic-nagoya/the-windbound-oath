# THE WINDBOUND OATH v0.58

GitHub Pages production-structure migration.

- Base64 image URLs were externalized into `img/battle/embedded/` (22 unique images).
- New finalized assets should use the canonical `img/battle/...` folders.
- CSS is now `css/style.css`.
- Production bridge/asset paths are in `js/`.
- COMMAND is a compact tab when closed and expands only when needed.
- Raider HUD is reduced and moved away from the center in landscape.
- Raider defeat-name stale-copy guard added.

The `embedded` folder is a migration compatibility layer only. It can be removed progressively as finalized named PNGs are placed in canonical folders.
