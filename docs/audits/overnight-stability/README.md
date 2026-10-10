# Overnight Stability Audit — 最終報告

RESULT: **PASS WITH WARNINGS**

START MAIN HEAD: `d3e299ac7ca90eb49629570a57a90ff678ad7591`

BRANCH: `work/overnight-stability-audit`

START WORKTREE: CLEAN。既存HD作業ブランチから変更を持ち込まず最新origin/mainから作成。

FINAL COMMIT: この報告を含むブランチHEAD（最終回答にSHAを記載）。

PUSH: 専用ブランチのみ通常push。main merge/push、Pages deployなし。

WORKTREE: 最終commit/push後CLEANを確認。

途中checkpoint: `0154cc2` → `4be5279` → `18f9e67` → `1314118` → 最終報告commit。

アプリHTML/CSS/JS、production画像、Battle数値、collision、cameraは変更0。
変更は本監査フォルダの報告、CSV、QA runner、実測JSON、資料contact sheetのみ。
完全互換の修正が必要と確定した内部bugはなく、ゲーム側fixは行っていない。

## ASSET AUDIT

187PNG、378,990,248bytes、RGBA176 / RGB11。全画像読込成功。
SHA-256完全重複0。dHash類似候補10組は主に意図したstate/frame違い。
全187行の寸法/alpha/サイズ/参照出典/未参照候補/類似候補は
[evidence/asset-inventory.csv](evidence/asset-inventory.csv) に保存。
178runtime request/registryパスはすべて存在。未参照候補9枚は削除せず保持。
RGB6枚のterrainは正常。Aidan特殊素材5枚の白系背景は未接続stateのP2警告。
細部と使用状況は [asset-audit.md](asset-audit.md)。

## CHARACTER QUALITY ROOT CAUSE / HD CLASSIFICATION

PCでは元画像を大幅縮小している。NPC強制pixelated、fractional座標、
camera transform、DPRの差が主要候補。Aidanはautoであり、追加の合成/rendering
比較候補。原因をsource不足と断定して大量upscaleしない。

|対象|分類|根拠|
|---|---|---|
|Aidan|B|PC1.8倍でも約1/9.6縮小。compositing/座標の比較を先行|
|Emma|B|約1/16.7縮小、pixelated|
|Children|B|大幅縮小＋pixelated。静止ポーズ移動は既知制限|
|Farmer|B|約1/11.75縮小、pixelated|
|Fisherman|B|PCで十分。DPR3/2.1倍のみC候補（物理1.26倍拡大）|
|General Villagers|B|nativeは十分、pixelated比較優先|
|Fiona|NOT PRESENT|production Field PNGなし。legacy CSS表現を新素材とみなさない|

B=rendering比較推奨。画質・デフォルト・サイズ変更は未実施。
5viewport/DPR条件×17camera設定=85ケース、3825frame行を測定。

## EMMA MOTION AUDIT

初回待機44.4s、初回移動44.5s。speed1.2px/s、rest24/36s、
目標offset(4,-2)/原点、実測最大変位4.08px。30分で54回、1回平均3.609px、
WAIT90.98% / MOVE9.02% / WORK0%。10分でもWAIT91.43% / MOVE8.57% / WORK0%。
EMMA種別はWORKER用WORKへ入らないためWORK0であり、タイマー停止ではない。
1.8倍でも最大7.34screen pxで、見落としやすい。
通常DEV focus/風OFFでも移動し、直接プレイヤーを32px以内に置くと安全に待機。

OPTION A: initial16–24s、rest18–26s、距離6–8px、speed1.2、work候補2s。

OPTION B: initial10–16s、rest12–20s、距離10–14px、speed1.4、work候補3–5s。

OPTION C: initial8–12s、rest8–14s、距離16–20px、speed1.6、work候補4–6s。

すべて提案のみ。選択後に新routeのcollision QAが必要。

## VILLAGE LIFE 30/60 MIN QA

風ON/OFF各60分相当、既存updateを0.1s刻みで実行。
13NPC維持、DOM797→797。消失/NaN/地図外/新しいstatic侵入/恒久stuck検出なし。
全家畜pen内、全移動NPCに進行あり。長時間実機wall-time試験ではない。

FISHERMAN RESULT: 30分11catch、WAIT88.83%；60分26catch、WAIT88.00%。正式sequence維持。

CHILDREN RESULT: 追跡/交代/反転/譲り合い、恒久stuckなし、building/river侵入なし。
静止ポーズ移動の既知visual WARNINGは維持。

DYNAMIC NAVIGATION RESULT: PASS。pig/child/villager/複数障害物のdestination保持・retry・resume。

WIND OFF RESULT: PASS。wind/birds停止、water/人/children/Emma/farmer/fisherman/家畜は継続。
鳥は接近TAKEOFF→WAITING、風OFF60s spawnなし、再開/reduced-motionも確認。

COLLISION RESULT: PASS。4view、全14建物1.00倍＋代表5種類1.50/1.80/2.10倍、計116ケース。
front props/door/corner/behind route/ground depth、侵入0。bbox拡張なし。

