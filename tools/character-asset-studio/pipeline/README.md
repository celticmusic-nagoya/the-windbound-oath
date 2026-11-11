# AI Collaboration Pipeline v0.5.1（CHARACTER-ASSET-STUDIO-06／07）

ChatGPT と Claude のあいだで、アセット制作の指示・成果物・検証結果を、機械が読める形で受け渡すための道具。人間向けの画面（`../index.html`）とは別に、コマンドラインで動く。

- 必要なもの: Python 3.9 以上、Pillow、numpy、jsonschema（AIのサンドボックスには通常そろっている）。jsonschema がない環境では、スキーマ検証は BLOCKED になる。
- 実行方法: リポジトリのルートで `python3 tools/character-asset-studio/pipeline/cas.py <コマンド>`

## QAの判定と終了コード（v0.5.1 で分離）
- **判定は JSON で読む。** QA系のコマンドは、`overall`（PASS／FAIL／BLOCKED／NOT_RUN）、`adoptionReady`、`adoptionBlockers`、`counts` を出力する。
- **`adoptionReady`:** すべての検査が PASS で、人間の検査が1件以上あり、そのどれも NOT_RUN でないときだけ `true`。NOT_RUN は採用できる PASS として扱わない。自動検査がすべて PASS でも、人間の検査が終わっていなければ `false`。`true` でも、採用にはディレクターの承認記録が別に必要。ツールの検査記録（正本の照合、MANIFEST、スキーマ検証、Android 実機QA）は採用対象ではないので、常に `false`。
- **終了コード:** 判定とは別で、既定（`--gate none`）では「コマンドが実行できたか」だけを表す。
  | 終了コード | 意味 |
  |---|---|
  | 0 | 実行できた（判定は JSON を見る） |
  | 1／2／3 | `--gate` を指定したときだけ。1 = FAIL、2 = BLOCKED、3 = 採用できない（`--gate adoption` のときの NOT_RUN など） |
  | 64 | ポリシーで拒否（保護対象・許されない上書き・承認状態での書き出し） |
  | 65 | 入力が不正（ファイルがない、JSON が壊れている） |
  | 70 | 内部エラー |
  - `--gate no-fail`: FAIL または BLOCKED のときだけ失敗にする
  - `--gate adoption`: `adoptionReady: true` でなければ失敗にする

## 上書きの範囲（v0.5.1 で整理）
厳しい規則から順に適用する。
1. 保護対象（正本17件と保護フォルダ）は、`--overwrite` を付けても書き込まない。
2. 新しいファイルは書ける。
3. 既存のファイルを置き換えるには `--overwrite` が必要。さらに、次の条件をすべて満たすものだけを置き換える。
   - `assets/` の下ではない（納品された候補は置き換えない）
   - パイプラインが作ったファイルである: qa-report、manifest、production-brief の JSON、生成マーカー（`<!-- cas:generated -->`）付きの Markdown、同じフォルダの `production_brief.json` に載っているガイドPNG
4. 素体・衣装・フレームの納品記録（asset-set）、候補画像、手書きの文書は、上書きの対象にならない。位置合わせと素体仕様の変換は、常に新しいファイルにだけ書く。
5. ブリーフを作り直すときは、書き込む前にすべての出力先を確認する。1つでも拒否されれば、何も書き込まない。

## 原則
1. **正本保護:** `protected_assets.json` に載っている17ファイルと、保護フォルダ（`assets/official/`、`assets/candidates/morwen/final-visual-canon-20261111/`）には、どのコマンドも書き込まない。上書き・再エンコード・移動もしない。SHA-256 が1つでも変われば FAIL。
2. **未承認データを自動で採用しない:** コマンドが書き込める状態は `UNAPPROVED_CANDIDATE`、`UNAPPROVED_REFERENCE`、`UNAPPROVED_INSTRUCTION`、`BLOCKED` だけ。`DIRECTOR_APPROVED` と `CANONICAL_PROTECTED` はディレクターの記録でしか付かない。承認記録（`approvals`）のない `DIRECTOR_APPROVED` は QA で FAIL。
3. **4分類:** 検査結果は必ず PASS／FAIL／BLOCKED／NOT_RUN のどれか。全体の結果は厳しい方を採る（FAIL → BLOCKED → NOT_RUN → PASS の順）。人間にしか判断できない項目（デザインの一致、骨格、年齢にふさわしい表現、装備の構造）は、人間の記録がない限り NOT_RUN。そのため、自動QAだけで全体が PASS になることはない。
4. **上書きしない:** 出力先にファイルがあれば停止する。例外は上の「上書きの範囲」のとおり。
5. **使えない素体を使わない:** `profiles/reference_bodies.json` で BLOCKED の素体（R2.1）は、ブリーフにも QA の参照にも使えない（BLOCKED）。

