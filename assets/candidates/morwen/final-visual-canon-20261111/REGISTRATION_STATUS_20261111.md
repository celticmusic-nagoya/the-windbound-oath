# MORWEN-FINAL-CANON-REGISTER-01 登録状況（2026-11-11、更新）

`MANIFEST.json` はディレクターが登録したもの。変更していない。

## 結果：4 方向すべて登録完了

| 方向 | ファイル | SHA-256 | MANIFEST との一致 | 形式 | 受け取り経路 |
|---|---|---|---|---|---|
| 正面 | `front.png` | a0f9bdbdfaf928aab49ea116d3ec40620f1558efe55f5f90aa55002213ae7bbd | 一致 | RGB 1152×1536（黒背景） | ZIP `MORWEN_FINAL_CANON_4VIEW_20261111_UPLOAD_READY.zip` の `canonical/front.png` |
| 背面 | `back.png` | 15c9d45283e0e7d1910ae35c8f271c80241e002b1c6b5a8ad1d71e0281eeb7eb | 一致 | RGB 1152×1536（黒背景） | 同じ ZIP の `canonical/back.png` |
| 左 | `left.png` | cd1dbc8447de72f0b4239cb6e76ea12c703df0812b1fc225ecb892c34db1b984 | 一致 | RGB 1152×1536（黒背景） | 同じ ZIP の `canonical/left.png` |
| 右 | `right.png` | f5b5787cce36806a365251095f1c43138e4a12409e176c24af8a8406642117d1 | 一致 | RGBA 1200×1600 | チャット添付 7684.png（54533373 で登録）。ZIP 内の `canonical/right.png` とバイト単位で同一 |

- 4 枚とも、受け取ったバイト列を無加工で保存した。
- ZIP 内のスクリプト `morwen_upload_final_canon.sh` は実行していない。

## 経緯
- 最初はチャットに添付された 4 枚を使おうとした。正面・背面・左は 1086×1448 に縮小・再エンコードされていたため、ハッシュが一致せず登録を見送った。右は一致したので先に登録した。
- その後、ZIP の原本を受け取ったので照合し、残りの 3 枚を登録した。

## 注意
これは見た目の正本として登録したものであり、ゲーム用の素材としての QA は済んでいない。
- 3 枚は黒背景の RGB、右だけ RGBA で、寸法もそろっていない。
- 透過処理・キャンバスの統一・アンカー合わせは、正本とは別の派生素材として行う必要がある。
