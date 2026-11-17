# MORWEN-REBUILD-01 — G1 BLOCKED checkpoint

2026-11-17 UTC. Base main: `539d76d8d7b644998b0bc7c5ca9b23e1b521993a`.
Branch: `feature/morwen-rebuild-01`. No geometry produced; Phase A–B are not complete.

## 正本調査（実行済み）

最新mainのAGENTS.md、HIGH_END_3D_CHARACTER_AND_WORLD_PRODUCTION_V1_1、CAUSAL_RETRY_AND_METHOD_SWITCH_V2、MORWEN_V561_CANONICAL_20261108、morwen-design-canonical.jsonを確認。
正本はJPEG実体1536×1024、SHA-256 `47d58cbeb0f8ad41f51543716d872bfcc8c7d0dc91d45196c9c02b22402df638`。
文書・JSONともバイナリ未登録。workspace画像2,468件をSHA照合、一致0。
非公開handoff mainの再帰ツリーにも7374/v561/Morwen画像の候補なし（該当はシナリオ文書のみ）。

非公開正典はAPIで取得し、Bible §36、ADD-002、AGE-CORRECTION、CANON_STATUSの関連箇所を照合。18歳・学院首席・研究院の関係を保護。全文を本PRに転載しない。
取得時Git blob: Bible `c20fc9b7ea7aaa0de7449e110463225dab07573e`、addendum `e1000869aaf232d989761d15c982ed798378b49d`、status `ec5940c2ca6466150810f93c7fc6a463ef7ebec3`。
旧本文の長髪記述と旧SCULPT仕様の7.749997頭身を新造形の根拠にしない。後発の指定v5.61を優先する。

PR #407 HEAD `062b9f0753aa1bf0a5dc6536d52ed9a81be18541`、#417 HEAD `932590522bcef219eb26526b794ce35b6d13862f`を取得。
#417のBlenderを4.3.2でスクリプト無効・背景モードで開き、埋め込み画像7件をハッシュ検査。比較シートは `d9730dad8b1791204bb39f52697a176d4556e82a33442fdc0c101059bcc7113b` で指定正本と不一致。4方向Layer0と重複2件も指定SHAでない。旧承認表記は今回の正本承認に流用しない。

## 過去PRとの関係・累積履歴

既存PRと原本は変更しない。履歴は各固定HEADの以下を参照する。

- #417 `docs/qa/morwen-head-sculpt-20261117/ATTEMPT_LEDGER.md`: 自動顔fit＋放射髪2 FAIL、annulus/zipper2 FAIL、停止。楕円体顔／管髪は却下。
- #407 `docs/qa/morwen-sculpt02/ATTEMPT_LEDGER_02.md`: broad Grab2回取り消し・停止、局所Grab＋低密度髪mass2美術FAIL・停止。
- #417 `docs/qa/morwen-sculpt03/ATTEMPT_LEDGER_03.md`: corner quadまぶた初回局所試作。64 quadの技術成果は保持するが、浮いた眼輪・旧写実顔・厚いヘルメット髪が残る。全身造形の基礎に固定しない。
- #417 `docs/qa/morwen-sculpt03/INDEPENDENT_REVIEW_20261117.md`: G2 FAIL、限定局所技術screenのみPASS。実際の独立レビューを参照した。REBUILDの独立QAは未実施。
- Blender仕様 `docs/production/CODEX_MORWEN_ART_DIRECTED_SCULPT_02_20261117.md` と `MORWEN_SCULPT03_RETOTOPO_PLAN.md` は技術履歴として確認。コピー／旧比率保持の指示は今回の全身再構築指示で置換する。

## 方式比較・暫定選定（未実行）

| 方式 | 品質・総工数・適法性・再現性 | 今回の判断 |
|---|---|---|
| 画像計測→手動全身control mesh→スカルプト→retopo | シルエットと非対称性を直接制御。作業時間は必要だが不一致基盤の補正を避けられる。自作形状として来歴管理可能 | 第一候補。正本取得後に計測し採否を確定 |
| Geometry Nodes | カメラ、診断、反復部品に再現性あり。人体identityの決定を代行しない | 補助のみ |
| 適法な既存人体base | 時間短縮可能。ライセンスと正式比率の確認・全面変更が必要 | 比較候補。既存SCULPT形状は採用しない |
| AI 3D補助 | 非対称／見えない面の捏造とretopo工数、出力ライセンスの確認が必要 | 未選定・未実行・課金なし |
| 旧局所Grab／primitive組立／Python人体推定 | 既知identity欠陥を継承、停止済み方式の再試行になる | 使用禁止 |

