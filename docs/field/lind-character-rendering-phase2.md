# Lind Character Rendering Phase 2 — PLAYER QA

RESULT: **PASS WITH WARNINGS**（技術QA。画質とEmmaの正式採用はPLAYER QA待ち）

START MAIN: `d3e299ac7ca90eb49629570a57a90ff678ad7591`

SOURCE HD BRANCH: `work/lind-character-hd-audit` / `bc376392576679008fa8b0b441e0906b33f58c41`

BRANCH: `work/lind-character-rendering-phase2`

IMPLEMENTATION COMMIT: `b362c7e`。FINAL COMMITはこの文書を含むブランチHEAD。

mainとの差分を監査し、前回HDの3実装ファイルと監査資料だけを継承するHDブランチをbaseにした。Overnight監査ブランチ、Battle Motionブランチは取り込まない。
mainへのmerge、mainへのpush、Pages deployは行わない。全production PNGはmainと同一。

## PLAYER QA操作

DEV → リルド村 · 素材仮配置 → プレイヤー表示をAidan A1にする。

- **キャラクター画質（試験）**: Original / Smooth HD / Crisp HD
- **適用対象（試験）**: Aidan／Emma／農夫 / 全キャラクター／NPC
- **Emmaの生活動作（試験）**: CURRENT / NATURAL / ACTIVE
- **フィールドカメラ倍率**: 1.00 / 1.50 / 1.80 / 2.10で比較
- **素材確認場所**: Emma、農夫、釣り人などへ移動

ページ読込時はOriginal・代表3actor・CURRENT。Camera初期1.00、全17倍率1.00–2.10は維持。選択は試験ページ内のみで、saveに書かない。
NATURALは推奨比較候補であり正式採用ではない。main/公開Pagesにはこの試験UIは追加されていない。

## CRISP HD IMPLEMENTATION

Root cause of Aidan blur: native resolution不足と断定できない。1536×1024の元画像がPC camera1.80では画像全体約160×107 CSS pxに縮小される。
PNGの透明余白も含む寸法であり、キャラクター本体の寸法ではない。画面座標・camera倍率・DPR・縮小サンプリング・合成レイヤーの組合せを比較する。

image-rendering: Originalは既存どおり（Aidan auto、NPC pixelated）。Smoothはauto＋Aidan表示フレームのwill-change:transform。
今回Chromiumではauto / crisp-edges / pixelated / -webkit-optimize-contrastがsupported、smoothはunsupportedでautoのまま。
crisp-edges/pixelatedは輪郭の荒れが目立ち、採用しない。-webkit-optimize-contrastも非標準方式なので採用しない。
CSS filter、contrast/saturate/sharpen、source画像加工は使わない。

subpixel: 同位置PC1920×1080、1.80でAidan画像rect x=879.8718、y=556.7813、w=160.2562、h=106.8468 CSS px。
1.00でもx=810.4844/y=582.6563とfractional。これは原因候補であり単独の原因証明ではない。
logical/visual positionとも丸めず、footprint22×10、anchor、移動速度、camera計算を変更しない。
位置snapは採用せず、canvasのbacking-store画素数だけを整数化する。CSS画像rectは同一で歩行中の座標丸めによる段差を追加しない。

camera scale/DPR: `round(worldImageWidth × cameraScale × devicePixelRatio)`をcanvas backing storeとし、元画像を`drawImage`・imageSmoothingQuality=highで表示解像度へサンプリング。
CSS world-space rectは元imgと同一。camera/DPR変更時に再描画する。production PNGのresize/upscale、AI生成はゼロ。

compositing: 強制GPU promotionを外すだけの第一候補はAidanが柔らかく見え、除外した。
最終候補は表示解像度canvasで、強制promotionは追加しない。ブラウザ/実GPUによる差はPLAYER QA対象。

実装: `js/field/lind-crisp-renderer.js`。1actorに1canvasを再利用、原画像srcとbacking寸法が同じなら再描画しない。
新規image load/decodeを行わず、既存loaded imgを使う。移動は親actorに追随。
MutationObserver＋coalesced microtaskで描画前に同期し、独立timer/RAF loopを追加しない。
最初のRAF遅延候補で、切替直後に原画像が1frame見える問題をQAで検出したため、同期方式へ修正・再検証した。
Original/SmoothまたはDEV退出でcanvas/opacity classを完全除去。30回切替×4画面で確認。

