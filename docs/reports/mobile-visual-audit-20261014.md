# モバイル表示監査（2026-10-14）

ブランチ: `work/codex-night-20261014-x3`。基準main: `aba3d8d`。担当: 新規の本MDと同名スクリーンショットディレクトリのみ。X1/X2への依存なし。

PC・縦・横で通常戦/レイダー戦6状態×3画面、代表6マップ×3画面を撮影し、描画/consoleエラー0。
既知の重なりと小さいCOMMANDを維持して記録。横の末尾コマンドはスクロール後に選択可能。
新たな数値確定・ゲーム修正・アセット差替えはせず、タップ領域の判断資料を納品する。

## 実行条件・再現

Chromium、PC1280×720、縦390×844、横844×390、deviceScaleFactor1。縦横はis_mobile/has_touchありのクラウドブラウザでありAndroid実機ではない。独立サーバー8843を各撮影runで自分で起動/終了し、全テスト直列。撮影スクリプトはリポジトリ外 `/tmp/night_x3.py`（SHA256: 0c94bdf30862b1eaea7afc7f985ab2980aa417cd348f402cdbdc9837e09852fb）。許可範囲に合わせてヘルパー・JSON・ログはrepoに追加しない。主要測定値は本MDへ転記。

通常戦: `/index.html?dev=1` → devJump('forest') → A1 ready → closeDialogue() → FieldMonsters.removeAll() → startAttackBattle('forestGob1',112)。異常化/通常ゴブリン複数体の現在の戦闘経路を使用。ボス: closeDialogue() → devJump('raider')。InputManager.state()='BATTLE_COMMAND'後1.6秒待つ。

initial=元の初期表示、open=setNormalCommandDrawer(true)またはsetRaiderCommandDrawer(true)、items=openNormalItems()/openRaiderItems()。APIは画面状態の準備だけに使用し、戦闘数値・CSS・DOMを上書きしない。レイダーの巨大サイズは採用仕様として評価し、縮小を提案しない。

フィールド: storyStage15、MossForest.enter({map:ID}) → encounters(false) / FieldMonsters.setFrozen(true) / closeDialogue() → 下表のfeetへteleportFeet。敵AI/接触を避けた静止画監査であり、自然ストーリー/歩行/性能を検証したものではない。砦はdefault spawn。村はpeace実IDを明示したDEV撮影。Fiona/エイダンの表示を確認、フィールドLouの加入前後網羅は今回未実施。

## 指摘・既知事項（重複起票しない）

| ID | 画面/再現 | 観測・判断 | 重大度/提案 | 画像根拠 |
|---|---|---|---|---|
| MV-K1（既知） | 横/レイダー/initial・open・items | Fiona近接HUDとLouの矩形重なり2451〜2578px²。Louが動くため瞬時値 | 既知、中。既存課題を再起票せずClaudeの対応待ち | [landscape-raider-initial.png](mobile-visual-audit-20261014/landscape-raider-initial.png) |
| MV-K2（決定済） | 縦横/両戦闘/initial | COMMANDが折りたたみ、PCは展開。過去指示の「方針未決」は古い。ユーザーの折りたたみ方針を維持 | 修正不要、採用決定を蒸し返さない | [portrait-raider-initial.png](mobile-visual-audit-20261014/portrait-raider-initial.png) |
| MV-K3（既知） | 縦/レイダー/open・items、横/open、PC/レイダー/open | 展開パネルが味方画像と重なる。縦ボスでは身体がほぼ覆われる。以前のKK/LLと同じ観測 | 既知、中。必要な操作時だけ展開する現方針を維持 | [portrait-raider-open.png](mobile-visual-audit-20261014/portrait-raider-open.png) / [pc-raider-open.png](mobile-visual-audit-20261014/pc-raider-open.png) |
| MV-K4（既知） | モバイル/initial・items | COMMAND 108×34(縦)・112×34(横)。44px基準より高さ不足 | 既知、低。今後のUI検討で44px候補、未適用 | [landscape-normal-initial.png](mobile-visual-audit-20261014/landscape-normal-initial.png) |
| MV-01（操作確認） | 横/両戦闘/open | 初期位置で末尾が切れるがoverflow-y:auto。wheel後、通常19px/ボス62pxスクロールしアイテムを実クリックできた | 低。操作不能とは報告しない。スクロールの存在を示す表示は提案のみ | [landscape-raider-open.png](mobile-visual-audit-20261014/landscape-raider-open.png) / [landscape-raider-scrolled.png](mobile-visual-audit-20261014/landscape-raider-scrolled.png) |
| MV-02（要判断） | 横/両戦闘/items | アイテム2種と戻るの各ボタン180×40px、縦は325×68px。横だけ44px基準を4px下回る | 低。min-height44候補をClaudeへ。端末の誤タップ頻度未測定、最終寸法未確定 | [landscape-normal-items.png](mobile-visual-audit-20261014/landscape-normal-items.png) / [portrait-normal-items.png](mobile-visual-audit-20261014/portrait-normal-items.png) |
| MV-DEV1（DEV限定） | 横/items、PC/items | 左上DEVボタン/DEV BUILDがITEMヘッダと重なる | 低。DEV overlayの問題として分離。本番の不具合とは断定しない | [landscape-normal-items.png](mobile-visual-audit-20261014/landscape-normal-items.png) |

