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
