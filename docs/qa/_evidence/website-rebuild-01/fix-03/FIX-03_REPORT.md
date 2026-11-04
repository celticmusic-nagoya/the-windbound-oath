# WEBSITE-REBUILD-01-FIX-03（Claude自己QA）

- BASE `44dd5e24dc7f919d9931de468a791e5fa8674990`（開始時のPR HEAD・main `e637805` に想定外の更新なし）
- 入力: [Codex FIX-02 QA](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/137#issuecomment-6632674738)（30 PASS / 1 FAIL / 2 BLOCKED。H1はCLSの非悪化条件でFAIL、E1はPR説明）
- 修正コミット `9941187418d74f48a7f70b7f54c276c24834cbe4`（`site/css/site.css` の1行）

## H1：CLS
- 原因: ルーのカード画像だけ `height:auto`。`width`/`height` 属性による比率は `auto` 扱いのため、1×1プレースホルダーの表示中は1:1の箱になり、本画像（720×658）に差し替わる時点で高さが変わっていた
- 修正: `.char-card__figure--small img` に `aspect-ratio: 720 / 658` を固定。他の遅延画像は比率固定の箱（`aspect-ratio` 指定の親＋`height:100%`）内のため影響なし
- 同条件比較（初回読み込み＋全スクロール、7画面×DPR1/2/3＝21条件、Google Fonts遮断）

| | 最大CLS | 発生源 |
|---|---|---|
| FIX-01 `5b8e5a9`（基準） | 0 | — |
| FIX-02 `44dd5e2` | 0.00016593（1440@1x。Codex実測 最大0.00061746） | `IMG｜ルー` |
| FIX-03 | **0（21条件×2回）** | — |

## 回帰
- qa_site.js 42 PASS / 0 FAIL（A5メニュー4サイズ・D4 sizes 54条件・JS無効12/12・reduced-motion・ライトボックス・キーボード）
- コントラスト 30 PASS / 0 FAIL
- HTML: ローカルNu 20.6.30で新規エラーなし（旧版特有の誤検出3件のみ）。**0エラー/0警告の判定は最新版を使うCodexの再検証に委ねる**
- 初回転送 PC 4.11MB / SP 4.29MB（変化なし）
- ゲーム本体: タイトル→NEW GAME→エイダンの家、エラー0（1回目は検証サーバーの一時タイムアウト、再実行でPASS）

## E1
PR説明を現行状態（最新HEAD・最新QA結果・ステータス）中心に書き直し、過去のQA経緯は「履歴」として分離。