COMMAND/アイテムパネル自体のviewport外突出0、主要hero矩形の画面外突出0。横COMMANDの内部末尾切れはパネル自体のクリップとは区別する。Lou/HUDの重なりはスクリーンショット確認済み。矩形は透明余白も含み、実画素の遮蔽率を意味しない。

## 全画像の一覧・測定値

戦闘18条件の目視を確認。minボタンは現在表示されるコマンド/アイテム（disabledも含む）の実DOM矩形、COMMAND toggleは別計測。hiddenな技を最小値に混ぜない。

| 画面 | 戦闘/状態 | COMMAND可視 / パネル可視 | 表示ボタン最小幅×高さ | 根拠 |
|---|---|---|---|---|
| pc | normal/initial | False / True | 310.0×46.0 | [pc-normal-initial.png](mobile-visual-audit-20261014/pc-normal-initial.png) |
| pc | normal/open | False / True | 310.0×46.0 | [pc-normal-open.png](mobile-visual-audit-20261014/pc-normal-open.png) |
| pc | normal/items | True / False | 180.0×40.0 | [pc-normal-items.png](mobile-visual-audit-20261014/pc-normal-items.png) |
| pc | raider/initial | False / True | 310.0×50.0 | [pc-raider-initial.png](mobile-visual-audit-20261014/pc-raider-initial.png) |
| pc | raider/open | False / True | 310.0×50.0 | [pc-raider-open.png](mobile-visual-audit-20261014/pc-raider-open.png) |
| pc | raider/items | True / False | 180.0×40.0 | [pc-raider-items.png](mobile-visual-audit-20261014/pc-raider-items.png) |
| portrait | normal/initial | True / False | なし | [portrait-normal-initial.png](mobile-visual-audit-20261014/portrait-normal-initial.png) |
| portrait | normal/open | False / True | 170.0×52.0 | [portrait-normal-open.png](mobile-visual-audit-20261014/portrait-normal-open.png) |
| portrait | normal/items | True / False | 325.0×68.0 | [portrait-normal-items.png](mobile-visual-audit-20261014/portrait-normal-items.png) |
| portrait | raider/initial | True / False | なし | [portrait-raider-initial.png](mobile-visual-audit-20261014/portrait-raider-initial.png) |
| portrait | raider/open | False / True | 170.0×68.0 | [portrait-raider-open.png](mobile-visual-audit-20261014/portrait-raider-open.png) |
| portrait | raider/items | True / False | 325.0×68.0 | [portrait-raider-items.png](mobile-visual-audit-20261014/portrait-raider-items.png) |
| landscape | normal/initial | True / False | なし | [landscape-normal-initial.png](mobile-visual-audit-20261014/landscape-normal-initial.png) |
| landscape | normal/open | False / True | 310.0×44.0 | [landscape-normal-open.png](mobile-visual-audit-20261014/landscape-normal-open.png) |
| landscape | normal/items | True / False | 180.0×40.0 | [landscape-normal-items.png](mobile-visual-audit-20261014/landscape-normal-items.png) |
| landscape | raider/initial | True / False | なし | [landscape-raider-initial.png](mobile-visual-audit-20261014/landscape-raider-initial.png) |
| landscape | raider/open | False / True | 310.0×46.0 | [landscape-raider-open.png](mobile-visual-audit-20261014/landscape-raider-open.png) |
| landscape | raider/items | True / False | 180.0×40.0 | [landscape-raider-items.png](mobile-visual-audit-20261014/landscape-raider-items.png) |

