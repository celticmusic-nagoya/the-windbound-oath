# DEV-WALK-GROUND-01-QA

局所修復画像の独立QA：**PASS**。DEV機能の作者QA：**PASS**。本番採用：**保留（ディレクター判断）**。Android実機：**NOT_RUN**。mainマージ・Pages公開なし。

## 固定した入力と責任

- PR #139：`d15aa83ab73e77e505895bea3c89485d3a9254bd`。Claudeの自己QAとは別に、Codexが画像の実バイト・編集範囲・形状を再検証した。
- DEVの基準：PR #138 `9ef73d3edaa27841d808297867ece9dade0a3040`。専用featureブランチ `feature/dev-walk-ground-01-qa` にのみ追加。PR #135・#136の4コマ比較を継承する。
- 候補SHA：`d87b2ec56660568bd46eecb8559edfed1c3802fe1e2675a018f78f3c23f970df`。
- 正式06 SHA：`b88fdf8e0b48bc303c065d0dcd179babbd2c6a55040f4ccca8a2c18ed8c55c00`。
- 候補PNG・mask・README・qa.jsonはPR #139から無加工で複製。README/qa.jsonはClaude作成時の自己QA記録を保持し、今回の独立結果に書き換えていない。原ブランチ・正式PNGは変更しない。採用状態は `CANDIDATE_NOT_ADOPTED` のまま。
- 画像レビューは別担当 `cycle_a01_visual` が独自スクリプト・比較画像で実施。DEVコードの実装・作者テストとは別。[独立画像レビュー](evidence/dev-walk-ground-01-qa/independent-image-review.md)。最終固定HEADの別担当コードQAはDraft PRコメントへ記録する。

## DEV比較

NEW GAME/CONTINUE後、会話を閉じる → DEV → 歩行モーションテスト → エイダン・下 → **接地比較条件**を押す。4コマ01→05→02→06、周期90、bob25%、06全身補正OFF、300world/s相当、1倍になる。06画像のA（正式）/B（未採用候補）を切り替えて再生・停止・コマ送りできる。切替時は停止して01へ戻すため、条件を揃えやすい。

候補参照はDEVの4コマ下方向descriptorの複製だけに適用。通常6コマ・上下左右の本番bank・共有キャッシュは変更しない。既定値はA。全身+8pxの旧比較は別項目として残すが今回のA/BではOFF。画像は2048×1280の全canvasをアンカー(1024,1230)、scale .0625で描画する。旧boundsのbottom1230で切らない。候補のalpha boundsは `[668,126,1524,1237)` で、旧画像と同じではない。

## 独立画像結果

|検査|結果・限界|
|---|---|
|寸法・形式・透過|両方2048×1280 RGBA。新たな不透明な分離足片なし。境界黒/白比較で明らかな矩形・マットなし|
|編集範囲|16,651画素、差分bbox `[990,1062,1126,1237)`（右下exclusive）。mask外0、y<1062全行一致|
|頭・腰・外套・反対脚|編集範囲外は完全一致。上半身・外套・腰の全4遷移ROI差もA/B同一|
|すね・足首・靴|下すねの滑らかな延長。靴内部矩形は元画像のY−7とRGBA完全一致。拡大比較で明らかな折れ・装飾破損・靴の変形なし。6.4%は110行の平均延長率で一様拡大率ではない|
|最下行|候補には旧bottom以降755画素、最大alpha30の薄い縁がある。ブラウザcanvasでも755画素を読出し、表示範囲内であることを確認。高alphaの靴が地面を突き抜けたという意味ではない|

中央列の支持靴輪郭と登録線の差（画像px、alpha輪郭の推定値）：

|コマ|alpha>128|alpha>200|
|---|---:|---:|
|01|4|5|
|05|4|6|
|02|4|5|
|正式06|11|12|
|候補06|4|5|

4px一致だけでPASSにはしていない。すね・足首・靴の原寸拡大、全身・反対脚・外套の保護、全4遷移と実ブラウザの画像・配置を別に検査した。輪郭の高さは荷重・物理接地の証明ではない。02の接地足の解釈は画像からの推定。

## 境界と残存事項

