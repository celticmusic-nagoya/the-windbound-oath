# Character Asset Studio v0.1 MVP

THE WINDBOUND OATH / candidate asset inspection studio. **No canonical images are modified.**

## Run

Unzip, then start a local HTTP server from the extracted directory:

```sh
python -m http.server 8000
```

Open http://localhost:8000/ . No installation or external dependencies. The interface supports mobile browsers; local file upload works without a server, but the bundled demo may require HTTP.

## Implemented

- Four views (front/back/left/right), per-view provisional landmarks, drag-edit anchors
- 1200×1600 master canvas, 50px grid, ground lines, alpha-checker preview
- Layered PNG import, per-view and per-frame (0–11) management, 1–24 FPS playback
- Transparent composite PNG, guide PNG, silhouette mask PNG export
- BASE_BODY_SPEC JSON export/import with validation
- QA JSON: source SHA-256, dimensions, alpha border, bbox, frame-0 view coverage
- Bundled Morwen **derived candidates** for testing; not authoritative originals

## Not implemented / BLOCKED

- Independent visual design verification, skeleton R2.1 authentication, anatomical QA
- Automatic rigging, occlusion correction, inverse kinematics, 1px image-generation accuracy
- GitHub integration, Draft PR creation, online synchronization
- Multiple master-canvas sizes / actual non-humanoid rig definitions

## QA caution

The included Morwen PNGs are previous **derived prototypes**, not new canon. Their alpha edges and anatomical consistency have not been approved. The landmark defaults are illustrative only, not official measurements. The tool must never mark them canonical based on mechanical QA alone.

## Files

- `index.html`, `styles.css`, `app.js` — standalone browser studio
- `demo/` — four derived candidate PNGs, non-canonical
- `docs/CLAUDE_HANDOFF.md` — next-stage implementation packet
- `docs/BASE_BODY_SPEC.example.json` — data contract example
