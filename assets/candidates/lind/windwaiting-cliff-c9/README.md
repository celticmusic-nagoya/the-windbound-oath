# 風待ちの崖 C9 制作候補

Draft PR #421。基準コミット `e8bb0f91467d364a27f9c2f4943e04678c88e872`。2026-11-19 に main の制作規約と非公開正本を照合。ここでの評価対象は仮ローカル座標の造形・材質候補。

| 工程 | 編集可能な原本 | 証跡 |
| --- | --- | --- |
| C9-A 岩盤 | [Blender](C9-A/windwaiting_cliff_C9-A_UNAPPROVED.blend) | [正式CGとの比較](C9-A/comparison.png)、[構造QA](C9-A/qa.json) |
| C9-B 材質 | [C8＋新PBR](C9-B/B_UNAPPROVED.blend)、[C9-A＋同一PBR](C9-B/C_UNAPPROVED.blend) | [固定条件のA/B/C比較](C9-B/comparison.png)、[素材台帳](C9-B/cc0_manifest.json)、[再オープンQA](C9-B/qa.json) |

C9-A は C8 の A/B/C を保持し、B のローカル岩面を輪郭と深さを別々に指定した5つの領域で編集した。編集頂点は `C9 edited rock face` 頂点グループに収録。追加の岩礁12点は4つの欠損直下に分け、編集できる実メッシュとして別コレクションに収録した。C8の既存岩礁と層理、C7由来の岬配置、85頂点の接続は継承した。

C9-B の比較 A は C8＋従来材質、B は C8＋新PBR、C は C9-A＋同一新PBR。カメラ・照明・解像度は条件ごとに固定。Poly Haven CC0 1024² の5マップをパックした。水際は高さで暗色・低粗さを制御。草土の変化はプロシージャル。岩面のGLノーマルと岩礁のバンプはシェーダーのみで、形状とUVはPBR処理前後で一致した。

**仮座標**。原点と変換はC8から継承。+Xは沿岸、−Yは沖、+Zは上。Z=0は仮海面。実寸と正式マップ配置は未承認。境界とローカルバウンドは [構造QA](C9-A/qa.json) を参照。

**表示ビュー**。[低視点](C9-A/cg_review.png) · [正面](C9-A/front.png) · [左](C9-A/left.png) · [右](C9-A/right.png) · [俯瞰](C9-A/elevated.png) · [水際](C9-A/shore_detail.png) · [夕景](C9-A/sunset.png) · [低視点の無地版](C9-A/cg_review_clay.png)。

## ゲート

| 項目 | 判定 | 根拠 |
| --- | --- | --- |
| G1 正本整合 | BLOCKED | CG・C8・素材のSHA、素材ライセンス、候補区分を照合。正式縮尺・配置は未承認。 |
| G2 独立美術QA | FAIL | 独立レビューおよび試行記録を参照。 |
| G3 構造・ファイル検証 | PASS（候補の検査範囲） | Blender 5.2.4、再オープン、3タイルの閉鎖・非多様体と自己交差の検査、85頂点とUV・法線、遷移傾斜、PNGデコード、SHA、パック画像を確認。海底接地や別メッシュ相互の交差は対象外。 |
| G4 ゲーム統合 | NOT_RUN | WebGL・Android・正式マップ接続は別工程。 |

[参考資料と利用条件](observations.md) · [独立レビューと試行履歴](art-qa.md)

## 再現

GitHub Actions run [44067700909](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44067700909) の `lind-cc0-rock-component-candidates` を別ディレクトリへ展開する。Blender Python `bpy==5.2.4`、Pillow、DejaVu Sansを使用。C8の原本と承認済みCGはSHAを照合する。次の `C8`、`CG`、`INTAKE` はそれぞれ原本、CG、素材展開先の絶対パス。

```sh
python scripts/sculpt_c9.py "$C8" "$PWD/C9-A"
python scripts/pbr_c9.py "$INTAKE" "$C8" "$PWD/C9-A/windwaiting_cliff_C9-A_UNAPPROVED.blend" "$PWD/C9-B"
python scripts/compare_c9.py "$(dirname "$C8")" "$CG" "$PWD/C9-A" "$PWD/C9-B"
python scripts/qa_c9.py "$PWD/C9-A/windwaiting_cliff_C9-A_UNAPPROVED.blend"
python scripts/qa_pbr_c9.py "$PWD/C9-B/cc0_manifest.json" "$C8" "$PWD/C9-A/windwaiting_cliff_C9-A_UNAPPROVED.blend" "$PWD/C9-B"
```
