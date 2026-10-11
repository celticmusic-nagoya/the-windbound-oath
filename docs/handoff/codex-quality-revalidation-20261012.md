# 依頼G再検証・m6_quest安定化

基準mainコミット: 最新候補は `b75a805`。旧基準 `57dc6aebc817b4255cf72cb907ab0623547b62b8` の結果も保持。
ブランチ: `work/codex-quality-main-20261012`（最新mainから作成）。旧検証は `work/codex-quality-revalidation`。
変更ファイル一覧: G移植を保持し最新mainをmerge。今回のゲーム本体への追加変更なし。今回のテスト変更は `tests/moss/m6_quest.py`。担当表、検証結果、画像ブロック、王都出口、Android手順を資料化。
追加・変更したID・フラグ: なし。
テスト結果: 最新main候補 `c5c3da2` の全回帰 **51/51合格**、m6_quest単独 **10回連続合格**。
未実装・要確認: 作者によるmain統合承認、Android実機QA、画像生成利用上限、王都受け側マップ。
STATUS: READY — 最新main基準の検証完了。main未反映、作者の統合判断待ち。

## 検証基準

| 対象 | commit | 状態 |
|---|---|---|
| 最新main | `57dc6ae` | G検証ブランチへ競合なしでmerge (`53eabe1`) |
| 更新後の最新main | `b75a805` | 敵3種を `1a597b3` でmainへmerge済み。ここから新候補を作成 |
| Claude G移植 | `65bf6d8` | 履歴を保持し新Codexブランチで検証 |
| スライム | `f80019e` | バットの祖先 |
| バット | `3259741` | ボアの祖先 |
| ボア | `8baa264` | 3種の積み重ねの最上段。PLAYER QA未承認 |
| m6_questテスト修正 | `f6f08bd` | テストのみ変更 |

共有済みClaudeブランチの履歴を変更せず、force push・main merge・本番deployは行っていない。

最新mainとの変更ファイル（G既存差分を含む）:

- アプリ: `js/field/field-movement.js`、`index.html`、`dev/moss-forest.html`（後2つはcache query）。
- テスト基盤: `tests/run_all.sh`、`tests/run_python.py`、`tests/field/frame_clock.test.js`、`tests/moss/m55_hz.py`、`tests/moss/m6_quest.py`。
- 素材棚卸し: `tools/moss/report_placeholder_art.py`、`docs/art/placeholder-inventory.md`。
- 引き継ぎ: `docs/handoff/CLAIMS.md`、`codex-quality-revalidation-20261012.md`、`codex-art-redelivery-20261012.md`、`codex-capital-exit-receivers-20261012.md`。
- QA: `docs/qa/codex-quality-foundation.md`、`docs/qa/android-symbol-performance-20261012.md`、`docs/qa/quality-foundation-results/`、`docs/qa/quality-revalidation-results/`（終了コード・代表ログ・バット静的メタデータ）。

## field-movement・長押し・遷移・正式素材

- main+Gの `moss-forest-runtime.js` は最新mainと同一blob。hold/onPointer、`hooks.onTransition` を戻していない。
- Gの変更は `FieldMovement.frameScale` の下限を `.1` から `Number.EPSILON` にするもの。pointerの `FieldNavigation.follow`、キーボード移動、敵AI（敵ブランチ）は同じ時間倍率を利用する。仕様・目標速度の再調整はしない。
- 敵3ブランチと `git merge-tree --write-tree` を個別実行。すべての競合は `docs/handoff/CLAIMS.md` の末尾追記のみ。各仮統合treeでGのmovement blobと各敵ブランチのruntime blobが保持されること、全JSの構文を確認。
- Raider CSS・BattlePartyLayoutはmainと同一blob。main+Gの納品済みヒーロー素材とmotion manifestもmainと同一。旧Codex素材に戻していない。
- 最上段ボアは途中で作者側によりmainへ統合済み。予定していた `work/codex-quality-symbol-validation` は未作成で取り止め、最新main候補で全回帰に含める。今回Codexが方式を変更したわけではない。

## m6_quest

固定2700ms待機を、実際の開始台詞が表示されmapがactive/非busyになるまでの待機に変更。非同期のマップ/素材ロードが遅れても、開始台詞が後からテスト会話を置換する状態を避ける。

会話送りはボックス中央の `#msg` ではなく `#msg .talkText` を実クリック。選択肢を含めたボックスのサイズ変更により中央がボタン位置になり得るため、本文を固定した対象とする。期待する2選択肢の全文はauto-retry付きexpectでも確認する。選択・辞退・報告・報酬・セーブの既存assertionは保持し、ゲーム本体のFieldTalk仕様は変更なし。

修正前4回は今回すべて合格。申告された1/4〜1/3の失敗率は今回の短い再現確認では再現しておらず、単一の原因を断定しない。修正後は `tests/run_all.sh` で単独10回連続を実行し **10/10合格**。各試行は新しいChromiumで起動。

## テスト記録

実行環境: Node `24.19.0`、Python `3.12.14`、Playwright `1.62.0`、system Chromium `154.0.8037.57`。仮想環境 `/workspace/.cloud-setup/venv`、`PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium`。素材取り込みテストにPillow `12.3.0`、NumPy `2.5.4`を追加。

すべて `tests/run_all.sh` を使い、ポート8765はrunnerが起動・終了する。初回全回帰でPillow/NumPy不足により最初の3件が失敗したため、依存を追加して該当テストを再実行する。これらをアプリの不具合と数えないが、再実行前に合格とも扱わない。

