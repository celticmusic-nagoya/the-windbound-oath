# AIDAN-ASSET-SOURCE-AUDIT — エイダンの家 素材調査・ライセンス監査

- タスク: MAP-ASSET-PREP-01 / 担当: Claude / 実施日: 2026-11-14 (JST)
- 状態: **RESEARCH_CANDIDATES_NOT_APPROVED**（候補選定のみ。正式採用・本体組込みなし）
- 機械可読台帳: [`aidan_asset_ledger.json`](aidan_asset_ledger.json)（38件）／SHA-256ロック: [`aidan_asset_sha256.lock.json`](aidan_asset_sha256.lock.json)（81ファイル）
- 検証ツール: [`tools/map_production/aidan_asset_ledger.py`](../../tools/map_production/aidan_asset_ledger.py)

## 0. 基準（G1入力）

| 項目 | 内容 | 検証 |
|---|---|---|
| 美術基準 | `assets/approved/world/rilde_village.png`（1672×941 RGB） | SHA-256 `c55af077…b51726a` を `docs/art/approved-world-event-sha256.json` と照合 **一致** |
| 屋根仕様 | 青灰色の石板葺き（2026-11-14ディレクター承認） | Draft PR #307 で `FIELD_VISUAL_OVERHAUL_20261108.md` を更新中。**mainは未反映（旧「赤茶屋根」のまま）** |
| 正典 | private handoff `reference/lore/THE_WINDBOUND_OATH_OFFICIAL_BIBLE_v5.0.md`（main `af0d068`）§8 リルド村、`WORLD_MAP_CANON_20261108.md` | 読取成功。エイダンの家は「主要構造」に列挙、**外観・寸法・階数の記述なし**。リルド村は「西部沿岸の農漁村」「生活感を非常に重視」（確定） |

背景CGから読み取れる様式（目視、推測を含まない範囲）:
- 壁: クリーム〜黄土色の**丸みのある不整形の乱石積み**。隅部は大きめの石。目地は浅く暗い。
- 屋根: 灰〜青灰の**天然スレート、行ごとに幅・厚みが不揃い**、苔・汚れの色むら、深い軒、木製破風板、ドーマー窓。
- 煙突: 石積み＋土管風の頂部。窓: 木製格子・暖色の室内光。生活小物: 樽、花箱、吊り看板、蔦。
- 参考計測（ライティング込みの平均色、アルベドではない）: 屋根 `#626363`〜`#746c5f`（S≦0.18）、壁 `#796f5f`〜`#847160`。

## 1. 調査方法
- Poly Haven: 公開API `api.polyhaven.com/assets|info|files` を直接照会（全869テクスチャ・モデル一覧から絞込）。各候補の作者・実寸・最大解像度・2Kマップの **provider md5** を記録。
- ambientCG: API v2 `full_json`（`downloadData`）で存在・配布サイズを確認。
- Sketchfab: API v3 `search`（`downloadable=true`、`license=cc0|by`）と `models/{uid}` で**ライセンスラベルを個別確認**。
- Kenney: 既存記録のアーカイブを再取得し SHA-256 一致と同梱 `License.txt`（CC0）を確認。
- Quaternius: `quaternius.com/license.html` 本文を取得（QAL v1.0, 2026-08-28）。
- 候補のサムネイルを**目視確認**し、時代・様式不整合を除外（下記 §4 の除外理由参照）。
- ライセンス根拠: Poly Haven <https://polyhaven.com/license>（全素材CC0）、ambientCG <https://docs.ambientcg.com/license/>（CC0 1.0）、CC BY 4.0 <http://creativecommons.org/licenses/by/4.0/>。

## 2. 推奨候補（優先素材別）

凡例: 商用=商用利用、改変=改変可、再配布=原素材の再配布可、表記=クレジット要否。適性は5段階（4以上を一次候補）。

