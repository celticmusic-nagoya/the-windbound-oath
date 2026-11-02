# DIRECTIVE-ART-05D — 王国一般兵士 正式採用画像の実装

- 基準 main `312bfb4` → ブランチ `feat/soldier-front-idle-v2`。**mainマージはユーザー承認待ち**。
- 採用画像: `img/field/moss/props/npc_soldier_idle_v2.png`（＝ART-05の`soldier_front_idle_112x168_alphafix_candidate.png`、SHA-256 `bd2c994ec87cc1290368ebff8dbe5098a2942b9ecb444f4d473d34d3bdda1957`、112×168）。

## A. 画像検証（納品原本 `54a42877…` との比較）

| 項目 | 結果 |
|---|---|
| RGBの差分 | **0px**（全画素一致） |
| α変更 | 8,805px。変更前のαは240〜254の範囲だけで、すべて255になった |
| その他のα | 0・1〜239・255の画素は変更なし |
| 形状（α>0の範囲） | 完全一致 |
| 槍・盾・兜・赤い房・足元 | 欠損なし（房の先端が上端に接する点は原画どおり。ART-05の軽微ADJUSTのまま） |

→ αの修正以外に差分はない。

## B. 実装

| 変更 | 内容 |
|---|---|
| `img/field/moss/props/npc_soldier_idle_v2.png` | 新規追加（採用画像）。旧`npc_soldier.png`は削除せずrollback用に残した |
| `img/field/moss/manifest.json` `^npc_slot_soldier$` | file→`props/npc_soldier_idle_v2.png`、表示 56×84 → **47.6×71.4 world**（0.85倍＝村人と同じ高さ）。下中央anchorの方式は従来どおり。`walk`（旧6コマ）は**変更なし** |
| `tools/moss/make_npcs.py` | 再生成ツールが採用済みのルール（`gen`がmake_npcs以外）を上書きしないようにした（再実行で旧兵士に戻る事故の防止） |

イベント・当たり判定・SAVE・戦闘・マップ遷移・map JSONは変更していない。正式259PNGのSHAは259/259一致。

**既知の暫定状態**: 巡回兵（砦の城壁`w_f2_lookout`、王都城前広場`w_r2_herald`）は、立ち止まると新しい正面idle、歩くと旧`npc_soldier_walk_01〜06`になる。旧コマは新しい表示枠（47.6×71.4）に縮小して描かれるので表示は壊れないが、**歩行中だけ旧兵士の画風に切り替わる**。正式な歩行6コマの制作は次工程。左向きの歩行で絵全体が左右反転する（盾が反対側に移る）のは、すべての巡回NPCに共通する既存の挙動。

## C. QA

| 区分 | 結果 |
|---|---|
| 回帰テスト（`tools/qa/run_all.sh --gameplay-ready`、コミット済みHEADのスナップショット） | m8_town_maps・m10_rilde・m12_attack_ruin・m11_dev_lazy の4本が合格、FAILなし、consoleエラー0 |
| 実描画（`docs/art/qa/art-05d/results.json`） | 襲撃後の村`p_rr_knight`・砦主塔`p_f3_armory`の固定NPC、王都の巡回兵`w_r2_herald`が、PC／Android横相当／縦相当の全9ケースで新画像を読み込み、47.6×71.4で表示。ページエラー0 |
| 画像 | `docs/art/qa/art-05d/qa_soldier_viewports.png`（3場所×3画面）、`qa_soldier_zoom2x.png`（2倍拡大、巡回兵は3時点） |
| Android | 画面サイズのエミュレーションのみ。**実機QAは未実施**（ユーザー確認待ち） |

再現: `python3 -m http.server 8765` → `python3 tools/art/qa_art05d.py`。
