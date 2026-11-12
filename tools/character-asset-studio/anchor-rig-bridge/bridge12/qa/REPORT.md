# MORWEN-BRIDGE-12 QA（自己QA・2026-11-12）

| 検査 | 結果 | 根拠 |
|---|---|---|
| 既存の座標・変換仕様との互換性 | PASS | `morwen.import.template.json` `import_rig.py` `sheet_to_rig.json` `joints.json` `bridge11.py` の SHA が PR #230 HEAD と一致（先頭12桁: 5938c5f52757 / 0c096e8af061 / f5b3d252dd3b / 8316cee984d5 / f945cfc820b4）。変更は `bridge12/` の新規ファイルのみ |
| 未解決値の安全な扱い | PASS | `delivery_slots.json` の17スロットはすべて `sha256:null`・BLOCKED。仮の値は入れていない |
| 実画像未納品時の BLOCKED 判定 | PASS | `import_rig.py` が exit 2・`status: BLOCKED`（MISSING_SOURCE / LAYER_NOT_AVAILABLE ×4 / ANCHOR_ALIGNMENT ×4）。`bridge11.py` も exit 2（意図どおりの部分 BLOCKED） |
| 既存テストのデグレ | PASS | bridge11 13/13、vendor 5/5、studio qa 52/52、pipeline 58/58。変更前後で同じ結果 |
| 正本・SHA の保護 | PASS | `cas.py protect-verify` 17/17 PASS |
| デザイン照合・年齢にふさわしい表現・Android 実機 | NOT_RUN | 実画像がないため |

独立QA（Codex など）は未実施。