### 2.1 青灰色の石板屋根（最優先）
| P | 素材 | 制作者 | ライセンス | 商用/改変/再配布/表記 | 形式・解像度 | 適性 | 所見 |
|---|---|---|---|---|---|---|---|
| 1 | [Poly Haven `roof_slates_03`](https://polyhaven.com/a/roof_slates_03) | Rob Tuytel | CC0 | ○/○/○/不要 | JPG/PNG/EXR, 最大8K, 実寸3m×3m | 4 | 天然スレート重ね葺き。最も近い。ただしアルベド平均 `#706e67`（H47 S0.08）＝**中性灰**。青灰にはマテリアル側で色相200〜215°・彩度0.08〜0.15へ寄せる必要（§5） |
| 2 | [Poly Haven `roof_slates_02`](https://polyhaven.com/a/roof_slates_02) | Rob Tuytel | CC0 | ○/○/○/不要 | 同上 | 3 | 暖灰褐色。全面ではなく色むら・汚れ帯のブレンド用 |
| ref | Poly Haven `grey_roof_tiles_02` / ambientCG `RoofingTiles003` | — | CC0 | — | — | 2 | 矩形が均一すぎ近代的。比較用のみ |

**重要:** テクスチャだけで石板屋根は成立しない。ゲーム表示幅（現行の `lind_aidan_house` は約290px）では、棟・軒・けらばの**輪郭の不揃い**と厚みが見えるかどうかが品質を決める（[構造監査](AIDAN_BLENDER_STRUCTURAL_AUDIT.md) §4）。

### 2.2 不規則な自然石の壁
| P | 素材 | 制作者 | ライセンス | 商用/改変/再配布/表記 | 適性 | 所見 |
|---|---|---|---|---|---|---|
| 1 | [Poly Haven `yellow_stone_wall`](https://polyhaven.com/a/yellow_stone_wall) | Sơn Nguyễn | CC0 | ○/○/○/不要 | 4 | 背景CGのクリーム〜黄土色の丸い乱石積みに最も近い（アルベド平均 `#af9778`） |
| 2 | [Poly Haven `castle_wall_slates`](https://polyhaven.com/a/castle_wall_slates) | Rob Tuytel | CC0 | 同上 | 4 | 扁平石の乱積み。煙突・基礎・破風の変化用 |
| 2 | [ambientCG `Bricks098`](https://ambientcg.com/a/Bricks098) | ambientCG | CC0 | 同上 | 4 | 灰〜ベージュ混在。P1との比較候補（2K ZIPのSHA-256記録済み） |
| 3 | Poly Haven `castle_wall_varriation` | Rob Tuytel | CC0 | 同上 | 3 | 灰色寄り。日陰・基礎の色むら |
| ref | Poly Haven `medieval_blocks_05` | Rob Tuytel | CC0 | 同上 | 2 | 他ブランチshortlistのP1。**整形ブロック・橙寄りで背景CGと不一致** |

### 2.3 古材の梁・柱・扉、木製格子窓・雨戸
| P | 素材 | 制作者 | ライセンス | 適性 | 所見 |
|---|---|---|---|---|---|
| 1 | [Poly Haven `rough_wood`](https://polyhaven.com/a/rough_wood) | Rob Tuytel | CC0 | 4 | 梁・柱・破風板。割れのある古材 |
| 1 | [Poly Haven `weathered_brown_planks`](https://polyhaven.com/a/weathered_brown_planks) | Dimitrios Savva, Rico Cilliers | CC0 | 4 | 扉・雨戸・花箱の板材 |
| 2 | [Poly Haven `medieval_wood`](https://polyhaven.com/a/medieval_wood) | Rob Tuytel | CC0 | 3 | 鋲打ち。正面扉のみ。全面使用不可 |

格子窓・雨戸・蝶番は既製モデルで適合する中世様式のCC0品を確認できず → **自作モデリング推奨**（板材PBRを適用）。

### 2.4 煙突・屋根棟・破風装飾
- 煙突本体: 壁と同系 `castle_wall_slates` / `yellow_stone_wall`。頂部の土管（チムニーポット）・棟石・破風板は**自作**（既製CC0で適合品なし）。
- 参考: Kenney Fantasy Town Kit 2.0 の `chimney*` / `roof-gable*` は寸法グリッド比較のみ（ローポリ・単一カラーマップ）。

### 2.5 石畳・苔・草地
| P | 素材 | 制作者 | ライセンス | 適性 | 所見 |
|---|---|---|---|---|---|
| 1 | [Poly Haven `cobblestone_floor_04`](https://polyhaven.com/a/cobblestone_floor_04) | Rob Tuytel | CC0 | 4 | 背景CGの暖色丸石の小道に近い |
| 2 | Poly Haven `grassy_cobblestone` | Charlotte Baglioni, Dario Barresi | CC0 | 3 | 玄関前の不定形敷石 |
| 2 | Poly Haven `forrest_ground_01` | Rob Tuytel | CC0 | 3 | 草地・土。草はジオメトリ／カードと併用 |
| 3 | ambientCG `PavingStones138`, `Moss002`, Poly Haven `mossy_rock`, `moss_01` | — | CC0 | 3 | 苔ブレンド・石の隙間 |
| 2 | Poly Haven `rock_moss_set_01`（モデル, 63k tris） | Kless Gyzen | CC0 | 3 | 敷地境界の苔石。LOD必須 |

### 2.6 樽・薪・花箱・生活用品
| P | 素材 | 制作者 | ライセンス | 表記 | 適性 | 所見 |
|---|---|---|---|---|---|---|
| 1 | [Sketchfab "Barrels!"](https://sketchfab.com/3d-models/barrels-1009f5c51391437e9ed2b97f04b9af31) | toomanydemons | **CC BY 4.0** | **必須** | 4 | 木製樽セット（18.9k面）。1〜2個に絞る |
| 2 | [Sketchfab "Log Pile (Game Ready / 2K PBR)"](https://sketchfab.com/3d-models/log-pile-game-ready-2k-pbr-3f4205a30a7d4adda50c775fb8cce06c) | meerschaumdigital | **CC BY 4.0** | **必須** | 4 | 薪の山（3,858面）軽量 |
| 2 | [Sketchfab "Old Lantern"](https://sketchfab.com/3d-models/old-lantern-game-ready-asset-42d15b68713f4a9ba0554ea2ea7efed0) | apariciosilva3D | **CC BY 4.0** | **必須** | 3 | 玄関灯。意匠がやや近世寄り |
| 2 | Poly Haven `wooden_bucket_01` / `wooden_crate_01` / `tree_stump_01` | James Ray Cock / Rob Tuytel | CC0 | 不要 | 3 | 桶・木箱・薪割り台 |
| 3 | Poly Haven `wicker_basket_01` | Kuutti Siitonen | CC0 | 不要 | 3 | 籠 |

Sketchfab素材は**ダウンロードにアカウント認証が必要**なためCIで自動取得・SHA固定ができない。採用時は手動取得→`aidan_asset_ledger.py`と同じ形式でSHA-256を追記し、`CREDITS`（作者名・URL・CC BY 4.0・改変有無）を登録すること。

## 3. 参照のみ（素材として取込まない）
- **Pinterest**: 既存 `tools/map_blender/pinterest_roof_reference_selection.json`（4ピン選定済み）を再利用。重複作成しない。画像の取込・トレース禁止。※今回Claudeはピン画像を目視していない（未検証）。
- **実写建築資料**（Wikimedia Commons, CC BY-SA 2.0, 参照のみ）:
  [Bridge Cottage](https://commons.wikimedia.org/wiki/File:Bridge_Cottage_-_geograph.org.uk_-_6191145.jpg)（ウェールズの石板葺き石造コテージ：軒・棟の納まり）／[Tyddyn Bach](https://commons.wikimedia.org/wiki/File:Tyddyn_Bach_-_geograph.org.uk_-_1405730.jpg)（小農家の石積み・煙突）。
- **既存ゲームの技法**（画像・形状は一切流用しない。技法の一般論のみ）:
  - 3Dジオラマ＋2Dドット人物（HD-2D系）: 建物は実寸3Dで陰影・被写界深度を付け、人物スプライトの輪郭を背景より高コントラストに保つ。
  - 固定角クォータービューの2Dスプライト配置（RO系）: 建物は**ゲーム角度で事前レンダリング**し、足元基準点と奥行きソート用の接地線を別データで持つ。
  - 共通: 近距離で見えない微細ジオメトリよりシルエット・明度差・色むらに予算を使う。

## 4. 除外・保留（理由付き）
| 素材 | 判定 | 理由 |
|---|---|---|
| Poly Haven `reed_roof_03` / `thatch_roof_angled`、ambientCG `ThatchedRoof*` | **REJECTED** | 茅葺き。2026-11-14承認の青灰色石板屋根と矛盾。他ブランチの `aidan_pbr_shortlist.json` で `thatch` がP1のまま → 要修正（§6） |
| Poly Haven `Barrel_01` | REJECTED | 目視: 近代の金属ドラム缶（爆発物ラベル） |
| Poly Haven `Lantern_01` | REJECTED | 目視: 近代の灯油式ハリケーンランタン |
| Poly Haven `hatchet` | REJECTED | 目視: ゴムグリップの近代手斧 |
| Poly Haven `planter_box_01` | 参照のみ | 目視: 内側にプラスチックライナー |
| Sketchfab "Crates And Barrels" | REJECTED | 目視: 金属ドラム＋防水シート |
| Sketchfab "Firewood_HP" | 参照のみ | 50k面。ベイク元としてのみ |
| Sketchfab "Village Cottage - Low Poly Medieval" (CC0) | 参照のみ | ローポリ様式。形状借用禁止 |
| Quaternius Medieval Village MegaKit | **BLOCKED** | QAL v1.0: 素材単体の再配布禁止。公開リポジトリへ原素材を置けない。ビルド同梱可否は法務判断待ち |
| ambientCG `Ground111` | 参照のみ | 他ブランチでは「UNVERIFIED」だったが、API v2 `full_json?id=Ground111` で**存在を確認**。ただし瓦礫混じりで平和な村の庭に不適 |

## 5. 色仕様の提案（ディレクター確認待ち・正式値ではない）
正典に屋根色の数値はない。背景CGと承認文言「青灰色」から、マテリアル側の目標を次のとおり**提案**する:
- 屋根スレート アルベド: 色相 200〜215°、彩度 0.08〜0.15、明度 0.32〜0.45。スレート1枚ごとに明度±0.06・色相±8°の揺らぎ、軒先と棟付近に苔／汚れ帯（`roof_slates_02` ブレンド）。
- 壁石: `yellow_stone_wall` 系の暖色を維持し、屋根との寒暖対比で輪郭を立てる。
- 採否はディレクターがゲーム表示サイズの比較画像で判断（G2）。

## 6. 既存資料との照合結果
| 既存資料（ブランチ） | 照合結果 | 対応 |
|---|---|---|
| `tools/map_blender/aidan_pbr_shortlist.json`（feature/aidan-home-quality-master-01） | `thatch` がP1、`medieval_blocks_05` が壁P1 | 屋根正典と矛盾。本台帳で REJECTED / REFERENCE_ONLY と判定。**他担当ブランチのため未変更**。担当側で更新を推奨 |
| `tools/map_blender/AIDAN_HOME_PBR_INTAKE_PLAN_01.md`（同上） | 「3. thatch: reed_roof_03」 | 同上 |
| `tools/map_blender/EXTERNAL_ASSET_INTAKE.md`（同上・map-blender-08） | 「red-brown pitched roof」を次期試作目標に記載 | 旧仕様。更新推奨 |
| `tools/map_blender/aidan_external_asset_sources.json`（同上） | Kenney SHA `1a7530c0…cd8676ef` | 再取得して**一致を確認** |
| `docs/design/FIELD_VISUAL_OVERHAUL_20261108.md`（main） | 「赤茶屋根」 | PR #307（Draft）で更新中。本PRでは触らない |

管理先の判断: 他ブランチの `tools/map_blender/` は制作担当（ChatGPT側）の作業領域のため、監査・台帳は依頼どおり `docs/map-production/` に新設し、既存ファイルは参照・照合のみとした。

## 7. 取得・照合手順
```bash
python3 tools/map_production/aidan_asset_ledger.py validate            # オフライン: 台帳・ライセンス・基準CGのSHA
python3 tools/map_production/aidan_asset_ledger.py check-online         # 提供元APIで作者・md5の変化を確認
python3 tools/map_production/aidan_asset_ledger.py fetch --locked-set \
  --out /tmp/aidan-assets --lock /tmp/aidan-assets/lock.json \
  --expect-lock docs/map-production/aidan_asset_sha256.lock.json       # 再取得してSHA-256再現性を検証
```
- `fetch` はリポジトリ内への出力を拒否する。原素材はコミットしない（CC0でも容量・管理の都合でハッシュのみ管理）。
- 実施結果（2026-11-14）: P1〜P2のCC0候補15件・81ファイル・約137MBを取得。Poly Haven提供md5と全件一致、2回目の取得でSHA-256が全件一致（再現性PASS）。

## 8. 未検証・残課題
- Sketchfab CC BY素材3件の実ファイル（認証必須で未取得）、ポリ数以外の品質。
- Pinterestピン画像の目視。
- 各PBRの**ゲーム表示サイズでの見え方**（Blender上の比較レンダは未実施。次工程）。
- 格子窓・雨戸・煙突頂部・棟石・破風装飾は既製の適合品なし → 自作が必要。
