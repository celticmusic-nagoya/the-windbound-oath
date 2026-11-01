# DIRECTIVE-25A — 本編プレイアブル品質監査

**総合結果: PARTIAL。監査項目: 61。** COMPLETE: 43 / PARTIAL: 10 / MISSING: 1 / BUG: 5 / BLOCKED: 2。

基準main `5ab60c5db833821744d73080f91ffcd559ebf0a4`（PR98）。ユーザー確定のPhase4/5A/5B COMPLETE、各Android実機QA PASS、Fiona眉問題CLOSEDを維持。正式259PNG、Lou未採用2表情、閉じ目静止4表情の扱いは変更なし。今回変更したものは監査資料・証拠・監査専用テストだけ。画像、素材参照、描画、瞬き周期、台詞、分岐、戦闘数値、SAVE形式の変更なし。

## 結論と実装終点

実装領域はプロローグ終了の砦に加え、砦酒場のリアム加入、街道検問、王都門／市場／城前広場／住宅、宿／ギルドと王都2依頼まで存在し、分割回帰で接続を確認した。王都職人地区・東地区・王城内、森深部は次の未接続境界。村のTBD出口はstory hookで接続済みであり、それらと混同しない。

**ニューゲームから王都までの同一SAVE・無改変連続プレイを完走したとは判定しない。** 新規通常経路probeでは家→Fiona会話→木人6行動で勝利→村南出口→断崖登頂→夕日/帰路→襲撃開始stage5まで実測した。snapshotのMossForest.mapIdは非表示断崖mapのcacheであり、stage5の表示fieldはlegacy村。それ以降のDEV/状態設定/teleport/DEV撃破を含む分割回帰は、対象moduleの検証としてのみ扱う。全経路到達性・初見balance・総合Android実機QAは残件。

監査で発見したBUGは製品報酬とQA基盤を区別して記録する。P0は今回の証拠で未検出であり、不存在保証ではない。現行仕様の通常戦闘立直し／Raider再戦、意図的静止表情、将来未接続mapを独断でBUGにしない。

## 実測とQAの内訳

- ブラウザ: **35本PASS / 1本FAIL / 全36本回収**。exitだけでなく印字FAIL/FAILSも確認。[原版33本](evidence/directive-25a/browser/results.json)／[追加probe・訓練・再戦](evidence/directive-25a/probe/results.json)。FAILは報酬等の実測を原文保存し、合格扱いしない。
- Node原版: **12suite PASS / 2suite FAIL**。[結果と各log](evidence/directive-25a/node/results.json)。別のin-memory抽出診断20+37ケースPASSは原因確認であり、原版FAILを置き換えない。
- 素材原版回帰: **1本FAIL**（旧Android全件未確認assert）。一方、台帳build --check／audit／実参照checkはPASS・0errors。259/259固定SHA一致。
- 監査成果物の整合性QAと独立exact-head QAは別gate。監査で発見した製品／旧テストのFAILは次案件へ分離し、本監査PRには修正を混入させない。製品全体PASS／release-readyを意味しない。
- 既存33本のsource head `e70942ea6876f8f7409bf9040abedbd85d929f1e`、追加3本 `535ed142b21975b3bfb68eed4dedb529fc13bebd`。異なるheadを同じと偽らず、製品1456ファイルの[固定manifest](evidence/directive-25a/runtime-SHA256SUMS)で基準mainとのbyte同一性を確認。

各検証対象の再現手順・期待・実測・判定・根拠・Android要否は[監査matrix全項目](evidence/directive-25a/audit-matrix.json)が正本。[検証条件と限界](evidence/directive-25a/coverage-notes.md)／[ソース所見・イベント一覧](evidence/directive-25a/source-findings.md)／[30map・63transition・259SHA](evidence/directive-25a/static-inventory.json)。30mapのうち2つはDEV用。

## 項目別判定

