# モスの森・納品素材検証

基準mainコミット: `ce2b3663b031631c858f922ded8390a89ffd48cf`
ブランチ: `work/codex-moss-delivered-art-verification`
STATUS: WIP

## 統合済み状態

着手時点ですでにClaudeが `feat/moss-delivered-art` (`26cb6fc`) をmainへmerge済み。機能mergeは `ce2b3663b031631c858f922ded8390a89ffd48cf`、第一parentは `0372ef604b39205f1a356e6c6b417f44e02ac0b0`。remoteの `rollback/pre-moss-delivered-art` が第一parentに一致することを確認。対象branchとmainのtreeも同一。二重の素材mergeは行わない。

既存機能mergeの変更ファイル: `img/field/moss/art/` の68枚、manifest、`index.html` のcache query、`js/field/forest-loader.js`、`js/field/moss-forest-runtime.js` のopening画像適用、`tests/moss/m6_asset_swap.py`、`tools/moss/check_assets.py`、`tools/moss/install_delivered_art.py`、素材依頼資料。本検証の変更は未納品一覧とCLAIMS・この報告・QA記録だけ。
追加・変更したID・フラグ: 本検証ではなし。

## 見た目

外部 `/tmp/moss_visual_check.py` で指定9座標を撮影。リポジトリのtoolsや画像を変更せず、退避mainの同じ座標も比較。1280×720、PC Chromium。指定DEVページの結界自体はforest-dev.jsの色付きplaceholderで、本番の納品結界画像を検証できないため、index.htmlのMossForestで別途状態を撮影した。

| map / 座標 | 確認結果 |
|---|---|
| A3 門 (3900,3420) | DEVの結界は色付きplaceholderのまま。本番の4状態は別撮影。 |
| A3 棘 (4100,2850) | 棘の足元と周囲の石の接続に明確な浮きなし。広場の緑のplaceholderが残る（未納品の古代樹等、以前から存在）。 |
| A3 紋様 (4320,2860) | 紋様の光は透過して地面に乗る。明確な白い矩形縁なし。未納品placeholderが周辺に残る。 |
| A3 小屋 (5600,3780) | 小屋の足元は地面に接地。近くの道の斜線区間で水平の継ぎ目が目立つ。道の区間重なりは以前もあり、新しい高密度テクスチャで目立ちやすい。 |
| A2 橋 (3775,4120) | 横長の橋画像が縦向きの渡河通路に配置され、橋の床が通路/川幅を覆わない。以前は縦長の仮表示だった。向き/寸法のPLAYER QAが必要。 |
| A2 滝 (1200,3560) | 小型の滝画像が導入されたが、茶色の崖と水色の縦長矩形地形は以前のまま残り、接続が不自然。背景の仮形状は以前から存在。 |
| A2 根のアーチ (6206,4360) | 足元が地面に接地し、明確な透過の白縁なし。河川側の背景は簡易地形のまま。 |
| A1 小屋 (5560,1440) | 明確な足元ずれ・白縁・過大なサイズなし。 |
| A1 道標 (1687,5690) | 地面に接地し、矢印を視認できる。明確な白縁なし。 |

ゲーム画像の置換・向き/サイズの調整・地形変更は行っていない。スクリーンショットで確認できる範囲の指摘であり、全ピクセルの境界保証ではない。

## PLAYER QA

- A3結界の閉鎖・割れる途中・開放・紫侵食が見分けられるか、開放後に通行できるか。
- A2橋の向きと足場、滝と背景地形の接続。
- A3未納品古代樹の仮表示、道の継ぎ目。
- 宝箱・植生・石の接地とサイズ、スマホでの表示負荷（Android実機未測定）。

## ロールバック

素材全体を戻す場合:

```bash
git revert -m 1 ce2b3663b031631c858f922ded8390a89ffd48cf
git push origin main
```

比較用branch `rollback/pre-moss-delivered-art` は `0372ef6`。reset / force pushは使用しない。後続変更がある場合は通常のrevert競合を解決して検証する。
