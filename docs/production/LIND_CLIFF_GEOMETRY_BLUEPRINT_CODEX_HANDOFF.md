# 風待ちの崖｜Geometry-to-Blueprint / Codex 実装引き継ぎ v0.1

Status: TECHNICAL SPEC / UNAPPROVED BLUEPRINT / NOT A CANON CHANGE
Owner: map team, existing Draft PR #421; no new PR, no main merge.
Input: C9-B `assets/candidates/lind/windwaiting-cliff-c9/C9-B/C_UNAPPROVED.blend`; C10 script `assets/candidates/lind/windwaiting-cliff-c10/sculpt_c10.py`; latest C10 Actions artifact (SHA-verified). Consult main `AGENTS.md`, `docs/production/SESSION_CONTINUITY_INDEX.md`, private canonical refs, and approved cliff CG before drawing conclusions.
Known QA: C10 topology-only PASS (4 masses, 51 vertices / 36 faces each, no boundary/non-manifold/degenerate edges); independent visual G2 FAIL (visible diagonal green seam, abrupt rock junction, repetitive bands); G1 canonical CG comparison BLOCKED; G3 PARTIAL; G4 NOT_RUN.

## Objective and design principle
Create an **inspectable, numerical production blueprint** from the *actual* editable Blender scene, not a collection of separately hallucinated orthographic images. A blueprint may specify intended landmarks and geometry changes but never assert candidate geometry is canon-approved. Preserve the original .blend and all source hashes. Provisional local coordinates are permitted; world transforms remain pending.

## Codex task 1 — read-only extraction
Use `tools/production_qa/lind_blueprint/export_blueprint.py` with Blender 5.3.0. Supply an output directory, a locked input SHA, and a provenance reference as shown below. Do not save/mutate input .blend. Produce deterministic, versioned `scene.json`, `mesh.json`, `materials.json`, `landmarks.json`, `manifest.json`, and `qa.json`. JSON must be sorted/stable and use documented coordinate convention, float precision and Blender version.

- Objects: persistent names, type, collection hierarchy, world/local 4x4 transforms, bounds, parent links, visibility, modifier stack and evaluated/non-evaluated geometry flag.
- Meshes: vertex IDs and local/world XYZ; edges with vertex pairs, seam/crease/sharp attributes when present; polygons with ordered vertex IDs, loop IDs, face material slot, normals, area and smoothing; UV per **face corner/loop** including island/seam metadata; custom attributes and vertex-group weights where present. Record evaluated mesh separately; never conflate sculpt cage and evaluated render geometry.
- Diagnostics: zero-area faces, loose vertices/edges, boundary/nonmanifold edges, normal orientation, duplicate faces, disconnected components, self-intersections and inter-object intersections when computationally feasible. Mark expensive/unavailable tests NOT_RUN, never PASS by omission.
- Materials: material slots, node graph types and socket links, image dependencies and SHA-256/license/provenance when known; do not invent licensing. Distinguish texture color space and missing images.
- Render contract: renderer, resolution, samples, color management, transparent/world settings, all seven named cameras with type, lens/ortho scale, clipping and transforms, lights with types/power/color/transforms, compositor settings and render seed if used.
- Landmark candidates: rock boundary, crest, central overhang, grass-rock transition, shoreline, road/walkable edge; record actual measurable coordinates separately from proposed art-director targets, with `source` and `confidence`. Unknowns = null / BLOCKED.
- Manifest: source and output SHA-256, input Git commit, provenance, status UNAPPROVED, generator version, runtime Blender exact version, dependencies.

## Codex task 2 — views and cross-view validation
Generate **six orthographic engineering views** (front/back/left/right/top/bottom) from the same evaluated geometry with world-axis labels, a provisional local coordinate grid, bounding dimensions, feature IDs, and a separate camera map. Also output existing seven production camera renders for visual comparison without modifying their positions. Produce vector SVG overlays for silhouette, landmarks and callout indices; heavy per-vertex data stays in JSON, not text printed on image. Provide face-ID/vertex-ID detail sheets only for selected rock junction regions. Do not infer hidden/backside shape from a single CG.

