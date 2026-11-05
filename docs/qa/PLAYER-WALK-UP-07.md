# PLAYER-WALK-UP-07 — 本番統合チェックポイント

**状態：BLOCKED。検査FAILを検出したため、ディレクターの「問題が発生した場合は停止」の指示に従い停止。mainマージ・Pages公開は未実施。** 本番仕様を追加修正したり、検査を緩めてPASSへ変更したりしない。

基準main `6e28466751f124fc5a483be3d89c65f35a320b5c`、実装／失敗検査HEAD `7c7ea60232c993eff98d52593de4d94d392bdbaf`。専用branch `feature/player-walk-up-07-production`。

## 実装済み・未マージ

- PR153 `c15a715fe450e76820153e71ea7b04e70e258d6d` の最終PNGを無加工で `img/field/characters/aidan/up5/aidan_walk_up_pushoff.png` へ登録。
- SHA256 `1bde96684c85739e821e8c7e5e8f07831b8819414569d07d6a3bbb3613e80dfd`。PR154独立QAで確認されたファイルとバイト一致。RGBA2048×1280、alpha bbox[604,126,1497,1230]、anchor(1024,1230)、scale.0625。
- 新しい正規キー `aidan_walk_up_pushoff` →03→04→01→06、upのbob.25、周期90。斜め上は既存の向き解決で同じup bankを使用。描画エンジン・移動速度・衝突・SAVE形式は変更しない。下ARM-02・左右180・他キャラクターは維持。
- 既存02や03のPNGを上書きせず、独立した正式パス／キーとup5/adopted-walk.jsonを追加。中央素材台帳はユーザー採用承認とPR153/154の出典・画像QAを記録するが、これは今回の統合QA PASSではない。
- PR153/154の候補ディレクトリ、DEV比較、QA用up02エイリアス、init_scriptは取り込まない。indexの対象JSキャッシュキーだけ更新。
- Nodeの明示bank／5コマ／上bob期待値と、既存m62の上方向期待値を承認仕様に合わせて更新。下方向や他方向の既存検査は維持。新規m67は通常NEW GAME・通常キー移動・既存DEV／SAVE UIを使い、進行値や描画policyの直接代入を行わない。

## 実施結果

|対象|結果|
|---|---|
|PNG／採用マニフェストSHA・寸法／RGBA境界|PASS|
|Node全17ファイル|PASS、skip0|
|PC960×540 上直進|コマ順・実画像・90world周期・許容時間範囲・quarter bob・停止／保護状態PASS|
|PC 左斜め上|同上PASS|
|PC 右斜め上|5コマ実画像／順序・ラップPASS、**90world／約0.300秒の実測検査FAIL**|
|M67全体|exit1、19項目PASS・1項目FAILで停止|
|M67の残り／縦横／SAVE/CONTINUE|未実施|
|統合後の完全な独立QA／回帰|未実施|
|mainマージ／Pages／公開ファイル照合|未実施|
|Android実機|未実施|

直進の保存済み周期中央値は90world／0.33335秒、左斜め上は90world／0.300秒。右斜め上は `pc/ur 90world/.300second measured` で停止し、原因未確定。周期距離・時間・標本数をまとめたassertのため、どの数値条件が外れたかをこのログだけで断定できない。

失敗したURの生rowsは、field_checkのassertがruns.appendより先にあるため保存されていない。保存されたのは先行する直進／左斜め上の生データとPC部分動画である。欠落した数値を推測で補完しない。過去のPR154で録画負荷による参考6コマの遅延を観測したが、今回も同じ原因であるとは証明できない。原画像・再生順は通過していても、統合動作をPASSとはしない。

[失敗ログ・部分動画・保存済み生データ](evidence/player-walk-up-07/)を保持。動画はPC原寸の部分記録であり、全経路完走やモバイル成功を示すものではない。

## 次に必要な作業（未実行）

ディレクターから再開指示を受けた場合、まず失敗前にUR生データ／各判定値を保存する診断方法を用意し、通常描画の時間・world距離・RAF間隔を確認する。性能・経路・fixtureのいずれかを証拠で切り分ける。仕様や期待値を勝手に緩和しない。

原因解消後に、新しい固定HEADでPC・縦横・SAVE/CONTINUE・下ARM-02・左右・共通DEV・素材保護を再実行し、実装者以外の独立QA PASSを得るまでマージしない。マージする場合は最新main／head／差分／競合／必須チェックとrollback refを確認し、公開後にindex・JS・採用PNG／台帳の一致を照合する。現在のDraftはレビュー可能な停止チェックポイントであり、公開版ではない。

## 停止時の読取り専用確認

実装者以外が既存証拠と差分を読取り確認した結果、正式259SHA・既存1833PNG・新PNG原本一致、既存フレームメタデータ・他方向・共通描画／SAVEコード不変はPASS。QA用エイリアス混入なし。ただしブラウザ再実行はせず、完全な独立統合QAの判定はBLOCKED／HOLD。停止後に実装修正や期待値緩和は行っていない。詳しくは [STOP-REVIEW](evidence/player-walk-up-07/STOP-REVIEW.md) と [部分映像の限界](evidence/player-walk-up-07/STOP-VISUAL.md) を参照する。
