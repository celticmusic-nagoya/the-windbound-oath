# LAYER0-MALE-TRIO-REGISTER-01 — 原本登録済み / 透過正本BLOCKED

基準main: `cab9aa52da653198a712bd986992adc03ea4bfe2`。Draft PR #267。

## 登録内容

原本3点を `assets/characters/{aidan,liam,bram}/layer0/originals/` にバイト無変更で保存。元添付とのSHA-256一致を確認。原本RGBA PNG2点も背景を含め全画素alpha255。リアムは今回受領したJPEG実体を保護し、PNG原本と偽らない。

| 対象 | 原本 | 解像度 / mode | SHA-256 |
|---|---|---|---|
| エイダン | aidan_layer0_fourview_original.png | 1536×1024 / RGBA | 60baa676f6f9b2f5d7be957370fe1e7ec5d7c5b19edde1c06fb530ce95ed5716 |
| リアム | liam_layer0_fourview_original.jpg | 1280×853 / RGB | 9b44529a744fd135d45ba2f4fa09c82b67d9135c9f813595ff8ed324e82c0259 |
| ブラム | bram_layer0_fourview_original.png | 1536×1024 / RGBA | 28029eeb80ff5753c3dd40f8b6fbb620004fb3cfa3bcb796925111766d542831 |

## 背景処理: 各2回、上限到達で停止

image_genへ背景のみalpha0・人物維持を指定。1回目の結果を検証後、2回目は背景完全除去・人物画素および解像度保護を再指定した。2回とも人物RGB差分があり、リアムは1536×1024に変更されたため不採用。RGB差分は原本と同座標かつ加工後alpha>0で算出し、マスク内の原本画素保持ができないことを確認した。alpha0の画素は存在するが、これは背景全域の正確な切り抜きや輪郭無欠損のPASSを意味しない。

| 対象 | 1回目: 可視RGB変更画素 | 2回目: 可視RGB変更画素 | 結果 |
|---|---:|---:|---|
| エイダン | 590017 | 593623 | 原本画素保持FAIL |
| リアム | 解像度不一致で比較不可 | 解像度不一致で比較不可 | 解像度保持FAIL |
| ブラム | 805172 | 846111 | 原本画素保持FAIL |

6点を `assets/candidates/layer0-male-trio-register-01/{character}/background_attempt_0{1,2}.png` に不採用証跡として保存。SHA・解像度・RGBA・alpha統計は各MANIFESTとRECEIVED_IMAGE_QA.jsonに記録。生成PNGの隠れたRGBに背景色が残っていても、alpha0部分は不透明背景として数えない。

停止理由: 背景除去と人物維持を同時に満たさず、指定の2回上限に到達。3回目の処理や別手法による追加加工は実施しない。今後の代替は原本RGBを固定した手動マスク制作、または背景除去専用セグメンテーション。ただし今回の上限を越えて継続しない。

## 正本・採用・QA

指定の `assets/characters/{character}/layer0/{character}_layer0_fourview_master.png` は3点とも未登録。失敗画像をmasterへ置かない。エイダンのLayer 0デザイン正式採用は維持、リアム・ブラムは候補のまま。既存正式デザインに変更なし。

3枚とも正面、画面左向き側面、画面右向き側面、背面の4全身図を目視確認。エイダンの茶髪・緑黒金インナー、リアムの赤バンダナ・赤黒金インナー、ブラムの赤毛長髪・編みひげ・大型体格・茶黒金インナーを原本で確認。12方向の関節・体格・髪・衣装の測定整合性はNOT_RUN。人物基準の左右側面はアンカー計測時に確認する。切り抜き出力の輪郭無欠損・完全背景alpha0はNOT_PROVEN、原本画素保持はFAIL。独立画像QAはNOT_RUN。

共通17ボーンはPR #246固定コミット `a45ca2815675a4d186f08624de8d0329a6ed730c` の名前・親子関係を確認。17個一意・親参照解決はPASS。main採用とはみなさず、モルウェンの座標を他体格へ流用しない。原本から人型の関節対応を検討できるが、未計測・未接続のため互換性PASSとはしない。髪・ひげ・バンダナの付着・遮蔽も未検証。

再現検証: `python docs/qa/layer0-male-trio-register-01/verify_registration.py`。原本と不採用出力のSHA・実寸・mode・alpha極値、上限、master未作成、基準mainの既存ファイル無変更を確認。

mainマージ・ゲーム組込・サイト公開なし。Blenderリグ制作はモルウェン完成後に再開する。
