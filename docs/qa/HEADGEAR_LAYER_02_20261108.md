# HEADGEAR-LAYER-02｜隔離描画・公式原本監査

## 添付ZIPの検証
- ユーザー添付 `THE_WINDBOUND_OATH_ALL_CHARACTER_REFERENCES.zip` は外側ZIPの中に同名の内側ZIPを含む。
- 内側 `MANIFEST_SHA256.json` の172ファイルのSHA-256を全件照合し、**172 PASS / 0 FAIL**。対象にはゲーム正式全身イラスト・参考画像・候補・NPC・敵・公式サイト掲載画像を含む。
- 正式原本としてモルウェン `morwen-full-body-v3.png`、セレナ `serena-full-body-v1.png`、ブラム `bram-full-body.png` を参照。正式採用状態は別途ゲーム `assets/companions/MANIFEST.json` に従う。
- モルウェンv3画像には脚部を覆う濃色の衣服が描かれており、**ニーソックスの履き口を原本画像だけで確定できない**。ディレクターが指定した「ニーソックス」を後発の正式変更として扱い、頭部の髪型・眼鏡・帽子・配色は原本の造形を保護する。
- ユーザーが指摘したv5.3デザイン不一致は未解消。画像を正式合致済みとは判定しない。

## 実装
- `js/field/field-headgear-renderer.js`：4方向のベース・上中下段レイヤーを選択し、単一DOM親に合成。共通親のtransformのみでバウンスに同期。
- `dev/headgear-preview/`：本番と隔離した開発者プレビュー。候補PNG未制作のため**BLOCKED**を明示し、既存公式画像を誤用しない。
- `tests/moss/test_field_headgear_renderer.js`：方向・順序・競合・親transform構造を検証。

## 未完了
- 代表装備リボン/メガネ/兜の正式デザイン照合と独立RGBA PNG制作、足元anchor統一、透過PNG CIへの実アセット接続。
- 実ブラウザ表示と32/40/48px視認性、Android実機QA、戦闘・会話差分。
- 本番ゲーム・SAVEには未接続。候補が完成し全QAを通るまで本番採用禁止。
