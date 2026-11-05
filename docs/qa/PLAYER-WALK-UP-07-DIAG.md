# PLAYER-WALK-UP-07-DIAG — 周期FAIL原因切り分け

**原因分類：CASE D（初回URの直接原因は未確定）。本番統合BLOCKEDを継続。** 同条件の反復ではFAILを再現しなかった。確認できたQA側の記録欠落は修正済み。環境遅延で同じ種類のFAILになり得る機序は確認したが、初回事象への原因断定はしない。

対象はDraft PR155、固定HEAD `0494f6452548ea476b4cebbc69d9f41d878d540d`。新しい調査専用branch `feature/player-walk-up-07-diagnostics` にQA計測・数値・報告のみ追加。本番JS／歩行仕様／PNG／bank／判定許容値を変更しない。mainマージ・Pages公開は禁止を維持する。

## 初回FAILの保全

[元の停止報告](PLAYER-WALK-UP-07.md)と元証拠フォルダは固定HEADとバイト一致を確認し、一切更新していない。[保全記録](evidence/player-walk-up-07-diag/original-preservation.json)に全ファイルSHAを記録。初回は19項目PASS後 `pc/ur 90world/.300second measured` がFAIL、exit1だった。

旧コードはfield_checkでassertした後にruns.appendしており、失敗したURの生rowsが保存されなかった。この**証拠保存不具合（CASE B）**は確認できた。一方、初回の距離・時間・標本数のどの条件が外れたかは復元できない。直進90world／0.33335秒、左上90world／0.300秒という先行区間の値を、失敗URの値へ流用しない。

## 元の判定式と計測方法

変更していない条件：

- moving抽出：yが前標本より0.01超減少、移動transformが存在、採用PNGのいずれか。
- PNGの表示遷移を0〜4で追跡し、遷移iからi+5までを1周期の窓とする。
- 距離＝その窓の始終座標間の**弦長**hypot(dx,dy)。歩いた全経路長とは異なる。
- 時間＝窓の始終で観測した**RAF timestamp差÷1000**。壁時計時間であり、ゲーム時計の累積値ではない。
- 窓数>=4、abs(距離中央値−90)<12、abs(時間中央値−0.300)<0.080をANDで判定。すなわち78<距離<102world、0.220<時間<0.380秒。境界は厳密不等号。
- iを1ずつずらすため、窓は重複する。16窓／19窓を16回／19回の独立した周回と表現しない。

5コマ表示順／実decode／quarter bobの元assertも維持した。ASTで3つの判定式・moving／tr／cycles・decoded／transitionsが元HEADと同一であることを検証し、別担当も再確認。[独立静的証明](evidence/player-walk-up-07-diag/independent/criterion-static-proof.json)。

## 記録改善（許可されたQA変更）

m67のassert直前へ、atomic JSON・完全raw gzip・flush/fsyncしたログの保存を追加。判定式や許容値は変えず、合否の3条件を個別の真偽と理由で記録する。時間超過・距離不足・標本不足・空標本を含む6件の計測回帰（うち故障注入4件）で、失敗前の保存と空データをPASSにしないことを検証した。

各区間に次を保存：viewport／DPR／録画設定／実bank・速度・ブラウザ版、キーのkeydown/keyup時刻と座標、開始／終了時刻・座標、実経過時間・変位／経路長、標本数・遷移数・重複窓数、RAF全間隔／分布、frameScale、期待値・許容範囲、実測値・判定理由。生データと[比較CSV](evidence/player-walk-up-07-diag/comparison.csv)にUTC／単調時刻も保持する。

追加のobserverは公開getter・DOM・イベント・PerformanceObserverを読むだけで、RAFや時計を差し替えない。歩行・フラグ・所持品・SAVEを設定しない。observer自身の読取り時間も記録した。失敗を捕捉して次の試行へ進むのは今回承認された診断だけの動作であり、通常m67のassert停止は維持する。

## 実ブラウザ再計測

実行HEAD `3c6de54ea53a76b0378e46cc6e84696e23d9857f`。各試行で新しいChromium／contextを起動し、通常NEW GAME→自宅会話終了、元と同じキー順・準備経路・到達条件を使用。PC960×540、DPR1、has_touch=true、headless、録画サイズ960×540。録画あり5試行を先に、録画なし3試行を対照として直列実行。既知設定を揃えたが、初回ブラウザ版・負荷・RAF詳細は未保存のため、過去環境との完全一致を証明するものではない。

|条件|方向|試行数|周期距離中央値|周期時間中央値|標本数|最大RAF間隔|元判定FAIL|
|---|---|---:|---:|---:|---:|---:|---:|
|録画あり（元設定）|直進|5|90world|0.300秒|68〜69|33.4ms|0|
|録画あり（元設定）|左上|5|90world|0.300秒|83〜84|16.8ms|0|
|録画あり（元設定）|右上|5|90world|0.300秒|80〜84|50.0ms|0|
|録画なし（対照）|直進|3|90world|0.300秒|69〜72|33.4ms|0|
|録画なし（対照）|左上|3|90world|0.300秒|83〜85|33.3ms|0|
|録画なし（対照）|右上|3|90world|0.300秒|83〜84|16.8ms|0|

**24/24計測で周期FAILなし。** 距離の表示は丸め値（浮動小数誤差は約1e−12world）。別担当は全24のrawを元HEADの未変更field_checkで独立再計算し、72/72 assertと保存cyclesの一致を確認した。これは診断対象の3項目×24であり、未実施の全統合QA／SAVE／Android実機を代替しない。

今回の全移動標本では、同じrow位置のframeScale×5と実変位の誤差は最大約2.8e−13worldで一致。50.01msを超えるRAF間隔は0、経路弧長と弦長・headingも保存。測定後の5world先blocked()照会は全0だったが、実装内部の全sweep判定の完全再現とは扱わない。今回の経路・入力からUR固有の減速を示す証拠は得られなかった。

