# MORWEN-RIG-INTEGRATION-PREP-08

**統合基盤：合成検証PASS。実素材：BLOCKED。**

- 基準：PR #228 HEAD `0fdbbd4d3ad24da7070d318c9676bac793f72df6`。
- ブランチ：`feature/morwen-rig-integration-prep-08`、独立worktree。初期確認はAGENTS.md、PR #225〜#228、SOURCE-05と明示依存のみ。全履歴・無関係素材の探索なし。
- 容量不足で通常worktree展開に失敗したため、今回のworktreeだけ疎なcheckoutへ変更。既存worktree/PNGは撤去しない。

## 最小差分と依存

新規ファイルのみ：

- `rig-integration/import_rig.py`：Layer0〜3インポート、四面図変換、SOURCE-05ポーズ接続、接地QAアダプター。
- `rig-integration/morwen.import.template.json`：実入力用の未確定テンプレート。
- `rig-integration/README.md`：PNG/SHA/寸法/anchor/関節階層/zOrder/採用状態/4方向と座標・ポーズ契約。
- `qa/test_rig_integration_08.py`：合成15件。
- `qa/morwen-rig-integration-prep-08/`：実行証跡・本報告。

既存 `SOURCE-05.generate` / `pinned` / `world_point` と、Export04 converter・stance auditorをそのまま利用。既存PRファイルの上書きなし。PR225の丸め修正が基準に未反映のため、新アダプターは未丸めの足別最大値でもFAILを判定し、既存監査ファイルには触れない。

## 実装結果

- L0〜L3のPNG/SHA/RGBA/寸法/透明画素、4方向、anchor、全関節ID・親子循環・単一root、描画順、各view内のレイヤー間anchor/関節一致を検証。ファイル読取のみ、画像合成・再生成・再圧縮なし。
- Morwen v1.0参照SHAと階層を保持。ガーターは解剖学的R関節への所属が必須。L/R IDと親側を検証し、`mirrored=true`、負の行列式による反転を拒否。実ガーター位置・関節取付は未測定のためnull。
- 1536×1024四面図と1200×1600 rigを別空間として定義。明示crop＋crop-local→rigの6要素行列のみ採用。象限分割・単純寸法比・3D投影・体型合わせを推測しない。未確定変換はBLOCKED、変換済み座標もnull。
- SOURCE-05の左右6コマ入力にSHA固定 `poseInput` を追加できるアダプターを実装。frameId/方向/timeMs/関節/actorTransformを測定JSONと照合し、足裏heel/ball/toeと解剖学的L/Rを対応付ける。元SOURCE-05ファイルは変更しない。
- 接地は方向別にconverter→auditorへ渡す。stanceIdの切替、実測不足、足滑りを検出。カメラ・CSS・固定ground markerからworld接地を作らない。
- 技術PASSでも `adoptionReady=false / productionReady=false`。ラベル・SHAだけで人間の採用や視覚一致を認定しない。

## テスト・コマンド

新worktreeで実行：

```sh
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_rig_integration_08.py' -v
python -m unittest discover -s tools/character-asset-studio/qa -p 'test_*.py' -v
python -m py_compile tools/character-asset-studio/rig-integration/import_rig.py tools/character-asset-studio/qa/test_rig_integration_08.py
python tools/character-asset-studio/rig-integration/import_rig.py tools/character-asset-studio/rig-integration/morwen.import.template.json tools/character-asset-studio/motion-source/morwen_walk6.source-plan.json
```

| 対象 | 結果 |
|---|---|
| 新規合成fixture | PASS 15/15、初回成功。修正再試行0回 |
| QA全体 | PASS 52/52（既存37＋新規15） |
| 構文 | PASS |
| 実入力CLI | BLOCKED / exit 2、74件の不足理由 |
| 実PNG・接地・独立美術QA | NOT_RUN / BLOCKED |
| 正本保護SHA | PASS 17/17、完全な基準worktreeで確認 |

合成fixtureは一時ディレクトリのPNG/receipt/pose/measurementのみ。正常パイプライン12入力、左右逆転、反転指定、SHA不一致、座標欠落、描画順、循環階層、未確定変換、明示sheet変換、負行列式、左右接点逆転、actor欠落、5px足滑り、2.0000001px境界滑り、pose欠落を検証。合成の技術PASSを実素材のPASSとして登録しない。

既存回帰は容量制約のため、**無変更の完全なPR #228基準worktree**で実行（疎な新worktreeの全ゲーム回帰と称さない）：

```sh
node --test tools/character-asset-studio/tests/*.cjs
node --test tests/*.cjs tests/field/*.test.js
python -m unittest discover -s tools/character-asset-studio/pipeline/tests -v
python tools/character-asset-studio/pipeline/cas.py protect-verify
```

Studio 19/19 PASS、repository 52 PASS / 8 FAIL、pipeline 55 PASS / 3 FAIL。PR #228証跡と失敗IDが一致、新規IDなし。既存runtime/pipeline/test/PNGへの変更なし。基準実行のstdout/stderr・exitは `BASE_REGRESSION_COMMANDS.json`、差分と検証限界は `REGRESSION_DIFF.json`。新統合コードの検証は上記52件を新worktreeで実施したもの。

## 残課題

1536×1024四面図そのものとSHA、正式分割L0〜L3 PNG、実crop・行列・anchor・view別関節座標、Rガーター取付、実12コマpose/actor/contactデータが必要。テンプレートは入力欄をnullのまま提供し、既存v1.0の体型座標を作り替えない。実素材のPASS・正式採用・Export工程への自動移行は行わない。

公式PNG、正本SHA、PR #225〜#228は保護。画像再生成、ゲーム本体接続、mainマージ、公開なし。将来の入力は新manifestと新PNG参照を差し替えて投入でき、既存原本を上書きする必要はない。
