# 素材再生成の確認 (2026-10-12)

基準mainコミット: `57dc6aebc817b4255cf72cb907ab0623547b62b8`
ブランチ: `work/codex-quality-revalidation`（画像が0枚のため報告だけを同ブランチに保存）
変更ファイル一覧: 本報告のみ。正式素材・runtime・map JSONは変更なし。
追加・変更したID・フラグ: なし。
テスト結果: 画像生成APIを1回実行。HTTP 429 / `usage_limit_reached`。生成画像0枚。画像QA・透過検証・配信QAは未実施。
未実装・要確認: 下記すべての素材生成。利用上限が解除された後に再開。
STATUS: BLOCKED — IMAGE GENERATION USAGE LIMIT

## 確認した計画・仕様

- `work/codex-loading-cg` の `docs/art/loading-cg/README.md` と `production-plan.json`：現行28マップを16CGでカバーする。予定10CGのmap IDは捏造しない。最初に平和村・森・王都の代表候補を作り、作者の画風QA後に残りを進める。
- `work/leafy-boar-symbol-encounter` (`8baa264`) の `docs/art/redelivery_requests.md`：最新のバット・ボア不足一覧を確認。main版にはその追記がまだないため、main版だけを最新とは扱わない。
- 命名は既存規約のフィールド `<hero>_idle_<dir>.png` / `<hero>_walk_<dir>_01..04.png`、戦闘 `<actor>_<state>_NN.png`。戦闘は1コマごとに透過RGBA PNG、画面端に接しない。

## 今回の生成試行

既存計画の `rilde_peace` を優先代表として試行。横長・不透明背景、手描きアニメ/絵画調、深緑/アイボリー/古金、石と木の農村、東側の川と橋、風の石と井戸、文字/人物/ネタバレなし。

ツールは利用上限エラーで終了。保存可能な画像・実寸・SHA-256は存在しない。再試行を連打せず、他の画像も同じ生成上限が前提となるため保留した。予定した `work/codex-art-redelivery-20261012` は画像生成に至らず未作成。

## 再開順

1. 利用上限解除後、Loading代表CG（平和村・森・王都）を個別に生成・視覚QAし、作者の画風確認に提示。正式採用素材へ自動置換しない。
2. バット：attack/damage/ko専用コマ、小サイズのフィールド用、足元の影。
3. ボア：戦闘用約1000px高の透過RGBA個別コマ、専用歩行コマ。
4. フィオナ攻撃、エイダン左斜め前歩行、黒背景斬撃の透過RGBA再納品。

ゲーム仕様・配置・正式素材の置換は作者への事前確認が必要。画像生成が成功したら、候補の寸法・形式・サイズ・SHA-256・実alphaを記録する。