フィールド18条件の目視: プレイヤーは表示され、中心付近に収まり、主要画面外クリップや黒/白背景の異常は見つからなかった。世界がviewportより広いため背景の画面端切り出しはカメラの正常動作。モスの斜め光帯は `css/moss-forest.css:60-65` のlight shaftsに対応し、タイル継ぎ目として誤報しない。全tile/全座標の継ぎ目不存在を保証する監査ではない。

| map ID | 実際のfeet | PC | 縦 | 横 |
|---|---|---|---|---|
| rilde_village_01_peace | (1634.46,733.70) | [pc-rilde_village_01_peace-landmark.png](mobile-visual-audit-20261014/pc-rilde_village_01_peace-landmark.png) | [portrait-rilde_village_01_peace-landmark.png](mobile-visual-audit-20261014/portrait-rilde_village_01_peace-landmark.png) | [landscape-rilde_village_01_peace-landmark.png](mobile-visual-audit-20261014/landscape-rilde_village_01_peace-landmark.png) |
| moss_forest_01_sunlit_path | (5560.00,1440.00) | [pc-moss_forest_01_sunlit_path-landmark.png](mobile-visual-audit-20261014/pc-moss_forest_01_sunlit_path-landmark.png) | [portrait-moss_forest_01_sunlit_path-landmark.png](mobile-visual-audit-20261014/portrait-moss_forest_01_sunlit_path-landmark.png) | [landscape-moss_forest_01_sunlit_path-landmark.png](mobile-visual-audit-20261014/landscape-moss_forest_01_sunlit_path-landmark.png) |
| moss_forest_02_mossy_ravine | (3775.00,4120.00) | [pc-moss_forest_02_mossy_ravine-landmark.png](mobile-visual-audit-20261014/pc-moss_forest_02_mossy_ravine-landmark.png) | [portrait-moss_forest_02_mossy_ravine-landmark.png](mobile-visual-audit-20261014/portrait-moss_forest_02_mossy_ravine-landmark.png) | [landscape-moss_forest_02_mossy_ravine-landmark.png](mobile-visual-audit-20261014/landscape-moss_forest_02_mossy_ravine-landmark.png) |
| moss_forest_03_ancient_grove | (3900.00,3420.00) | [pc-moss_forest_03_ancient_grove-landmark.png](mobile-visual-audit-20261014/pc-moss_forest_03_ancient_grove-landmark.png) | [portrait-moss_forest_03_ancient_grove-landmark.png](mobile-visual-audit-20261014/portrait-moss_forest_03_ancient_grove-landmark.png) | [landscape-moss_forest_03_ancient_grove-landmark.png](mobile-visual-audit-20261014/landscape-moss_forest_03_ancient_grove-landmark.png) |
| cliff_moher_01_spiral_ascent | (2280.00,1262.36) | [pc-cliff_moher_01_spiral_ascent-landmark.png](mobile-visual-audit-20261014/pc-cliff_moher_01_spiral_ascent-landmark.png) | [portrait-cliff_moher_01_spiral_ascent-landmark.png](mobile-visual-audit-20261014/portrait-cliff_moher_01_spiral_ascent-landmark.png) | [landscape-cliff_moher_01_spiral_ascent-landmark.png](mobile-visual-audit-20261014/landscape-cliff_moher_01_spiral_ascent-landmark.png) |
| fort_dunvall_01_courtyard | (710.00,990.00) | [pc-fort_dunvall_01_courtyard-landmark.png](mobile-visual-audit-20261014/pc-fort_dunvall_01_courtyard-landmark.png) | [portrait-fort_dunvall_01_courtyard-landmark.png](mobile-visual-audit-20261014/portrait-fort_dunvall_01_courtyard-landmark.png) | [landscape-fort_dunvall_01_courtyard-landmark.png](mobile-visual-audit-20261014/landscape-fort_dunvall_01_courtyard-landmark.png) |

