# MORWEN PR419 — quad patch再構築01（未達・停止）

## 結論

実際の局所トポロジー置換、原本保存、4方向・局所・ワイヤー・屈曲render、保護検証、独立美術QAまで実行した。必須条件は未達。G2 FAIL／局所G3 FAILとして、この候補を正式採用せず造形の再試行を停止した。旧全身cage・局所fairingは実行していない。

## 入力・警告分類・境界

入力はbody-local-v01/MORWEN_BODY_LOCAL_SURFACE_V01_UNAPPROVED.blend（de6233e時点）。正本／既存原本は変更なし。既存Layer0四方向と独立QAを使用し、画像取得・SHA照合・素体download・参照scene再生成は行わない。

独立調査で旧cage比の新規法線警告15件を再現。全件が肩・側胸・上腕側のfree面で、膝0、中央胸頂点0。単なる90°閾値越えだけの例と、面積圧縮／大きなdihedralを伴う例を区別した。face10002は面積比約0.247・隣接dihedral約166.1°、10059は面積比約0.156・dihedral約100.2°。face10057は86.8→98.8°と閾値を跨ぐが、これだけで自己交差とはしない。位置・角度・面積・穿通pair一覧はINDEPENDENT_WARNING_ANALYSIS.md/json。

独立のBlender loop三角化／旧free領域screenでは非隣接実穿通59組（うち前方式から新規23）。このface集合と15警告をseedにdual graphで領域を選び、肩腋は左右2disk、膝前面は左右2diskとした。

|patch|旧面|境界edge数|新quad|新triangle|
|---|---:|---:|---:|---:|
|肩腋L|135|84|136|38|
|肩腋R|132|72|130|38|
|膝前L|240|68|176|24|
|膝前R|240|68|180|18|

全patchは1閉loopのdisk、全て旧free面内。混合境界面や保護中央胸を削除しない。

## 新方式と実置換

境界を旧頂点のまま保持し、harmonic UV domainに新しい内部点を配置した。旧rest面と現在境界の差を用いたrest-rail補間、膝蓋骨／膝蓋腱の局所起伏を作り、新三角化から四角面を組み合わせた。2D quadの凸性だけでなく3D first diagonal整合も候補選別に使ったが、後述の両対角線／穿通検査には不合格だった。

これは旧頂点の平滑化ではなく、747旧面を削除し740新面（622quad、118triangle）と535新頂点を構築した実retopology試作。601旧内部頂点を退役し、総頂点12,502→12,436、総面12,500→12,493。新patchのquad比率は84.1%、全体はquad12,375＋triangle118。これだけで解剖学的な面の流れを達成したとはしない。

stable属性RB_SRC_VID／RB_SRC_FID／RB_PATCH_IDで対応を保存。保護9,080頂点、存続した旧11,901頂点のlocal座標は完全一致。外部11,753面のsource-ID頂点列とUVを完全保持。境界edge0、非多様体edge（3面以上共有）0、loose vertex0。旧原本、改善済み胴体、頭・手・足はrest状態で維持。

## 必須条件の判定

|条件|結果|
|---|---|
|新規警告15件解消|FAIL：13/15が追跡sampleで閾値内、2件残存|
|肩幅精度維持|測定上維持：誤差2.333→2.333px|
|膝幅精度維持|誤差4.268→4.318px、差0.05px（参照不確実性以下）|
|胸・腰・骨盤外形維持|同じ対応bandの測定値不変|
|保護形状／外部topology／UV|限定screen PASS|
|自然な局所解剖・面の流れ|独立G2 FAIL、前段階より悪化|
|自己交差・quad形状|FAIL|
|屈曲変形|診断fixtureでFAIL、本番rig未実装|
|編集可能原本・実render保存|完了|

### 警告をID削除で消したことにはしない

旧15面のfirst triangleを各4点のbarycentric座標で取り、旧harmonicUVを介して新しい実三角面上へ追跡した。元source法線との角度を再測定し、全sampleが90°以下の場合だけその旧領域を閾値内とした。旧face IDの削除だけで解消扱いしない。

