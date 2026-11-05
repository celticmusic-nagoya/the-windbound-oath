# WEBSITE-REBUILD-01-FIX-04（Claude自己QA）

- BASE `11e526c4150102a8721412b68ec71b4ddd6885f4`。修正コミット `34c37c47f78a25a6358966a03debc402010e408b`（`site/css/site.css` のみ）
- 注記: 作業中に main が `e637805` → `74d0401` に進んだ（他作業のマージ）。`site/` と本PRのQA文書には変更なし。本ブランチのrebaseはしていない
- 入力: [Codex FIX-03 QA](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/137#issuecomment-6644824323)（31 PASS / 0 FAIL / 2 BLOCKED、H1はCLS条件でFAIL）

## 原因
低い横長画面用の `.hero__logo { width:auto; max-height:30svh }`。CSSの `width:auto` が属性の幅を上書きし、画像が届くまで寸法が決まらず 0px → 117px に伸びて、キャッチとボタンが下にずれていた。

## 修正
- 横長画面: `width: min(100%, calc(30svh * 1200 / 427)); height:auto; aspect-ratio: 1200 / 427`
- 通常レイアウトにも `height:auto; aspect-ratio:1200/427` を明示（既存の幅100%は維持）
- 表示サイズは変更前と同じ（844×390のロゴ 329×117、他の画面幅も座標一致: `hero_boxes_after.txt`）

## CLS（初回読み込み＋全スクロール、7画面×DPR1/2/3＝21条件、Google Fonts遮断）
| 条件 | 修正前 11e526c | 修正後 |
|---|---|---|
| ロゴを1.2秒遅延 | **0.02211878**（844×390、DPR1/2/3。Codexの値と一致） | 0 |
| HERO画像すべてを1.2秒遅延 | — | 0 |
| site/img 全画像を1.2秒遅延 | — | 0 |
| 遅延なし | 0 | 0 |
ルー画像のCLS修正（FIX-03）も維持（全条件で発生源なし）。

## 回帰
- qa_site.js 42 PASS / 0 FAIL（A5・D4・JS無効・reduced-motion・HERO重なり・ナビ・ライトボックス・キーボード）、コントラスト 30 / 0
- HTML: ローカルNu 20.6.30で新規エラーなし（旧版特有の誤検出3件のみ）。0エラー/0警告の判定はCodexの最新版に委ねる
- 初回転送 PC 4.11MB / SP 4.29MB（変化なし）。ゲーム本体はエイダンの家まで到達、エラー0