## Codex task 3 — reconstructibility QA
Write a read-only round-trip test: export mesh and scene, reconstruct in a temporary scene, compare topology counts, per-vertex positions (declared tolerance), face connectivity/winding, material assignments, UV loops, transforms and camera matrices. Run at least one fixed-view pixel comparison with documented engine and tolerance, distinguishing nondeterministic shading. A `rebuild.py` may be generated only after round-trip test demonstrates equivalence. Explicit QA statuses: G1 BLOCKED until canon comparison, G2 FAIL until independent art review, G3 PARTIAL until full checks, G4 NOT_RUN until game integration.

## Acceptance / stop conditions
1. All seven existing cameras and six new orthographic views reference **one source scene**.
2. Deterministic JSON hashes on two identical runs, except explicitly excluded timestamps/paths.
3. Complete vertex/edge/face/loop counts; UV and PBR data accurately attributed; source untouched.
4. Report source-vs-reconstructed maximum positional delta, winding/loop mismatches, missing textures and failed tests; no false PASS.
5. No production model sculpt, source overwrite, new PR, main merge, official adoption or game deployment in this first extraction stage.
6. Stop on missing canonical source only for dependent decisions; independent mesh extraction proceeds.

## Following phase (separate from extraction)
Art director compares actual orthographic geometry and official CG; defines a **measurable** landmark/shape target. Codex then implements a genuinely different local sculpt/integration method for the central junction, preserving C9/C10. Independent G2 reviewer compares fixed-camera render pairs and records PASS/FAIL before extending to entire cliff.

### Initial handoff status
Extraction scripts, blueprint JSON/SVG, reconstruction and new renders were **NOT_RUN** when this work order was created. Subsequent execution evidence follows.

## C9/C10 実メッシュ検証と中央接合部レビュー

C9-B の入力は `C9-B/C_UNAPPROVED.blend`（SHA-256 `886ad8d4d49b3951da84bf2b728505767bef2f8b4288d9472ac0c129a018d12a`）。C10 は [Run 44627719888 / Artifact 14580687938](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44627719888/artifacts/14580687938) の `windwaiting_cliff_C10_UNAPPROVED.blend`（SHA-256 `8d0618ddd9db7562492e94477503ed53b621e908d88ab34c7bd07afb0c159223`）。正式CGは `assets/approved/game/cliff/sunset_background.png`（SHA-256 `db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07`）。入力原本と正式CGは読み取り専用。図面の長さは仮の Blender unit。

[Run 44636490321 / Artifact 14584297407](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44636490321/artifacts/14584297407) で Blender 5.3.0 を実行。二重出力は C9/C10 ともファイル単位で一致。座標とUVは許容差 `1e-6` 以内。A/B/C タイルでカスタム法線の再エンコード誤差が最大 `0.000479856`、固定 EEVEE `cg_review` で最大 `2/255`（許容 `1/255`）で FAIL。JSONの法線ベクトルを再エンコードする方式を終了し、対象タイルは `master.blend` に保持する法線の内部表現とコーナー順序を使って座標・UVを復元する。

| 対象 | 実画像の所見 | 次の制作で検証する変更 |
| --- | --- | --- |
| `Cliff C8 B \| joinable coastal segment`、`C10 large rock 02`、`C10 large rock 03` | C10の低視点で、左寄りの突出部に斜めの緑の帯が走る。正面と水際で、横に長い棚が中央の短い段差に急接続する。正式CGの岩壁には不揃いの縦の切れ目と重なりがある。 | `landmarks.json` の対象の頂点IDと断面の面IDから接合域を選ぶ。暫定探索範囲は X 約 −10〜−3 BU、Z 約 0.5〜6.1 BU（C10の作成パラメータ由来）。Y と境界ループは出力座標に基づいて決める。 |
| 草地縁と亀裂 | C9/C10の草地縁は遠景まで連続し、中央だけが急に折れる。現行材質は法線と高さを使うため、緑の帯はマテリアルスロットの境界だけでは追えない。 | 地形上端・岩盤面・深い亀裂の戻りを、境界ループに縫合する一枚の局所面として構成する。草地の接合線を別途測り、幅・傾斜が急変する区間を確認する。 |
| 水際・道路・探索空間 | 候補の水際には柱状の独立岩が目立つ。カメラの登録と正式配置が未確定で、道路や歩行可能面の整合は未判定。 | 局所編集の範囲では海岸線と既存歩行側の頂点をロックし、正式座標に基づく配置・衝突・経路検査を別のゲートに記録する。 |