## 詳細観測（重複した状態を含む）

自動の30観測=COMMAND高さ10 + パネル/味方矩形重なり17 + 既知FionaHUD/Lou3。これは30件の新規バグではない。上記IDへ集約した。

| 画面/戦闘/状態 | 項目 | 瞬時値 | 画像 |
|---|---|---|---|
| pc/normal/items | small_tap / toggle | 112.0×34.0 | [pc-normal-items.png](mobile-visual-audit-20261014/pc-normal-items.png) |
| pc/raider/initial | overlap / commands,aidan | 31279.1px² | [pc-raider-initial.png](mobile-visual-audit-20261014/pc-raider-initial.png) |
| pc/raider/initial | overlap / commands,fiona | 608.5px² | [pc-raider-initial.png](mobile-visual-audit-20261014/pc-raider-initial.png) |
| pc/raider/open | overlap / commands,aidan | 31279.1px² | [pc-raider-open.png](mobile-visual-audit-20261014/pc-raider-open.png) |
| pc/raider/open | overlap / commands,fiona | 608.5px² | [pc-raider-open.png](mobile-visual-audit-20261014/pc-raider-open.png) |
| pc/raider/items | small_tap / toggle | 112.0×34.0 | [pc-raider-items.png](mobile-visual-audit-20261014/pc-raider-items.png) |
| pc/raider/items | overlap / items,aidan | 13742.5px² | [pc-raider-items.png](mobile-visual-audit-20261014/pc-raider-items.png) |
| portrait/normal/initial | small_tap / toggle | 108.0×34.0 | [portrait-normal-initial.png](mobile-visual-audit-20261014/portrait-normal-initial.png) |
| portrait/normal/open | overlap / commands,aidan | 5299.4px² | [portrait-normal-open.png](mobile-visual-audit-20261014/portrait-normal-open.png) |
| portrait/normal/open | overlap / commands,fiona | 5029.1px² | [portrait-normal-open.png](mobile-visual-audit-20261014/portrait-normal-open.png) |
| portrait/normal/items | small_tap / toggle | 108.0×34.0 | [portrait-normal-items.png](mobile-visual-audit-20261014/portrait-normal-items.png) |
| portrait/normal/items | overlap / items,aidan | 6316.0px² | [portrait-normal-items.png](mobile-visual-audit-20261014/portrait-normal-items.png) |
| portrait/normal/items | overlap / items,fiona | 6059.5px² | [portrait-normal-items.png](mobile-visual-audit-20261014/portrait-normal-items.png) |
| portrait/raider/initial | small_tap / toggle | 108.0×34.0 | [portrait-raider-initial.png](mobile-visual-audit-20261014/portrait-raider-initial.png) |
| portrait/raider/open | overlap / commands,aidan | 17929.6px² | [portrait-raider-open.png](mobile-visual-audit-20261014/portrait-raider-open.png) |
| portrait/raider/open | overlap / commands,fiona | 18945.8px² | [portrait-raider-open.png](mobile-visual-audit-20261014/portrait-raider-open.png) |
| portrait/raider/items | small_tap / toggle | 108.0×34.0 | [portrait-raider-items.png](mobile-visual-audit-20261014/portrait-raider-items.png) |
| portrait/raider/items | overlap / items,aidan | 16796.1px² | [portrait-raider-items.png](mobile-visual-audit-20261014/portrait-raider-items.png) |
| portrait/raider/items | overlap / items,fiona | 18945.8px² | [portrait-raider-items.png](mobile-visual-audit-20261014/portrait-raider-items.png) |
| landscape/normal/initial | small_tap / toggle | 112.0×34.0 | [landscape-normal-initial.png](mobile-visual-audit-20261014/landscape-normal-initial.png) |
| landscape/normal/open | overlap / commands,aidan | 17227.3px² | [landscape-normal-open.png](mobile-visual-audit-20261014/landscape-normal-open.png) |
| landscape/normal/items | small_tap / toggle | 112.0×34.0 | [landscape-normal-items.png](mobile-visual-audit-20261014/landscape-normal-items.png) |
| landscape/raider/initial | small_tap / toggle | 112.0×34.0 | [landscape-raider-initial.png](mobile-visual-audit-20261014/landscape-raider-initial.png) |
| landscape/raider/initial | overlap / fionaHud,lou | 2450.9px² | [landscape-raider-initial.png](mobile-visual-audit-20261014/landscape-raider-initial.png) |
| landscape/raider/open | overlap / commands,aidan | 19468.3px² | [landscape-raider-open.png](mobile-visual-audit-20261014/landscape-raider-open.png) |
| landscape/raider/open | overlap / commands,fiona | 16969.9px² | [landscape-raider-open.png](mobile-visual-audit-20261014/landscape-raider-open.png) |
| landscape/raider/open | overlap / fionaHud,lou | 2497.1px² | [landscape-raider-open.png](mobile-visual-audit-20261014/landscape-raider-open.png) |
| landscape/raider/items | small_tap / toggle | 112.0×34.0 | [landscape-raider-items.png](mobile-visual-audit-20261014/landscape-raider-items.png) |
| landscape/raider/items | overlap / items,aidan | 19468.3px² | [landscape-raider-items.png](mobile-visual-audit-20261014/landscape-raider-items.png) |
| landscape/raider/items | overlap / fionaHud,lou | 2578.2px² | [landscape-raider-items.png](mobile-visual-audit-20261014/landscape-raider-items.png) |

