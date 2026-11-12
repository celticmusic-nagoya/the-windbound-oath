# LAYER0-MALE-TRIO-REGISTER-01 — BLOCKED

基準main: `cab9aa52da653198a712bd986992adc03ea4bfe2`。対象: エイダン・リアム・ブラム。目的: 添付四面図の原本保護と登録。

## 現在の結果

- BLOCKED: 添付画像は会話上で閲覧できるが、実行環境の `/workspace/library-files`、`/workspace/shared`、`/workspace/scratch` に原本ファイルがなく、ダウンロード可能な添付IDも提示されていない。
- 原本PNGを受領していないため、SHA-256・実解像度・RGBA・透明度・輪郭保持・12方向の整合性を未検証。表示画像の再作成やスクリーンショットを原本として代用しない。
- 背景処理0回（上限2回）。原本の保存・保護自体も未完了。加工後PNGなし。nullのSHAは未取得を示す。
- エイダンのLayer 0デザイン正式採用はユーザー指定として記録。PNG技術QAのPASSとは区別。リアム・ブラムは候補を維持。
- 現行main AGENTS.md、関連アセット規約、およびprivate handoff mainのv5.0・追補・状態表の対象設定を参照。正典本文はこのPRへ転載しない。

## 登録予定パス

| 対象 | PNG（未登録） | 採用区分 |
|---|---|---|
| エイダン | assets/characters/aidan/layer0/aidan_layer0_fourview_master.png | Layer 0正式採用済み |
| リアム | assets/characters/liam/layer0/liam_layer0_fourview_master.png | Layer 0採用候補 |
| ブラム | assets/characters/bram/layer0/bram_layer0_fourview_master.png | Layer 0採用候補 |

各予定パスの隣のMANIFEST.jsonに未完了状態を記録。プレースホルダーPNGは作成しない。

## 共通17ボーン

PR #246の固定コミットの仕様を確認。17個の一意なボーン名・親参照はPASS。main採用とはみなさない。出典SHAと親子関係はCOMMON_17BONE_COMPATIBILITY.json参照。
3名の関節アンカー計測、左右側面の人物基準での特定、体格別調整、接続・変形はBLOCKED/未実施。互換性PASSとしない。

## 再開条件と検証

1. 原本PNG3枚をファイルとして取得し、人物との対応を確認する。
2. バイト無変更で各layer0/originals/へ新規保存し、SHA・解像度・チャンネル・alpha統計を記録する。既存ファイルがあれば上書きせず照合する。
3. 不透明背景の場合のみ背景アルファ処理を最大2回行い、原本と比較して髪・ひげ・指・足先・インナーと輪郭を確認する。未達なら原本保護のままBLOCKED。
4. PNG・MANIFESTのSHAを再照合し、四方向の体格・髪型・インナーと共通リグ接続可能性を検証する。

自己QA: JSONの構文、17ボーン参照、差分が新規メタデータのみであることを検証。独立画像QAはNOT_RUN。
mainマージ・ゲーム組込・サイト公開なし。Blenderリグ制作はモルウェン完成後に再開する。
