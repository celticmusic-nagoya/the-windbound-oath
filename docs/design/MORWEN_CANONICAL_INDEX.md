# Morwen visual references — 2026-11-12 director override

MORWEN-CANON-CLEANUP-02 / [Issue #240 最新指示](https://github.com/celticmusic-nagoya/the-windbound-oath/issues/240#issuecomment-6822050005)

**制作参照の唯一の受領セット:** `assets/references/morwen/reference_20261112/MANIFEST.json` が識別する、ディレクター添付ZIPのPNG12枚。全点 **REFERENCE_ONLY**。原本バイト・ファイル名・SHAを保護し、加工版や類似画像に差し替えない。

ZIP: `morwen_asset20261112.zip` / 11,828,264 bytes / SHA-256 `4a1a23fd0f0197b8b21019229d9f5340b1a8e28c0fd70607d54f02ff3d4bbcf9`。チャットでディレクターが本タスクに直接添付。CRC・12 PNG・原本一致を確認してから旧派生物を削除した。

| 役割 | 保護対象 |
|---|---|
| 構造参照・正面 | `REFERENCE_front.png` |
| 構造参照・右向き | `REFERENCE_profile_facing_right.png` |
| 構造参照・左向き | `REFERENCE_profile_facing_left.png` |
| 構造参照・背面 | `REFERENCE_back.png` |
| 補助参照8枚 | 同manifestの `file_*.png`。最終4方向の対応を推測で割り当てない |

目視メモ: 構造参照と衣装付き参照が混在し、眼鏡・帽子装飾・衣装・ポーズ・縮尺は全画像で同一ではない。補助2枚はRGBで黒背景が画像自体に含まれる。四方向構造参照にも衣装図にも複数版がある。これらを勝手に合成・背景除去・リカラー・採用統合しない。採用判断・細部の整合は今後のBlender制作と審査で解決する。

**将来の高品質Blender完成版:** `FUTURE_CANON_PENDING_APPROVAL`。完成・審査・ディレクターの明示的な正式承認後にのみ新しい正式ビジュアルとなる。参考12枚の受領は完成版や本番採用の承認ではない。今回リグ・画像の新規生成、ゲーム組込、mainマージ、サイト公開は行わない。

旧v5.61/v3/公式3方向/HD/歩行候補の保存場所や `official` / `master` / `canonical` の名前だけで、新しい正式ビジュアルへ昇格させない。過去の「唯一の制作正本」規定は、本指示が変更した旧ビジュアル保存方針について履歴扱いとする。既存の動作素材・サイト参照・共有パイプライン・必要QAは、代替完成版の承認と導入まで保護する。

公式設定・年齢・物語・台詞・SAVE・性能値は変更しない。現行mainの規約とprivate canon mainの参照照合を行い、非公開本文は転載していない。

旧素材のKEEP / DELETE / BLOCKED、削除パス・元SHA・根拠、依存監査、実行QAは `docs/qa/morwen-canon-cleanup-02/` を参照。過去の大規模棚卸しは [PR #241](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/241) を再利用し、本PRの判定は最新ディレクター指示を優先する。
