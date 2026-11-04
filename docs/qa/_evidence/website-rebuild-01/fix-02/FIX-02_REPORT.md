# WEBSITE-REBUILD-01-FIX-02 修正記録（Claude自己QA）

- 作業開始時: PR #137 HEAD `5b8e5a94c1febd6ffbbdff279342813bef15660c` / main `e63780543d7ba1719a39a2f68b9924dc6d5b3933`（想定外の更新なし）
- 入力: [Codex独立再QA](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/137#issuecomment-6630994528)（28 PASS / 3 FAIL / 2 BLOCKED、H1 FAIL 24件）
- 修正コミット: `f42c5947dc2a6f03fe01e9b09434d71e3008e2c8`（`site/` のみ）
- 文書・証跡コミット: QA指示書（E1）と本ディレクトリ

## 修正（原因 → 修正 → 検証）
| ID | 原因 | 修正 | 検証（修正前 5b8e5a9 → 修正後） |
|---|---|---|---|
| A5 (P2) | 960px以下のメニューに高さ制限・縦スクロールがなく、844×390では6リンク目が下端から15.81pxはみ出す | `.site-nav` に `max-height: calc(100dvh - var(--header-h))`（100vhフォールバック）＋`overflow-y:auto`＋`overscroll-behavior:contain`。低い横長画面では行間を縮小 | 最終リンク下端 405.81 → 337.81（/390）。390×844・360×640・768×1024も画面内。Escでトグルへフォーカス復帰 |
| D4 (P3) | ギャラリーが `auto-fill` で列数が暗黙的に変わるのに、sizesは `46vw, 290px` の2段階のみ | 列数を明示（≥1184px:4列／883–1183px:3列／≤882px:2列）し、sizesを同じ区切りの計算式にした。登場人物カードも同様に実幅に合わせた | 9幅×DPR1/2/3＝27条件×2種で、申告幅と実幅の乖離 最大9.8% → 6%以内、候補不足0。844@1xは 360w → 640w を選択 |
| E1 (P3) | QA指示書の許可パスに、追加した2文書が含まれていない | 指示書E1に許可対象4つを明記。報告形式の「31項目」を「33項目」に訂正。PR説明を同期 | 文書のみ |
| H1 (P2) | 遅延画像が `data-src` のみで `src`/`srcset` がない（13件）、`srcset` なしの `sizes`（11件） | 遅延画像に有効な1×1プレースホルダー（`img/placeholder.gif` 42B）を `src` に設定。`sizes` は `data-sizes` に移し、JSが `srcset` と同時に設定。ライトボックス画像にも同じプレースホルダー | 24件 → 0件（下記の検証器の注記を参照） |
| 追加 | faviconがゲームの看板素材（1,093,660B）を直接参照 | 64px派生PNG（2,294B）を `site/img/` に作成。原本は不変 | 初回転送 −1.09MB |

## HTML検証
- 使用した検証器: Nu HTML Checker **20.6.30**（ネット制限のため最新版を取得できず、公開リポジトリ同梱のjarを使用）
- 修正前: 27件 ＝ Codex指摘の24件（src欠落13、sizes単独11）＋旧版の誤検出3件
- 修正後: **3件。いずれも旧版の誤検出**（`img` の `fetchpriority`、`source` の `width`/`height`。現行HTML仕様では有効で、Codexが使った26.11.4では出ていない）
- Codex指摘の24件は0件。**最新版（26.11.x）での0件確認はCodexの再検証待ち**
- 警告2件（旧版）: `dialog` のブラウザ対応、`dialog` 上の `aria-label`。エラーではない

## 転送量（DPR1、Google Fonts除く）
| | 修正前 5b8e5a9 | 修正後 |
|---|---|---|
| PC 初回（favicon込み） | 4.11MB + 1.09MB = 約5.20MB（Codex実測 5,183,700B） | 約4.11MB |
| SP 初回（favicon込み） | 4.29MB + 1.09MB = 約5.38MB（Codex実測 5,365,264B） | 約4.29MB |
| 全スクロール後 PC / SP | 9.01 / 9.19MB | 9.01 / 9.20MB |
| 高DPR 全スクロール後 | 13.3〜13.5MB | 13.31〜13.49MB |
- Playwrightのヘッドレス計測ではfaviconが要求されないため、faviconはファイルサイズで加算

## 回帰（Claude自己QA）
- `qa_site.js`: 修正前 40 PASS / 2 FAIL（A5・D4を検出）→ 修正後 **42 PASS / 0 FAIL**（横スクロール6幅、画像・CLS0・lazy、ナビ、メニュー、ライトボックス、キーボード、reduced-motion、JS無効12/12、HERO重なり7サイズ、メニュー4サイズ、sizes 54条件）
- `qa_contrast.py`: 30 PASS / 0 FAIL
- ゲーム本体: タイトル → NEW GAME → エイダンの家、エラー0
- 本記録は自己QA。最終判定はCodex独立再QA

## BLOCKED（PASS扱いにしない）
- F4 Google Fonts 実適用（接続不可）
- F3 Pages公開容量（Jekyll実ビルド未実施、artifact API空）
- Android実機
- Nu 26.11.x による最新版での0件確認（Codex側）
