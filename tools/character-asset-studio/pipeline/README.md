# AI Collaboration Pipeline v0.5（CHARACTER-ASSET-STUDIO-06）

ChatGPT と Claude のあいだで、アセット制作の指示・成果物・検証結果を、機械が読める形で受け渡すための道具。人間向けの画面（`../index.html`）とは別に、コマンドラインで動く。

- 必要なもの: Python 3.9 以上、Pillow、numpy、jsonschema（AIのサンドボックスには通常そろっている）。jsonschema がない環境では、スキーマ検証は BLOCKED になる。
- 実行方法: リポジトリのルートで `python3 tools/character-asset-studio/pipeline/cas.py <コマンド>`
- 終了コード: 0 = FAIL・BLOCKED なし、1 = FAIL、2 = BLOCKED、64 = ポリシー違反で停止（保護対象への書き込みなど）

## 原則
1. **正本保護:** `protected_assets.json` に載っている17ファイルと、保護フォルダ（`assets/official/`、`assets/candidates/morwen/final-visual-canon-20261111/`）には、どのコマンドも書き込まない。上書き・再エンコード・移動もしない。SHA-256 が1つでも変われば FAIL。
2. **未承認データを自動で採用しない:** コマンドが書き込める状態は `UNAPPROVED_CANDIDATE`、`UNAPPROVED_REFERENCE`、`UNAPPROVED_INSTRUCTION`、`BLOCKED` だけ。`DIRECTOR_APPROVED` と `CANONICAL_PROTECTED` はディレクターの記録でしか付かない。承認記録（`approvals`）のない `DIRECTOR_APPROVED` は QA で FAIL。
3. **4分類:** 検査結果は必ず PASS／FAIL／BLOCKED／NOT_RUN のどれか。全体の結果は厳しい方を採る（FAIL → BLOCKED → NOT_RUN → PASS の順）。人間にしか判断できない項目（デザインの一致、骨格、年齢にふさわしい表現、装備の構造）は、人間の記録がない限り NOT_RUN。そのため、自動QAだけで全体が PASS になることはない。
4. **上書きしない:** 出力先にファイルがあれば停止する（`--overwrite` は保護対象以外にだけ効く）。位置合わせは必ず新しいファイルに書き出す。
5. **使えない素体を使わない:** `profiles/reference_bodies.json` で BLOCKED の素体（R2.1）は、ブリーフにも QA の参照にも使えない（BLOCKED）。

## 共通スキーマ（`schemas/`、JSON Schema 2020-12）
| `schema` の値 | ファイル | 用途 |
|---|---|---|
| `cas/asset-set/0.5` | asset-set.schema.json | 素体・衣装レイヤー・歩行フレームの納品記録（QAの入力）。キャンバス、アンカー、フレーム数、方向ごとの PNG と SHA-256、許容値、人間のレビュー記録、承認記録 |
| `cas/anchor-set/0.5` | anchor-set.schema.json | 方向・フレームごとの関節や接地のアンカー（正規化座標 0〜1） |
| `motion-reference/1.0` | motion-reference.schema.json | モーション参考（画面の `motion-core.js` が書き出す。常に `UNAPPROVED_REFERENCE`） |
| `BASE_BODY_SPEC` 2.0 | `../docs/BASE_BODY_SPEC.schema.json` | 素体仕様（画面の 06 から書き出す。v0.2 のまま） |
| `cas/manifest/0.5` | manifest.schema.json | SHA-256 付きの MANIFEST |
| `cas/production-brief/0.5` | production-brief.schema.json | AI画像生成向けの制作指示 |
| `cas/qa-report/0.5` | qa-report.schema.json | QA結果（PASS／FAIL／BLOCKED／NOT_RUN と件数） |

座標の扱いは画面と同じ（`studio-core.js` の `toPixel`／`toNorm`／`placement`。丸め方も JavaScript に合わせ、テストで一致を確認している）。アンカーは「足の裏の最下行（アルファ128以上）＝ y」「最下行から6行上で測った靴底の外側の幅の中央＝ x」。

## コマンド
| コマンド | 内容 |
|---|---|
| `validate FILE...` | `schema` の値から種類を判定して検証する。種類が分からないファイルは BLOCKED |
| `qa ASSET_SET [--report OUT]` | 画像の自動QA（下記）を行い、`cas/qa-report/0.5` を出力する |
| `brief --task-id --kind --character --preset --out-dir --deliver-to [--frames] [--slot] [--body-spec] [--description]` | 方向ごとのガイドPNG（透明背景）とプレビュー（正本を薄く重ねた確認用）、`production_brief.json` を作る。納品先は `assets/candidates/` の下だけ |
| `align SRC DST --preset ID [--no-x]` | 接地点をアンカーに合わせた新しい候補PNGを作る（サイズが違う場合は、縦横比を保ったまま下端中央に配置する）。不透明な部分がはみ出す場合は書き出さず FAIL |
| `manifest-build ROOT --out FILE` | SHA-256 付き MANIFEST を作る（保護対象のファイルは `CANONICAL_PROTECTED` になる） |
| `manifest-verify FILE` | MANIFEST と照合する。ハッシュの違い、ファイルの欠落、MANIFEST にないファイルは FAIL |
| `protect-verify` | 保護対象17件の SHA-256 を照合する |
| `protect-diff --base REF` | git の変更に保護対象が含まれていれば FAIL |
| `pr-summary REPORT... [--out MD]` | QA結果を Draft PR 用の Markdown 表にまとめる |
| `pr-append --repo O/R --pr N --file MD [--footer F]` | まとめを PR 本文の末尾に追記する。PR が開いた Draft でなければ何もせず BLOCKED。マージや Draft の解除はしない |

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
4. **集約:** `cas.py pr-summary` で Markdown を作り、`cas.py pr-append` で Draft PR に追記する。QA の JSON はコミットする。
5. **採用:** ディレクターが人間の検査項目を記録（`humanReviews`）し、承認（`approvals`）したときだけ採用候補になる。本番への組み込みは別の承認が必要。

## 例
- `examples/demo_candidates.asset-set.json`: 画面に同梱している非正本の候補4方向。QA の結果は自動検査がすべて PASS、人間の検査が NOT_RUN（全体は NOT_RUN）。
- `examples/morwen_walk_brief/`: 8コマ歩行のブリーフの例（ガイド4方向とプレビュー）。ランドマークはテンプレートの値で、実測した骨格ではない（`TEMPLATE_NOT_MEASURED`）。制作の発注ではない。

## テスト
`python3 -m unittest discover -s tools/character-asset-studio/pipeline/tests -v`（17件。座標・テンプレート・JSON出力が `studio-core.js` と一致すること、合成画像で各検査が FAIL を検出すること、保護対象への書き込みが拒否されること、など）
