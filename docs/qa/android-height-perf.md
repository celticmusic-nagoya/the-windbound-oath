# Android 高さプロトタイプ性能計測

STATUS: WIP — Android実機は未検証。

担当: Codex / `work/codex-height-tools` / 基準 `feat/field-height-prototype` (`2ddeaed`)。
対象は新規 `tools/moss/check_levels.py`、`js/dev/perf-meter.js`、本手順書、任意の `tests/moss/run_all.sh` とindex.htmlのscriptタグ1行のみ。Claude編集中の高さ・衝突・移動・マップ生成・m19ファイルは読むだけ。本編マップ/セーブ/ストーリー/戦闘/採用素材を変更せず、mainにはmergeしない。

## 開き方と指標

1. 対象branchをリポジトリ直下で `python3 -m http.server 8765` により配信し、Chromeで `http://localhost:8765/index.html?dev=1&perf=1` を開く。実機は同一ネットワークのPCのIPへアクセスするか、承認済みのDEV配信先を使う。セッションから実機への接続はない。main/公開Pagesへは反映しない。
2. DEV Jumpで計測マップへ移動し、ロードと画面切替の完了後にボタンを押す。DEV Jumpから見つからない場合はPCリモート検査で `MossForest.enter({map:'dev_height_proto'})` を使用する。高さマップは実装統括の専用DEV入口に従う。
3. 「60秒計測してJSONをコピー」を押し、同じマップで60秒間歩く。計測中は画面を前面に保ち、他のマップへ移動しない。levelの変更は可。終わると自動コピーを試み、JSON欄にも残る。権限拒否や非HTTPSでは「JSONをコピー」を押すか、JSON欄を選択してコピーする。実機はHTTPS/localhost以外でClipboard APIが使えない場合がある。
4. JSONを結果表と一緒に貼る。ページが非表示になった、マップが変わった、開始時にフィールドがなかった場合は `valid:false` と理由を記録する。その試行を採用せず再計測する。

パネルは `window.WINDBOUND_DEV === true` と `perf=1` の両方を満たす時だけ生成される。perfなし/DEV=falseではUI・計測API・計測ループを生成しない。このbranchの既存prologue-dev.jsはDEV=true固定であるため、`dev=0` というURLだけでは本番モードにはならない。公開版でDEV=falseにする作業はこの依頼の対象外。

画面表示は直近5秒、JSONはその試行全体。FPS平均は `1000 / 平均rAF間隔(ms)`、最小は `1000 / 最大間隔`、1%ローは遅い順に `ceil(N*0.01)` 件の間隔の平均の逆数。フレーム時間は平均・中央値・p95・p99・最大等を含む。遅いフレームを削除/上限固定しない。これはrAFタイミングであり、GPUの実描画FPS/OSの提示フレーム数ではない。

経路計算は `FieldNavigation.status.milliseconds` の直近値を表示する。JSONにはmap/plan counterが変わった時の値を記録する。1フレーム間に複数の計画がある場合に全呼び出しを捕捉する計測ではない。JSヒープは対応Chromeのみ、取得不可はnull。画像のデコードメモリ/GPUメモリ/プロセス全体のメモリとは別。計測オーバーレイ自体の負荷は含まれる。

## 端末の記録欄

| 項目 | 記録 |
|---|---|
| 対象branch / commit | |
| 機種 | |
| Android / Chrome バージョン | |
| 画面解像度 / CSS viewport / DPR | |
| 画面更新Hz | |
| 向き | |
| 回線 / 初回・キャッシュ済み | |
| 電源 / バッテリー / 発熱状態 | |
| 表示中の敵数 / 他アプリの状態 | |

JSONのUAと画面サイズだけから端末機種や更新Hzを断定しない。端末の設定値も記録する。

## 3条件 × 各3回

各条件で同じ経路・同じキャッシュ/向き/敵配置を使い、各回60秒。初回/キャッシュ後を混在させない。高さマップは橋の上/下・階段/坂、モスA2は橋周辺の歩行、リルド村は平和な村の同じ周回経路で比較する。本編の通常セーブは消さず、DEV試行に分ける。

