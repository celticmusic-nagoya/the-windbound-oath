# Bram director-confirmed replacement
Director explicitly confirmed that the GitHub-uploaded `bram_fullbody_original_alpha0_new.png` should be used even though its bytes differ from the chat attachment.
- GitHub-uploaded source SHA-256: `403f9e01a05d6b5ae4dbca1b7614b3d17b2797f6054ab8a2797f67c43cf5e191`.
- Chat attachment SHA-256 (not used): `9a77b5644a016237463d4dd308aaf957b9fda88a51dfc20e14508dc7ac7669da`.
- GitHub Actions [run 42176528107](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/42176528107): source SHA verification, image dimensions and alpha extrema, master copy, WebP creation and removal of superseded uploads passed.
- Current master: `assets/companions/bram/master/bram-full-body.png`.
- Current WebP derivative: `web/companions/bram.webp`.
- Superseded `assets/companions/bram/bram_fullbody_original_alpha0.png` deleted from current tree; mistaken Japanese-named upload and temporary `bram_fullbody_original_alpha0_new.png` deleted from feature branch.
- Previous versions remain recoverable in Git history; no history rewrite.
- No runtime code changes. Browser/game QA not run.
