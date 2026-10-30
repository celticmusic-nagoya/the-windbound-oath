# Phase4 Android feedback — 2026-10-30

Baseline: main `fac97543d19f85e85e8de38679162877e4577cf0` (PR90 / DIRECTIVE-20D).

User report in this session:
> フィオナとルーのまぶたが斜めなので修正したいです。エマは合格です。

- Emma: user-declared Android QA PASS. Leave all images/coordinates/rendering unchanged. This records the practical QA verdict; the original PROVISIONAL_ANDROID_QA adoption ledger is preserved, without inferring a separate formal-adoption declaration.
- Fiona / Lou: eyelid shape/angle requires revision; Android art verdict CHANGES_REQUESTED. Do not label final art PASS based on the prior technical pixel checks.
- Technical20D checks proved faithful rendering of source PNGs; they did not prove the eyelid artwork was aesthetically accepted. Correct the material geometry rather than rotating the whole portrait or distorting the shared renderer.
- Protect formally adopted normal3, Aidan54, eventCG10 and current Emma assets. Retain20C originals and version revised candidates separately.

## Evidence and scope

User supplied Android screenshots `6805.jpg` / `6806.jpg`. Both show the DEV portrait lab and closed-eye characters; the controls are scrolled so the active face/status is not visible. The visible last buttons (`relieved`, `determined`) alone do not establish which face is selected. User subsequently confirmed **both** normal blinking and expression images require eyelid correction.

Source20C: `b8517c2cf74445362ce1a557cf7c4ecd280d94fe` in private handoff `handoff/phase4-20c-claude-20261030`.
- Normal blink: `reports/PHASE4-20C-20261030/specs/{fiona,lou}_normal.json`, per-eye `closed` curves and intermediate stages; runtime16PNG under each `provisional-20c/blink/`.
- Static expressions: per-face `specs/expr/*.json` and `expressions/*.png`; only the affected registered faces may be revised. Lou smile/relieved remain excluded.

## Acceptance for a revision

Preserve face tilt and original eye corners. Align the closing lines naturally with each eye's own axis and make both eyes consistent; do not force all eyelids to screen-horizontal or rotate character images. Inspect intermediate frames as well as fully closed eyes, including eye corners/eyelash tips, source-sized magnification and Android-sized full portraits. Keep head/hair/ornaments/wings/clothes/alpha outside the intended eye changes invariant. Recheck natural blink, actual eye pixels, expression switching and lifecycle with the shared renderer. New art acceptance remains subject to user Android review.

## Visual correction reference

User clarified: **両方** (blink and expression images). Image-generation edit produced a review sheet of Fiona/Lou open→half→closed eyes, preserving the intended face tilt and illustrating coherent eyelid curves. This is an ART-DIRECTION REFERENCE, not pixel-compatible game assets; do not register this composite sheet or replace the approved normal PNGs with generated faces. Candidate reference: `docs/portraits/review/eyelid-shape-reference-20261030.png`.

User approved this shape reference: 「素晴らしいです！バッチリです！」. The approval covers the eyelid correction direction for both blinking and expressions; new derived runtime assets remain Android-QA provisional.

STATUS: IMPLEMENTED — technical QA12files PASS; corrected derived assets await Android recheck. Versioned blink16PNG plus12 registered Fiona/Lou expressions; Emma excluded. Production patches preserve the prior expression exactly outside explicit per-eye masks and preserve its full alpha. The composite sheet is never used as a game portrait.
