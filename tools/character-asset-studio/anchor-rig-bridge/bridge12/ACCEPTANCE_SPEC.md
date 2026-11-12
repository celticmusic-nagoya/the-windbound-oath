# MORWEN-BRIDGE-12｜実アセット受入仕様（BLOCKED：実画像未納品）

基準: Draft PR #230 / HEAD `9d06cbc88d933f87a68b1c16402cc3a0ffd2f53f`。
本タスクはドキュメントとデータのみ。新規コードなし。PR #230 の座標・変換行列・検証コードは変更していない。

## 1. 受入に使う既存契約（重複実装しない）
| 役割 | 既存ファイル | 状態 |
|---|---|---|
| 取込契約 | `rig-integration/morwen.import.template.json`（`cas/rig-import/08`） | 変更なし |
| 取込・検証 | `rig-integration/import_rig.py`（0 PASS / 1 FAIL / 2 BLOCKED） | 変更なし |
| レイヤーQA | `pipeline/cas.py layer-qa`（`cas/modular-character/0.7`） | 変更なし |
| 正本保護 | `pipeline/cas.py protect-verify`（17件） | 変更なし |
| 汎用テンプレート→リグ | `anchor-rig-bridge/mappings/sheet_to_rig.json` | 変更なし（DERIVED_CANDIDATE・汎用専用） |

納品ごとの差し替えは、テンプレートを**新しいファイル名**でコピーして値を埋めるだけ。コードは変えない（データ駆動）。

## 2. 画像仕様
| 種別 | サイズ | 空間 | 形式 | 条件 |
|---|---|---|---|---|
| 四面図シート（designSource） | 1536×1024 | `sheetPx` | PNG | デザイン照合用。合成には使わない。面ごとの `crop`＋`matrix` は**このシート上で測った値**だけ。bridge-11 の汎用行列は流用禁止 |
| レイヤー画像 L0〜L3 × front/back/left/right（16枚） | 1200×1600 | `rigPx` | RGBA 8bit | 本物の透明（α=0）を含む／外周α=0／`mirrored:false`／取込時のリサイズ・色変換・α書換えなし |

- 同じ方向の全レイヤーで、アンカー（接地点）と関節座標が一致すること（`ANCHOR_ALIGNMENT`）。
- 方向ごとに別のPNGを用意する。片方の方向を反転して別方向に使うことは禁止。
- 既存の正本4方向（`final-visual-canon-20261111/`）は保護対象。サイズが混在しており、3枚はRGB（透過なし）のため、レイヤー画像としては受け入れない。デザイン照合にだけ使う。

## 3. 配置・命名・SHA-256
```
assets/candidates/morwen/layers-<deliveryId>/
  sheet/four_view.png
  L0/{front,back,left,right}.png   … L3 も同じ
  delivery.json                    （全ファイルの SHA-256・制作者・日付・status: UNAPPROVED_CANDIDATE）
```
- `deliveryId` の例: `chatgpt-20261112-01`。納品のたびに新しいディレクトリを作り、前回分は上書きしない。
- 取込JSONの例: `rig-integration/morwen.import.<deliveryId>.json`。各 `image` に `{path, sha256}` を書く。SHA は読み込む前に照合する（既存の動作）。

## 4. 計測分類（PR #230 の分類をそのまま使う）
| 分類 | 条件 |
|---|---|
| MEASURED | 納品画像そのもののマーカーや書き出しデータから読み取った値。元画像の SHA を添える |
| DERIVED | MEASURED の値から、記録した規則で計算した値。規則と入力値を一緒に保存する |
| UNRESOLVED | null のまま理由を書く。関係する検査は BLOCKED になる |

禁止: bridge-11 の汎用マネキン座標、SYNTHETIC_ONLY のフレームや接地データ、テンプレートの値を、モルウェンの MEASURED／DERIVED として登録すること。

## 5. 年齢ゲート（既存スキーマのとおり）
`AGENTS.md` §5 の現行記載はモルウェン17歳。`modular-part`／`modular-character` スキーマにより、L0 の `bodyGuidePolicy` は `minor_neutral_structure`（特徴のない中立的なマネキン型の構造ガイド）だけが通る。デザイン保護（`profiles/morwen_design_protection.json`）と年齢にふさわしい表現の確認は、人間が記録するまで NOT_RUN。

## 6. 未解決の仕様（推測で埋めていない）
- **L1 の名称の不一致:** `rig-import/08` では L1 = 「base clothing」、`layer_catalog 0.7` では L1 = `L1_UNDERWEAR`。どちらも変更せず、ディレクターの判断を待つ。
- テンプレートにある `attachments.rightGarter` は `jointId` と `anchor` が null のまま。
- 歩行（pose／root／contact）の実データはない。real contact は BLOCKED、ドリフトは NOT_RUN。

## 7. 納品後の手順
1. `delivery.json` の SHA と実ファイルを照合する。
2. 取込JSONを新しく作り（テンプレートは編集しない）、`import_rig.py` を実行する。結果は BLOCKED か FAIL か PASS。
3. modular 定義を作り、`cas.py layer-qa` を実行する。続けて `cas.py protect-verify` を実行する。
4. 人間のレビュー（デザイン・年齢・構造）を記録し、ディレクターが承認するまで `adoptionReady=false`。

## 8. 現在の判定
17スロット（シート1＋レイヤー16）はすべて NOT_DELIVERED のため BLOCKED。詳細は `delivery_slots.json`。実画像の納品を待つ間、これ以上の仮実装は行わない。