## 共通スキーマ（`schemas/`、JSON Schema 2020-12）
| `schema` の値 | ファイル | 用途 |
|---|---|---|
| `cas/asset-set/0.5` | asset-set.schema.json | 素体・衣装レイヤー・歩行フレームの納品記録（QAの入力）。キャンバス、アンカー、フレーム数、方向ごとの PNG と SHA-256、許容値、人間のレビュー記録、承認記録 |
| `cas/anchor-set/0.5` | anchor-set.schema.json | 方向・フレームごとの関節や接地のアンカー（正規化座標 0〜1） |
| `motion-reference/1.0` | motion-reference.schema.json | モーション参考（画面の `motion-core.js` が書き出す。常に `UNAPPROVED_REFERENCE`） |
| `BASE_BODY_SPEC` 2.0 | `../docs/BASE_BODY_SPEC.schema.json` | 素体仕様（画面の 06 から書き出す。v0.2 のまま） |
| `BASE_BODY_SPEC` 1.0（旧形式） | base-body-spec-1.0-legacy.schema.json | 読み込みと変換専用（v0.1 の `docs/BASE_BODY_SPEC.example.json`）。新しいデータは 2.0 で書く |
| `cas/manifest/0.5` | manifest.schema.json | SHA-256 付きの MANIFEST |
| `cas/production-brief/0.5` | production-brief.schema.json | AI画像生成向けの制作指示 |
| `cas/qa-report/0.5` | qa-report.schema.json | QA結果（PASS／FAIL／BLOCKED／NOT_RUN と件数） |

座標の扱いは画面と同じ（`studio-core.js` の `toPixel`／`toNorm`／`placement`。丸め方も JavaScript に合わせ、テストで一致を確認している）。アンカーは「足の裏の最下行（アルファ128以上）＝ y」「最下行から6行上で測った靴底の外側の幅の中央＝ x」。

## コマンド
| コマンド | 内容 |
|---|---|
| `validate FILE... [--report OUT]` | `schema` の値から種類を判定して検証する。種類が分からないファイルは BLOCKED。`--report` を付けると QA 結果として保存する |
| `measure-canon --character ID --observations FILE --out-dir DIR` | 正本4方向を読み取り専用で計測する（接地と足は自動、ほかの関節は観察ファイルから）。可視／推定／測定不能を区別した根拠 JSON、BASE_BODY_SPEC v2.0 の未承認候補、ガイドPNG、QA結果を作る。測定不能の関節を計測値として扱うことはない（v0.6） |
| `body-spec-upgrade SRC --out DST [--preset ID]` | 旧形式 1.0（ピクセル座標）の素体仕様を 2.0（正規化座標）に変換して、新しいファイルに書く。元のファイルは変更しない。結果は画面（`studio-core.js`）の変換と完全に一致する（信頼度 provisional、出典 imported_spec、状態 candidate_not_canonical） |
| `qa ASSET_SET [--report OUT]` | 画像の自動QA（下記）を行い、`cas/qa-report/0.5` を出力する |
| `brief --task-id --kind --character --preset --out-dir --deliver-to [--frames] [--slot] [--body-spec] [--description]` | 方向ごとのガイドPNG（透明背景）とプレビュー（正本を薄く重ねた確認用）、`production_brief.json` を作る。納品先は `assets/candidates/` の下だけ |
| `align SRC DST --preset ID [--no-x]` | 接地点をアンカーに合わせた新しい候補PNGを作る（サイズが違う場合は、縦横比を保ったまま下端中央に配置する）。不透明な部分がはみ出す場合は書き出さず FAIL |
| `manifest-build ROOT --out FILE` | SHA-256 付き MANIFEST を作る（保護対象のファイルは `CANONICAL_PROTECTED` になる） |
| `manifest-verify FILE` | MANIFEST と照合する。ハッシュの違い、ファイルの欠落、MANIFEST にないファイルは FAIL |
| `protect-verify` | 保護対象17件の SHA-256 を照合する |
| `protect-diff --base REF` | git の変更に保護対象が含まれていれば FAIL |
| `pr-summary REPORT... [--out MD]` | QA結果を Draft PR 用の Markdown 表にまとめる |
| `pr-append --repo O/R --pr N --file MD [--key K] [--footer F] [--dry-run]` | PR 本文の中の `<!-- cas:summary:begin key=K -->`〜`<!-- cas:summary:end key=K -->` の範囲を置き換える（なければ末尾に追加する）。同じ内容をもう一度送ると `unchanged` になり、本文は変わらない（冪等）。v0.5 の旧マーカー `<!-- cas-pipeline-summary -->` は、本文を変えずに key=legacy-v0.5 の範囲に変換する。同じ key のマーカーが重複・欠けている場合は推測せず BLOCKED。PR が開いた Draft でなければ何もせず BLOCKED。マージや Draft の解除はしない |

### 画像の自動QA（`qa`）
- 方向ごと: フレーム番号の欠落・重複・範囲外、フレーム間の寸法の一致、接地行のばらつき、外接矩形の高さのばらつき、（歩行フレームの場合）同じ画像が連続していないか（再利用はアニメーション素材ではない）
- フレームごと: ファイルの有無、SHA-256、寸法、アルファチャンネル、本物の透明部分（アルファ0）、外周が透明か、中身の有無、接地（足の最下行とアンカーの y）、アンカーの x（歩行フレーム以外）、フレーム別アンカーの範囲
- 全体: スキーマ、状態、アンカーがキャンバス内か、px と正規化座標の一致、参照ファイルの SHA-256、BLOCKED の素体を参照していないか
- 足のない衣装レイヤー（帽子など）は、接地の検査をしない
- 人間による検査（NOT_RUN）: デザインの一致、骨格と頭身、年齢にふさわしい表現、装備の構造を推測していないか、`profiles/<character>_constraints.json` の各項目

