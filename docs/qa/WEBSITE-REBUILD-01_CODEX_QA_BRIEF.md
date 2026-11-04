# WEBSITE-REBUILD-01｜Codex独立QA指示書（PR #137）

- 対象PR: https://github.com/celticmusic-nagoya/the-windbound-oath/pull/137 （Draft）
- 対象ブランチ: `feature/website-rebuild-01`
- **QA対象SHA（固定）: PR #137 の依頼コメントに記載した40桁SHA**（依頼時点のPR最新HEADと一致させる。開始前に `git ls-remote origin feature/website-rebuild-01` で一致を確認し、不一致なら BLOCKED として報告し再指定を待つ）
- ベース: main `e63780543d7ba1719a39a2f68b9924dc6d5b3933`
- 実装者: Claude Code（自己QA 28 PASS / 0 FAIL：`docs/qa/_evidence/website-rebuild-01/qa_result.txt`）。本QAは実装者以外による独立QA。
- 環境: Claudeの作業環境とは別の、独立した環境（クリーンなclone）で検証する。
- 権限: 読み取り・ローカル実行のみ。**コード修正・commit・push・mainマージ・公開設定変更は禁止**。不具合は再現手順と修正案で報告。

## 0. 前提
```
git fetch origin feature/website-rebuild-01
git checkout <QA対象SHA>
python3 -m http.server 8765        # リポジトリルートで起動
# サイト: http://localhost:8765/site/   ゲーム: http://localhost:8765/
```
Claudeの自己QAスクリプトは `site/tools/qa_site.js`。**その結果を流用せず、自分のテストで判定すること**（スクリプト自体の妥当性もレビュー対象）。

## 1. 判定項目（各 PASS / FAIL / BLOCKED、根拠を1行）

### A. PC・スマートフォン表示
- A1 1440×900 / 1280 / 1024 / 768 / 390×844 / 360×740 で横スクロールなし
- A2 8セクション（HERO〜FOOTER）が全幅で崩れず、文字の重なり・はみ出しなし
- A3 スマホHERO: ロゴ上部・エイダン左下・キャッチ・ボタンが重ならず判読可
- A4 画像の縦横比維持（引き伸ばしなし）、透過素材の背景に白抜け・黒縁なし
- A5 横向きスマホ（844×390）の表示

### B. ナビゲーション・ライトボックス
- B1 ヘッダーの6リンクが各セクション先頭へ移動（固定ヘッダーで見出しが隠れない）
- B2 スマホメニュー: 開閉・リンク選択で閉じる・Escで閉じる・`aria-expanded` 連動
- B3 ギャラリー: クリックで拡大、前/次、閉じる、背景クリックで閉じる、7枚で循環
- B4 PLAY GAME（3箇所）がゲーム本体 `../` へ遷移、ABOUT THE GAME が STORY へ

### C. アクセシビリティ
- C1 キーボードのみで全操作（Tab順、skip link、Enterで拡大、←/→、Esc、閉じた後のフォーカス復帰）
- C2 フォーカス表示が全インタラクティブ要素で視認できる
- C3 コントラスト（WCAG AA）: 本文・サブ文字（#AAB7AC on #1B2B25 等）・HEROキャッチ・ボタン
- C4 画像alt（装飾は空alt）、見出し階層（h1→h2→h3）、landmark（header/nav/main/footer）
- C5 `prefers-reduced-motion` でスムーズスクロール・ホバー拡大が止まる
- C6 axe-core等の自動検査があれば実施（違反の重大度付きで列挙）

### D. 画像読み込み・表示速度
- D1 初回表示の転送量（Claude計測: PC/SP 約4.1〜4.3MB、全スクロール後 約9.0MB @DPR1、約13.3MB @DPR2〜3）を独立計測
- D2 遅延読み込み（`data-defer` + IntersectionObserver）がスクロール時に確実に読み込み、未表示画像が残らない
- D3 CLS（レイアウトシフト）0.1未満。画像に width/height 指定あり
- D4 srcsetがDPR1/2/3で妥当な幅を選ぶ（過不足）
- D5 Lighthouse（モバイル/デスクトップ）Performance・Accessibility・Best Practices・SEO の数値
- D6 `site/img/IMAGE_REPORT.json` と実ファイルの一致（寸法・バイト数）、原本SHA-256が main と一致（原本無変更）
- D7 JS無効時の挙動（遅延画像は非表示になる仕様。致命的崩れがないか）

### E. ゲーム本体への影響
- E1 `git diff --stat e637805..<QA対象SHA>` が `site/` と `docs/qa/_evidence/website-rebuild-01/` のみ
- E2 ゲーム（`/`）: タイトル表示 → NEW GAME → エイダンの家 到達、コンソールエラー0
- E3 既存テスト（必要範囲）が main と同じ結果（既知FAILは `docs/qa/KNOWN_ISSUES.md` 基準で区別）

### F. GitHub Pages公開適合性
- F1 相対パスのみで `/the-windbound-oath/site/` 配下で動作（絶対パス・`file://`依存なし。og:imageのみ絶対URL）
- F2 公開元は main（Jekyll「pages build and deployment」）。`site/` 内に Jekyll が除外する `_` 始まりのファイル/フォルダがないこと
- F3 公開対象容量: 直近デプロイのartifactは 1,312,331,579 bytes（Claude調査）。追加量（`site/` 約36MB）と、GitHub Pagesの1GB目安超過のリスク評価。QA証跡は `docs/qa/_evidence/`（`_` 始まり）に置き、Jekyllの公開対象外になっていること（2026-11-04 ディレクター承認・案A）
- F4 外部依存は Google Fonts のみ（ネット接続環境でCinzel/Noto Serif JP/Noto Sans JPが適用されるか）。Claudeの検証環境では接続不可のため未検証

### G. 掲載内容（ディレクター方針との整合）
- G1 保留素材（CG02・CG04・CG05・ゴブリン・レイダー）とゲームプレイ候補画像が未掲載
- G2 SYSTEM・CHARACTERSの記述が現行mainの実装・AGENTS.md と矛盾しない（未実装機能を実装済みと書いていない）
- G3 STORY紹介文・エマ紹介文が「準備中」のまま（推測の創作文がない）
- G4 NEWS 4件の内容が実際のマージ済みPRと一致

## 2. 報告形式
- 冒頭に総合判定（PASS / CONDITIONAL / FAIL）、QA対象SHA、**mainマージ可否の提案**（可／条件付き可／不可と理由）
- **31項目すべて**を PASS / FAIL / BLOCKED で報告（未実施を省略しない）
- 項目別表（ID / 判定 / 根拠 / 環境：エミュレーション or 実機を明記）
- 不具合: 重大度（P0〜P3）・再現手順・期待/実際・修正案
- 証跡（スクリーンショット・ログ）は `docs/qa/_evidence/website-rebuild-01/codex/` に置く想定。push権限の扱いはディレクター指示に従う
- **Android実機は未検証と明記**する（実機確認はユーザー担当。ブラウザのモバイル表示を実機確認済みとして扱わない）
- マージ可否は提案のみ。mainマージ・公開の判断はディレクター承認事項