次の局所候補では、載せた岩塊を再度変形する方式を止め、キャリアの対象面を境界を維持した置換パッチにする。仮説は、地形の稜線と亀裂を同じメッシュで接続すれば、低視点の斜めの緑線と急な境界を抑えながら前後の岬の視認性を維持できること。成功条件は、置換パッチの境界差分が `1e-6 BU` 以下、新規の非多様体・退化面・自己交差がゼロ、C9の低視点の近中遠可視基準 `10/4/13` を下回らず、同カメラのカラー・無彩色画像で独立レビューが接合の改善を確認すること。境界破壊、可視数の低下、または独立G2で同じ接合欠陥が残る場合は拡張を停止する。

[Run 44637577247 / QA Artifact 14583663674](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44637577247/artifacts/14583663674) の記録を展開し、図面とJSONのSHAを確認。固定画像は C9/C10 とも `780×494`、全チャンネル差ゼロ。キャリア B および C10 岩盤は数値往復 PASS。外側 A/C の法線差の最大値は `1.58e-6` で、全体往復は FAIL。入力座標を固定小数点桁で丸める処理を廃止し、Blender値をJSONから同じ浮動小数点値に復元する方式を Run 44638743443 で検証する。

中央断面の実測平面は `X=-7.903945208 BU`。岩盤 02 の沖側極値は頂点 26 `(-6.767872334, -6.136016846, 4.554579258)`、岩盤 03 は頂点 33 `(-5.883973122, -5.038241863, 2.515624285)`。BVHの三角形接触は 02↔B が484（262面ペア）、03↔B が933（538面ペア）、02↔03 が12（7面ペア）。02の非隣接自己接触は1。面IDは `qa.json:junction_intersections.pairs` に収録。体積の包含と、共有頂点を持つ三角形間の自己接触は対象外。

中央の実造形は、元の輪郭を押し出す方式から、連続しているキャリア B 本体に方向と深さが異なる二つの亀裂を切り込む方式へ切り替えた。別候補上で独立岩盤 02/03 を非表示とし、正確ブーリアン差分でキャリアの逆斜面を形成する。原本はSHA保護する。変更を許す外周は実測値に基づく `-9.0 ≤ X ≤ -4.9 BU`。可視性 `10/4/13`、外周頂点、キャリア閉鎖、退化面、局所の自己接触を検査し、固定低視点・正面・水際・無彩色の比較を保存する。独立 G2 は候補の実レンダリングを受領後に実施する。

### ローカルでの再実行

Blender 5.3.0 と、照合済みの原本への絶対パス `SOURCE`、台帳の `SOURCE_SHA`、原本の来歴 `INPUT_REF`、未作成の出力ディレクトリ `OUT` を使う。EEVEEに対応した環境で次を実行する。Linux CI は既存のソフトウェアGLと `xvfb-run` を使用する。

```bash
TOOLS=tools/production_qa/lind_blueprint
blender -b --disable-autoexec "$SOURCE" --python-exit-code 1 \
  --python "$TOOLS/export_blueprint.py" -- "$OUT" \
  --source-sha "$SOURCE_SHA" --input-ref "$INPUT_REF" \
  --texture-register assets/candidates/lind/windwaiting-cliff-c9/C9-B/cc0_manifest.json
blender -b --disable-autoexec --python-exit-code 1 \
  --python "$TOOLS/rebuild.py" -- "$OUT" --render
```