外部制作研究・素材ライセンス調査は未完了。新規素材導入なし。Blenderは利用可能であり、今回の阻害要因はソフト不足ではなく正本バイナリ不足。

## Phase A 計測とPhase Bの解除条件

正本取得後にSHA・JPEG・1536×1024を検証し、原本を変更せず参照登録する。
頭頂（帽子と頭蓋を区別）、顎、肩、胸郭、腰、股、膝、足底、手足端、衣装外周、左右の非対称装備を画面座標で記録。直接観測と遮蔽／奥行き推定を分け、寸法と色は未取得のまま捏造しない。斜め絵を正投影測定図にしない。正面／側面／背面の根拠と不確実性を明示してから頭身と世界座標を決める。

全身control meshと主要衣装外形を新規制作し、固定正投影カメラ・同一照明・同一スケールで正面、左右側面、背面、左右斜めを保存。対応する正投影資料がある場合のみ輪郭／ランドマーク差を計測する。斜め絵は並列美術照合に限定。顔拡大と想定ゲーム表示も比較する。
独立美術QAで全身が成立するまで顔精密化、UV／リグ／アニメへ進まない。制作原本とゲーム最適化版は別ディレクトリにする。

## 実績と未実行

G1 BLOCKED: CANONICAL_BINARY_UNAVAILABLE。G2/G3/G4 NOT_RUN（REBUILD候補がない）。
全身設計の数値確定、ベースmesh、.blend新作、レンダー、シルエット比較、顔比較、独立美術QAはすべて未実行。旧Blenderを新作成果物として提出しない。
正本取得前に不一致モデルを増やさない。解除には指定SHAと一致する元画像そのものが必要。

## 追加ディレクター指示 — 上位品質規約と最終制作目標

2026-11-17の本タスク追加指示を適用する。
「THE WINDBOUND OATH｜ハイエンド3D世界・アセット自律制作指示 v1.0」および「全自動・高品質ファースト自律開発プロトコル v3.4」を上位規約として指定。今回確認したmainとprivate treeに両文書の原文は特定できず、#362のv3.4整合提案を原文の代用とはしない。本節はユーザーが直接提示した要件を記録する。

- 最終目標は正式採用四方向に忠実な7.5〜8頭身のフル3D。顔・人体・髪・衣装・装備・PBR材質・リグ・アニメーションを一貫した品質で制作し、複数視点と独立美術QAで評価する。この頭身範囲は今回明示された設計目標であり、旧モデル比率の自動承認ではない。
- Layer 0参照シーンは準備成果物。画像配置・原本再オープン・CI成功はモデル完成でもG2 PASSでもない。画像平面を人体meshとして計上しない。
- 参照シーンのQAは画像バイトSHA、front/back/left/right対応、左右反転の有無、ピクセル比、上下・接地位置、表示／非表示切替、保存後再オープンを確認する。正本が斜め絵なら正投影図として数値評価しない。
- 参照QA後は既存制作と担当を再確認し、独立した全身ベースmesh制作へ自律的に進む。全身不一致のまま顔細部・リグへ進めない。
- 既知失敗方式を繰り返さない。高品質base、sculpt、retopo、PBR、適法素材、AI補助を品質と総工数で評価する。

担当確認: open PR #407（SCULPT02）、#417（SCULPT03）、#419（本REBUILD）、#411（AI制作調査）、#362（v3.4整合提案）を照会した。#419はCHARACTERの再構築調査を担当し、他PRの造形・MAP作業を変更しない。open PRだけでは他担当者の実行中状態は確定できないため、造形着手時に再照会する。

現時点ではLayer 0参照シーン自体も未生成／QA未実施。追加指示は特定の画像バイト列や所在を示していないため、旧埋め込み7画像と指定v5.61との正本相違は未解決。解除には正式採用四方向の実ファイル／取得先と、その正本指定（v5.61 SHAロックとの関係を含む）が必要。上位規約原文の所在も取得して内容を照合する。未確認部分を推測して制作規則に加えない。

## BLOCKED解除実行 — 正式Layer 0の取得・参照シーン完成

本節が上記の旧BLOCKED checkpointを更新する。旧preflight.jsonは当時の証跡として保持。
最新指示で正式参照の用途が分離された: v5.61（11月8日）は外観デザイン、四方向Layer 0（11月16日）は身体構造・プロポーション。両画像群のSHA相違は競合ではない。身体構造作業にv5.61の未取得を全体停止条件として課さない。

