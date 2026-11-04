# WEBSITE-REBUILD-01｜QA証跡をGitHub Pages公開対象から外す方法（提案・未実施）

## 現状調査（2026-11-04）
- 公開元: `main` ルート、GitHub標準の「pages build and deployment」（`actions/jekyll-build-pages`、Jekyllビルド）。直近 run 41622166154（main `e637805`）成功、artifact `github-pages` = 1,312,331,579 bytes
- リポジトリに `_config.yml`・`.nojekyll`・Pages用workflowはない → Jekyll既定設定で全ファイルを公開
- `docs/` は追跡 約527MB（うち `docs/qa/evidence/` 約41MB）。ゲーム実行時に `docs/` を参照するコードはない（`js/assets.js` のコメント1件のみ）
- Jekyllは名前が `_` で始まるファイル・ディレクトリを階層に関係なく公開しない（既存例: `docs/qa/moss-delivered-art-20261012/**/_tmp_*.log`）

## 案（推奨順）
| 案 | 方法 | 影響範囲 | 評価 |
|---|---|---|---|
| **A（推奨）** | 本PRの証跡を `docs/qa/_evidence/website-rebuild-01/` へ移動（ファイル移動のみ） | 本PRの追加ファイルだけ。Pages設定・ゲーム・既存証跡は不変 | 最小。Jekyll公開を続ける限り有効。将来 `.nojekyll` や独自workflowへ移行すると公開対象に戻る点に注意 |
| B | ルートに `_config.yml` を新設し `exclude: [docs/qa/evidence/website-rebuild-01/]` | サイト全体のJekyllビルド設定 | 設定は1行だが全体のビルドに関わるため要承認。対象を `docs/` 全体に広げれば公開容量を約1.31GB→約0.8GBへ減らせる（別案件） |
| C | 証跡を非公開の handoff リポジトリへ移し、本PRにはリンクのみ | 本PRのファイル削減 | 既存運用（handoff=証跡置き場）と整合。PR上で画像を直接見られなくなる |

## 注意
- Pagesの公開物が実際に変わるのは main マージ後。現時点の公開サイトには影響なし
- 案A採用時は `CANDIDATES_PREVIEW.md`・`candidates-preview.html`・QA指示書内のパスを同時に更新する
- 承認まで実施しない
