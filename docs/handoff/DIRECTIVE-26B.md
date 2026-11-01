# DIRECTIVE-26B handoff

基準main: `ad4a3d679987a540fc0248c9b5bfd0e8c43a15a3`（PR100）
ブランチ: `codex/26b-early-rewards`。既存work refは保全。
ユーザー26Bの明示的実装範囲: 既存indexの報酬handler・最小item定義・互換性・対応QA。所有記録に基づく新規のシナリオ作業は追加しない。

製品4ファイル: index（旧家2＋依頼2grant、LOAD成功後欠落antidote=0、cache3）、rilde-village（新家2grant＋新規antidote在庫reset）、item-data（保持専用antidote）、battle-action-targets（antidoteのみ選択／効果適用拒否各1行）。Inventory・SAVEv30・既存flags/APIを再利用。新効果・解毒・状態異常・新コマンド・新報酬システムなし。

R01薬1/R02金3/R03薬2/R04毒消し2 PASS。初回・重複・新旧取得口cross・map再訪・SAVE/LOAD/coldCONTINUE・旧SAVE無補償・失敗/取消LOAD・新規開始の13Nodeケースと3viewport96browserチェックで確認。Node原版14＋新規suite、故障8/8、既存回帰13種類（16実行）すべてPASS。259PNG固定SHA、1452その他runtime、採用台帳、portrait/render/blink、全原文/分岐/表情指定、過去QA証拠不変。

m53のfullindexhashは承認済reward差分へ更新。追加reward QAの可逆diff oracleで4ファイルを正確に基準mainへ戻してbyte一致を要求するため、単なる期待緩和ではない。会話behaviorhash4d9…は不変。

詳報: `docs/qa/DIRECTIVE-26B.md`／`docs/qa/evidence/directive-26b/`。
独立exact-head QA、rollback remote SHA読み戻し、最新main/PRhead/checks/競合後に通常merge。Pagesはmerge後に公開実データ/main一致を回収。Android実機は未実施、全経路連続プレイは次26C。

STATUS: READY_FOR_REVIEW
