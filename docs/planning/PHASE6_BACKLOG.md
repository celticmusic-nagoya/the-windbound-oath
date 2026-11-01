# Phase 6 backlog — DIRECTIVE-25A

監査基準: main `5ab60c5db833821744d73080f91ffcd559ebf0a4`（PR98）。本書は計画であり、機能追加・仕様承認・素材採用を意味しない。[監査結果](../qa/DIRECTIVE-25A.md)が検証状態の正本。Issue IDは本監査内の追跡ID（GitHub Issue作成済みという意味ではない）。Phase4/5A/5Bは完了を維持する。

P0は今回の証拠で確認できたものなし。全領域に不存在と保証したものではない。未接続の将来コンテンツ、仕様どおりの敗北時復帰、静止表情をBUGに数えない。以下の優先度は製品への影響で決め、実装順は依存関係を優先する。

| ID | 重要度 | 影響範囲・現在の状態 | 推奨対応／担当 | 依存関係 | 完了条件 | 順序 |
|---|---|---|---|---|---|---|
| P6-QA-01 | P2 | **COMPLETE: DIRECTIVE-26A**（[修復QA](../qa/DIRECTIVE-26A.md)）。25A時点はNode2本が旧会話関数抽出でFAIL、素材回帰1本がAndroid未検証固定assertでFAIL。製品SAVE破損の証拠ではない | `startup_race`の`function say(t)`固定抽出と`continue_restore`の新helper未取込、およびasset_registry_auditの全件UNVERIFIED固定assertを台帳準拠へ修正。Codex | なし | 原版Node20/37ケースと素材回帰が実際の現行コード／採用状態でPASS。故障注入の検出力を維持。抽出対象空文字を即FAILにする | 1 |
| P6-REWARD-01 | P1 | **COMPLETE: DIRECTIVE-26B**（[修正QA](../qa/DIRECTIVE-26B.md)）。25A時点は序盤の取得／依頼報酬が表示と所持数が実測で不一致（4ケース） | 家drawer/pot、風船、迷子猫の実給付を確定仕様に合わせる。毒消しは既存定義不在を先に整理し、未承認の効果を作らない。Codex／必要なitem仕様はユーザー | QA-01。不具合4ケースを再現test化 | 取得数/金額が実増、再調査で重複なし、SAVE/LOAD後も一致。旧SAVEの受取履歴を捏造・自動補償しない。台詞・条件不変 | 2 |
| P6-QA-02 | P1 | ニューゲームから王都までの無改変・連続通常プレイ証拠が不足 | 既存分割回帰と区別した全経路テスト＋ユーザー実機通しプレイ。Codex／ユーザー | QA-01、REWARD-01。今回の通常経路プローブ結果を引継ぐ | DEV jump・teleport・instant kill・story/HP/flag代入なし。開始から砦、リアム加入、王都2クエストまで。途中SAVE→冷起動CONTINUE、敗北復帰も記録。進行不能なら再現と別修正案件 | 3 |
| P6-PARTY-01 | P1 | リアムは加入・保証人・成長・装備あり。実戦ターンとHUDは主にエイダン／フィオナ固定 | 既存PartyManagerを基点に3人目から4active/2reserveへ段階拡張。Codex。仕様差の確認はユーザー | QA-02で現行基準確定。ART-01の描画契約 | 任意activeの行動・対象・KO・報酬・保存が同一actorモデルで動作。reserve100%EXP、ルーSUPPORT維持。既存レイダー難度不変 | 4 |
| P6-STORY-01 | P1 | 王都職人地区／東地区／王城内、森深部は未接続。現在の終点以降 | 次に実装する区間と到達目標を先に承認し、既存正史と接続条件を仕様化。ChatGPT／ユーザー、承認後Codex | QA-02。必要ならPARTY-01。正史・シナリオ承認 | 台詞・分岐・マップ・保存・アセット仕様が承認済み。TBDを無断で埋めず、対象1区間ずつ到達QA | 5 |
| P6-QA-03 | P2 | `capital_story_test.py`の宿舎回復等に`or True`があり実測を保証しない | 無条件真を外し、HP/MPと操作復帰を独立検証。Codex | QA-01 | 実回復を壊す故障注入でFAILし、現行仕様ならPASS。直前waitで検証済みの`check(True)`とは区別 | 6 |
| P6-BAL-01 | P2 | 既存戦闘回帰は演出／固定fixture中心。通常初見の所要ターン・消費・再戦率は未測定 | LV/装備/行動方針/乱数条件を固定した戦闘計測。Codex／ユーザー | QA-02、QA-03 | 雑魚・異常ゴブリン・レイダー各条件の実測分布。数値は自動変更せず、承認済みレイダー難度を保護 | 7 |
| P6-ANDROID-01 | P2 | 今回の総合実機テスト・OSバックグラウンド復帰は未実施 | 縦横、タップ連打、回転、タブ非表示、OS復帰、coldLOADを機種／Chrome版付きで実行。ユーザー、Codex証拠整理 | QA-02 | 全経路とUIの端末結果回収。過去Phase4/5実機合格を今回の通しプレイ合格に流用しない | 8 |
| P6-PERF-01 | P2 | headless計測のみ。実機性能・長時間メモリ増加は未確定 | 実機remote debuggingと反復遷移／会話の計測。Codex／ユーザー | ANDROID-01 | 端末・CPU・時間・map・p99/heapを記録、改善要否と予算を決める。cloud FPSだけでAndroid性能合格にしない | 9 |
| P6-AUDIO-01 | P2 | FieldBgmの生成音楽はリルド3profile。多地域の宣言IDに未対応 | 地域ごとの無音／生成音／納品音源の方針承認から実装。ChatGPT／ユーザー、Codex | STORY-01の地域範囲、ASSET_GAP_LIST AUD-01 | 採用音源／生成profileが選択地域で鳴る。ミュート／再開／重複再生を検証 | 10 |
| P6-ART-01 | P2 | リアム戦闘用の正式描画契約が未確定。field7枚を戦闘素材と混同不可 | 必要pose、pixel寸法、anchor、透過、向き、納品方法を先に確定。ChatGPT／Claude／ユーザー | PARTY-01のレイアウト設計 | 合意済み仕様と採用記録、実戦で顔・武器が欠けず動く。既存立ち絵259枚不変 | 11（PARTY-01設計と並行、制作は契約後） |
| P6-FIELD-01 | P2 | stage5〜8はlegacy襲撃fieldで文字・CSS図形NPCが残る。現在mapはpixel Rildeだが本編経路は旧描画を使う | 既存正式ruin-map/field素材の再利用とlegacyイベント接続を先に設計。Codex／Claude | QA-02、MAP-03素材照合。台詞/条件を維持 | 救助・再会・北側戦闘・逃走を既存flagsのまま、同じ村として自然なfieldへ接続。条件/セーブ回帰PASS。素材不足時のみ別制作契約 | 12 |
| P6-MOTION-01 | P3 | 一部戦闘motionは静止fallback。現行の操作を止めない | [不足素材一覧](ASSET_GAP_LIST.md)の動作単位で必要性を選定し制作。Claude、採用ユーザー、接続Codex | ART-01、優先する戦闘体験の決定 | 承認済み新素材のみ接続。ルー失神演出は専用triggerの設計と合わせる。未採用stun等を勝手に採用しない | 13 |
| P6-REGISTRY-01 | P3 | 全1196記録中885UNKNOWN等。branch原本と派生frameの統合状態は別 | 現行runtime／原本保管／未使用をcross-link。Codex | なし。優先障害を先に処理 | 既存採用履歴を保持し、Raider元sheet5件を「画面で不足」と誤認しない。259保護SHA維持 | 14 |

26AでQA-01、26BでREWARD-01を完了。次案件は **QA-02（DIRECTIVE-26C）→PARTY-01→STORY-01**。表の優先度・順序番号は25A監査時点の記録を維持する。QA-01を先行した理由は後続の正常性判定を信頼できる状態にする依存関係による。P0が次の通しプレイで見つかった場合は、その修正を最優先の別案件にする。