`master.blend` は入力とバイト一致する編集用コピー。再構築ではそのネイティブ材質・モディファイア・シーン設定を参照し、JSONから座標・UV・トポロジーを再現する。カスタム法線を持つメッシュではネイティブのコーナー順序と法線の内部表現も保持する。JSONの頂点・辺・面・ループのIDは0始まり。図面は画面上の各方向の射影に、断面は指定したX平面と評価後三角形の交線に基づく。海面は工学図面の表示範囲から除き、シーンとメッシュのJSONに収録する。

### Blender 5.3.0 の最終往復結果

[Run 44638743443](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44638743443) の C9（124,673頂点・248,112辺・123,617面）と C10（124,877頂点・248,452辺・123,761面）は、原本と評価後の双方で座標・コーナー法線・UVの最大差がゼロ。接続・面の向き・材質・シーン設定の検査、二重出力のファイル比較、固定 `cg_review` 画像（780×494）の画素比較が PASS。G3の総合判定は、全シーン交差・テクセル密度・汎用属性の復元範囲が残るため BLOCKED。

- [全設計図・JSON・Blender・固定画像 Artifact 14584513706](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44638743443/artifacts/14584513706) SHA-256 `fbc393922d2b0954edcb09983493d0e9f15390d8a7a549fa7803d7f7b1ada684`
- [確認用の小容量 QA Artifact 14586635022](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44638743443/artifacts/14586635022) SHA-256 `7dac1c4c25430d52015a92c36c36ac5e79462deeb79100746ba5c1eedf14f4b6`

### 中央切削試作の停止記録

[Run 44639234123 / Artifact 14585742052](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44639234123/artifacts/14585742052) で実造形と4枚のレンダリングを実行。ZIP SHA-256 は `d0fb1933530b76c4ca4da8053da53937040fa3c7b47d8fe787bf40cafe218a14`。編集可能な `junction_UNAPPROVED.blend` の SHA-256 は `e363269d37c29bc02463247c70408ef8c2275dc673a285c72f3b4c1a54818c14`。ZIPと収録出力のSHAを展開後に照合済み。

仮範囲外の差分頂点ゼロ、開境界・非多様体辺・退化面ゼロ、低視点可視数 `10/4/13`。低視点の斜めの緑線は軽減したが、水際の長い横帯と中央の垂直段差は残る。局所の非隣接三角形自己接触が `0 → 2` に増え、G3 FAILで拡張を停止。C10原本のG2は過去の独立レビューでFAIL。切削試作の独立G2はNOT_RUN。比較ファイルを独立レビュー用に保存した。

次は切削試作の局所自己接触2組を面ID付きで抽出し、接触箇所を含む面だけを境界固定で再トポロジー化する。再実行条件は新規自己接触ゼロ・外周頂点差ゼロ・可視数 `10/4/13` 以上。固定カメラの比較で改善が維持できた候補を独立美術レビューに渡す。

## v2.0 中央岩盤の局所リトポロジー

担当は環境3D制作 Codex、既存 Draft PR #421、`feature/lind-cliff-rock-art-study-20261118`。指示基準と着手時HEADは `ac033fa005150da3cd133976254a329d381e62dc`。新候補の実行コミットは `4a4b7c329be4ed47d0ccecc7e2f92277a65a6a16`。正式CG・C9-B・C10の原本と採用区分は上記台帳に従う。作業座標は仮BU。

