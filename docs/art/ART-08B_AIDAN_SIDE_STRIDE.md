# DIRECTIVE-ART-08B — エイダン横向きの歩行周期 試験版（90 → 52）

- ブランチ `test/aidan-side-stride`（main `85fa777` から）。**試験版。ユーザー承認なしにマージしない**。正式採用素材は変更なし。正式259PNGのSHAは259/259一致。

## `STRIDE_CYCLE=90` の適用範囲（`js/field/moss-forest-runtime.js`）

| 使用箇所 | 内容 |
|---|---|
| エイダンのコマ送り（62行目付近） | 全方向共通。`phase = floor(dist / (90/コマ数)) % コマ数`。正面・背面（6コマ）と横（4コマ）の両方に効く |
| エイダンの歩行の上下の弾み（68行目付近） | `sin(dist / (90/2) · π)`。全方向共通 |
| フィオナのコマ送り（93行目付近） | フィオナの全方向（横向きの side セットを含む） |

→ 方向ごとに分けられる。今回の試験版では、**エイダンの左右だけ**を新しい定数 `AIDAN_SIDE_STRIDE = 52` に変えた（コマ送りと弾みの両方）。正面・背面とフィオナは90のまま。DEVビルドでは `?aidanSideStride=90` で旧周期と見比べられる。`index.html` のキャッシュ用バージョンも更新。

## 比較

| ファイル | 内容 |
|---|---|
| `docs/art/qa/art-08b/aidan_ingame_side_stride90_x3.mp4` | 実ゲーム（平和村の道）：右→左→下→上と歩く、周期90（`?aidanSideStride=90`）、3倍 |
| `docs/art/qa/art-08b/aidan_ingame_side_stride52_x3.mp4` | 同じ操作、周期52（試験版の既定） |
| `docs/art/qa/art-08b/aidan_side_cadence_compare_offline.gif` | 地面の目盛りに対する足の滑りの比較（左90／右52、オフライン描画） |

所見: 52では接地している足の滑りが半分以下になる。そのぶんコマの切り替えが速くなり、4コマの欠点（04→01で通過のコマがないまま脚が入れ替わる）も目に付きやすくなる。根本的な解決には横6コマ化（ART-08C）が必要。

## QA（実装者による）

回帰テスト（`tools/qa/run_all.sh --gameplay-ready`、このブランチのコミット済みHEAD）: m9_hero・m31_aidan_heading・m10_rilde・m12_attack_ruin・m11_dev_lazy の5本が合格、FAILなし。Androidは未確認（この試験版は録画をPCのみで行った）。
