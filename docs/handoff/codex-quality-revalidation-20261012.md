# 依頼G再検証・m6_quest安定化

基準mainコミット: `57dc6aebc817b4255cf72cb907ab0623547b62b8`
ブランチ: `work/codex-quality-revalidation`
変更ファイル一覧: G移植を保持し最新mainをmerge。今回のゲーム本体への追加変更なし。今回のテスト変更は `tests/moss/m6_quest.py`。担当表、検証結果、画像ブロック、王都出口、Android手順を資料化。
追加・変更したID・フラグ: なし。
テスト結果: 下記参照。全回帰・敵ブランチ実行共存検証は進行中。
未実装・要確認: 作者によるmain統合承認、Android実機QA、画像生成利用上限、王都受け側マップ。
STATUS: WIP — REGRESSION IN PROGRESS

## 検証基準

| 対象 | commit | 状態 |
|---|---|---|
| 最新main | `57dc6ae` | G検証ブランチへ競合なしでmerge (`53eabe1`) |
| Claude G移植 | `65bf6d8` | 履歴を保持し新Codexブランチで検証 |
| スライム | `f80019e` | バットの祖先 |
| バット | `3259741` | ボアの祖先 |
| ボア | `8baa264` | 3種の積み重ねの最上段。PLAYER QA未承認 |
| m6_questテスト修正 | `f6f08bd` | テストのみ変更 |

共有済みClaudeブランチの履歴を変更せず、force push・main merge・本番deployは行っていない。

## field-movement・長押し・遷移・正式素材

- main+Gの `moss-forest-runtime.js` は最新mainと同一blob。hold/onPointer、`hooks.onTransition` を戻していない。
- Gの変更は `FieldMovement.frameScale` の下限を `.1` から `Number.EPSILON` にするもの。pointerの `FieldNavigation.follow`、キーボード移動、敵AI（敵ブランチ）は同じ時間倍率を利用する。仕様・目標速度の再調整はしない。
- 敵3ブランチと `git merge-tree --write-tree` を個別実行。すべての競合は `docs/handoff/CLAIMS.md` の末尾追記のみ。各仮統合treeでGのmovement blobと各敵ブランチのruntime blobが保持されること、全JSの構文を確認。
- Raider CSS・BattlePartyLayoutはmainと同一blob。main+Gの納品済みヒーロー素材とmotion manifestもmainと同一。旧Codex素材に戻していない。
- 最上段ボアとの実行共存は別の `work/codex-quality-symbol-validation` で検証する。main統合候補に未承認のシンボル方式を混ぜない。

## m6_quest

固定2700ms待機を、実際の開始台詞が表示されmapがactive/非busyになるまでの待機に変更。非同期のマップ/素材ロードが遅れても、開始台詞が後からテスト会話を置換する状態を避ける。

会話送りはボックス中央の `#msg` ではなく `#msg .talkText` を実クリック。選択肢を含めたボックスのサイズ変更により中央がボタン位置になり得るため、本文を固定した対象とする。期待する2選択肢の全文はauto-retry付きexpectでも確認する。選択・辞退・報告・報酬・セーブの既存assertionは保持し、ゲーム本体のFieldTalk仕様は変更なし。

修正前4回は今回すべて合格。申告された1/4〜1/3の失敗率は今回の短い再現確認では再現しておらず、単一の原因を断定しない。修正後は `tests/run_all.sh` で単独10回連続を実行し **10/10合格**。各試行は新しいChromiumで起動。

## テスト記録

実行環境: Node `24.19.0`、Python `3.12.14`、Playwright `1.62.0`、system Chromium `154.0.8037.57`。仮想環境 `/workspace/.cloud-setup/venv`、`PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium`。素材取り込みテストにPillow `12.3.0`、NumPy `2.5.4`を追加。

すべて `tests/run_all.sh` を使い、ポート8765はrunnerが起動・終了する。初回全回帰でPillow/NumPy不足により最初の3件が失敗したため、依存を追加して該当テストを再実行する。これらをアプリの不具合と数えないが、再実行前に合格とも扱わない。

全回帰の確定値は完了後に記入する。

## 別作業・PLAYER QA

- [画像生成ブロック](codex-art-redelivery-20261012.md): HTTP429利用上限、0枚。
- [王都3出口](codex-capital-exit-receivers-20261012.md): 受け側JSON未作成、3件ともTBD/null維持。
- [Android計測手順](../qa/android-symbol-performance-20261012.md): 実機未測定。3種同時表示は通常配置に存在しないため各マップ計測と区別。
- PLAYER QA: 長押し方向変更/離す際の停止、30/60/120Hzでの移動感、RaiderモバイルHUDと納品motion、クエスト受諾/辞退/報酬、敵3種の接触/回避/突進。スライム→バット→ボアの承認順を維持。
