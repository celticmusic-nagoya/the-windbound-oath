# Final Bram image adoption QA
- Correct source `assets/companions/bram/BRAM_CORRECT_SHA9a77b564.png` retained as canonical uploaded original.
- SHA-256: `9a77b5644a016237463d4dd308aaf957b9fda88a51dfc20e14508dc7ac7669da`.
- Git Blob SHA: `a1435ee4c295bf7783096099e067408387b3c0e0`.
- Dimensions: 1024×1535, RGBA, alpha 0–255, all corners alpha 0.
- Copied source without modifying bytes to `assets/companions/bram/master/bram-full-body.png`; SHA-256 verified in GitHub Actions [run 42185346908](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/42185346908).
- Rebuilt `web/companions/bram.webp` with transparency; QA PASS.
- Deleted mistaken copies `bram-approved-final.png` and `bram_fullbody_original_alpha0_new(1).png` from working tree.
- Old versions remain recoverable from Git history.
- No runtime game code or other character artwork modified. Android/browser visual QA pending.
