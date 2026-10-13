# 剣付きエイダン18コマの受入（P）

基準main88ae6c0、branch work/codex-aidan-walk-acceptance。STATUS: READY（検品ツール/手順、実素材は未着・未検品）。
要約: 18個別RGBAコマの枚数/寸法/本物のalpha/足元登録/体高/任意の機械反転を読取検査する。正常ダミー18合格、7種類の異常を検出。背中の剣/顔/服/歩行は目視判断を残す。

## 入力契約

元の生成指示は `origin/feat/aidan-side-walk-v4:docs/art/chatgpt_aidan_walk_prompts.md`（mainには無い）で確認。**右側面4＋前斜め左6＋後ろ斜め左6＋斜め待機左2＝18**。左右の全方向を18に数え直さない。斜め右は左の反転から生成予定。元納品は白背景の横一列シートなので、原シートは目視確認し、Claudeが切出し/透過/登録後のprepared個別PNGを本ツールへ渡す。シートから自動で人物を切り出す/背景を消す処理は今回追加しない。

intake aliasはtemplate JSONのside_right/front_left/back_left/idle_front_left/idle_back_left。ゲームの正式frame IDではない。現install_hero_frames.pyはdown/left/right/upの4方向のみなので、斜め素材のruntime組込はClaude側の追加設計が必要。検品合格だけで8方向がゲームに実装済みとは扱わない。

prepared標準の参考は現AidanFieldAssets: canvas2048×1280、anchor(1024,1230)、scale0.0625。templateはこの値を使い、入力の正規化規約が変わるならmanifestで明示してから検査する。採用済み画像/manifestを変更せず、原納品・prepared候補・採用先を別々に保つ。

## 自動検査 / 合否

| 項目 | 検査 | 判定/限界 |
|---|---|---|
| 枚数/phase | exact18、各group4/6/6/1/1、index1..N、重複fileなし、未登録PNGなし | 不足/過剰/phase欠落はFAIL |
| 寸法 | manifest.canvasと一致 | 無断resizeしない。raw sheetは対象外 |
| 透過 | PNG/RGBA、alpha0ピクセル、四隅透明、opaque bboxが端に接しない | 偽checkerboard/白背景の不透明preparedはFAIL |
| 接地基準 | alpha>=235のbody最下端とanchorY、許容8source px | 実際の足首/影を意味認識しない。opaque shadowが残る場合は目視再確認 |
| 横登録 | body下6%のopaque帯中心とanchorX、許容32source px | 32px×0.0625=2world px。歩行の足開きで動くので体幹/boot確認も必要 |
| サイズ感 | opaque体高の共通中央値から±4% | 剣/髪/マントをbodyから自動分離しない。原納品の縮尺判断は目視 |
| 左右対称 | mirror_file指定時、RGBA全channelの機械反転一致、feet center XのW−X/足元Y一致 | 18原コマには逆向きがない。mirror未提供は未実施/REVIEW。独立描き下ろしを完全mirror必須にしない |
| 個別表 | technical PASS/FAIL、feet dx/dy、error、review | technical PASSでも正式採用はREVIEW_REQUIRED |

alpha bboxの底と下部帯は登録proxyで、剣の有無・身体パーツ・影・爪先の本物の接地を自動保証しない。threshold/許容値はprepared契約の検査用で、ゲーム速度/戦闘数値の確定ではない。納品候補の不一致を自動修正しない。

## 目視チェックリスト（Claude/作者）

- 全18コマで背中に鞘付きの父/誓い設定に合う剣がある、柄の位置/長さ/角度/ストラップが一貫、手に木剣や別武器を持たない。
- 同じ17歳のエイダン、髪/緑の目/緑マント/象牙上衣/古金の装備/顔が一致。合成シートの隣人や背景片が混ざらない。
- 側面4の通過/かかと上げが読み取れ、前後斜め6で左右の足が交互。待機2が同じ縮尺/角度。コマ間にマント/頭/足の急な形変化なし。
- 原白背景シートの各人物が全身/余白付きで分離でき、preparedの透過縁に白線/halo/地面/影が残らない。
- 足元は軸足/かかと/つま先のどこが接地するかを確認。登録proxyが剣/影/マント末端を拾っていない。
- 反転で剣・利き手・服模様が矛盾しない。RGB差は正しい機械flipを検証するもので、キャラの左右デザインの承認を代行しない。
- 採用前にDEV候補としてPC/390×844/844×390で歩行/停止/方向転換を確認。現在は実素材未着なので未実施。

## 実行 / テスト分類

```sh
python3 tools/field/check_aidan_walk_assets.py --template > /tmp/aidan-intake.json
python3 tools/field/check_aidan_walk_assets.py /tmp/aidan-prepared --manifest /tmp/aidan-intake.json
python3 tools/field/check_aidan_walk_assets.py /tmp/aidan-prepared --manifest /tmp/aidan-intake.json --json
python3 tools/field/check_aidan_walk_assets.py --self-test
```

依存Pillow（環境の既存venv）。self-testはtempfile内で18コマ/逆向きを作成して検証し削除。合格: 正常18、7負例（寸法/RGB alpha/基準線/横ずれ/欠落/誤反転/枚数）。個別合否と負例はdocs/qa/aidan-walk-acceptance-dummy-20261013.json。失敗なし。実画像の見た目・人体の足元・Android・ゲーム組込は未実施。sourceは読取のみ、正式採用/差替えなし。

変更ファイル: 新規tools/field/check_aidan_walk_assets.py、本書、template JSON、ダミーQA JSON、status/CLAIMS。main未更新。次は素材受領後に原シートの目視→prepared検品→ClaudeがDEV組込→正式採用判断。要判断: 名前/正規化契約、斜め方向runtime、背中の剣の向き。mainロールバック不要。
