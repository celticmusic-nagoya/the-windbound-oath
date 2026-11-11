# MORWEN-LAYER0-03-QA-02 — Codex execution handoff

Status: READY_FOR_CODEX / execution NOT_RUN
Branch: feature/character-asset-studio (verify latest HEAD before work)
Scope: tools/character-asset-studio/qa/ only

## Execute (from repo root)

```sh
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*morwen_v10_candidate.py' -v
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_audit_stance_contact.py' -v
python tools/character-asset-studio/qa/audit_layer0_rig.py tools/character-asset-studio/layer0/morwen-master-v1.0/MASTER_BODY_SPEC.v1.0.candidate.json
python tools/character-asset-studio/qa/audit_stance_contact.py tools/character-asset-studio/qa/stance_contact_fixture_v1.json --tolerance-px 2
```

Expected: migration unit tests PASS; stance-contact unit tests PASS; rig audit 8/8 PASS; synthetic fixture PASS with 4 stance samples and max drift 1 px. These are **expectations, not observed results**.

## Real-motion integration

The fixture is synthetic and does not establish real animation correctness. Locate existing generated frame/pose data; if only PNGs are available, mark real-motion integration BLOCKED and document required coordinate export. Never fabricate world-space contact positions from the fixed ground marker. Determine stance/swing from authored gait data, or flag it NOT_RUN. Produce a separate JSON evidence file with frame IDs, foot side, phase, worldPx and original data path. Audit the resulting file and report drift by foot.

## Stop conditions

Do not change the original v0.8/v0.9 source, official PNGs, or adopted designs. Limit similar repair attempts to two. Keep PR Draft, do not merge/publish. Report actual command output, SHA and regression deltas by failing test ID. Coordinate with Claude to avoid concurrent edits.
