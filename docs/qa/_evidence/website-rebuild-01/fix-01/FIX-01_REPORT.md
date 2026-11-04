# WEBSITE-REBUILD-01-FIX-01 修正記録（Claude自己QA）

- 修正前の基準: `26ea03e4ab2239d4780fb220442a4cd298b705f9`（前回のQA証跡移動を含むHEAD）
- 修正コミット: `6b3af1d4c3ee53b95829e5965c807b606488e1ed`（`site/` のみ）
- 本記録・証跡: このディレクトリ（`_` 始まりのため Pages 非公開）

## Codex報告書の所在
PR #137 のコメント・レビュー、ゲームrepoの全ブランチ、handoff repo（commits / issues / branches）を確認したが、**Codexの33項目報告書と証跡は見つからなかった**（2026-11-04 21:20 JST 時点）。
そのため、ディレクター指示の A〜C は指示文に基づいて修正し、「残り2件」は特定できていない。下記 D は Claude 自身の再監査で見つけた不具合候補であり、Codex の FAIL と一致する保証はない。

## 修正一覧（原因 → 修正 → 検証）
| # | 項目 | 原因 | 修正 | 検証（修正前 → 修正後） |
|---|---|---|---|---|
| A | スマホHERO重なり（A3） | Aidan を `position:absolute; height:40%` で背景に置き、キャッチ・ボタンを `margin-top:auto` で下寄せ → 360/390px でキャッチ×Aidan、ボタン×Aidan が重なる | ≤768px はHEROを4行グリッド（ロゴ／人物／キャッチ／ボタン）に変更。人物は `height:0; min-height:100%` で余白行に収め、縦横比は object-fit contain で維持。ボタンは2列等幅・折返し可 | 重なり 360×640/360×740/390×664/390×844：FAIL → PASS（`qa_site_*.txt`） |
| B | キャッチのコントラスト（C3） | 文字の背後が明るい空・雲。文字影のみで背景パネルなし | キャッチに半透明パネル（rgba(8,13,11,.72)）。SPは枠付き | P99背景輝度で 2.75〜4.22:1 → 11.1〜13.1:1（`contrast_*.txt`） |
| C | 動きを減らす設定（C5） | reduce 時も `.gallery-item:hover img` の `scale(1.03)` が残る（transitionだけ無効） | reduce 時は hover/focus の transform を none。scroll-behavior を全要素 auto | reduce：hover拡大 matrix(1.03…) → none |
| D1 | 横向きスマホ（A5） | 844×390 でHEROが 570px になりボタンが画面外（下端506/390）、ヘッダーの PLAY GAME が2行に折返し | 低い横長画面用にロゴ高さ30svh・ボタン横並び。ナビは `white-space:nowrap`、960px以下はハンバーガー | ボタン下端 506 → 357（/390）、折返しなし |
| D2 | JS無効時（D7） | 遅延画像が `data-src` のみで、JS無効だと12枚が表示されない | 各遅延画像に `<noscript>` フォールバック | 0/12 → 12/12 |
| D3 | その他のコントラスト | STORYの章ラベル（accent #C4A66A）4.1〜4.5:1、ギャラリー見出し（グラデーション）1.4:1 | 章ラベルを #E4CF9A、見出しを不透明度.86の帯に | 30/30 PASS |
| D4 | lightbox の空 `src=""` | 初期HTMLの `<img src="">` は不正なHTML | `src` 属性を削除（開いた時に設定） | — |

## 回帰（Claude自己QA）
- `site/tools/qa_site.js`：修正前（26ea03e）30 PASS / 7 FAIL → 修正後 **37 PASS / 0 FAIL**
- `site/tools/qa_contrast.py`：修正前 13 PASS / 17 FAIL → 修正後 **30 PASS / 0 FAIL**
- 初期表示の転送量は変化なし（PC 4.11MB / SP 4.29MB @DPR1）
- ゲーム本体：タイトル → NEW GAME → エイダンの家、エラー0
- 本記録はClaudeの自己QAであり、最終PASSではない。Codex独立再QAが必要

## BLOCKED（PASS扱いにしない）
- **Google Fonts 実適用**：検証環境から fonts.googleapis.com に接続不可。CSSのURLとウェイト（Cinzel 500/700、Noto Serif JP 500/700、Noto Sans JP 400/500/700）の指定は確認済み。代替フォントでの日本語表示は確認済み。Cinzelの実幅でのナビ折返しは未確認（960px以下はハンバーガーのため影響範囲は 961px 以上）
- **GitHub Pages 公開容量・適合性**：公開元（main・Jekyll）と直近artifact 1,312,331,579 bytes は確認済み。Jekyll 3.10.0 の EntryFilter による再現で `site/` 全件公開・証跡0件。実ビルド（Jekyll本体）と公開URLでの表示は、この環境では未実施
- **Android実機**：未検証（ユーザー担当）

## 証跡
`hero_sp_before/after.webp`（360×640 / 360×740 / 390×664 / 390×844）、`hero_landscape_844_before/after.webp`、`hero_pc_1440_before/after.webp`、`full_pc_1440_before/after.webp`、`full_sp_390_before/after.webp`、`qa_site_before_26ea03e.txt` / `qa_site_after.txt`、`contrast_before_26ea03e.txt` / `contrast_after.txt`