- [面ID監査 Run 44642587402 / Artifact 14587586465](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44642587402/artifacts/14587586465)。保護入力は切削試作 `junction_UNAPPROVED.blend`、SHA-256 `e363269d37c29bc02463247c70408ef8c2275dc673a285c72f3b4c1a54818c14`。接触候補は面8518・37372。三角形17073↔75164と17073↔75168の平面交線上で、長さ0.00291762166と0.00692991652 BUの重複を確認した。判定許容差は `1e-7 BU`。面37372は切削側の47頂点面で、隣接する折り返しをまたぐ三角分割が局所交差を生んでいた。
- 既存頂点37429–37430を結ぶ対角線を拘束し、面37372だけを45三角形に分割した。キャリアBの頂点数は37,720のまま、面数は37,386→37,430。自己接触は2→0、外周47頂点の座標差は0、近・中・遠景の可視数は10/4/13。開境界・非多様体辺・退化面は0。変更面のUVと材質割当、周囲の面接続・UV・材質・コーナー法線を照合した。
- [実形状・設計図・ログ Run 44643792489 / Artifact 14587169190](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44643792489/artifacts/14587169190)、ZIP SHA-256 `a72e8dfefb2d1f159885ca0c79bd0dc15118c4853e5cda5948163130994ea2e4`。候補と `master.blend` のSHA-256は `056ba4a3f672dde75a9f129af8486f547c3971ad41cd6cee1dc360b275591f2c`。全設計図は125,112頂点・248,715辺・123,789面。二重生成一致、188メッシュ検査、座標・UV・コーナー法線の最大差0、780×494固定EEVEEの画素差0。ネイティブ属性と材質は `master.blend` を使用。
- [比較・断面・局所QA Artifact 14587134163](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44643792489/artifacts/14587134163)、ZIP SHA-256 `543c8a0c594c86e60336fc819c5a1e582ce911527b5303cb08dcc841112e1b3a`。固定低視点、正面、水際、上方、無彩色、差分画像、3断面と外周頂点照合を収録。切削試作→リトポの固定表示差は2ピクセル、最大1/255。これは局所交差の修正として評価し、広域造形の改善は独立に判定する。
- Run 44643037944 はレンダリング環境準備中に打ち切り、造形試行は未実行。幾何出力とレンダリング準備を分離し、利用可能なランナーのMesaを再利用し、不足時だけ制限時間付きで導入する。再実行は同ワークフローの対象ファイル差分で選択し、入力ZIPとBlenderのSHAを照合する。

### v2.0 独立美術QAと継続条件

独立レビュアーが正式CGとC10原本・新候補の固定カメラ、正面・水際・上方、候補の無彩色レンダーを個別に目視した。**G2 FAIL**。手前中央の三角形状の草地の垂れ込みはC10原本から改善し、岬の並びは維持された。手前稜線の急な段差と直下の丸い張り出し、中央から右奥へ続く平行な横帯が残る。草際は広範囲で薄く均一で、亀裂の奥行きと岩塊の厚みは正式CGの読みへ未達。正式CGは別のカメラと照明のため、造形の比較に用いた。

G1 BLOCKED（正式縮尺・配置・CGカメラ未登録）、G2 FAIL（独立目視）、局所・再構築G3 PASS、総合G3 BLOCKED（全シーン交差、テクセル密度、汎用属性の全量復元は別途検証）、G4 NOT_RUN。既存QA JSONのG2 NOT_RUNは機械ジョブ終了時点の記録。

次は再現性を確認した候補を基準に、キャリアBの手前から中央を覆う主要岩塊の厚みと縦の破断面を精密メッシュで一体造形する。局所面の再分割は交差解消のために完了し、横帯・稜線の改善は新たな造形工程とする。開始条件は固定カメラと保護外周を再照合できること。継続条件は局所交差ゼロ、外周頂点差ゼロ、可視数10/4/13以上、固定低視点と無彩色で横帯の途切れ・岩塊の奥行き・草際の不規則さを独立QAが確認すること。

## 手前〜中央岩盤の造形候補

担当は環境3D制作 Codex、既存 Draft PR #421、`feature/lind-cliff-rock-art-study-20261118`。着手時HEAD `27b43b47dde64e48730eddf38819a0a98d27d2eb`。入力は上記の再現性確認済み `junction_retopo_UNAPPROVED.blend`（SHA-256 `056ba4a3f672dde75a9f129af8486f547c3971ad41cd6cee1dc360b275591f2c`）。正式CG・原本は上記台帳のまま。仮ローカルBU、作業範囲は `-13 < X < 1.15`、前回確定した亀裂の保護帯 `-8.10 ≤ X ≤ -7.50`。入力ArtifactのZIPとBlenderのSHAを照合する。

