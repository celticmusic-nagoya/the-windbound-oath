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

## 自動テスト実行結果（2026-11-08）
- GitHub Actions `Prologue escape-return static QA` run **42440757926**: **SUCCESS**。
- ジョブログの `node tests/prologue-escape-return-static.test.cjs` に **15/15 static integration checks passed** と各15項目のPASSが出力されたことを確認。
- `Rilde CG registry QA` run **42440758117**: **SUCCESS**。
- この2件は静的整合・既存CGの検査であり、ブラウザでのゲーム通しプレイ・旧SAVEの実ロード・Android実機QAを代替しない。

## 次の実行QAの受入チェック
1. 新規開始から川へ飛び込む12ページを連続タップし、最後にモスの森の川岸へ到達する。
2. 森でルー加入、誓いの剣契約、レイダー戦終了後にリルド帰還15ページが一度だけ再生される。
3. エマとの再会台詞が順番どおりで、終了時のみ砦へ進み、支給装備を一度だけ取得する。
4. 旧SAVE stage13をロードするとレイダー討伐後の会話から再開する。
5. 旧SAVE stage14をロードすると従来どおり砦シーンから再開する（帰還イベントへ強制遷移しない）。
6. 旧SAVE stage15をロードするとプロローグクリア後へ復帰する。
7. 帰還会話中はSAVE不可、帰還完了後の砦では通常のSAVE仕様を維持する。
8. Android縦・横で立ち絵、会話タップ、画面遷移、再起動時の動作を確認する。

判定: **STATIC CI PASS 15/15 / EXISTING CG CI PASS / RUNTIME & SAVE REPLAY NOT_RUN / MERGE BLOCKED**。

## SAVEルート自動QA結果（2026-11-08）
- GitHub Actions run **42441895896**: **SUCCESS**。ジョブログで旧SAVE v1/v2 stage13/14/15の6ケース＋討伐記録不整合1ケースの **7/7 PASS** を確認。
- 追加テスト `tests/prologue-return-save-guard.test.cjs`：実際の `saveGrowthData()` をNode VMで実行し、帰還会話中はlocalStorageへ書き込まず通知を表示、帰還外ではversion30で通常保存することを確認する設計。
- 上記SAVEガード実行テストは追加直後のため**CI結果未確認**。旧SAVE実ファイルのブラウザロードやAndroid実機は引き続きNOT_RUN。
