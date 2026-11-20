# TWO｜風待ちの崖 試遊候補

既存 Draft PR #421 上の独立したプレイテスト。Blender 座標は右手系 Z-up、海側は −Y、原点は継承した暫定ローカル原点。数値は未確定 Blender unit。glTF は右手系 Y-up、変換は `(X, Z, −Y)`。

## 試遊

リポジトリまたは展開した Actions ZIP のルートで `python -m http.server 8621 --bind 127.0.0.1` を起動し、`http://127.0.0.1:8621/dev/windwaiting-cliff/` を開く。WASD、矢印、クリックまたはタップで移動。ドラッグでカメラを旋回。「出発点へ」で位置とカメラを戻す。Three.js 0.180.0 は同梱の MIT 版。GLTFLoader のユーティリティ参照のみ同梱位置に合わせた。

## 照合と試験統合

- **#421**。岩盤Eは run 44713884694 / artifact 14617769408 のファイルを SHA 検証して読み込んだ。C13 に保存されたD4キャリアをジオメトリSHAで照合し、C12の対応CSVで指定された面だけをEのコピーへ転写。左右パッチ境界のXYZ、接続、非隣接交差を検査した。大型岩03は C13 接合候補に差し替え、既存の岩01・04を継承。海岸側の既存岩同士の接触と微細な岩盤修正は保留。
- **#351**。海岸道路の `Village_to_coastal_promontory` を流用。仮の両端に平面変換し、細分後に実地形へ鉛直投影。道路原本とそのWORLDコンテキストは保存。別ローカル座標で計測したため旧支持工・橋・広域地形は持ち込んでいない。
- **#357**。広葉樹、草カード、短草、花、沿岸石を再使用。沿岸石のコピーを苔材で覆い、花・短草・石は試遊用に軽量化。株元の接地、高低差、斜面、路肩、崖際の余白をチェックし、木と苔石にコライダーを設定した。植生原本とテクスチャは入力SHAを記録。
- **#353**。出典・軸・単位・仮配置・幾何SHAを機械可読化。公式CGは `assets/approved/game/cliff/sunset_background.png`。左の広葉樹、手前の花草、斜めに続く崖、青い海、海上の夕日と反射を参照した。道路位置と森の分布は試遊用の仮配置。岩材出典は既存候補の Poly Haven CC0 `rock_face_01` と `boulder_01`。

## 保存物とQA

- `cliff_UNAPPROVED.blend` は画像をパックした編集原本。Cycles で原本を再開して `sunset.png`、`gameplay.png`、`coast.png` を保存。
- `cliff.glb` と `navigation.json` が試遊入力。接地は実メッシュへ下向きレイを使う。グリッドの支持、斜度、高低差、崖際の周辺サンプル、木・岩の半径コライダーで移動を制限。カメラは追従・旋回・地形レイによる距離制限。GLBの材質差は試遊側の空・海・岩／草のシェーダーで補正。
- `manifest.json` に入力SHA、変換、植生配置、道路間隙、主崖の合成検査。 `browser-qa.json` とブラウザ画像に Chromium/SwiftShader での計測。 `SHA256SUMS` は試遊一式をリポジトリルートから検証できる。
- G1 は参照CGと入力のSHA照合を実施。正式寸法・位置は BLOCKED。G2 は岩盤E・既存道路・植生の既存FAILを継承。組み上げたシーンの独立美術レビューは NOT_RUN。G3 は合成キャリア・接地サンプル・再開・書き出しの限定検証。G4 は隔離したブラウザ試遊の範囲で検証し、Android実機、本編統合、製品性能判定は NOT_RUN。正式採用と main マージは対象外。

## 再検証

```sh
sha256sum -c assets/candidates/lind/windwaiting-cliff-playable/SHA256SUMS
node tests/field/windwaiting-cliff-nav.test.mjs
python tests/field/windwaiting-cliff-browser.py http://127.0.0.1:8621 /tmp/windwaiting-qa
```

再生成は Blender 5.3.0 を使用。`build_windwaiting_playable.py` の引数は SHA 固定のEファイル、#351 `route.blend`、#357 `eco_kit_v1.blend`、出力ディレクトリの順で、ECOテクスチャは ECO blend と同じ階層の `textures/` に置く。C12／C13と参照CGは既存ブランチから読み込む。ビルドは原本に書き戻さない。