## THREE WAY COMPARISON / AIDAN

| Mode | 技術方式 | 視覚上の確認・判断範囲 |
|---|---|---|
| Original | production相当 | NPCのpixelatedな輪郭を保持 |
| Smooth HD | 前回auto補間＋Aidan合成レイヤー | NPCのジャギー軽減、Aidanは環境次第で柔らかさが残る |
| Crisp HD | 表示解像度canvas、高品質補間 | harsh nearestにせず輪郭/ディテールを比較。優劣を一律に確定しない |

Hair/Face/Armor/Cloak/Sword: 比較スクリーンショットで同じ顔・髪・鎧・マント・一本の剣を維持。
追加的な白縁/黒縁/色変更/欠損を視覚確認で検出しなかった。
Face/Eyesの可読性と緑マントの背景への馴染みは、小さな表示サイズ・実ブラウザでもPLAYER QAが必要。
Alpha edge: 元RGBAをそのままcanvasへ描画し、matte/filterを付けない。髪/マント/剣の背景境界を確認。全端の客観的halo検出器による保証ではない。
Motion stability: north/south/east/west、斜めpointer、keyboard、20 A1 framesを確認。canvasと元img rect差は4画面とも最大0 CSS px。
元A1に存在するframe間の描き味や足滑りの好みまで改善済みと主張しない。

CAMERA 1.00 / 1.50 / 1.80 / 2.10: 4画面、同位置、代表actorで各3方式を比較。サイズ・inline image style・logical座標は不変。

[1920/1.00 Aidan＋Emma](qa/lind-character-rendering-phase2/comparison-1920-1-emma.png) · [1.80](qa/lind-character-rendering-phase2/comparison-1920-1.8-emma.png) · [2.10](qa/lind-character-rendering-phase2/comparison-1920-2.1-emma.png)

[1920/1.00 Aidan＋農夫](qa/lind-character-rendering-phase2/comparison-1920-1-farmer_male.png) · [1.80](qa/lind-character-rendering-phase2/comparison-1920-1.8-farmer_male.png) · [2.10](qa/lind-character-rendering-phase2/comparison-1920-2.1-farmer_male.png)

上の資料は同一位置のスクリーンショットから切り出したQA比較で、game assetではない。原寸full-screen PNGは実行環境`/workspace/onboarding/lind-character-rendering-phase2/`に保存。

## EMMA

| Mode | Speed world px/s | Rest sec | Route offset | Work sec | 30分 WAIT / MOVE / WORK | 最大原点距離 |
|---|---:|---|---|---:|---|---:|
| CURRENT | 1.2 | 24/36、初回44.4 | (4,-2) ↔ home | 状態なし | 90.98 / 9.02 / 0% | 4.08 px |
| NATURAL | 1.4 | 12/20 | (12,-2) ↔ home | 4 | 51.03 / 32.93 / 16.03% | 11.76 px |
| ACTIVE | 1.6 | 8/14 | (18,-2) ↔ home | 5 | 28.61 / 48.62 / 22.78% | 17.76 px |

WORKは休憩の先頭に含まれる。数値は境界dt=.1秒、arrival .5px閾値で小さな差が出る。
既存collision/プレイヤー32px proximity/interaction pause/blocked returnを再利用し、mode切替でteleportしない。
CURRENT復帰時はhomeへ安全に戻って現行routeに復帰するため、経過中timerまで過去時点に巻き戻すものではない。
風ON/OFF各30分相当で全modeの実updateを検証、penetration0。WORKは既存画像で少し見る・向く程度の-0.6°gesture、reduced-motionでは静止。
新しいEmma sprite・story・大きな徘徊は追加していない。

## ALL NPC DEV TEST / REGRESSION

Children: Chase/避譲/範囲・interaction維持、Crisp全NPCで動作。単一ポーズ移動は既知WARNING。
Farmer: idle/walk/workの画像切替・routine維持。
Fisherman: 12frameのwait→bite→reel→catch→inspect→return維持。風ON/OFF各60分相当26catch、WAIT約88%。旧30分11catch/約89%の低頻度方針を変更していない。
General Villagers: 職業/配置/interactionを変更せず補間方式のみ比較。

