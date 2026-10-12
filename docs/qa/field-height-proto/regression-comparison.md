# 高さプロトタイプ第2弾：退行比較

STATUS: READY — 3本×2基準を単独実行し比較完了。既存コード・テストの修正なし。
担当: Codex / `work/codex-height-analysis`。prototype基準 `528f46e`、main基準 `0d48324`。mainへのmergeなし。

## 条件とコマンド

mainは `git worktree add --detach /tmp/main-wt origin/main`、main静的サーバーは8766、prototypeは8765。両サーバーはPython http.serverで各rootを配信するが、ブラウザテストは常に1本のみ。mainの3本→prototypeの3本の順。Chromium154 / Playwright1.62.0 / Python3.12.14、全テストの上限300秒。同じ3本のソースSHA-256が両方で完全一致することを確認。

3本は8765をハードコードしてPORTを読まない。テストファイルを編集せず、外部 `/tmp/height_compare_run.py` でPage.gotoのlocalhost:8765を指定PORTへ置換し、Chromium executableだけ指定した。初回gotoは各logに残り、mainが誤ってprototypeへ接続しないことを確認。

各rootで1本ずつ、以下の形で実行（外部 `/tmp/run_height_comparison.py` が自分のserverの起動・終了と300秒timeoutを管理）:

```bash
PORT=8766 PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium /workspace/.cloud-setup/venv/bin/python3 -u /tmp/height_compare_run.py tests/moss/m13_elder_attack_text.py
PORT=8766 PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium /workspace/.cloud-setup/venv/bin/python3 -u /tmp/height_compare_run.py tests/moss/m4_e2e.py
PORT=8766 PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium /workspace/.cloud-setup/venv/bin/python3 -u /tmp/height_compare_run.py tests/moss/m55_hz.py
# prototypeのrootでは同じ順で PORT=8765
```

機械可読のraw log/command/port/test hash/実行HEAD/時間は `regression-comparison.json`。prototypeの実行HEADは担当記録のみを加えた作業branchで、ゲーム・既存テストは528f46eと同一。

## 比較結果

| テスト | main 0d48324 | prototype 528f46e | 失敗メッセージの要点 / 分類 |
|---|---|---|---|
| `m13_elder_attack_text.py` | 失敗、exit1、5.484秒 | 失敗、exit1、5.386秒 | peaceful elder cycles to the morning line / mainにも存在 |
| `m4_e2e.py` | 失敗、exit1、175.402秒 | 失敗、exit1、185.339秒 | Fiona stage-9 line (elder/Emma warning wording) / mainにも存在、今回はtimeoutなし |
| `m55_hz.py` | 成功、exit0、21.456秒 | 成功、exit0、21.187秒 | 両方成功。申告の失敗は今回未再現 |

### mainでも失敗する項目：原因候補（各3行以内）

**m13_elder_attack_text**
- elder_closedに森の奥地警告が追加され、朝の「風が少し重い」は4番目（talk-data-rilde.js）。
- テストはcycleを初期化してtalkを3回呼び、3番目が朝の台詞と期待している。cycle実装は呼ぶごとに1つ進む。
- 両基準で同じ1項目のみ失敗。高さ機能より、追加台詞と固定回数期待値の不一致が原因候補。

**m4_e2e**
- テスト30行目は「近付くなって」を固定文字列で期待するが、現在の森到着会話（talk-data-scenes.js）は「奥には絶対行くなって」。会話構成/表示時点も変わった。
- 両基準とも結界/シンボル3戦/Lou/祭壇まで実行し、errors []。今回のexit1はその台詞assertion1件で、300秒timeoutではない。
- 過去の300秒timeoutの原因は未確定。元log/停止座標/入力・イベント状態がないため、今回の台詞失敗から過去timeoutの原因を推定しない。

### m55_hz と prototypeだけの失敗

m55は両基準で森林約300px/s、uncapped/default比約1.00、village/keyboard比も基準内。申告の失敗詳細は元log未提供のため原因未確定。今回の単独実行では未再現。prototypeだけの失敗は3本にはなく、その最小再現手順の対象もなし。これを他のテストや全環境の無退行保証とは扱わない。

## 変更/未検証/確認事項

変更は新規比較資料/JSON、新規 `tests/moss/m19_plan_bench.py` と表/JSON、新規Phase2素材下書きのみ。編集禁止の既存m19・高さ・衝突・移動・マップ/生成元、本編/セーブ/戦闘/採用済み素材は変更しない。今回の新規m19_plan_benchは依頼Eの明示的な追加対象。

未検証: 過去のm4 300秒timeoutとm55失敗の再現、全moss回帰、Android実機。原logがあれば停止時点を比較できる。今回は修正/修正差分を作成していない。

## 依頼E/Fの納品・実行結果

- E: 新規 `tests/moss/m19_plan_bench.py`。実マップを準備し、高さinstanceのpublic plan/setLevel/blockedAtLevelとFieldNavigationのpublic destination/follow/cancelだけで探索を測る。既存planner内部を差し替えず、探索コードを編集しない。
- Eコマンド: `PATH=/workspace/.cloud-setup/venv/bin:$PATH PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium TEST_TIMEOUT_SECONDS=300 TEST_RESULTS_DIR=/tmp/height-plan-bench-final bash tests/run_all.sh tests/moss/m19_plan_bench.py` → exit0、16条件×10回=160/160成功、console/pageerror0。最終頂点のXYとlevelも検査する。
- E結果: `plan-bench.md` / `plan-bench.json`。最終測定の高さ遠距離中央値は1倍12.75/16.50/14.90ms、4倍46.95/75.40/74.65ms。4倍の高台最大98.30ms。以前の200/750msと同じ経路/実装/測定方式/環境とは限らず、改善倍率を断定しない。2Dの3経路は距離が近い比較用で、衝突や呼び出し範囲の差を明記。
- Eの初回測定も全160回成功。最終版では終点の検査とsource/benchmark SHA-256の保存を追加して再測定。JSONのrepo_shaは測定時の担当記録HEADで、benchmarkはその時点で未commitだったため、正確なコード同定にはbenchmark_sha256/source_hashesを併用する。最終commitの同じファイルとhash一致を確認済み。
- F: 新規 `docs/art/height_asset_requests.md`。岩壁/遺跡石積み、4方向石段、4方向坂、橋床板、左右欄干、橋脚、天端の縁、前景樹冠を表と16個の単体プロンプトで用意。56world pxとunitScale2.5の扱い、@2x寸法、透明余白と連結辺の例外、アンカー、色補正耐性を記載。画像生成や既存素材の置換なし。
- `git diff --check` 成功。新規成果物以外のコード/既存テスト/本編マップ/保存形式/素材に差分なし。main/元prototypeのrefを更新しない。

統括への確認: 既存テストの新しい台詞/会話順への追従方針は別作業で判断する。旧timeout/m55失敗の原logが必要。素材のアンカー/方角別投影/追加の角部品はPhase1承認後のPhase2描画設計で確定する。
