# PROLOGUE-ESCAPE-RETURN-INTEGRATION-01｜統合QA（2026-11-08）

## 対象
- PR #169: `feature/prologue-escape-fix-01` （川への自発的脱出・漂着）
- PR #170: `feature/prologue-return-01` （村帰還・エマ再会・砦への遷移）
- 統合ブランチ: `qa/prologue-escape-return-integration-01` （PR #170から派生しPR #169の2つの脚本ファイルとindex.html暗転トリガーを取り込み）
- mainは未変更。公開サイトへの反映なし。

## 静的整合チェック（11/11 PASS）
1. 脱出台詞12ページ
2. 脱出立ち絵12件
3. 脱出暗転トリガー `escapeIndex===9`
4. モスの森の川岸への漂着
5. リルド帰還台詞15ページ
6. 帰還立ち絵15件
7. 帰還シーン中タップ分岐
8. 帰還終了→砦シーンの呼出
9. 砦の既存装備支給 `fortIndex===6`
10. storyStage 14/15の既存番号維持
11. 森到着時の旧崖落下文言除去

## 追加で発見した要修正事項
- **P0: storyStage=14の意味が旧SAVEの砦と新帰還シーンで衝突**。既存のSAVE復帰仕様を完全に調査・実行確認するまで互換性を保証できない。
- **P1: 帰還シーンは既存の`aftermathScene`を再利用する15ページの会話のみ**。リルド廃墟マップを歩く現地再訪・任意のエマ護符受注は未実装。
- **P1: 帰還シーンの追加台詞（コナーの息子を認識する騎士、エマの補間台詞等）**は正典全文と逐語照合していない。正式採用として扱う前に脚本レビューが必要。
- **P1: `index.html`はPR #169と#170の双方が変更している**。両PRを別々にmainへマージすると統合QAの保証が失われる。統合ブランチでQAし、マージ戦略を確定すること。
- **P1: 脱出時の北側UI誘導と実地形の整合**は未検証。地理上の川・橋・崖とプレイヤー誘導を追加確認。

## 未実施の検証
- ブラウザでの実行とイベント完走
- Android実機の縦横・連打・バックグラウンド復帰
- 旧SAVE stage13/14/15の復帰、セーブ中断・ロード
- 自動回帰・全シナリオ・CG・戦闘テスト
- 村再訪の地理・エマ護符任意クエスト

## QA判定
**STATIC PASS (11/11), INTEGRATION QA PARTIAL, MERGE BLOCKED**。
現時点ではどのPRもmainへマージ・公開しない。

## 追加調査: SAVE/CONTINUE (2026-11-08)
- `js/prologue-progress.js`: 保存形式version 2、stage13は`AFTERMATH`、stage14は`FORT_FINALE`、stage15は`PROLOGUE_END`。旧SAVEのstage14→砦復帰は維持。
- `js/save-continue.js`: タイトルからのロードも`PrologueProgress.plan()`を使用。
- 統合QAブランチの`index.html`で`saveGrowthData()`のガードに`rildeReturnActive`を追加し、帰還会話中の中断セーブを禁止。帰還完了後は従来の砦stage14へ遷移。
- 不確定な新規補間台詞を一部ト書きへ変更し、未承認設定を断定しないよう修正。
- **追加静的確認8/8 PASS**：ガード、旧stage13/14の復帰ルート、stage14復帰処理、帰還開始・終了、再会台詞、SAVE version不変。
- **制限**：帰還中のアプリ終了時は直前SAVEからの再開。会話途中からの再開には非対応。実行・Android・旧SAVE復帰テストはNOT_RUN。独立QAなしにマージしない。