| 条件 | 回 | 平均FPS / 最小 / 1%ロー | frame ms平均 / p99 / 最大 | 経路計算ms | JSヒープ開始→終了 | valid / JSON / 備考 |
|---|---|---|---|---|---|---|
| dev_height_proto | 1 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| dev_height_proto | 2 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| dev_height_proto | 3 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| moss_forest_02_mossy_ravine | 1 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| moss_forest_02_mossy_ravine | 2 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| moss_forest_02_mossy_ravine | 3 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| rilde_village | 1 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| rilde_village | 2 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |
| rilde_village | 3 | 未検証 | 未検証 | 未検証 | 未検証 | 実機なし |

3回の個別値と中央値を残す。PC Chromiumの結果は動作確認に限り、Android性能の代替値としてこの表に入れない。

## 高さデータ検査（依頼A）

```bash
python3 tools/moss/check_levels.py dev_height_proto
python3 tools/moss/check_levels.py --json dev_height_proto
python3 tools/moss/check_levels.py
```

map IDまたは複製JSONへのパスを指定できる。高さなしのmapは無視。高さmapがない時は無出力/exit0（--jsonなら空maps/問題0のJSON）。問題はexit1。元マップを変更しない。

足元基準で22×10px（feetから左11px/上10px）の衝突箱を検査し、16px格子・各辺2px以下の移動サンプルでconnectorのfrom/to/axis/fromEnd/zone規則を適用する。default spawnから状態 `(XY,level)` をBFSし、上位levelの到達不能セルと通過できないconnectorを検出する。eventZones/transitionsの矩形中心、treasurePoints/spawnsの足元が少なくとも1levelで歩行可か検査する。同一XYに立てるlevelの組をJSONで全列挙する。

低地と上位の重なりはoverpassかconnectorとして宣言する、というデータ安全条件を検査する。上位walkを覆う低地blocker/overpass/connectorの矩形和を厳密に検査し、格子間の1px拡張でも未宣言の重なりを拾う。橋の上下の合法な重なりはエラーにしない。level0の未到達セル数も出すが、そのセルだけでは問題扱いしない。

限界: 16px格子による到達性は連続空間の完全な証明ではない。inWalkは現仕様と同じ四隅判定。条件付きblockerのフラグ状態、procedural node scatterの衝突はこのツールだけで確定できないため問題として明示し、成功扱いしない。polygon/ellipse blockerは現FieldCollision同様に非対応。実際の操作すり抜け・描画順・入力の確認はClaude側m19/PLAYER QAと分ける。

## 逐次ランナー（依頼C）

```bash
PATH=/workspace/.cloud-setup/venv/bin:$PATH PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium bash tests/moss/run_all.sh
# 一部だけの実行も可能
bash tests/moss/run_all.sh tests/moss/m9_hero_intake.py
```

tests/mossのPythonを1本ずつ実行し、exit code/所要秒/注記をTSVと画面に出す。失敗後も続行し、1件でも失敗すれば全体exit1。既知のm6_questやbranch依存のm4不一致を注記する。8765が使用中なら既存サーバーへ接続せずexit2。rootから自分のhttp.serverを起動し終了時に停止する。ログは `TEST_RESULTS_DIR` または/tmp。通常900秒、seal600秒、`TEST_TIMEOUT_SECONDS` で上書き可能。m19の画像出力はOUTでログディレクトリへ分ける。Chromium指定は既存 `tests/run_python.py` の環境変数を利用する。

## 実行結果と引き継ぎ（2026-10-12 / PC）

基準 `2ddeaed8fcb58f3579903e3c4fcf0c74365941de`。実行環境はPython 3.12.14、Node 24.19.0、Playwright 1.62.0、system Chromium 154.0.8037.57。スクリプト/壊した複製/計測JSON/画像は/tmpに保存し、許可されていない新規テスト・レポートファイルはリポジトリへ追加しない。