## ChatGPT ⇄ Claude の受け渡し手順
1. **指示（ディレクター補佐 → 制作者）:** `cas.py brief ...` で `production_brief.json` とガイドPNGを作り、作業ブランチにコミットする。数値は JSON から読む（画像から読み取らない）。
2. **制作（制作者）:** ブリーフの `outputRequirements` に従って PNG を作り、`deliverTo` のフォルダに置く。全ファイルを `cas/asset-set/0.5`（`status: UNAPPROVED_CANDIDATE`、各ファイルの SHA-256 付き）に記録する。
3. **自動QA（受け取った側）:** `cas.py validate` → `cas.py qa` → `cas.py protect-verify` を実行する。FAIL なら原因を直して再提出する（同じ問題の再試行は最大3回）。BLOCKED なら、足りない前提を報告する。
4. **集約:** `cas.py pr-summary` で Markdown を作り、`cas.py pr-append --key <用途>` で Draft PR の該当範囲を置き換える（何度送っても重複しない）。QA の JSON はコミットする。
5. **採用:** ディレクターが人間の検査項目を記録（`humanReviews`）し、承認（`approvals`）したときだけ採用候補になる。本番への組み込みは別の承認が必要。

## 例
- `examples/demo_candidates.asset-set.json`: 画面に同梱している非正本の候補4方向。QA の結果は自動検査がすべて PASS、人間の検査が NOT_RUN（全体は NOT_RUN）。
- `examples/morwen_walk_brief/`: 8コマ歩行のブリーフの例（ガイド4方向とプレビュー）。ランドマークはテンプレートの値で、実測した骨格ではない（`TEMPLATE_NOT_MEASURED`）。制作の発注ではない。

## テスト
`python3 -m unittest discover -s tools/character-asset-studio/pipeline/tests -v`（31件。正本の計測（v0.6）を含む。座標・テンプレート・JSON出力・素体仕様の変換が `studio-core.js` と一致すること、合成画像で各検査が FAIL を検出すること、保護対象への書き込みが拒否されること、PR 本文の更新が冪等であること、`adoptionReady` と終了コード、上書きの範囲、など）

## v0.7 4階層モジュラーモデル（CHARACTER-ASSET-STUDIO-10）
全キャラクター共通の論理階層（`profiles/layer_catalog.json`）:

| 階層 | 内容 |
|---|---|
| `L0_BASE_BODY` | 体の構造ガイド（身長・頭身・骨格の比率、関節、接地点、4方向で共通の体格）。成人は露骨でない人体構造ガイド（`adult_nonexplicit_anatomy`）、未成年は中立的な構造ガイド（`minor_neutral_structure`）を使う |
| `L1_UNDERWEAR` | インナー、ガーターベルト、ニーソックスなど下層の衣装 |
| `L2_BASE_OUTFIT` | ブラウス、スカート、パンツ、基本の防具 |
| `L3_OUTER_ACCESSORIES` | ローブ、ケープ、帽子、バッグ、眼鏡、武器、装飾 |

- 階層は分類で、描く順番ではない。描く順番はパーツごとの `zOrder`（同じ値なら `partId` 順）と、`occlusion`（前後関係のメモ）で決める。たとえば、背面のローブは L3 でも、体より後ろ（zOrder が小さい）に描ける。
- スキーマ:
  - `cas/modular-part/0.7`（パーツ1枚 = 1つの階層・方向・フレーム）。必須項目は characterId、view、frameIndex、canvas、layerId、partId、zOrder、anchorSet、sourceAsset、sha256、approvalStatus、measurementStatus、sourceEvidence。
  - `cas/modular-character/0.7`（パーツの集合）。`baseBodySpec` で既存の BASE_BODY_SPEC v2.0 を参照する。v2.0 自体は変更していない。
- **計測状態（measurementStatus）:**
  | 値 | 意味 |
  |---|---|
  | VERIFIED | 実測・検証済み |
  | ESTIMATED | 推定、または AI の目視で人間の確認がないもの |
  | UNKNOWN | 測定不能 |
  | TEMPLATE | テンプレートの値 |
  | DESIGNED_CANDIDATE | 新しく設計した候補値で、正本の計測値ではない |

  計測状態は、採用状態（approvalStatus）とは別の項目。v0.6 の計測からの対応は、自動で測った可視点 → VERIFIED、AIの目視で求めた点と推定 → ESTIMATED、測定不能 → UNKNOWN。
- **スキーマで強制する規則:**
  - L0 のパーツには bodyGuidePolicy が必須。
  - 未成年キャラクターは `minor_neutral_structure` 以外を使えない。
  - DIRECTOR_APPROVED には承認記録が必須。