| ID | 対象 | 判定 | 根拠 |
|---|---|---|---|
| S01 | タイトル／NEW GAME | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S02 | SAVE／CONTINUE／旧データ保全 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S03 | ニューゲーム→実装終点の連続通常プレイ | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S04 | フィオナ会話・訓練・訓練後移動 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S05 | 断崖ベンチの選択・夕日→襲撃 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S06 | 襲撃後の村・建物制限 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S07 | 襲撃の救助・再会・北側2戦・王国騎士・河川脱出 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S08 | 森到着・古代石・封印条件 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S09 | A1→A2→A3・3symbol勝利・ルー入口 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S10 | ルー初対面・父の剣破損・風の舞・加勢・誓い契約CG | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S11 | 父の剣→誓いの剣・装備解禁 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S12 | レイダー勝利→余韻・ルー加入 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S13 | 砦・PROLOGUE END・自由探索 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S14 | リアム加入・断る分岐・退場 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S15 | 街道検問・リアム保証・王都入口 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S16 | 王都2依頼・売店・装備・保存 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S17 | 現在の実装終点 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S18 | 次区間の王都3出口・森深部 | MISSING | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S19 | エマのお守り依頼／選択分岐 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S24 | 平和村の風船・迷子猫依頼 | BUG | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S20 | 老人／農婦の依頼・報酬重複防止 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S21 | 本編立ち絵・表情115ページ | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S22 | DEV表情28種・瞬き・静止4種 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S23 | 瞬き実画素・reduced-motion・後片付け | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M01 | 平和村/室内の境界・出入口・interact | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M02 | 砦/街道/王都map遷移・未実装出口guard | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M03 | tap/hold移動・停止 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M04 | 8方向・歩行アニメ・camera | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M05 | ルー登場後の追従・退場 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M06 | Android縦横tap移動・横scroll | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M07 | 全30データmapの全壁／全境界網羅 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B01 | 雑魚開始・ターン・勝利・報酬・field復帰 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B02 | バットAI・吸血・接触・再生成 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B03 | ボアAI・戦闘・突進 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B04 | 戦闘演出・アクション・勝利表示 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B05 | 風の舞・MP/TP/RUNE・学習gate | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B06 | Raider敗北→再戦→勝利 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B07 | 通常戦闘の低HP復帰 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B08 | 戦闘balanceの通し実測 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B09 | 3人目／4active＋2reserve戦闘 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| B10 | 加入者EXP・王都SAVE/LOAD | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| U01 | 店UI・買物・所持金・保存 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| U02 | 装備UI・ロック・SAVE | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| U03 | ボタン押しやすさ・文字・回転 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| U04 | Android端末のOS中断/復帰・実機通しプレイ | BLOCKED | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| A01 | 正式採用259PNG不変 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| A02 | 素材台帳・map/manifest参照 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| A03 | 画像の仮素材・未使用・未承認区分 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| A04 | field BGM対応範囲 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| A05 | 戦闘motion・次地域アセット | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T01 | console/Promise/HTTPエラー | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T02 | timer/owner/連打/LOAD世代 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T03 | 旧Node fixture2件 | BUG | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T04 | 素材回帰の旧Android assert | BUG | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T05 | 無条件真assertの検出力 | BUG | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T06 | cloud frame-time／node／heapの基準測定 | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T07 | 長時間memory／実機性能 | BLOCKED | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T08 | テストcover範囲 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| T09 | 現在のPages公開構成（基準main） | COMPLETE | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| S25 | 家のdrawer/pot取得メッセージと実給付 | BUG | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |
| M08 | 本編襲撃fieldの正式pixel素材接続 | PARTIAL | [手順・実測・証拠](evidence/directive-25a/audit-matrix.json) |

## 確認した課題

