# tools/ci (AUT-01, isolated branch - not merged to main)
- `PROFILE`: `main` (tests that exist on main) or `int02` (INT-02 + P0-D candidate). Changing the profile is part of the integration step, not of this branch.
- `run_tier.py`: serial, bounded runner. FAIL on exit!=0 / `FAIL` lines / `FAILS n>0`; a listed-but-missing test = exit 4; budget overrun = NOT_RUN (exit 5), never a pass. `--rerun-failed` is diagnostic only. Foreign server on 8765 is refused, never attached to.
- `source_guard.py`: full-run integrity (git work tree + clean protected paths before; SHA-256 snapshot before/after).
- Tiers: T0 static -> T1a P0 gate / T1b Loading+UI (int02 only) -> T2 battle/input -> T3 full (4 shards, manual). Tier is chosen by `workflow_dispatch` input, or on this isolated branch by pushing to `ci-measure/<tier>`.
- CI is a self-check aid; it never replaces Codex independent review, and a green run does not mark a P0 VERIFIED.
