# Codex 指示 LL〜PP (2026-10-13 夜2) — GG〜KK 取り込み後の追加分
基準: 最新main(49c842f以降)。standing-orders に従う。**js/・css/・index.html・採用素材は変更しない**(tests / tools / docs / .github のみ)。不具合は直さず、再現手順つきで報告。
GG〜KK は main に統合済み(GG指摘2件は修正済み: 旧宿屋店主のEnter、1フレーム内の確認キー二重)。HH の縮小版ルーは field に採用済み(`img/field/characters/lou/`)。作業ブランチは `work/codex-ll-pp`。

## LL: 戦闘UI構造の自動検証(「戦闘UI改善」仕様の確認)
仕様: PCは左操作・右戦場で味方を拡大/スマホ縦は下部コンパクトCOMMAND/スマホ横は左操作・右戦場/戦場・バトルログ・COMMAND・展開コマンド・アイテム選択を構造的に分離(相互に重ならない)/雑魚戦とボス戦で共通UI/戦闘演出中は通常UIを隠し終了後に復元。
- `tests/battle/ui_structure.py` 新規: 通常戦闘(`startAttackBattle('forestGob1',112)`)とボス戦(`devJump('raider')`)を PC(1280x720, 1920x1080)・縦(390x844)・横(844x390)・小型(360x640)で開き、各領域(戦場 / バトルログ / COMMAND / アイテム一覧 / 味方HUD)の矩形を取得して、(1)COMMAND とアイテム一覧が画面外にはみ出さない (2)バトルログが COMMAND/戦場スプライトと重ならない(重なる場合は面積%を記録) (3)PC では味方スプライトが左右どちらに寄るか・拡大率 (4)演出中(`body.actionCinematic` / `battlePresentationBusy`)に通常UIが非表示になり、終了後に元に戻る を検証。
- 仕様を満たさない箇所は FAIL にせず「仕様差」として一覧化(`docs/qa/battle-ui-structure-20261013.md`、スクショ付き)。

## MM: セーブ互換性(v30 追加のみ)の回帰
- 過去バージョンのセーブ(v26〜v30。`git log -p -S"version:2"` 等で各時点の `saveGrowthData` 形式を再現、または既存テストの fixture を利用)を `tests/system/save_compat.py` で読み込み、(1)欠けた項目に既定値が入る (2)装備・インベントリ・クエスト・会話フラグ(`FieldTalk.serialize`)・`PartyManager.support.joined`(ルー合流)・位置/レベルが保持される (3)v30で保存→再読込で等価、(4)壊れたJSON/未知キー/型違い(数値が文字列等)で例外を出さず既定値に戻ることを確認。
- 成果: テストと `docs/qa/save-compat-20261013.md`。

## NN: ルー合流の整合性監査(ストーリー進行 vs フィールド表示)
フィールドのルー追従は `PartyManager.support.joined` を見て表示する。
- `support.joined = true` になる全経路(`grep` で列挙: シーン、`prologue-dev.js` のDEVジャンプ、ロード等)を一覧化し、通常進行(DEV無し)でルー救出前(`storyStage<13`)にルーが表示される経路がないか、ロード直後・マップ遷移直後・屋内(`story.interior`)・戦闘後復帰で表示/非表示が正しいかを検証。
- `tests/moss/m34_lou_story_gate.py`: 新規ゲームから `storyStage` を進めながら(DEVジャンプではなく自然な流れに近い関数呼び出し)ルー表示の有無を記録。DEVジャンプのみ表示される場合は「DEV専用」として明記。
- 成果: `docs/qa/lou-story-gate-20261013.md`(表: 経路 / 時点 / 表示 / 想定との差)。

## OO: 全フィールドマップ巡回スモーク
- `tests/moss/m35_all_maps_smoke.py`: `data/maps/*.json` の全マップを `MossForest.enter` で順に開き(ルー合流あり/なし、昼/夜の両方)、各マップで (1)pageerror/console error 0 (2)読み込み時間 (3)spawn 地点で `S.blocked` でない (4)追従(フィオナ/ルー)がプレイヤーと数百px以上離れない (5)出口(transitions)の遷移先マップ ID が実在、を確認し一覧表に。
- 失敗は一覧化して原因を切り分け(マップデータ起因 / コード起因)。

## PP: 回帰の自動実行(GitHub Actions)
- `.github/workflows/regression.yml` を新規(PR と main push で `tests/run_all.sh` 相当を実行、Chromium は Playwright で取得、失敗時はログを artifact に保存、所要時間が長ければ「高速セット(スモーク)」と「全件(夜間 schedule)」に分割)。
- mainへ反映される前に作業ブランチで yaml を静的検証(actionlint 相当があれば使用)。実際の Actions 実行はユーザー側で GitHub 上で確認するため、手順を `docs/qa/ci-setup-20261013.md` に。
- 注意: 既存の保護対象(ゲームコード)は触らない。workflow の権限は `contents: read` のみ。

## 報告
各項目完了ごとに `codex-status.md` を更新して通常push。利用制限で止まったら wip コミット。最終コミット・結果・未解決点を報告。