参照ブランチ `feature/morwen-reference-binary-01` の固定HEAD `8cc6687ce4498b6f0ea5bd59f0ebe2d7017629f1` から4 PNGと既存manifest・setup script・workflowを取得。既存mainにはQUALITY_FIRST_3D_PIPELINE_V1が無いため、指定参照ブランチの同文書を読み、mainのAGENTS・Autonomous v1.0・高品質v1.1・causal retry v2と照合。ユーザー追加指示により参照の用途分離と7.5〜8頭身目標を適用。原規約の書換え・他PRのマージなし。

| 方向 | 原ファイル | 確認SHA-256 |
|---|---|---|
| 正面 | 7809.png | b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed |
| 右 | 7807.png | 9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737 |
| 背面 | 7810.png | b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f |
| 左 | 7808.png | 69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa |

4/4 PNG、RGBA、384×1024、manifest一致。元PNGとmanifestのバイトを変更しない（manifest内の未upload記述は歴史情報であり現在の取得実績とは分ける）。実画像も目視し、正面・右向きprofile・背面・左向きprofileの対応を確認。明示された身体参照用途でG1 PASS。

既存run 43380121634（feature/mvp-blockout-01、ea33594af49d2a51643820600f887135b71aae8e）はsuccess。Artifact 14016615602はexpired=false／92,633 bytes。ただしworkspace ZIP取得は配布先403で失敗した。既存スクリプトが未梱包画像を保存することも確認したため、既存処理を本ブランチで実行して補完する。

### 実制作済みの参照シーン

- `assets/candidates/morwen-rebuild-01/reference-scene/MORWEN_LAYER0_REFERENCES.blend`
- `tools/blender/production_mesh_08/prepare_layer0_references.py`: 既存生成処理を変更せず使用。
- `tools/morwen_rebuild01/finalize_reference_scene.py`: 4画像をpack、4正投影camera追加、独立再open、投影四隅・upright・左右非反転・元SHA・寸法・lock・hide切替検証。
- `docs/qa/morwen-rebuild-01/reference-scene/`: 両段階のQA JSON、実行log、SHA256SUMS。

Blender4.3.2でローカル実行済み。画像4件をpackした自己完結原本。人体meshは0件でありモデル完成ではない。2.0は画像キャンバスの正規化高であり、公式身長2mや接地登録を意味しない。画像内の頭頂／足底余白はそのまま保持。骨格landmark・接地・頭身測定は未実行。G3参照シーンの限定検査PASSは、人体G3認定とは区別する。

### 次の高品質素体工程へ着手

#335のbody担当PRはcoordination only／造形未実施と確認。#407/#417の累積停止方式と独立美術FAILを再読。旧局所Grab・自動realistic顔fit・放射髪・annulus/zipper・primitive人体loftを再実行しない。

参照QAの後、Blender公式Human Base Meshes 1.4.1のCC0 **stylized female**素体の取得・原本検証・別ファイル取り込みへ進む。旧SCULPTのrealistic形状とは別の素材。取り込みは新しいモルウェン形状の完成や正本適合を意味しない。旧PRで検証済みのarchive SHA／展開後Blender SHAと照合し、原頂点・面は変更せず、正規化表示だけ行う。

ローカル公式mirrorアクセスはHTTP403で取得不可。Actionsの独立jobで公式取得を試し、成功時に6方向render・編集可能source intake・QA・log・SHAをArtifactsへ保存する。失敗時は技術障害として記録し、primitive推定生成で代替しない。

次の造形はLayer0の観測landmarkと姿勢差を明示した全身target、手動sculpt／retopoによる身体形状編集。source intakeは未加工のため素体美術QAを合格扱いしない。全身G2が未PASSなら精密顔・髪・衣装・rigへ進めない。v5.61未取得は最終外観デザイン照合のみに残るBLOCKED。

### CI実行の実績と技術修正

Run 44148074813は両job success。参照Artifact 14356469200（3,865,981 bytes）、素体Artifact 14357033627（1,762,949 bytes）が実在。素体は公式archive／展開後source SHA一致、stylized female 12,502頂点／12,500面、原座標不変、6 PNGを実生成した。
GitHub connector経由で素体ZIPを取得し実画像を確認した。初回の全身表示が横にずれており、表示transform式の誤り（元object位置も高さで除算する必要）が原因。形状変更なしで修正し、評価後mesh全頂点の画面内検査を追加。これは参照fitや新しい美術candidate生成ではなく、source intakeの表示不具合修正。

またaptの非固定Blenderが5.0.1を導入しており、local4.3.2でその.blendを開けなかった。旧Artifactを消さず保持し、新workflowはPython3.11＋bpy4.3.0に固定して再実行する。local4.3.2との完全な同等性を暗黙に認定せず、取得後の再openを検査する。旧source intakeのG3は未認定のまま。CI成功をモデル／美術完成と解釈しない。