CAMERA RESULT: PASS。17設定監査、4代表値で実操作。
各view/scaleにつきpointer10往復＋keyboard10往復、合計各160橋往復。
壁滑り/角補助/blocked destination維持。初期1.00倍は既知WARNINGのまま。
Aidan footprint22×10、4idle/16walk、anchor/scale/save復帰を維持。

詳しい数値・methodは [field-audit.md](field-audit.md)。

## BATTLE / IDLE / FOREST BAT

AIDAN BATTLE IDLE AUDIT: PASS。00→01→00→02→00、cycle5.4–7.9s、fade220ms。
03は3–5cycle後。60s実測で24.560s/56.816s、00表示約69.4%。
小さなpose変化と長い00保持が静かに見える理由。frequency変更なし。
足元primary差0、secondary差約1px。

両PCはnormal/Raider各120sの全assert完了stdoutを保持。長い一括runner中断のため
PC詳細frame行のcombined JSONは未保存（明記したcompletion記録で区別）。
スマホ横/縦は独立runnerで各normal/Raider120sを完了し詳細JSON保存。
guard/action/presentation pause/resume/reduced-motion/KO/Victory race/exit cleanupを確認。

FOREST BAT ASSET STATUS: 4/4、1536×1024 RGBA、透明56.31–59.15%。
背景焼込みの明らかな問題なし。body位置/wing余白のPLAYER QA必要。生成/飛行実装なし。

BATTLE ASSET AUDIT: 全74画像、native/alpha/pathと実描画rectを記録。
Raider既存rectはPC1280で537.59×504、1920で720×640。縮小変更なし。

BATTLE REGRESSION: PASS。4viewでnormal/Raider、実COMMAND、target、通常攻撃、
Critical（820ms lunge＋既存hit-stop）、一閃/cut-in/TP30、被弾→Idle、
Fiona Prayer MP-6/RUNE+28、guard、DEV撃破、enemy KO/Victory、古いtimer保護。
itemはAPIの一回消費/KO/Lou除外確認（全item UI組合せは本監査で再実施していない）。
Raider HP1250、巨大表示、HUD独立、phase境界維持。

構造/各数値は [battle-performance.md](battle-performance.md)。

## PERFORMANCE / PRELOAD

PC1280×720/1920×1080、mobile emulation844×390/390×844、Field/Battle確認。
実RAF平均Field16.67–20.74ms（同時QA負荷あり）。実機スマホ速度を保証しない。
3review再入場でDOM/listener増加傾向なし。Idle単独shared RAF1本、cache1組。
明示decodeはField20＋Idle4の24枚各1回、重複なし。NPC/釣りframeはmount後再利用。

全187枚の理論展開量約1.03GiB。review時loaded-source nominal RGBA約543–597MiB。
GPU常駐メモリ計測値ではない。全2x化は約4.11GiB、Aidan20枚のみでも追加360MiB。
PCにsource不足根拠なし。HDは1actorずつ実機予算と画質approvalを先行。

404: **0**

JS EXCEPTIONS: **0**

CONSOLE ERRORS: **0**

INVALID REFS: **0**（静的/registry/runtime監査範囲）

20DEV導線×4view＋機能suiteで観測。embedded / asset_数字 / oldLou参照各0、embeddedフォルダなし。
40JS module構文検証成功。修正したQA helperの失敗・実行セッション中断はゲーム例外と区別。

## NEXT PHASE READINESS

|対象|判定|
|---|---|
|Aidan Battle Motion|READY WITH WARNINGS|
|Forest Bat Idle|READY WITH WARNINGS|
|Character HD|READY WITH WARNINGS|
|Emma Motion|READY WITH WARNINGS|
|Lind Interiors|NOT READY|
|Aidan House / NEW GAME|NOT READY|
|Fiona Field|NOT READY|
|Party Follow|NOT READY|
|Location Card|READY WITH WARNINGS|
|Cinematic Camera|READY WITH WARNINGS|
|Moss Forest|READY WITH WARNINGS|

READY WITH WARNINGSはprototype/設計へ進める条件で、本番見た目承認や自動実装許可ではない。
理由・素材/仕様gateは [next-phase.md](next-phase.md)。

## WARNINGS / PLAYER QA REQUIRED

PC画質の比較、Emma A/B/C選択、別motion branchのIdle頻度、Bat body/wing登録、
Aidan未接続特殊5素材の背景修復、実機mobile性能、初期camera1.00、children静止pose。
PC長Idle詳細combined JSONなしという証跡制限はcompletion記録に明記。
画像加工・大量置換・好みの確定を行っていない。

RECOMMENDED NEXT 3 TASKS:

1. 現PNGのままPC renderingのopt-in比較PLAYER QA。
2. Emma CURRENT/A/B/C previewとroute collision確認。
3. 既存Aidan/Bat motion prototype PLAYER QAとattack frame素材gate。

mainは変更せず終了。本番Pages公開なし。
