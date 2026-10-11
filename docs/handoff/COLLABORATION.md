# GitHub経由の共同開発運用（Claude / Codex）

作者指示による運用。チャットだけに決定を残さず、GitHub上の資料とブランチを進捗共有のsource of truthとする。従来の担当規則と相違する場合は本指示を優先。

## 1. 作業開始とcheckpoint

- 最新remote mainを取得し、基準SHAとworktreeを確認。Codexは `work/codex-<topic>` を使用する。
- 着手前に `docs/handoff/CLAIMS.md` へブランチ名・触るファイル・状態を記録しpushする。Claudeも同じ場所に記録する。他ブランチのCLAIMSもfetchして確認する。
- 着手時、設計確定時、テスト合格時、停止・ブロック時に、意味のあるcheckpointをcommitして自分のブランチへpushする。
- 未完成コードはWIPと明記。安全なcheckpointを保ち、不安定な状態をmainへ入れない。
- 画像生成失敗等も専用報告MDへ理由・再開条件を書き、`STATUS: BLOCKED` としてpushする。
- 作者の追加承認: Raiderモバイル修正は統合・公開まで承認済み。以降は危険でなくClaudeの作業と干渉しない変更は、検証後に承認待ちなしでmainへ通常push可能。危険な変更・担当の干渉・Pages設定変更は事前確認を維持。

## 2. 担当と依頼

Claude所有: `index.html` 全体、`js/field/moss-forest-story.js`、`js/field/talk-data-*.js`、`tools/moss/build_*.py` 等。
Codex: 新規ツール・素材・戦闘・音の担当領域。ただしパス名だけで所有を推測せず、CLAIMSと依頼書を確認する。

Claude所有ファイルへ変更が必要なら直接編集せず、`docs/handoff/` の専用MDへ「対象・箇所・必要な変更・理由・テスト条件」を書いてpushする。以前のscript行／cache queryの例外も、新しい依頼ではこの運用に従う。
`data/maps/*.json` は生成物。手編集せず生成元担当へ依頼する。

## 3. 仕様共有

マップID、spawn名、フラグ名、データ形式、命名規則の確定／変更は `docs/handoff/HANDOFF.md` または専用MDに残す。
依頼Cの受け側IDが確定したら、`tools/moss/capital_exits.json` に入れてほしい値を次の表で共有し、ClaudeがTBDを接続する。

| 既存出口ID | 受け側map ID | 受け側spawn名 | 条件・備考 |
|---|---|---|---|
| 未確定 | 未確定 | 未確定 | 確定値だけを書く |

## 4. 固定報告書式

各ブランチに `docs/handoff/<topic>.md` を置く。

```
基準mainコミット:
ブランチ:
変更ファイル一覧:
追加・変更したID・フラグ:
テスト結果:
未実装・要確認:
STATUS: READY / BLOCKED / WIP
```

READYは記載した基準での作業完了を意味する。作者承認／main統合／本番公開済みを意味しない。
テストは実行基準SHAと結果を記録し、未実行・失敗・既存warningを区別する。

## 5. main統合前の再検証

Claudeが作者承認の下でmainを更新するため、開始時SHAのまま統合依頼しない。
最新origin/mainへrebaseして、関連テストと必要な回帰を再実行後に統合承認を求める。
共有済みブランチの履歴を無断で書き換えず、通常pushできない場合は最新mainから別の統合候補ブランチを作り、旧ブランチを保持して移植・再検証する。force push禁止を維持。
競合時は担当変更を勝手に上書きしない。資料で共有しBLOCKEDとする。

作者から共有された直近のmain変更（実際のsourceを確認してから作業）:
- `tr_rd_to_capital`: リアム未加入では王都の検問を通れない。
- `moss-forest-runtime.js`: 長押し移動、onPointerのhold処理、hooks.onTransition。
- 新歩行素材、Aidan attack/skillの納品済み戦闘モーション。
