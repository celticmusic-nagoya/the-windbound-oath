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
| 歩行フレーム汎用化 | `<id>_walk_01`〜`_06` を LindFieldContentBounds に登録すれば自動読込。歩行4fps(農夫と同一)/走り6fps。移動中のみ進む専用クロック。画像が無い NPC は idle のまま(偽アニメなし)。農夫の旧 `_walk` 1枚は従来どおり |
| 漁師の釣り間隔 | 旧: 60秒クールダウン後に18%判定(平均およそ110秒)→ 新: CATCH から CATCH まで 45〜75秒の一様乱数(平均60秒)。BITE/REEL の前置き 2.2秒を逆算し、WAIT がオーバーシュートしない |

## 検証
- `node tests/field/fisherman.test.js`: 30分×4シード、全間隔 45〜75秒、平均 60.3秒。
- ブラウザ内 60分シミュレーション(村生活全NPC、30Hz): 漁師 60回(=1回/分)、全 life NPC が WALK/到着を継続、console error 0。
- 未実施: PC/モバイル実機の見た目、カメラ 1.00–2.10 の全倍率目視、戦闘回帰(コード変更なしのため差分は無いが目視は PLAYER QA)。

## 歩行フレーム素材(2026-10-10 受領)
ユーザー提供の素材を取り込み済み(`tools/lind/prepare_walk_frames.py` + `walk_frames_manifest.json`)。1フレーム=1枚の透過RGBA PNG、idle と同一キャンバス・同一スケール(幾何は idle の bounds を使用)。

| NPC | 枚数 | 状態 |
|---|---|---|
| farmer_female | 4 | 組込み済み |
| boy / girl | 各4 | 組込み済み(走り RUN/CHASE は 6fps、歩行は 4fps) |
| emma | 3 | 組込み済み(依頼は 4〜6 枚。3 枚循環は硬く見える可能性。追加歓迎) |
| farmer_male | 1(既存) | 変更なし。4〜6 枚への拡張は未 |

フレーム順: 受領ファイル名がランダムのため、循環ポーズ距離が最小になる順を採用(差が小さく順序は断定できない)。違和感があれば `walk_frames_manifest.json` の `frames` を並べ替えて `python3 tools/lind/prepare_walk_frames.py <素材フォルダ> --write-bounds` を再実行。

## ASSET GENERATION REQUIRED(未受領)
この環境では画像を生成できません。以下の歩行フレーム(4〜6枚/体、透過RGBA PNG、idle と同一キャンバス、右向き)が必要です:
young_man / young_woman / elder_man / elder_woman / merchant / innkeeper / caretaker。
配置: `img/field/lind/npc/villagers/<id>_walk_01.png …`。受領後に manifest へ追記して上記スクリプトを実行するだけで組み込めます。
fisherman は専用の釣りポーズ系で別管理(歩行は対象外)。

## メモリ・負荷の注意
各フレームは idle 同様のフル解像度(約1MB、展開時約6MB)。15枚追加で `img/field/lind/npc` は約30MB。全NPC分を足すと展開メモリが増えるため、モバイルで問題があれば表示解像度に近い縮小版への置換(幾何は bounds で吸収)を検討。

## 停止点
PLAYER QA。Crisp 既定化、Emma ACTIVE、釣り間隔 60 秒の体感確認をお願いします。
