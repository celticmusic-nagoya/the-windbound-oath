# MORWEN-LAYER0-03-QA-05 — Independent GitHub Actions evidence

Status: AUTOMATED_QA_PASS / VISUAL_AND_REAL_MOTION_NOT_RUN
Repository: celticmusic-nagoya/the-windbound-oath
Commit tested: b6026659426fa569925efe42fde1ecfbdf87663d
Workflow run: https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43028229706
Run ID: 43028229706
Job ID: 130548259435

## Verified via GitHub Actions job API

- Workflow conclusion: success
- Job morwen-rig-qa: success
- Migration regression tests: success
- Stance contact regression tests: success
- v1.0 rig metadata and hierarchy audit: success
- Synthetic stance fixture: success

This is the GitHub Actions result, not an independently repeated local test.
The synthetic fixture is not real authored walking animation. Real motion contact drift, Android device QA, and human visual review remain NOT_RUN.
Candidate adoption remains NOT_RUN. No main merge or official asset promotion is authorized.

## Next evidence required

1. Actual authored motion frame IDs and stance/swing phase data.
2. Foot world-space contact coordinates per frame (not the static ground marker).
3. Independent visual review of four-view PNGs and Layer 0/1 composites.
4. Regression comparison with pre-existing failures by test ID.

Stop after two similar repair attempts; avoid overlapping Claude/Codex writes.
