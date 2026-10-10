# Lind Character Motion Phase 3 — 作業記録(再始動)

BRANCH: `work/lind-character-motion-phase3`(新規。旧ブランチはリモートに存在しないため b04e4c5 から作り直し)
START: `b04e4c5` (Rendering Phase 2 FINAL)
STATUS: **コード側は実装済み / 歩行フレーム画像が未制作(ASSET GENERATION REQUIRED) / PLAYER QA 待ち**
main への merge、push、Pages deploy は行わない。

## 実装済み(コード)
| 項目 | 内容 |
|---|---|
| Crisp HD 全NPC | DEV レビューの既定を Crisp HD + 「全キャラクター/NPC」に変更。Original/Smooth は比較用に選択可能のまま |
| Emma ACTIVE | 既定を ACTIVE(候補)。正式採用は PLAYER QA 判断。CURRENT/NATURAL も選択可 |
| 歩行フレーム汎用化 | `<id>_walk_01`〜`_06` を LindFieldContentBounds に登録すれば自動読込。毎秒4コマ(農夫と同一ケイデンス)。画像が無い NPC は idle のまま(偽アニメなし)。農夫の旧 `_walk` 1枚は従来どおり |
| 漁師の釣り間隔 | 旧: 60秒クールダウン後に18%判定(平均およそ110秒)→ 新: CATCH から CATCH まで 45〜75秒の一様乱数(平均60秒)。BITE/REEL の前置き 2.2秒を逆算し、WAIT がオーバーシュートしない |

## 検証
- `node tests/field/fisherman.test.js`: 30分×4シード、全間隔 45〜75秒、平均 60.3秒。
- ブラウザ内 60分シミュレーション(村生活全NPC、30Hz): 漁師 60回(=1回/分)、全 life NPC が WALK/到着を継続、console error 0。
- 未実施: PC/モバイル実機の見た目、カメラ 1.00–2.10 の全倍率目視、戦闘回帰(コード変更なしのため差分は無いが目視は PLAYER QA)。

## ASSET GENERATION REQUIRED
歩行フレーム(1フレーム = 1枚の透明 RGBA PNG、4〜6枚、既存 idle と同一キャンバス比・足元アンカー、向きは右向きのみ=左は scaleX 反転):
`img/field/lind/npc/villagers/<id>_walk_01.png … _06.png`
対象: farmer_female / young_man / young_woman / elder_man / elder_woman / boy / girl / merchant / innkeeper / caretaker(各 4–6 枚)、farmer_male は既存 walk 1枚を 4–6 枚へ拡張、emma は `img/field/lind/npc/emma/emma_walk_01..` 。
追加後に必要な作業: 各PNGの content bounds を `lind-content-bounds.js` へ登録(既存の監査スクリプトの方式)。
boy / girl は LindChildren 駆動のため、歩行フレームの接続は別途確認が必要。

## 停止点
PLAYER QA。Crisp 既定化、Emma ACTIVE、釣り間隔 60 秒の体感確認をお願いします。