| コマンド/検証 | 結果 |
|---|---|
| `python3 tools/moss/check_levels.py dev_height_proto` | exit0 / 問題0、level0 11511/11511、level1 906/906到達、4connectorに0↔1、共有XY350点 |
| 同コマンド `--json dev_height_proto` / map指定なし | exit0 / JSONをparse確認、全height mapの問題0 |
| `python3 tools/moss/check_levels.py /tmp/height-no-connectors.json` | 意図的な失敗: exit1、connectors全削除で上位到達不能 |
| 同 `/tmp/height-expanded-walk.json` | 意図的な失敗: exit1、橋walkを[1460,480,200,640]に拡張、未宣言重なり検出 |
| 同 `/tmp/height-one-pixel-walk.json` | 意図的な失敗: exit1、橋walk幅120→121だけでも未宣言重なり検出 |
| 同 `moss_forest_01_sunlit_path` | exit0 / 出力0 bytes、高さなしmapを無視 |
| 同 `/tmp/height-invalid.json --json` | 意図的な失敗: height:nullはexit1 / parse可能な問題JSON |
| `node /tmp/check_height_geometry.cjs` | 実際のFieldHeight/FieldCollisionと全16px格子点で一致（world内の22×10足元箱、0/1の11511/906、共有XY350） |
| `node --check js/dev/perf-meter.js` / `bash -n tests/moss/run_all.sh` / `git diff --check` | 成功 |
| `PATH=/workspace/.cloud-setup/venv/bin:$PATH TEST_RESULTS_DIR=/tmp/height-perf-ui-final TEST_TIMEOUT_SECONDS=180 bash tests/run_all.sh /tmp/check_height_perf.py` | exit0 / 実時間60秒、UI/コピー/DEVゲート/JSON/fallback/縦横画面、console/pageerror0 |
| `PATH=/workspace/.cloud-setup/venv/bin:$PATH PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium TEST_TIMEOUT_SECONDS=1 TEST_RESULTS_DIR=/tmp/height-runner-timeout bash tests/moss/run_all.sh tests/moss/m9_env.py tests/moss/m14_hold_move.py` | 意図的なtimeout: 2件ともexit124、各1秒、次のテストへ進む。全体exit1 |
| 同runner、timeout上書きなし、`tests/moss/m9_hero_intake.py` | exit0、30秒 |
| 同runner、`VIEWS=pc`、`tests/moss/m19_height_proto.py` | exit1、91秒、FAILS1、pageerror0。下記の既存境界期待値を確認 |

UI検証で取得したJSONはelapsed60000.7ms、3495フレーム、map=dev_height_proto、level0→1、valid=true。Clipboard APIから読み戻したJSONが結果と完全一致し、コピー拒否時もJSONを選択できた。memory APIがない時の取得不可、390×844/844×390のパネルboundsも確認。これはPCでの動作確認値であり、Androidの表には転記しない。

初回UI外部テストは60秒計測/自動コピーまで成功した後、拒否テストを注入するPlaywright評価式が関数を返して即実行されexit1となった。注入式だけを修正して再実行し、上記の最終exit0を確認。コード側のコピー拒否処理は変更していない。JS比較の初回も、raw blockedAtLevelだけではactorのworld外(y=0)を除外できないため不一致となった。比較側にworld内の足元箱条件を加えると全点一致した。

### 壊した複製の再現手順

```bash
python3 - <<'PY'
import copy, json
from pathlib import Path
src=json.loads(Path('data/maps/dev_height_proto.json').read_text())
a=copy.deepcopy(src); a['height']['connectors']=[]
Path('/tmp/height-no-connectors.json').write_text(json.dumps(a))
a=copy.deepcopy(src); a['height']['levels']['1']['walk'][0]=[1460,480,200,640]
Path('/tmp/height-expanded-walk.json').write_text(json.dumps(a))
a=copy.deepcopy(src); a['height']['levels']['1']['walk'][0][2]+=1
Path('/tmp/height-one-pixel-walk.json').write_text(json.dumps(a))
PY
python3 tools/moss/check_levels.py /tmp/height-no-connectors.json # exit1
python3 tools/moss/check_levels.py /tmp/height-expanded-walk.json # exit1
python3 tools/moss/check_levels.py /tmp/height-one-pixel-walk.json # exit1
```

### 統括側への確認事項

m19の橋脚項目は、停止位置feet.x=1591で `x < 1590` が失敗。足元箱右端はx+11、橋脚はx=1604からなので、1591の右端1602は障害物の手前。実FieldHeightの判定もfeet1590/1591/1593はlevel0で非衝突、1594は衝突、同じXYのlevel1は非衝突だった。境界期待値の見直しが必要か統括側で確認する。編集禁止のm19/衝突/高さ本体は修正しない。

同m19でlevel遷移、上下同一XY、階段/坂、橋と高台への往復、位置+level往復、通常2D map、24,000歩でblocked positions0/level leaks0は合格。個別の境界失敗を隠して「m19合格」とは報告しない。

### 未検証

Android実機全9試行（ADB/USB/端末リンクなし）、height Phase 1の本番公開、スマホタッチの実機性能、全mossスクリプトの一括実行。m19はPCのみで、portrait/landscapeの全m19は未検証。性能パネルの縦横収まり確認とは別。mainは更新しない。
