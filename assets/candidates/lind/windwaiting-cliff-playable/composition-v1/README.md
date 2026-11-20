# 風待ちの崖｜独立美術QA提出資料

Draft PR #421 の e6da37151c160000fcd0d7b300a92e84fd9c4244 を基準とした未承認試遊候補。制作規約は main の 3b9f5c19518ce0982f982f9eb6addf36c38f49c9 で確認。非公開引き継ぎ資料は main の af0d068f4055bf0b207ffa9e02127df8c258438d を参照。正式CGは `assets/approved/game/cliff/sunset_background.png`。main と基準 HEAD の参照PNGが同一 SHA-256 であることを確認した。正式配置は未承認。

## 実モデルと描画

- **道路**。旧舗装は4,000三角形の別メッシュで、16,000サンプルの地表との差は +0.02456〜+0.02844 BU、貫通は0。面法線は上向きで Z は0.962〜1.000。旧舗装にUVはなく、写真材質は世界座標 XZ を使用。旧路面の頂点色だけを無効にした対照で黒い帯が解消した。写真色に既存の暗い頂点色が乗算されることが主因。地表と同じ描画面に路面と路肩を統合し、旧メッシュは接地レイと移動判定に使用する。Blenderでも旧舗装を隠し、地表材質に路面を組み込んだ。
- **広葉樹**。実GLBとECO v2の編集原本を照合し、根張り、幹の法線、既存の枝と葉の接点を保った風上への樹冠の傾きを調整した。幹UVの反復密度は横1.5倍・縦2.4倍。Poly Haven の Rob Tuytel による CC0 の *Bark Brown 02* を使用。元ZIPのSHAと各マップのSHAを検証した。2,446三角形、GLBの風ウェイトとプロファイル、既存の共有インスタンシングを維持した。枝分岐の全再トポロジーは未実施。
- **遠景**。左の低い岬、中心奥の主稜線、右へ落ちる岩棚と離れ岩を4つの実メッシュ断面で組み立てた。838三角形の遠景メッシュを既存の試験用遠景に差し替えた。視点切替LODの追加は不要と判断した。背景メッシュは移動対象外。固定視点の全体描画は258,080→252,758三角形、109 draw calls。GPU性能やAndroid実効値は未測定。
- **正式CG**。左の広葉樹、中央から右へ下る崖、右の水面に落ちる夕日の反射を照合した。CGと試遊はカメラが異なるため画像は構図比較。試遊の前後と材料切り分けは同一カメラ。正式CGに比べ、手前の主崖プロポーション、岩の破断と段差、花畑の密度、夕景の色と反射に差が残る。主崖の既存E/C12/ROCK03候補を継承した。今回の新規造形は樹木と遠景。正式寸法・座標が未確定のため、Blender Z-up、海側 −Y、既存のローカル原点、暫定BUを使用。glTF は (X, Z, −Y) に変換した。

## レビュー手順

1. `SHA256SUMS` を検証し、`comparison.png` のCG、旧描画、頂点色対照、候補を確認。路肩と手前草地の境目、樹幹と根、海岸の輪郭と奥行きについて個別に判定する。
2. `offshore-blueprint.png` は書き出したGLBから作成した平面・海側正面・側面・断面。A は左岬、B は中央の最高点、C と D は右の離れ岩。詳細座標は `geometry-qa.json`。Blenderを開き、3視点のPNGで立体形状と接地を照合する。
3. 対象ブランチのルートをローカル配信し、`/dev/windwaiting-cliff/?composition=1&photo=1` を開く。写真参照一式は GitHub Actions run 44818357345、artifact 14670447492 から `photo-pbr/` に展開し、同梱SHAを検証する。写真材質なしの確認は `?composition=1`。旧版の既定動作も利用可能。
4. 独立レビューで G2 の判定、視点、指摘箇所、正式CGとの差、再検証条件を返す。今回のデスクトップ検証は `webgl-photo-qa.json`、根本原因のRGB対照とゲートの範囲は `technical-qa.json`。

## 再生成と検証

Blender 5.3.0 の配布SHAを検証済み。作業コピーで別の出力先を指定する。

```sh
blender -b -noaudio --python-exit-code 1 --python tools/map_blender/lind/build_windwaiting_composition.py -- /path/to/new-output
node --test tests/field/windwaiting-cliff-{nav,eco}.test.mjs
python tests/field/windwaiting-cliff-composition.py http://127.0.0.1:8629 /path/to/new-review
```

G1 は正式配置・寸法が保留。G2 の独立判定は未実施。G3 の原本再開、GLB、材質対照と G4 の隔離デスクトップ試遊を実施。本編統合とAndroid実機は未実施。