- 01→05：画像・全身配置とも変更なし。
- 05→02：画像を変更しないため既存の外套差は不変。左外套ROIのMAE50.92/255、右39.46、腰49.04（A/B同一）。時間的なちらつきの知覚スコアではない。
- 02→06：候補の局所7px下降で、alpha128の推定支持輪郭差は両側 `.625world`（bob .375を含む）。正式06は1.0625world。全身位置は動かさず、下すねの接続と靴の輪郭を拡大検査した。
- 06→01：候補の推定輪郭差は両側 `.25world`、正式06は `.6875→.25`。上半身・腰・外套の新しい段差は追加しない。脚の元のポーズ差は残る。
- bob25%の連続持上げは残る。4コマ・.300秒/周は依然速めで、4姿勢だけから完全な荷重移動や滑りのない歩行を断定できない。**局所修復は改善、全歩行品質・正式採用の最終判断は保留**。

推奨A/B条件は **候補06・90・bob25%・06全身補正OFF・1倍**。旧全身+8px方式の±.5world段差を避けつつ輪郭差を縮める。既存05→02の外套差を修復済みとは報告しない。

## 自己QAと証拠

- `m61_dev_ground_candidate.py` 作者実行：110/110 PASS、HEAD `9fbf1515de20dc2374d630fe9229e36348ba6f75`。PC1920×1080、縦390×844、横844×390。実際にdecodeした01/05/02/06、約.300秒/周、実描画画素差、旧範囲以降のalpha、他方向/Fiona/6コマへの非適用、timer解除、HTTP/console/Promiseを検査。その後、ラベルを「全身06」と明確化し、A/Bのtop/transform一致assert3件を追加。最終HEADは別担当再実行で確認する。
- m59既存4コマ回帰98項目、SAVE/CONTINUE25項目、素材台帳監査：3/3 PASS（実装HEAD `24a01c5`、後続差分はDEVラベル・検査・証拠）。Node17本PASS。正式259PNGの固定SHA検査PASS。
- ベースに存在する原本1831PNGのバイト不変、本番 `js/field`・data・img・index・css・assets/images差分0（今回のPR138基準の追加差分）。[保護検査](evidence/dev-walk-ground-01-qa/original-protection.json)。259枚は249会話立ち絵＋10イベントCGを含む。
- 初回runnerはsandbox内プロセス起動がOperation not permittedで未実施（125）。ネットワーク許可付き同runnerで再実行。次のm61は既存URLの`?v=`を比較fixtureが考慮しないためFAIL。検査をバージョンsuffix対応に修正して再実行PASS。失敗ログも保持し、製品不具合や成功として上書きしない。

[証拠一式](evidence/dev-walk-ground-01-qa/)：実ブラウザのA→B動画3本、原寸足元/すね/靴/alpha比較、02→06→01全身画像、実測JSON、自己QA・失敗ログ・Node出力。動画は実viewportのブラウザ録画をPC/横640×360、縦360×640へ符号化したもので、実viewportサイズを変更した検証ではない。独立画像plateのDPR相当表示は静的リサンプルであり、実機スクリーンショットではない。

再現：専用featureを取得し `python -m http.server 8000` → `/index.html?dev=1&title=1`。Androidでは同一LANのPCのIP:8000を使用する。既存Pagesには公開しない。ブラウザ回帰は `PLAYWRIGHT_BROWSERS_PATH=<ffmpegを含むcache> PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium QA_OUT=<out> bash tools/qa/run_all.sh --gameplay-ready --git-history --out <logs> tests/moss/m61_dev_ground_candidate.py tests/moss/m59_dev_down_cycle.py tests/system/save_continue_lifecycle.py tests/system/asset_registry_audit.py`（直列）。

## Android実機での判断項目（未実施）

1. 同一90/1倍/bob25%/全身補正OFFでA/Bの06支持靴の浮きが改善するか。
2. すねの長さ、足首の曲がり、靴装飾・影・輪郭が自然か。
3. 02→06→01で脚の切替が自然か。05→02の既存外套差と区別する。
4. 縦横で最下行の欠けがないか。等倍で連続再生・停止・コマ送りを確認する。
5. .300秒/周のテンポとbobの浮きが許容できるか。採用・追加調整はディレクター判断。