Collision: footprint22×10、Static Collision/Final Lockのソース変更なし。橋pointer/keyboard往復、wall slide、corner assist、blocked destinationを4画面×4倍率で回帰。
Movement: 4方向、斜め、実mouse/touch/key、動的豚/子供/村人障害物の待機・再開とkeyboard cancelを確認。
Village Life: Crisp＋NATURALの風ON/OFF各60分相当。13NPC保持、DOM827→827、NaN/地図外/静的侵入/永久停止/永久重なりなし。
Wind OFF: 水/人/子供/Emma/農夫/釣り人/家畜は継続、風駆動環境と鳥は停止。Terrain/水/建物/props/animalsのrenderingは変更しない。
Battle: 全Battle JS/CSS/assetsとinline Battleコードはmainと同一。
4画面で通常/Raider COMMAND、DEV kill during action→KO→Victory、race protection確認。
Raider HP1250、giant scale/HUD独立、phase境界を維持。別Battle Motion branchは変更しない。
追加のattack/Critical/一閃cut-in/Prayer/Item回帰の結果は同梱証拠JSONを参照。

## PERFORMANCE / RESPONSIVE

90実RAF interval/方式、camera1.80、PC DPR1/mobile emulation DPR3。約1.5秒の短い比較で実スマホの性能保証ではない。

| viewport | Original mean ms | Smooth mean ms | Crisp mean ms | Crisp canvas RGBA allocation |
|---|---:|---:|---:|---:|
|1280×720|16.67|16.67|16.67|502,428 bytes|
|1920×1080|16.67|16.67|16.67|502,428 bytes|
|844×390 DPR3|16.67|16.67|16.67|4,527,216 bytes|
|390×844 DPR3|16.85|16.67|16.67|4,527,216 bytes|

測定範囲では大きなFPS低下なし。Crispは全14actorでPC約0.48MiB/mobile約4.32MiBのbacking store追加。
この値はcanvas nominal RGBAだけで、GPU/compositor内部copyやresident process memoryではない。既存PNGの枚数・source decode budgetは不変。
LayoutDuration（各90frames累計）はOriginal約26–42ms、Smooth約29–34ms、Crisp約26–39ms。
独立paint/composite GPU時間はこのheadless測定から断定しない。heap/task/style metricsは`crisp-qa.json`に保存。
PC両サイズ・スマホ縦横でUI切替、canvas reuse/clear、全NPC、移動・anchor・既存導線を検証。

## ERRORS / WARNINGS / PLAYER QA POINTS

404: 0。JS exceptions: 0。Console errors: 0（完了した今回の機能QA）。
Invalid refs: 0。旧embedded/番号asset/Lou旧path: 0。新規画像パスは追加していない。追加script/linkは実ファイルと一致。

WARNINGS:

- Crispは表示サンプリング候補。元にない眼/顔の情報を作り出すHD処理ではない。実GPU/Safari/実Androidの見え方は未確定。
- source PNGの透明境界は変更していないが、補間の好み・haloの最終判定はPLAYER QAが必要。
- Canvas高品質補間の実装品質はブラウザ依存。今回検証はChromium。
- Childrenの静止ポーズ感を解決する新規animationは作らない。
- Emma CURRENT/NATURAL/ACTIVEと画質のproduction defaultは未変更。
- このbranchのみの試験。公開main/Pagesで試験可能とは報告しない。
- QA初回のcanvas1frame遅延検出は修正済み。初期除外候補・未完了試行を最終PASSの根拠に混ぜない。

PLAYER QA POINTS:

1. Original/Smooth/CrispのAidanでどれがよいか（髪/顔/鎧/マント/剣/足元）。
2. Camera1.00/1.80/2.10で自然か。
3. 歩行・方向転換で鮮明さと滑らかさが両立するか。
4. Emma CURRENT/NATURAL/ACTIVEのどれが年齢と生活感に合うか。
5. 全Field Character/NPCへの展開が適切か。Fisherman/Childrenも確認する。

証拠・再実行runner: [QA directory](qa/lind-character-rendering-phase2/)。旧HD資料とは別ディレクトリで今回の完了runを保存。

**PLAYER QA READY**
