> **2026-11-08正式設定更新**: モルウェンは王立魔法学院首席生徒（17歳）であり、王立魔法研究院の特例研究協力生。旧文書の「研究院所属」「研究院首席生徒」はこの新設定で読み替える。参照: `docs/lore/MORWEN_CANON_20261108.md`。HDドット補足: `docs/design/FIELD_HD_PIXEL_ART_DIRECTION_20261108.md`。

# FIELD-VISUAL-OVERHAUL-06 — 公式デザイン準拠・HDピクセル制作規約
2026-11-08 / 正式制作方針 / **画像制作・全キャラ一致検証は未完了**

## 絶対条件
- 公式Webサイトとゲーム本編の**正式採用キャラクターイラスト**を正本として参照。サイトの表示画像とGitHubの採用原本に不一致があれば**推測で統合せず**差分を記録する。
- RO/HD-2Dは表現上の方向性であり、第三者ゲームの素材・固有デザイン・ロゴを複製しない。
- **2.8–3.0頭身**を人型基本。高密度ピクセル、手打ち感のある明瞭な輪郭と選択的な階調、髪・布・金属・タイツの光沢を重厚な25–30°クォータービュー背景と調和させる。縮小しただけのイラストを正式ドット絵と扱わない。
- 32/40/48pxの実表示で顔・瞳・装備・足元が識別可能なこと。画像ファイルの内部解像度とゲーム上の表示サイズを区別する。
- キャラの**個性・年齢・役割**を優先。年齢不相応な体型の強調を一律適用しない。**17歳のエイダンとモルウェンの性的強調は禁止**。モルウェンは知的で凛とした公式制服と黒タイツを再現。成人と確認されたキャラのみ適切なスタイル表現を適用。
- エマはフィオナの養母で銀灰髪・丸眼鏡・仕立て屋のエプロンドレス、背を少し丸めた包容力ある老婆。若返らせない。

## 正式デザイン参照と確認事項
| キャラ | 参照元の候補（正本判定は別途） | 固有の描画ポイント |
|---|---|---|
| エイダン | `assets/images/characters/portraits/aidan/aidan_normal.png` | 17歳。公式髪型・顔・青金装束・肩当て・背中の剣 |
| フィオナ | `assets/images/characters/portraits/fiona/fiona_normal.png` | 聖導士。長い髪・ロングローブ・優しさと芯の強さ |
| セレナ | `assets/companions/serena/master/serena-full-body-v1.png` | 正式衣装と髪飾り、成人設定を確認の上でS字姿勢 |
| モルウェン | `assets/companions/morwen/master/morwen-full-body-v3.png` | **王立魔法研究院**首席生徒・17歳。眼鏡、公式制服、黒タイツ、ブーツ |
| エマ | `assets/images/characters/portraits/emma/emma_normal.png` | 老婆・銀灰髪・丸眼鏡・仕立て屋のエプロンドレス |
| リアム | `assets/companions/liam/source/liam_character_design_04.png` | **候補・個別正式採用未確認**。弦楽器・弓・探索者装束 |
| ブラム | `assets/companions/bram/master/bram-full-body.png` | **MANIFESTのapproved表記を確認**。髭・ドワーフ体型・ルーン盾 |
| ルー | `assets/images/characters/portraits/lou/lou_normal.png` | 小型の妖精・浮遊・発光 |
参照画像は原本のまま保持。公式サイトの参照URL: https://celticmusic-nagoya.github.io/the-windbound-oath-website/ 。表示画面と正本の照合・原本画像の画素単位の目視照合は**NOT_RUN**。

## ファイル形式と本番ゲート
- 正式化前は `assets/candidates/field-hd-pixel/<character>/<direction>.png` に新規追加。**背景透明RGBA PNG**、方向 `down,left,right,up`、全方向同一キャンバス寸法と足元anchor。各原本はSHA-256で記録。
- 生成物はシート・比較画像・キャラ単独透過画像を区別。**背景つき比較シートの自動切り出しを「透明PNG完成」と見なさない**。
- `scripts/qa_field_hd_pixel.py` で候補PNGの透過・サイズ・足元・4方向・SHAを検証。CI PASSだけでデザイン一致は保証されない。**人間による公式画像比較、32/40/48px表示とAndroid実機確認**は別の必須ゲート。
- JS/CSS静止方向スプライト+揺れは既存 `js/field/field-sprite-motion.js` を使用。動作は表示専用でSAVE/衝突/当たり判定に影響しない。
- QA全項目PASSした新規候補だけ採用台帳を更新して段階切替。未検証素材のmain登録は「候補」のまま許容するが、**本番参照切替はしない**。
- 既存正式PNGの上書き・削除禁止。旧歩行PR #139/#140/#144/#145/#153/#154 HOLD。

## 実行状況
規約と候補QAの実装のみ。新しい公式合致スプライト、シート、全方向透過PNGの納品、ブラウザ目視/Android実機QAは**未実施**。実機の自動遠隔操作がない場合はPASSと報告しない。
