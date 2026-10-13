# X: Android実機 性能計測プロトコル

STATUS BLOCKED（スマホ単独のDEV高さmap起動導線が未提供。手順/メーター仕様は納品、**Android実機は未測定**）。work/codex-tz。高さを本編で有効にする前の計測用であり、有効化の承認や合格認定ではない。ADB/PC/USB接続は不要。ゲームJSを変更しない。

## 端末だけで計測する

1. Claudeが計測対象commitをHTTPSで配信し、配信commitを記録する。Chromeのシークレットタブで `<配信URL>/index.html?dev=1&perf=1` を開く（通常プレイの保存と分離）。実際に配信されたcommitを不明のまま記録しない。
2. 現在はDEV→「09 苔の森入口」でruntimeを初期化し、会話を閉じ、A1または実歩行でA2へ移って対照計測する。**高さprotoのボタンは現行DEV一覧に無い**。index.htmlの候補はjs/prologue-dev.js:9,52の一覧再生成で消されるため、スマホのボタン操作だけで高さprotoを起動する手順は未提供。Claudeが下記提案を適用/配信した後、再度DEV→高さprotoを選ぶ。初期読込後約10秒待つ。
3. 画面向きを固定し「60秒計測してJSONをコピー」を押す。同じマップ上で歩き、橋の上/下・階段・坂・長距離タップを試す。マップ出口/戦闘へ入らず、タブを切替えたり画面を消したりしない。
4. 完了後「JSONをコピー」を押し、下のテンプレとJSON全文を報告する。権限拒否時は表示されたtextareaから選択コピーする。`valid:false` は無効なrunとして残し、理由を添えて再実行する。向きを途中変更したrunも手動で無効にする。
5. 同条件を3回。縦/横それぞれ実施し、対照として「苔むした森」から同じA2マップに留まって3回計測する。端末の省電力、発熱、他アプリ、Chrome設定を条件間で変えない。移動手順/停止時間も揃える。
6. 実マップ高さdraftの計測は、Claudeが配信したDEV overlayを指定し `?dev=1&perf=1&feature=heightSpecs` を使う。その同一マップでflag無し/有りを比較する。現在のDEV protoとA2の比較だけで、28マップ本番高さの性能合格とはしない。通常配信の高さflagはOFFのまま。

ページを開いてボタンで取得できるのは既存メーターの範囲。アセットの転送量・戦闘読込秒・GPUメモリ・Androidの実提示fpsは取得しない。冷/温キャッシュの読み込み時間が必要なら別runで端末側ストップウォッチ等の方法を記録し、60秒field計測と混同しない。

## 指標と出典

既存 `js/dev/perf-meter.js`（dev===trueかつperf=1、60秒）。画面に平均fps/最低fps/1%low/平均frame ms/最新planner ms/JS heap、JSONにp95/p99/max frame、map/level timeline、画面情報、UA、heapの初期/末尾・サンプル、観測planner更新を出す。clipboard失敗時のtextarea fallbackも実装済み。メーター自体の新規JS実装は不要。ただし高さprotoへのDEVメニュー項目が必要。

- fpsはrAF間隔の逆数、GPUの実提示fpsではない。最低fpsは最長の1フレームに対応する。
- 1%lowは遅いceil(N×.01)フレームの平均間隔の逆数。`tests/moss/m19_perf.py`はfloorを使うため厳密同値ではない。
- JS heapはChromiumの任意推定、GPU/画像decodeメモリは含まない。取得不可(null)を0扱いしない。
- plannerは最新値のサンプリングで、1フレーム内の複数planを取りこぼし得る。完全な呼出時間分布ではない。
- page_hidden/no_active_field/map_changed/no_frame_samplesでinvalidとなる。向き変更/充電/発熱は自動判定しないので記録する。

`m19_perf.py` はコンテナChromiumの8秒×PC/縦/横、CPU throttle可の参考値。Android実機の代用として採用しない。

## 合格基準案（作者要判断）

60Hz端末向けの初期目安: 平均≥50fps、1%low≥30fps、p95 frame≤33.3ms。height有りが同一マップflag無しから平均fps10%以上/1%low20%以上悪化する場合は調査。画面ちらつき/入力停止/階段で長い停止があれば数値だけで合格にしない。

観測plannerが常時50ms超、100ms超の停止が繰り返される場合も調査する。JS heapは5往復などの同じ操作を反復し、増加が収束するか比較（ブラウザGCを考慮）。高リフレッシュ端末は実際の設定Hzと対照runで基準を調整する。

これらの数値は提案であり確定値ではない。複数端末/最悪の実マップ/素材密度/敵の同時表示/長押し移動も揃えてから、作者が有効化を判断する。まだAndroid実測がないため現時点で本編高さONへ進めない。

## 報告テンプレ

```text
配信commit / URL:
端末名 / Android / Chrome:
画面Hz / 解像度 / DPR / 縦横:
バッテリー・省電力・充電・温度感:
map / feature flag / level / run1〜3:
キャッシュ（初回/温） / 移動操作・経路:
平均fps / 最低 / 1%low:
p95 / p99 / 最大frame ms:
観測planner最新・最大 / JS heap初期・末尾:
valid / invalid_reasons:
引っかかり・入力遅延・表示崩れ:
JSON全文:
```

## こちらで確認した範囲

d153d06のPC Chromiumでは、森へ一度入るUI操作の後、検証用にAPIで高さprotoへ移動してメーターを確認する。これはスマホのGUI-only導線の確認とは区別する。証跡android-perf-kit-check-20261013/。実機性能は未測定。テスト結果はUI機能確認と区別して保存する。変更は本手順/証跡/statusのみ。次はユーザー端末での実測とClaudeによる配信commit確認。main変更なしでロールバック不要。

## Claudeへの必要な導線追加案（未適用）

js/prologue-dev.jsのentriesへ `['map:dev_height_proto','DEV 高さプロトタイプ(2.5D)']` を追加する案。初期画面からmapジャンプする経路のruntime初期化も確認する。暫定手順は一度「苔の森入口」へ入ってからmapを選ぶ。CodexはXの「新規実装が必要なら提案のみ」に従い、JS/DEV一覧を変更していない。導線修正後は実機で上の手順を確認する。

機能確認の最終結果: PASS、console/page error0。縦横パネル画面内、60秒valid JSON、clipboard JSON同値。初期のDEV jump timeoutと、再生成後のDEV一覧に高さボタンがないことを切り分けた。検証では森入口をUIで選び、MossForest.enter({map:'dev_height_proto'})をAPIで呼んだ。GUI-onlyの成功として扱わない。
