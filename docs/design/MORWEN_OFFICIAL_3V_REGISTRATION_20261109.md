# MORWEN-3V — director-approved registration tracking

Date: 2026-11-09
Status: DESIGN APPROVED; BINARY UPLOAD NOT YET COMPLETED; NOT PUBLISHED

Official images: right profile, left profile (without satchel, hat flower/ribbon decoration, or shoulder crest), back view.

Expected source PNGs (1024x1536 RGBA; original alpha max 254; preserve bytes):

| Direction | SHA-256 |
|---|---|
| right | 7eeff76ac07f631c14cb536e0e08346cfe815247a88520fb5a68cf0e877e5548 |
| left | d858c428c64007596302057453f414dd43c580bc1546b9578c3d1dfb0af17591 |
| back | 9cf2f27448303aa60c603f0f32a7baada234fec8cae5108bf8103a9ae7547e69 |

Target path: assets/official/characters/morwen/turnaround/

Source: director-provided MORWEN_3V_DEPLOY_READY_20261109.zip on Google Drive.

Do not enable website references before all three PNGs are present and hashes verified. Do not replace existing Morwen portrait, v5.61 canonical reference, or walk-72 sprites. Android QA remains NOT_RUN.

## 2026-11-10 追記（MORWEN-HD-CANONICAL-V2）
- 上表の **left（`d858c428…`）は SUPERSEDED / EXCLUDE_FROM_PRODUCTION**。左向きの正本は `assets/official/characters/morwen/hd-v2/originals/pixel/left.png`（`5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8`）。ファイルと履歴は保護し、削除しない。
- right・backは、v2のイラスト版（`originals/real/right.png`・`back.png`）と見た目は同一だがバイトが異なる。詳細は `data/morwen-hd-canonical-v2.json` の `equivalents`。