- 序盤の取得／依頼報酬は、表示・完了flagと実給付を比較する。タンス1potion、壺3gold、風船2potion、迷子猫2毒消しの実測値はprobeのseeded_rewards。仕様上の報酬に実数が追いつかない場合、P6-REWARD-01として別修正。毒消し定義不在を理由に新しい戦闘効果を勝手に追加しない。
- Node2件は旧`function say(t)`抽出／新`storyPortraitPage`未取込。素材回帰は全件Android UNVERIFIED固定assert。原版FAILを保持したままP6-QA-01へ。
- 宿舎回復などの`or True`は検証力不足。該当assertだけで全回復・台詞一致をPASSにしない（P6-QA-03）。直前waitによる実検証がある`check(True)`とは区別する。
- リアムは加入／保証人／EXP／装備／保存があるが、実戦のactor／HUD／turnは主に2人固定。4active/2reserve/Lou SUPPORTの確定方針に対してPARTIAL。次地域の本編は未接続で、無断でstoryを補完しない。
- BGM宣言9IDのうち生成profileはリルド3。その他6IDの対応方針は未完成。存在しないmp3参照の404とは判定しない。

## 性能測定

[環境](evidence/directive-25a/environment.json): Linux x86_64・3CPU、Chromium154 headless、CPU slowdown1倍、2map×3viewport、移動中各8秒。参考値でありAndroid実機のFPS／熱／memory leak合格判定ではない。

| viewport/map | 平均fps | p99 ms | 最大ms | DOM nodes | heap MiB |
|---|---:|---:|---:|---:|---:|
| pc/dev_height_proto | 58.8 | 33.3 | 50 | 130 | 6 |
| pc/moss_a2 | 41.3 | 50 | 166.6 | 171 | 18 |
| portrait/dev_height_proto | 59.8 | 16.8 | 33.4 | 126 | 6 |
| portrait/moss_a2 | 59.3 | 16.8 | 116.6 | 145 | 14 |
| landscape/dev_height_proto | 59.5 | 16.8 | 33.4 | 126 | 9 |
| landscape/moss_a2 | 58.9 | 16.8 | 133.4 | 144 | 13 |

[生の測定値](evidence/directive-25a/performance.json)。PC相当A2の低下と最大spikeは条件付き参考値として残す。合意済み性能予算がないためBUGと断定せず、実機/反復計測をP6-PERF-01へ。OS pause/resume、thermal、長時間heap、端末touchはNOT_RUN。

## 次期計画・素材仕様

[PHASE6_BACKLOG](../planning/PHASE6_BACKLOG.md): P0/P1/P2/P3 = **0/4/8/2**。14追跡IDに影響、担当、依存、完了条件、実装順を記録。最優先は **QA-01→REWARD-01→QA-02**。P2を先に置く理由は、P1全経路の判定基盤を直す依存関係による。

[ASSET_GAP_LIST](../planning/ASSET_GAP_LIST.md): **10制作／接続検討単位**。用途・scene・サイズ/比率・alpha・画風・優先度・代替を記載。未承認寸法はTBD、Raider元sheetとruntime派生frameを区別。885UNKNOWN等を不足件数に換算しない。画像生成・新規採用は実施しない。

## 再実行と公開

```bash
QA_OUT=/tmp/25a-shots PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium \
  bash tools/qa/run_all.sh --gameplay-ready --out /tmp/25a-qa \
  tests/system/playable_audit_25a.py tests/moss/m10_flow.py tests/battle/raider_wipe_rematch.py
python tests/system/directive25a_artifact_audit.py
python docs/qa/evidence/directive-25a/collect_inventory.py
```

ブラウザは直列。全33本の対象・testSHA・server停止と所要秒はresults.jsonを参照。`node -r docs/qa/evidence/directive-25a/node/fixture_preload.cjs tests/startup_race.test.cjs`等は診断専用で、原版PASSの代用は禁止。

基準mainのPages buildと299公開ファイル（259正式PNG含む）は[取得結果](evidence/directive-25a/pages-verification.json)で一致。本監査PR公開のmain/build/文書byte一致はマージ後に別途回収して完了報告する。Pages設定変更なし。rollback ref・独立exact-head QA・通常PR merge・必須保護を遵守。今回の総合Android実機確認はユーザー対応の残件。