## 追加スクロール確認

横の開いたパネル上でmouse wheel600（Chromium）→末尾まで移動→アイテムをforce無しでクリック→#normalItems visible=trueを確認。
通常: scrollTop19/max19、ボス:62/max62。[landscape-normal-scrolled.png](mobile-visual-audit-20261014/landscape-normal-scrolled.png) / [landscape-raider-scrolled.png](mobile-visual-audit-20261014/landscape-raider-scrolled.png)
これはブラウザのwheel/クリックの確認であり、Android実機の指スワイプの代用ではない。

## テスト結果・未確認・Claudeへの確認依頼

撮影36/36完了 + スクロール追加2/2合格、PNG38枚。撮影run console/pageerror0。スクロールrunも例外なしで完了（全console監視は36撮影runのみ）。厳密なUI仕様合否テストではなく監査。重大な新規描画停止は観測されず、UI候補は上記表へ記録。

未実施: Android実機/fps/転送量、戦闘演出中/KO/勝利/セーブロード、全フィールド座標、タイル全件網羅、Chrome実機のツールバー伸縮/指の操作。全回帰はこのタスクに含まれず未実施。スクリーンショットのiframeサイズはviewport固定、safe areaノッチの再現なし。3画面以外の小型端末は未撮影。

Claudeへ: 横アイテムの40→44px候補の採否と既知HUD/Lou対応を判断してください。モバイルCOMMAND初期折りたたみの決定は維持。採用素材/ゲームコードを変更していない。mainへマージ/PR作成なし。統合はClaude担当、main未更新なのでロールバック不要。STATUS: READY（監査完了、全指摘修正済みという意味ではない）。

追加ファイル: 本MD + `docs/reports/mobile-visual-audit-20261014/*.png`38枚。commitは本ブランチ履歴とチャット納品表を参照。