実装は `tools/production_qa/lind_blueprint/sculpt_bedrock.py`。23か所の制御断面で岩盤の前後差と層の高さを変え、左右で傾きの異なる縦の戻り面を既存の連続メッシュ上に作る。足元と内陸側に変形を減衰させる。色・材質、カメラ、照明を固定する。評価条件は作業範囲の自己交差ゼロ、保護頂点の変位ゼロ、近・中・遠景の可視数10/4/13以上、再構築一致。美術判定は固定比較、正面、水際、上方、無彩色で行う。

- Run 44647954488 は生成前の出力ディレクトリ競合で停止。既存ディレクトリを使用する修正で実造形を開始した。
- [初回実造形 Run 44648236036 / 全成果物 14590271090](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44648236036/artifacts/14590271090)。9,621頂点を変更し、28,099頂点を固定。最大変位はY 0.49095、Z 0.35532 BU。可視数11/4/13、開境界・非多様体・退化面ゼロ。二重出力・座標・UV・コーナー法線・固定カメラ画像の再構築結果が一致。一方、上端の45頂点面37383と面10434で真の交差1組が生じ、G3 FAIL。交線区間は0.0788399 BU。候補SHA-256 `4359aafc33007745b5da41dc43fb9a2dc8795c4c8f70d228b586ee4b783821d4`。
- [初回の独立目視用資料](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44648236036/artifacts/14590740646)。独立G2 FAIL。手前中央の縦割れと局所的な草際の凹凸は改善。最前部の尖った稜線と丸い張り出し、海側中央〜右の長い横帯、厚い岩塊の重なり不足が残った。違いが確認できる部位は固定低視点の左寄り。
- 再試行 `3858748` は制御断面や変位量を維持し、測定済み上端面37383の入力時点の43三角形を明示的な面に固定してから造形する。変形後に長い多角形が別の対角線で自動分割される原因を取り除く。安全停止条件は新規局所交差、保護頂点の変位、可視数の低下。
- [再試行 Run 44649866738 / 全成果物 14590827331](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44649866738/artifacts/14590827331) は成功。候補 `bedrock_wall_UNAPPROVED.blend` と `master.blend` のSHA-256 `a88fd51546a31242e2e63a423988548ed253e4831c501aae430713eac406d334`。全パッケージZIP SHA-256 `a4741a790c76af4c37fc45c8fff7d727bad5670c910fbe802140024d7fb0826f`。キャリアBは37,720頂点・37,472面、保護28,099頂点の変位ゼロ。作業範囲と確定済み亀裂の自己接触0、開境界・非多様体・退化面0、可視数11/4/13。全設計図は125,112頂点、248,757辺、123,831面。二重生成一致、座標・UV・コーナー法線・固定EEVEE画像の再構築差0。
- [再試行の確認用資料 14590631976](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44649866738/artifacts/14590631976)。ZIP SHA-256 `1e11a7d62b3425b122ad3f3815f5041b9e51660c1b937ed7bf9d8b6ff6c97e3b` をダウンロード後に照合。初回造形から再試行への固定低視点の最大RGB差は1/255、他方向・無彩色も最大2/255。入力リトポ候補からの形状変更と再構築差は別計測。
- 独立レビュアーは再試行の固定・正面・水際・上方・無彩色を再度目視し、**G2 FAIL** を維持。再試行による新たな目立つデグレは確認されず、縦割れと草際の改善は維持された。尖った稜線、丸い棚、中央から右に続く横帯、岩塊の厚み不足が次の対象。G1 BLOCKED、局所・再構築G3 PASS／総合G3 BLOCKED、G4 NOT_RUN。正式採用前の候補として保存する。

次は、固定低視点で最前部の草の稜線（画像X約275 px）直下の丸い張り出しを対象とする。頂面から裾へ続く深い破断面で二〜三の岩塊を前後に構成し直し、破断面で横棚を止める。開始時は保護帯と外周の頂点対応を照合し、交差ゼロ、外周変位ゼロ、可視数10/4/13以上を維持する。固定カメラと無彩色で頂面〜裾の連続した破断面、段差と横帯の変化を独立美術QAで評価する。
