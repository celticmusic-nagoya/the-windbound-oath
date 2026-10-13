# Codex LL〜PP 納品 / 2026-10-13

LL→MM→NN→OO→PPを完了、各区切りでGitHubへ通常push。
初回mainf0fe968、最終maindeadf3d。作者の上方向歩行変更をwork branchへ取り込み関連テストも確認。
ゲーム/採用素材を編集せず、mainへはマージしていない。実Actions/Androidは未実施。

基準mainコミット: deadf3da88c416cea420905ef4dbeb7a12893015
ブランチ: work/codex-ll-pp
追加・変更したゲームID/フラグ: なし
STATUS: READY（検証・設定案納品。未解決はClaude/作者判断）

## 一覧 / 結果

| 項目 | 報告 | 最終結果 | 最初の納品commit |
|---|---|---|---|
| LL | [battle-ui-structure-20261013.md](../qa/battle-ui-structure-20261013.md) | 10シナリオ/70状態、FAILS0。84仕様差観測/50画像。CSS probeの可視も別記 | d3820d4 |
| MM | [save-compat-20261013.md](../qa/save-compat-20261013.md) | 47検査・39合格/8失敗。uncaught0。v28〜30の履歴と26/27合成を区別 | 1abb1cb（最終判定e12431a） |
| NN | [lou-story-gate-20261013.md](../qa/lou-story-gate-20261013.md) | 17検査・15合格/2失敗。通常storyでは早期表示なし、欠落/型不正loadでstage9に表示 | 2737e37 |
| OO | [all-maps-smoke-20261013.md](../qa/all-maps-smoke-20261013.md) | 動的30map×4=120/120合格、console/pageerror0。遷移JSON不存在11（TBD8/旧hook3） | ba1f276 |
| PP | [ci-setup-20261013.md](../qa/ci-setup-20261013.md) | actionlint/YAML/Bash合格、ローカル高速7/7合格53.5秒。実Actions未実行 | 9d14914（高速source4532bc7） |

LL/NN/OOはlatest field描画の追試f9136bf、MMはe12431aで再確認。最終report/source照合/commitは本branchのGitHub履歴を参照。初回MMの戻り値だけで失敗にした2件は指示の安全な既定値という基準で訂正し、旧結果は保存した。全79回帰は今回未実施、CI fullは未解決診断で赤くなる見込み。

## 変更ファイル

新規tests: tests/battle/ui_structure.py、tests/system/save_compat.py、tests/moss/m34_lou_story_gate.py、tests/moss/m35_all_maps_smoke.py。
.github/workflows/regression.yml、.github/requirements-ci.txt。
上記5報告/JSON/ログ、LL50画像・NN3画像、CI静的結果と高速runner全ログ、codex-status/CLAIMS/本一覧。ゲームに対するCodex独自差分は0（origin/main比のjs/css/index/img/maps照合）。作者のmain差分はmerge4532bc7でそのまま取り込んだ。

## 未解決 / 要判断

- LL: COMMAND/itemsと味方の重なり、PCの左寄り/拡大不足、busy中に残るUI。CSS actionCinematic probeでもPC通常COMMAND/ボスlogが可視。作者側で構造/CSS優先度を検討。
- MM: member level文字列/負gold/アイテム文字列/未知active/合流文字列、欠落warm-loadの以前値残存、DEV height保存のmap/level fallback。実在しない26/27 serializerを確認済みとはしない。
- NN: 合流後にsupportのない早期saveをloadすると以前のtrueが残る。joined='false'もBooleanで表示。通常進行の早期表示とは区別する。
- OO: TBDとlegacy/hookのJSON不存在。実際の出口通行不能11件とはしない。王都受け側はJSON確定後に接続する。
- PP: GitHub側でActions許可/PR job/main push/手動full/scheduleを確認する手順が必要。contents:readのみ、Secret不要。実Actionsはユーザー側確認という指示を維持。

## PLAYER QA / 次の提案

1. battle UIの左右配置、COMMAND展開/items/logと味方の重なり、演出中/後の復元を縦横で確認。
2. loadの型/既定値/整合性ガードをClaudeが判断し、MM/NN再実行。
3. hookと未接続出口の検証契約を決め、Actions PRの高速・手動fullを確認。

## 再開 / ロールバック

最新fetchでmaindeadf3d、LL〜PP後の新briefなし。status/standing/main/新briefsと本branchの履歴から再開し、完了作業は再実施しない。
mainは未更新なので戻す操作不要。Claudeが統合する場合はrollback branchをpush→機能単位no-ff→push前回帰。統合後はgit revert -m 1 <merge>、通常push。force pushなし。