### 固定runtime再検証・納品済み状態

[Run44149109934](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44149109934)、code d9f0c08101be02190551bf8cd6fcc85cb752bac1、verify-reference / cc0-base-intakeともsuccess。
参照Artifact14357757704（3,871,939 bytes）／素体Artifact14358710788（2,522,919 bytes）は2026-12-17 UTCまで保持。両ZIPをGitHub connector→workspace経由で取得し、local Blender4.3.2で実際に再openした。CLIからの旧ZIP403はconnector取得で解消。素体の表示移動を修正し、6方向の評価後全頂点がフレーム内に収まることを確認。元control geometry SHA606a5cbed38aa3318626a48185bde66d3ce9f9c1f39d2fe9b6e66783f9740c4cは不変。

取得済み素体 `.blend` と6 PNGは `assets/candidates/morwen-rebuild-01/base-source-intake/` に保存。QA／取得・Blender logは `docs/qa/morwen-rebuild-01/base-source-intake/`、ローカル再openはCI_LOCAL_REOPEN.json/logに保存。編集可能ファイルはBlender4.3系。初回5.0.1のArtifactは失敗証跡として保持し置換しない。

未解決: ソース素材のmask_arms／mask_legs表示切替driverが参照先を欠き、再open時にinvalid driver警告2件。元sourceを改変せず保存したため、本体制作前に別working copyで不要driverを整理しviewport／render parityを検証する必要がある。原素材の顔形状・A-pose・頭身はLayer0へfitしておらず、元素材の見た目をモルウェンとして採用しない。ノイズのある低サンプルclayは取り込み検査用で商業品質rendererではない。

判定: 身体参照G1 PASS／最終外観G1 BLOCKED（v5.61未取得）。G2 NOT_RUN（新しいMorwen造形なし・独立美術QAなし）。参照scene G3限定PASS、素体sourceは再open／有限座標／原形状／6方向framingの限定screen PASSだがdriver・UV・rig等の本体G3は未完了。G4 NOT_RUN。
次は別working copyでdriver整理、Layer0ランドマークと直接観測／推定を分けた全身設計、7.5〜8頭身targetの手動sculpt／retopo。全身シルエットの独立美術QAが未PASSのため精密顔・髪・衣装・rigへ進まない。高品質素体の調達・編集可能source取り込みまでは実行したが、正式形状の素体制作は未完了。

### 最終追補 — sourceの表示driver障害を作業用copyで解除

調査するとmask修飾子自体は存在せず、2本のdriverだけが残った孤立参照だった。元CC0 intakeは変更せず保持し、`tools/morwen_rebuild01/prepare_sculpt_workspace.py` で別working copyから2本を除去。初回調査で修飾子の存在assertが失敗したlogも保持。修飾子欠落を確認した後、該当driverのみ除去して再保存・再openし、control頂点／面のSHA不変を検証した。

編集可能な作業原本: `assets/candidates/morwen-rebuild-01/body-workspace/MORWEN_BODY_SCULPT_WORKSPACE_UNAPPROVED.blend`。
QA: BODY_WORKSPACE_QA.json、BODY_WORKSPACE.log。source再open時の警告はlog前半に残るが、cleanup後の再openでは再発せず、driver数0をassertした。
これによりdriver障害は解除。全キャラクターG3はBLOCKEDからNOT_RUNへ更新（UV／rig等の全体認定は行わない）。身体G1 PASS／最終外観G1 BLOCKED／G2 NOT_RUN／G3 NOT_RUN／G4 NOT_RUN、限定技術screen PASS。新しい身体形状はまだsculptしていない。元の任意人体形状やA-poseを正式採用と誤認しない。

## 最新工程: 実全身形状変更（準備工程は再実行しない）

[実造形v02報告](MORWEN_REBUILD_01_BODY_EDIT.md)を最新実績とする。既存原本の12,502頂点を実編集しafter4viewを保存、独立QAも実施。G2 FAIL、限定技術screen FAIL。準備の繰り返しではなく、実形状変更と改善／悪化の証跡を納品した。v01/v02同cagefamilyは2回失敗で停止し、今後は局所解剖surface手法へ切替える。

## 最新停止記録 — quad patch再構築01

MORWEN_QUAD_PATCH_01_FAILED.mdを最新の実行結果とする。747面を740新面に置換し、旧15警告を新patch上で追跡したが2件が残った。自己交差・quad折れ・屈曲・独立G2もFAIL。保護9,080頂点と外部11,753面は維持。必須完了条件未達のためこの候補を採用せず、指示に従って追加造形を停止した。原本と失敗比較証跡を保持する。
