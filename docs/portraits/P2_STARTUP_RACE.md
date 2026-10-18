# Issue #16 re-QA (CODEX-P2-REQA-20261019): startup-opening race — classification

Product code is unchanged from 5d915ed9097a8d584d93ee28ee98b27fb62060cd. This branch adds only test support.

Cause: `RildeVillage.startOpening` speaks 「朝の風が窓を揺らしている…」 350 ms after the opening map commits (`js/field/rilde-village.js`, identical on main). Tests that wait a fixed 1.5–2.5 s and then start their own conversation (m30, m31, kb_field) or call `devJump` (m4_save, whose map is overwritten by the boot `enterMap('rilde_in_aidan')`) race with it when the machine/assets are slower. A late opening replaces the running line; P2 correctly revokes the portrait (owner=null).

Not a P2 defect: kb_field and m4_save fail the same way on main (throttled 4x; and 1 of 3 plain kb_field runs on main at normal speed).

Added (originals untouched, no assert/timeout changed):
- `tests/support/run_python_ready.py`: runs an unmodified test after the opening line was shown (goto and reload). `LATE_MS` delays the opening to simulate a slow machine.
- `tests/moss/m34_startup_opening_race.py`: A) late opening replaces a Fiona conversation and the portrait is revoked; B) after the opening the conversation is stable. Run with the plain runner.

Separate dev issue (not fixed here): a late startup `say` can replace an active conversation and the boot `enterMap` can overwrite a `devJump`; to be settled with the Scene lifecycle fix (cc3aad4c…).
