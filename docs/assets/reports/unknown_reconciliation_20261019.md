# 台帳 UNKNOWN 照合レポート（第1回 / 2026-10-19）

対象: `approval_status = UNKNOWN` の885件（台帳 957件中）。方針: **UNKNOWN を根拠なく APPROVED に変えない**。採用の証拠（Issue・ハンドオフ・納品記録・指示）が見つかったものだけ更新する。

## 1. 内訳（照合後）
| 区分 | 件数 | 判定 | 根拠 |
|---|---|---|---|
| main 上・実装済み（実行時参照あり） | 707 | **統合済み・正式採用記録は未確認** | オーナーがマージした作業（下表の導入コミット）で本編に組み込まれている。採用記録（Issue/ハンドオフ）は未発見のため UNKNOWN のまま |
| main 上・参照なし | 20 | 未使用（保管・将来用）。削除しない | §3 |
| ブランチのみ（未マージ） | 158 | 未採用（採用記録なし） | §4 |

## 2. 参照検出の誤判定を修正（台帳の精度向上）
- 従来、`x_f{n}.png` / `x_{n}.png` のような**テンプレート指定**（manifest の `walk.file`、`field-monsters.js` の `file:'leafy_boar_{n}.png'`）と、`'_'+state+'.png'` の**動的組み立て**（`lind-animals.js`）を静的検索が見逃し、170件が「参照なし」と誤判定されていた。
- `build_registry.py` にテンプレート名の照合を追加（連番末尾→`{n}`）。Lind 動物8枚は `registry_overrides.json` で参照元を明記。
- 結果: 参照なし 170 → **20**。「採用済み・未実装」候補: **0**（Lou KO が実装済みになったため）。

## 3. main 上の参照なし 20件
| 素材 | 件数 | 所見 | 扱い |
|---|---|---|---|
| `img/battle/characters/{aidan,fiona}/*_alt.png`, `aidan_reference_sheet.png`, `aidan_skill_wind_slash_alt.png` | 4 | 代替版／参考シート（原本保管） | 未使用のまま保管。採用記録なし |
| `lou_skill_heal.png` | 1 | `charge→heal` の静止画（Lou heal は `lou_support_heal.png` を使用）。採用記録なし | 保管 |
| `moss/art/fx_seal_01〜04`, `fx_treasure_glint_01〜04`, `treasure_chest_glint_01〜04` | 12 | 10/12 の納品（モス素材取込 WIP）。エフェクト枠のみで、manifest/マップに割当なし | **納品済み・未実装・採用記録なし**（候補扱い）。採用指示があれば封印演出／宝箱きらめきとして接続可能 |
| `moss/standin/ground_{dirt,grass}.png`, `moss/town/guildhall.png` | 3 | 仮絵（standin）／未配置の建物 | 保管 |

## 4. ブランチのみ 158件
| 素材 | 件数 | 所見 | 判定 |
|---|---|---|---|
| `feat/aidan-side-walk-v4`: `aidan_diagonal_pool`（斜め歩行プール）／`aidan_side_v4/diagonal` | 約57 | コミット「archive diagonal pool (old+new) and list missing parts」＝**採用前のアーカイブ（欠け部位あり）** | 未採用。2.5D 試作の素材要件に関わるため、採用判断が必要 |
| `assets/rilde-interior-v1`: `rilde_interior_v1`（壁・床・建築・プレビュー） | 約10 | 10/16 アップロード。数百バイトの小さなタイルが多く、main には既に12の屋内（`rilde/furn` 等）あり | 採用記録なし。屋内マップとの照合要（要オーナー確認） |
| `assets/staging` / `rilde-interior-v1`: `bg02_forest`, `bg03_sanctuary`（main＋fore）、`bg01_foreground`（BG-01 fore） | 約8 | 戦闘背景 BG-02/03 と BG-01 前景。`feat/bg02-bg03-prep-claude` は準備段階（index.html 未接続）。`battle-background.js` は BG-01 のみ割当、`fore:null`（前景は「未制作」と記載） | **納品済み・未実装・採用記録なし**。BG-01 前景は納品物があるのに本編コメントが「未制作」のまま → 要確認 |
| その他（title/goblin field 等） | 残り | WIP・テスト保留 | 採用確認まで保留 |

## 5. 結論と次のアクション
- **正式採用済みで未実装の素材: 検出なし（0件）**。したがって今回は追加の実装・統合は行わない（候補素材を無断で採用に変えない）。
- オーナー判断が必要な**納品済み・採用記録なしの候補**（採用指示があれば順次実装・統合）:
  1. 戦闘背景 BG-02（森）/BG-03（聖域）と BG-01 前景（どの敵・どの場面に割り当てるかの指示が必要）。
  2. モスの封印／宝箱きらめき FX 12枚。
  3. Aidan 斜め歩行プール（2.5D 試作と関係）。
  4. リルド屋内 v1 タイル。
- 引き続きの照合（第2回以降）: main 上の707件は導入コミットを台帳 `notes` に記録済み。Issue/ハンドオフに採用の記述が見つかった素材から、証拠つきで APPROVED へ更新する。

## 6. 主な導入コミット（main・UNKNOWN の大半）
| 領域 | 件数 | 導入コミット（日付） |
|---|---|---|
| `moss/rilde` | 213 | 0761744 Rilde Village main-story integration（10/11） |
| `moss/props` | 100 | M9 weather/canopy（10/11） |
| `lind/npc` | 83 | Lind NPC idle + 6-frame walk（10/10） |
| `moss/art` | 68 | Moss delivered art intake（10/12、コミット名に WIP/unmerged、現在は main 収録） |
| `moss/town` | 38 | Dunvall Fort / Royal Capital 29 props（10/11） |
| `moss/real` | 32 | M9 Fiona field sprite 等（10/11） |
| `field/characters/aidan` | 30 | Aidan A1 standalone sprites（10/09） |