未解消は3859（最大約114.9°）と10002（最大約92.1°）。13領域の閾値内という結果も、全体の解剖品質や自己交差の解消を意味しない。

### 交差と面の連続性

同じ固定fan三角化を用いた厳密segment-triangle内部穿通screenでは、置換領域に関わる非隣接polygon-face pairは56→89組、候補patchに関わる隣接face内部穿通は別に9組。coplanar面積重複screenは0。独立初期調査の59はBlender loop三角化＋旧free領域という別scopeなので56の代用にしない。

両quad対角線の三角法線整合検査では新patch27面にfold flag。接続が閉じていることと、実3D面が折れていないことは別である。最初のtriangle-level集計98には隣接face9組を含んでいたため、非隣接89／隣接9へ分離して記録した。角度やquad flagだけで反転／穿通は断定せず、実穿通結果も併記する。

### 屈曲テスト

肩30°/60°、膝45°/90°の診断rotation-weight shape keysを保存しrenderした。本番armature・ウェイト・アニメーションではない。rest Basis不変、保存時の4キー値0を確認。

|pose|patch非隣接穿通pair|patch quad fold flag|
|---|---:|---:|
|肩30°|42|23|
|肩60°|42|34|
|膝45°|89|27|
|膝90°|89|32|

肩の初回診断selectorが腰／上腿を誤って含む設定不具合を検出。初回JSONと代表PNGをinitial-diagnostic-setupに保持した。腕membershipと60°撮影範囲だけを訂正し、rest geometryを変えず肩4PNGを再検査した。腰誤weightは解消したが、腋webbingが残る。診断weight自体は本番向け未検証なので、patch要因とweight要因を分ける。修正後も屈曲acceptanceはFAILであり、適切なrig品質を認定しない。

## 独立美術QA

別AI reviewerが元／変更原本を独立再openして置換・保護・rest不変を確認し、四方向・拡大・実polygon wire・訂正後診断poseを確認。肩frontの放射状ridge／深い腋溝、膝frontのcheckered faceting／profileの三角状折れが、前段階より改善せず悪化したと判定。局所解剖G2 FAIL／全身G2 FAIL。技術screenの部分成功を美術合格にしない。

## 成果物

assets/candidates/morwen-rebuild-01/body-quad-v01/MORWEN_ANATOMICAL_QUAD_PATCH_V01_UNAPPROVED.blend（診断4キー付き）。同directoryにrest4方向、局所5、旧／新polygon-wire6、屈曲8の計23PNG。

docs/qa/morwen-rebuild-01/body-quad-v01/: 独立warning調査と美術QA、quad-patch-recipe.json、旧／新mesh記録、UV対応追跡JSON、保護QA、交差・屈曲QA、比較5PNG、測定CSV、実行log、失敗診断設定の原記録。

## 根本原因と停止

このharmonic-domain／rest-rail自動quad再構築方式の初回がFAIL。細長く折れた腋境界と現在poseの強い変位を、円盤domainと境界補間で接続しても、3Dの自然なedge-flow／局所Jacobianを保証できなかった。2D convex quadの組合せは両3D対角線整合を保証せず、膝のgridも膝蓋骨–腱の流れに沿っていない。

ユーザーの「品質未達の場合は原因と証拠を記録して停止」に従い、geometry候補を固定後は検査と証跡収集のみ実施。パラメータ変更で再試行していない。旧cage2FAIL/STOP、局所fairingの再試行禁止も維持。

必須完了条件未達。次に必要なのは、この自動disk再構築の調整ではなく、3D解剖guideと意図的な境界方向／loop配置を持つ作者制御patchの再設計である。本タスク内で追加造形は行わない。身体G1は既存PASS維持、G2 FAIL、局所G3 FAIL、全キャラクターG3未認定、G4 NOT_RUN。正本置換・mainmerge・公開・正式採用なし。
