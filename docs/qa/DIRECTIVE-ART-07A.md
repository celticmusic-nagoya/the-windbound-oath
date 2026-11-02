# DIRECTIVE-ART-07A — 王国一般兵士 歩行6コマの正式実装

- 基準 main `85fa777` → ブランチ `feat/soldier-walk-v2`。**mainへのマージはユーザー承認待ち**（Draft PR）。
- 採用素材: ART-06Rの6コマ（採用idleの脚パーツ差分）。`img/field/moss/props/npc_soldier_walk_v2_01〜06.png` は、レビューした候補とバイト単位で同一（SHA先頭: `aa1ff653` `2ff7ac98` `d3d76d71` `96b06b3d` `0ed92836` `6840d1d0`）。

## 変更

| ファイル | 内容 |
|---|---|
| `img/field/moss/props/npc_soldier_walk_v2_01〜06.png` | 新規追加 |
| `img/field/moss/manifest.json` `^npc_slot_soldier$` | `walk.file` → `props/npc_soldier_walk_v2_{n}.png`（6コマ）。idle・表示サイズ47.6×71.4 world・anchorは変更なし。fpsはゲーム側の既定値7のまま |
| `docs/assets/ASSET_CHANGELOG.md` | 1行追記 |

旧`npc_soldier_walk_01〜06.png`はrollback用に残した（参照は外れている）。イベント・当たり判定・SAVE・戦闘・遷移・map JSONは変更していない。正式259PNGのSHAは259/259一致。

## QA（実装者による。独立QAはCodex待ち）

| 区分 | 結果 |
|---|---|
| 回帰テスト（`tools/qa/run_all.sh --gameplay-ready`、コミット済みHEAD） | m8_town_maps・m10_rilde・m12_attack_ruin・m11_dev_lazy の4本が合格、FAILなし、consoleエラー0 |
| 実行時の確認（`tools/art/qa_art07a.py` → `docs/art/qa/art-07a/results.json`） | 巡回兵2体（王都 城前広場`w_r2_herald`、砦 城壁`w_f2_lookout`）× PC／Android横相当／縦相当 の6ケースすべてで次を確認 |
| ・素材の読み込み | 兵士の画像リクエストはすべてHTTP 200。歩行中はv2の6コマだけ、停止中は採用idleだけを表示 |
| ・タイミング | コマの切り替え間隔の中央値は128〜141ms（40ms間隔のサンプリングのため誤差あり。設定値は7fps≒143ms） |
| ・左右反転 | 向きが左（dir<0）のときだけ`scaleX(-1)`。全サンプルで一致 |
| ・途中からの再開 | 休止後の歩き出しは walk_03／walk_05 から始まり、前回止まったコマから続く（最初のコマに戻らない） |
| ・表示 | 枠は常に47.6×71.4、足元の下中央配置のずれは0 |
| 画像 | `docs/art/qa/art-07a/qa_walkers.png`（歩行中の1コマ、3倍） |
| Android | 画面サイズのエミュレーションのみ。**実機QAは未実施** |

再現: `python3 -m http.server 8765` を起動したうえで `python3 tools/art/qa_art07a.py`。