旧main `57dc6ae` + G + `f6f08bd`：全48件実行、45件合格・3件はPillow/NumPy不足で失敗。依存追加後の3件再実行は3/3合格。全48対象に合格結果がある。初回の失敗結果も削除せず `docs/qa/quality-revalidation-results/old-main-full.tsv` と `old-main-dependency-retest.tsv` に保存。

`quest-10-results.tsv` は10試行の終了コード。runnerは同じテスト名のログを上書きするため、`quest-10-last-run.log` は10回目のみのログであり全試行のtraceではない。最新main `b75a805` は途中で敵3種を統合したため、旧基準の合格だけで統合可能とは判定せず、最新main候補で再検証する。

最新main `b75a805582f076c6a8ceb67fd1bf9d5c75769e53` + G + m6修正の検証用merge `c5c3da2a1307c7336d9f8d609eb0bdb9576d1864`：`tests/run_all.sh` **51本実行・51本合格・失敗0**。スライム/バット/ボアの専用シンボル回帰3本も含む。結果は `latest-main-full.tsv`。長押し・onTransitionの王都ゲート・通常/uncapped速度・全ストーリー通し・Raider・正式素材取り込み・クエスト/セーブ/装備を確認。

同じ最新候補で `m6_quest.py` を単独10回、各試行新しいChromiumで実行して **10/10合格**。`latest-main-quest-10-results.tsv` と10回目のみのログを保存。開始時の旧基準10回と合わせて20試行だが、最新基準の連続10回だけで今回の要件を満たすことを確認。runner対象51本はすべて実行し、非zero終了・timeout・未実行対象はない。テスト内部の条件分岐・未納品素材の警告はログのとおり。Android実機・未生成CGのQAは別の未実施項目。

最後のfetchでもorigin/mainは `b75a805` のまま。テスト後、画像・map JSON・runtime/story/field-monsters・Raiderレイアウトは最新mainと同一で、一時テスト差し替えは復元済み。保存したログは末尾空白のみ整理し、終了コードやassertion結果は変更していない。

クラウド設定ドラフトの `install_script` にPillow/NumPy、`start_skill` にfull runnerの起動/ポート条件を追加保存・該当コマンドを検証済み。設定保存は公開ではない。再利用する場合は環境設定で確認・保存し、環境をPublishする。新しいタスクへの復元は未検証。

## 別作業・PLAYER QA

- [画像生成ブロック](codex-art-redelivery-20261012.md): HTTP429利用上限、0枚。
- [王都3出口](codex-capital-exit-receivers-20261012.md): 受け側JSON未作成、3件ともTBD/null維持。
- [Android計測手順](../qa/android-symbol-performance-20261012.md): 実機未測定。3種同時表示は通常配置に存在しないため各マップ計測と区別。
- PLAYER QAはCOLLABORATION第6節に従いmain反映後。長押し方向変更/離す際の停止、30/60/120Hzでの移動感、RaiderモバイルHUDと納品motion、クエスト受諾/辞退/報酬を確認する。
- 敵3種はスライム→バット→ボアの順に探知距離/追跡速度の妥当さを確認。ボアは予備動作0.6秒/硬直1.4秒で横に避けられるか、バットは与ダメージ60%の吸血が厄介すぎないか、スマホで重くないか。数値の調整は今回行わない。

## main反映可否と戻し方

最新main `b75a805` から作った検証用mergeは `c5c3da2a1307c7336d9f8d609eb0bdb9576d1864`。main上のmergeではない。G移植と今回のテスト修正をまとめて含み、main/Claude側の担当コードは保持。

アプリ差分は `FieldMovement.frameScale` の高fps下限修正、`index.html` とDEV harnessのcache queryのみ。移動速度設定・操作方式・ストーリー・セーブ・戦闘ルール・エンカウント方式・正式素材は変更しない。この範囲は品質修正として新運用の対象候補だが、全回帰完了前に反映可とは確定しない。また作者の今回の問いは「入れてよいか」の判断依頼であり、元の明示指示に従いCodexはmain反映を行っていない。

**最終判断: 依頼Gは新ルールの対象としてmainへ統合可能と判断し、統合を推奨する。** 基本システムを新設/改変する変更ではなく、同じ目標速度をfpsに依存せず保つ修正とテスト/資料基盤で、最新main上の全回帰が合格している。`65bf6d8` の元ブランチだけを直接入れるより、最新main基準と今回のm6安定化を含む `work/codex-quality-main-20261012` を統合対象とする。mainへのmerge・push・ロールバックタグ作成・Pages deployは今回未実施。PLAYER QAは実際に反映した後に行う。

実際に承認してmainへ入れる担当者は、最新mainに追加更新が無いか確認して必要な再検証後、直前のmain SHAにロールバックタグ `rollback/before-quality-foundation-20261012`（予定名、未作成）を付けてpushし、機能単位で `git merge --no-ff`。mainのmerge SHAをCLAIMSに記録する。ここには未実行のタグやmain mergeが存在したとは記載しない。

戻し方:

- **現在の検証ブランチだけを戻す場合**: `work/codex-quality-main-20261012` 上で `git revert -m 1 c5c3da2a1307c7336d9f8d609eb0bdb9576d1864`。Gを入れる前の `b75a805` に対する逆差分を新commitとして作る。
- **将来mainへ統合した後**: main上で `git revert -m 1 <そのmain統合merge SHA>` を行い、必要な回帰確認後に通常push。`c5c3da2` はmain統合SHAの代わりに使わない。上記予定タグは比較/復旧確認用の目印。`reset`・force pushで履歴を巻き戻さない。
- Gだけを戻す逆差分は、すでにmainにある敵3種・Raider・納品モーションを削除しない。PLAYER QA不具合が見つかったら、再現条件・端末条件・どのmergeを戻すかを記録する。
