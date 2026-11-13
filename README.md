# THE WINDBOUND OATH
### Mionn na Gaoithe

Original Celtic-flavored browser JRPG / portfolio project.

## Morwen Blender production progress

[モルウェン制作進捗・レンダリングQA](docs/design/MORWEN_PROGRESS.md) — confirmed status, GitHub Actions and production references. Status is updated manually; the linked Actions page shows live runs.

## Current portraits / DEV

Phase 4 and Phase 5A are COMPLETE. Approved portraits for Aidan/Fiona/Lou/Emma are connected to115production dialogue pages; user Android QA5/5PASS. Fiona brow repair is CLOSED.259formal PNGs remain SHA-protected.

Game → DEV ▶ → 立ち絵・モーションテスト:28approved expressions,24blinking/4intentionally static. [Current DEV guide and authoritative adoption records](docs/portraits/DEV_PORTRAIT_GUIDE.md). Older QA/handoff documents preserve their historical status; Lou smile/relieved remain unadopted.

## Development stack
- HTML
- CSS
- Vanilla JavaScript
- GitHub Pages
- Responsive PC / Android Chrome

## Current handoff baseline
**v0.66 — Impact Effects**

The project is transitioning from rapid prototype iteration into repository-based development with Codex.

## Read before editing
Codex/AI coding agents must read:

1. `AGENTS.md`
2. `docs/GAME_DESIGN.md`
3. `docs/ROADMAP.md`

`AGENTS.md` contains confirmed rules and regression hazards. Do not redesign stable systems without an explicit request.

## Project direction
The goal is a polished original indie-style JRPG vertical slice, not a generic HTML demo.

Theme:
> 守れなかった者たちが、今度こそ誰かを守る

Tagline:
> 失った故郷。残された仲間。そして、風だけが知っていた真実。

## Asset policy
Production graphics should be stored as normal files under `img/` and referenced by relative paths.
Final battle characters/monsters use individually generated transparent assets, not crops from composite design sheets.

## Development policy
Keep DEV-only Event Jump / one-hit-kill utilities during development, but gate them clearly and remove/disable them for public release.

See `docs/ROADMAP.md` for the recommended next task.