録画群を先に実行したため順序／時間の交絡があり、録画の因果効果をランダム化比較したものではない。observer読取り時間最大は録画14.6ms、対照0.7msで、記録自体の影響をゼロとは主張しない。元の失敗時はこの情報がなく、今回の成功から過去の原因を否定／確定できない。

## 実装・入力・時計の調査

移動は共通tickで方向ベクトルをsqrt(dx²+dy²)で正規化し、同じFieldMovement.advanceを呼ぶ。右上固有の速度／周期分岐はない。左右の符号、headingのflip、衝突形状による差はあり得るため、実キーイベント・heading・実変位・弦／弧長を比較した。上斜めの描画はどちらも同じup bankを使用。今回の条件では方向ごとの周期差は確認できなかった。

未変更のFieldMovement.tickClockはframeScaleを最大3に制限する。60Hz基準なので、RAF間隔が50msを超えると、ゲームが進める時間は1フレーム最大50ms相当になる。最大移動量15worldは5コマの1段階18worldより小さく、**コマ順は正しいまま実時間だけ長くなる**機序がある。

別担当が未変更のFieldMovement／FieldWalkMotion／Aidan素材定義を隔離VMで実行した[反実仮想データ](evidence/player-walk-up-07-diag/independent/clock-counterfactual.json.gz)では、60Hzは3方向とも90world／0.300秒、人工の100ms RAFは3方向とも90world／0.600秒・5コマ順を維持し、元の時間条件だけFAILとなった。[再現コード](evidence/player-walk-up-07-diag/independent/clock-counterfactual.cjs)は実ブラウザや実ゲームの時計を変更していない。

これは**CASE Cの可能な機序**を示すソース関数の対照実験であり、実ブラウザの初回UR FAILの再現・原因証明ではない。初回URのRAF／frameScaleが失われているため、そこに100msなどの具体値を付け加えない。

## 原因分類と最小対応

- **CASE A：未確認。** 本番コードの修正を要する実装不具合は今回観測していない。存在しないと証明したわけではない。
- **CASE B：記録欠落は確定・修正済み。** assert前の保存と条件別の理由記録だけを追加。元の周期判定式自体の誤りは確認していない。
- **CASE C：機序は確認、初回事象への適用は未確定。** RAF遅延と移動時計上限は候補だが、新24計測はその上限を超える遅延を観測していない。
- **最終はCASE D。** 初回原因は不明のまま、統合BLOCKEDを継続する。

許可範囲の最小修正は今回のQA証拠保存。ゲーム時計・歩行bank・速度・bobの変更は提案／実装しない。時間許容を広げたり、frameScaleによる計算時間を代わりのPASS基準にしたりしない。

## 統合QA再開の判断材料

**自動再開／マージは不可。ディレクター判断待ち。** 再開する場合は、計測追加版を固定し、元の閾値と失敗履歴を維持して全統合QAを再実行する案を推奨する。単一ブラウザで他の重い処理を直列化し、録画条件・負荷・RAF・全判定値を必ず保存する。再度FAILならこの保存データで条件ごとに切り分ける。FAILを無効標本へ付け替えてPASSにする運用は行わない。

追加調査項目：初回相当の環境負荷／ブラウザ条件の再確認、実キー発火間隔とheading切替、元の弦長と実経路長、実装clockと観測callbackの対応。必要な環境条件変更／新しい判定仕様／本番修正は別途承認を得る。PR154のPASSや本診断24件の成功だけで統合PASSへ昇格しない。

## 証拠・再現

[条件と集計](evidence/player-walk-up-07-diag/summary.json)、[比較表・全入力／座標](evidence/player-walk-up-07-diag/comparison.csv)、[実行ログ](evidence/player-walk-up-07-diag/diagnostics.log)、[各ケースのJSON・raw・判定理由（無損失archive）](evidence/player-walk-up-07-diag/measurements.tar.gz)、[独立レビュー](evidence/player-walk-up-07-diag/independent/REVIEW.md)。新録画5本は作業領域に保持し、[SHA一覧](evidence/player-walk-up-07-diag/recording-manifest.json)を保存。診断の数値証拠は全件同梱し、初回部分動画は元PR155の証拠にそのまま保持している。

環境にChromium／Playwright／ffmpegを用意し `QA_OUT=<新規出力先> PW_CHROMIUM_EXECUTABLE=<実行パス> python tests/moss/m68_up07_diagnostics.py`（必要ならPLAYWRIGHT_BROWSERS_PATH指定）。同条件5＋対照3、各3方向を実行し、FAILが出ても診断コホートを完了して結果を保存する。通常m67は従来どおり最初のassertで停止する。`python tests/system/up07_diag_logging.py` は6件の計測回帰、`python tools/qa/summarize_up07_diag.py --input <出力先> --out <集計先>` は数値集計だけを行う。隔離VMは `node <証拠>/independent/clock-counterfactual.cjs <repo>`。

本番JS／画像／bank／registryは固定HEADと差分0。正式259SHA・既存1833PNGと固定HEADのPNG＋元証拠1850ファイルは独立照合一致。main・Pages・PR155 HEADは変更していない。Android実機は未実施。

数値の元JSON／ログ96ファイルは `measurements.tar.gz` に全件無損失で格納し、[内部ファイル別SHA](evidence/player-walk-up-07-diag/measurements-index.json)と読戻し一致を確認した。表示用CSV／集計JSONは展開不要。アーカイブを同証拠フォルダへ展開すれば `measurements/<case>/` を参照する再集計コマンドをそのまま使える。初回FAIL証拠には触れていない。
