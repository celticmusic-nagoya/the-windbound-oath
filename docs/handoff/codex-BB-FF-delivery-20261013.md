# Codex BB〜FF 納品（2026-10-13）

BB/CC/EE合格、FFは開始時最新main169f197で全75合格。DDは216条件の実エンジン比較を納品し、数値未採用。AAは別branchの未採用draftで、overlay-only物語gateの採用条件は未達。

## 変更ファイル

- `tests/moss/m28_aidan_walk_assets.py` / `m29_leafy_boar_assets.py` / `m30_raider_dodge.py`
- `tools/sim/wind_dance_policy_bench.py` / `tools/moss/validate_height_schema.py`
- `docs/qa/aidan-walk-acceptance-20261013.md`、`leafy-boar-acceptance-20261013.md`、`raider-dodge-20261013.md`、`old-save-level-ambiguity.md`、`full-regression-20261013-FF.md` と各証跡
- `docs/handoff/wind-dance-policy-sim.md` / `codex-status.md` / `CLAIMS.md` / 本書
- AAのみ: height lint/helper、cliff height-spec新規、m27、entity宣言案/検証報告（map本体・js・素材は不変）

## 結果と既知の問題

|依頼|結果|未決・限界|
|---|---|---|
|AA|lint/入口→頂上0→1→2実歩行合格。提案fixtureは夕日→襲撃合格|overlay-onlyはベンチgate FAIL1。頂上entity level宣言の別変更待ち|
|BB|初回24枚合格、FFの36枚（直進/idle24+dl/ul12）も合格|向き・剣の描画内容は自動判定しない。前後斜めの旧素材警告は更新前の結果|
|CC|戦闘23/field11のRGBA・寸法・足元・中心、rush8-10/KO1-6合格|KO6は結果画面中保持、閉じると非表示。保持を消す案は提案のみ|
|DD|216×8=1728record、実走1608/reuse120、errors0|8seedの固定方針。回復閾値も方針間で異なり、舞だけの因果効果ではない。数値未採用|
|EE|回避/命中8経路、型/ref/実spawn到達、孤立上階負例/階段正例すべて合格|levelなし旧XYの曖昧さ、finite-only load防御はレビュー提案|
|FF|75合格/main既存0/新規0/未実施0、全source hash不変・server停止|cloud Chromium。Android実機未測定|

BB/CC/EEのconsole/page errorは0。FFのconsole収集は各testの範囲であり、runnerの共通監視は追加していない。従来の台詞2件は今回実行して合格。

## PLAYER QA / 要判断

1. 新しい直進と斜めの向き、背中の剣、足運びと足元。
2. ボアの薄いKO6を結果画面中に保持する演出でよいか。
3. 風の舞/回復/MP回復の方針差。最終数値の決定は行っていない。
4. 高さ導入時のentity宣言と旧saveのfloor選択。Android未測定なので本編高さONは行わない。

## ブランチ・commit / 戻し方

- 納品 `work/codex-bb-ff`。完了checkpoint `8f5ce84`、本書を含む最新commitはgit log参照。
- FF snapshot `work/codex-ff-source` / `fb2bfff`、main基準 `169f197`。追加はm28/m29/m30のみ。
- AA `work/codex-height-spec-draft` / `3979e54`。物語gateを保つ採用条件は未達、branch全体を自動採用しない。
- main更新・force pushなし。元worktreeのbranch切替なし。js/採用素材/map本体のCodex編集なし。
- 統合はClaude担当。main更新前にrollback branchを確保し `--no-ff`。統合を戻す場合 `git revert -m 1 <merge commit>`。

次の調査候補: 回復閾値とqueued危険対応を共通にした舞ON/OFF比較。最終fetchのmainは169f197で、新規指示書なし。進行中/未コミット懸念なし（本書のcommit/push後）。再開はstatusとlatest main/git logから。
