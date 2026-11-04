# PLAYER-WALK-PRODUCTION-01

実装・作者QA：**PASS**。main統合：**HOLD（Pages公開承認と分離できないため）**。Android実機：**NOT_RUN**。

## 承認仕様と変更

ディレクターの2026-11-04の本指示により本番採用。最新main `e63780543d7ba1719a39a2f68b9924dc6d5b3933` から専用 `feature/player-walk-production-01` を作成した。PR #139/#140のDEVコード・試作・比較UIは取り込まない。

- 本番bank：正式01 → 正式05 → 正式02 → PR #139修復06。
- 周期90world、bobは既存連続波形の25%（最大.375world）、06全身位置補正0。
- 共通アンカー(1024,1230)、scale .0625、canvas2048×1280。移動速度・衝突・SAVE形式は変更しない。
- 修復06本番パス：`img/field/characters/aidan/down4/aidan_walk_down_06_ground.png`。
- SHA：`d87b2ec56660568bd46eecb8559edfed1c3802fe1e2675a018f78f3c23f970df`。PR #139 `d15aa83ab73e77e505895bea3c89485d3a9254bd` の候補をバイト単位で複製。再加工なし。独立画像QAはPR #140。
- 元06 `img/field/characters/aidan/aidan_walk_down_06.png` は保存、SHA `b88fdf8e0b48bc303c065d0dcd179babbd2c6a55040f4ccca8a2c18ed8c55c00` 不変。

[採用マニフェスト](../../img/field/characters/aidan/down4/adopted-walk.json)が4枚の順序・SHA・承認根拠を固定する。中央台帳も更新した。6枚をまとめた旧groupはPARTIALとし、01/05/02以外の旧画像を一括で新規承認しない。新規修復06のみAPPROVED、実機UNVERIFIED。台帳のMAINは**PR統合後に適用する予定状態**であり、現時点のmain反映完了を表さない。実際の統合状況は本報告・PRを正本とする。

`AidanFieldAssets.walkBanks.down` に順序、`bobScale.down` に.25を登録。共有 `FieldWalkMotion` が設定を読み、通常フィールドも単純な連番名ではなくbankのframe.keyを描画する。通常フィールドと既存の共通DEVテストが同じ設定を使う。旧素材レビュー用 `AidanFieldActor` の独立した旧6コマ表示は今回の対象外。本編・共通DEVとは区別する。

上・左右・Fionaなどは既存bankとbob設定のまま。左右180worldを維持。既存の斜め下操作は従来どおり下向き絵を共用するため、採用down bankを使う。方向判定・移動ベクトルは変更しない。

修復06のalpha boundsは `[668,126,1524,1237)`（右下exclusive）。boundsメタデータは `[x,y,w,h]=[668,126,856,1111]` に更新。旧bottom1230で切らず、全canvasを描画する。旧bottom以降の755画素は最大alpha30の薄い縁であり、不透明な靴が地面を突き抜けたという意味ではない。

## 作者QA

- baseline main：m58左右180・SAVE/CONTINUE・素材監査 **3/3 PASS**。
- 実装HEAD `d4b7dc9`：m62下歩行、m58左右180、m55共通歩行DEV、SAVE/CONTINUE、素材監査、m49正式SHA **6/6 PASS**。Node17本PASS（walk_motionは採用bank/bobの検査を追加した9サブテスト）。
- HEAD `6e27ac8`：移動開始座標からの厳密なbob波形検査とフィールド06撮影を追加したm62、および出典SHAを固定した台帳監査 **2/2 PASS**。アプリ描画コードは最初の実装から変更なし。その後の台帳MAIN表記は提案状態として明示した文書変更。
- m62はNEW GAME→自宅で通常キー入力・タッチのみ使用。強制移動・flag/HP/SAVE改変なし。3表示条件で実PNGの01/05/02/修復06の循環、90worldの実移動差、約.300秒/周、.375world上限と移動距離に一致するbob、全コマ同一アンカー、壁で停止、反転・再開、touch移動、状態保護を確認。
- PC1920×1080、Android相当390×844／844×390。既存DEVでも同じ4枚を表示し、実canvasから755画素の透過縁を読出した。上下・左右の他bank、Fiona、全味方・敵・NPCの既存DEV操作を検査。
- 正式259PNGの固定SHA一致（249portrait＋10eventCG）。既存1822PNGすべて不変。追加画像は修復06の1枚だけ。data、シナリオ、SAVE、移動・衝突実装、既存DEV、259素材参照は変更なし。
- console／Promise／HTTPの新規エラーなし。未使用Raider起動画像が実際にdecode済みの登録済みidleに置き換わる既存の特定abortだけは、厳密条件付きで既存helperが検証する。

[証拠](evidence/player-walk-production-01/)：各runner結果・全テスト出力、Node出力、保護SHA確認、通常歩行とDEVの3表示動画・画像、移動距離/表示URL/transformのraw JSON（可逆gzip＋SHA）。動画符号化はPC/横640×360、縦360×640であり、実検証viewportは上記のまま。最終固定HEADの実装者以外による独立QAはPRコメントに記録する。作者PASSを独立PASSとして扱わない。

## 統合ゲート：Pagesの別途承認

GitHubのmainはPages公開に接続されている。最新mainのPR #127 mergeから2秒後に、GitHub管理 `dynamic/pages/pages-build-deployment` がmain SHA `e637805` で開始し成功した。直前の複数main mergeも同様。現在のrepository metadataも `has_pages:true`。

根拠：[run41622166154](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/41622166154)、[取得記録](evidence/player-walk-production-01/pages-gate.json)。ローカル`.github/workflows/`にこの公開処理の設定はなく、GitHub管理の公開をアプリ差分だけで分離できる根拠はない。

ユーザーはmainマージを承認した一方、「Pages公開は別途承認待ち」と指定している。公開を伴う可能性を承知でmainを進めない。公開設定の変更、workflow停止、未検証のskip指示、安全確認の回避も行わない。**実装・独立QA・専用PRまでは完了させ、Pages公開の扱いが確定するまでmainマージを保留する。** これはコードQAのFAILではない。

## Android確認手順（実機未実施）

公開承認後のmain/Pages、または専用featureをローカルHTTPで開く：

1. `/index.html?title=1` → NEW GAME（既存SAVEは上書きしない）→冒頭会話を閉じる。
2. エイダンの家の空いた床を下へ移動。01→05→02→修復06の接地・.300秒ループ・外套の切替を確認。
3. 停止・再開・上方向への反転と左右移動。下方向の全身が瞬間移動せず、上/左右のテンポが従来どおりか確認。
4. 縦横回転、タッチ移動、SAVE→再起動→CONTINUEを確認。必要ならDEV→歩行モーションテストでエイダン下方向を1倍・コマ送りで確認する。
5. 実機で問題があれば、端末・表示方向・操作・コマと動画を添えて修正タスクへ分離する。

現行Pagesには未公開。本番統合・公開が承認されるまで、この変更を既存Pagesで確認できるとは案内しない。同一LANの検証はfeature取得後 `python -m http.server 8000`、AndroidからPCのIP:8000を使う。
