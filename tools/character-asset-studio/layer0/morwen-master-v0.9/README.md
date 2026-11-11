# モルウェン Layer 0 関節構造改善 v0.9（MORWEN-LAYER0-02）

**状態: 未承認の候補。Layer 0 の正式採用は NOT_RUN（ディレクターが判断する）。** v0.8 の成果物は上書きしていない（別フォルダ、ハッシュを照合済み）。

作り方: `python3 tools/character-asset-studio/pipeline/cas.py articulated-body --v08-spec tools/character-asset-studio/layer0/morwen-master-v0.8/MASTER_BODY_SPEC.candidate.json --transforms tools/character-asset-studio/normalized/morwen-final-canon-20261111/view_transforms.json --out-l0 <このフォルダ> --out-l1 tools/character-asset-studio/layer1/morwen-base-v0.9 [--overwrite]`

## 改善した構造（中立的なマネキン形状のまま。性的な身体表現はない）
| 部位 | 変更内容 |
|---|---|
| 頭部 | 頭蓋（楕円）、顎（多角形）、首（先細りの円柱）を別の形にした。首は頭蓋の下・後ろの `neckTop` につながる |
| 肩 | 肩甲帯（首の付け根から両肩へ）、肩の球関節、先細りの上腕で、なめらかにつないだ |
| 胴体 | 胸郭（卵形）・腰・骨盤を、輪郭線のある別のブロックにした |
| 股関節 | 球関節を回転の中心 `hipL`／`hipR` に置き、＋印で示した |
| 四肢 | 肘・手首・膝・足首を球関節にして、間を先細りの部位でつないだ |
| 足 | かかと・母趾球・つま先の支点を追加した。接地点 (600, 1540) と接地範囲（−50〜+50）は v0.8 と同じ |

## 関節座標
- `MASTER_BODY_SPEC.v0.9.candidate.json`: 3D関節、運動の木構造、歩行用の回転軸（股・膝・足首・母趾球・かかと・肩・肘・腰・首、範囲はすべて設計値）、4方向の投影座標。
- `JOINT_CHANGES_v0.9.json`: v0.8 の関節座標の変更は **0件**。追加した関節は12個（neckTop、jawL/R、waist、heelL/R、ballL/R、toeL/R、handL/R）で、それぞれ理由を書いている。追加した関節はすべて DESIGNED_CANDIDATE。

## ファイル
| ファイル | 内容 |
|---|---|
| `*_articulated_guide.png` | 4方向のガイド（基準線と回転中心つき） |
| `*_layer0_part.png` | ラベルなしの Layer 0 パーツ |
| `compare_4views_structure.png` | 4方向の構造比較 |
| `*_stack_with_canon.png` | Layer 0＋1 を正本（Layer 2・3 にあたる）の下に重ねた確認用 |
| `LAYER01_MODULAR.json` | Layer 0／1 を `cas/modular-character/0.7` にまとめたもの |
| `LAYER01_QA_v0.9.json` | レイヤーの検査（各レイヤーの ON/OFF を含む） |
| `layer_onoff_previews/` | 各レイヤーの ON/OFF 合成と、4方向の比較 |
| `BODY_QA_v0.9.json` | QA |
| `MANIFEST.json` | SHA-256 |

## QA（`BODY_QA_v0.9.json`：PASS 47／FAIL 0／BLOCKED 0／NOT_RUN 16）
| 区分 | 項目 | 結果 |
|---|---|---|
| 自動 | 4方向のキャンバス・接地点 (600, 1540)・頭頂 175 | PASS |
| 自動 | 頭身・関節の高さ・脚の長さが4方向で一致 | PASS |
| 自動 | 正面と背面の鏡像、左右の側面の鏡像 | PASS |
| 自動 | 骨格がつながっている（全関節が骨盤に到達する）、左右の部位の長さが同じ | PASS |
| 自動 | 描いた形の中で関節が途切れていない（4方向とも1つの形） | PASS |
| 自動 | 歩行用の回転軸（回転中心は動かず、部位の長さは保たれ、子の関節だけが動く） | PASS |
| 自動 | かかと・母趾球・つま先が接地線上にある | PASS |
| 自動 | v0.8 の関節が変わっていない、v0.8 の成果物が変わっていない | PASS |
| 自動 | Layer 1 が Layer 0 に沿っている（4/4）、Layer 1 が胴体と腰を完全に覆う（4/4） | PASS |
| 自動 | Layer 0／1 が正本（Layer 2・3）の内側に収まる割合（L0: 99.99／99.7／98.8／99.2%、L1: 99.8／99.4／98.0／98.8%） | PASS |
| 自動 | 正本17件の SHA-256 | PASS |
| 人間（NOT_RUN） | 独立した目視レビュー、Layer 1 が露出の少ないデザインかの確認、デザイン保護12項目、Layer 0／Layer 1 の最終採用 | NOT_RUN |
