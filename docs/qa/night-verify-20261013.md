# 夜間K: 独立検証 (2026-10-13)

ブランチ: `work/codex-night-k`。基準実装: `feat/equipment-unlock-sword` **be6af1f235d879ed892138610e9a0557bba704f4**。基準main: `0d48324`。STATUS: READY（検証報告完成、対象実装には失敗あり）。mainマージなし。既存コード・マップ・テストは編集していない。

## 結果

指定5本は **4合格 / 1不合格**。独立追加検証は **62項目中59合格 / 3不合格**。各実行のサーバーは生存しHTTP200を返し、最後に自身で終了。指定テストと独立検証の記録上、console/page errorは0。対象は最新be6af1fで、開始時03d053eから入ったPartyManager参照修正を含む。終了前fetchでも同SHAを確認した。

統合前に修正/再検証が必要な点は、m18の古いページ数期待値と成功終了コード、旧セーブへ戻った際の風の舞の習得残留、旧Aidan装備の鉄剣/鋼剣の消失。表示面では横画面で祭壇文章が人物に重なる。修正はClaude担当へ依頼し、本ブランチには入れていない。

## 指定テスト（順次・単独プロセス）

| テスト | 結果 | 終了コード | 時間(秒) | 失敗/console |
|---|---|---|---|---|
| tests/system/equipment_test.py | PASS | 0 | 3.394 | 失敗0・console0 |
| tests/system/equipment_ui_flow_test.py | PASS | 0 | 8.601 | 失敗0・console0 |
| tests/moss/m18_moss_scenario.py | FAIL | 0 | 14.03 | ページ数30期待/実37・console0 |
| tests/moss/m20_sword_equipment.py | PASS | 0 | 8.875 | 失敗0・console0 |
| tests/moss/m21_wind_dance.py | PASS | 0 | 6.048 | 失敗0・console0 |

m18は `FAIL altar has 30 lines (37)` / `FAILS 1` を出すが **exit 0**。本runnerは終了コードだけでなくFAIL行/FAILS値を確認し、失敗扱い・runner exit1にした。テスト本体のassertion/終了コードは変えていない。順序、誓い、武器の切替、風の舞の習得はこのテストでも合格。m21の前報告の不合格は、03d053eの `window.PartyManager` lookup（constのPartyManagerはwindowのpropertyではない）がbe6af1fで修正され、今の実行では合格した。

原本5テストのSHA256は実行前後で一致（test-results.jsonに保存）。hardcoded localhost:8765は実行用adapterで127.0.0.1:8783へ移し、PORT対応テストにはPORT=8783を渡した。Chromiumの実行ファイルだけ環境の `/usr/bin/chromium` を指定。期待値/タイムアウト/待機/入力操作は未変更。600秒の上限、同時実行なし。

## 祭壇の順序・誓い・旧演出

- 結界は `MossForestStory.flags()` が討伐3体で開放、ルーイベントも3体未満は開始せず、祭壇イベントはlouFoundが必要。ここはソース読取確認で、今回の独立検証は討伐をseedして祭壇へ進めた。全徒歩での結界→最奥地ルートは未検証。
- 祭壇は **37ページ**、最長59字。異変8→Raider12→奇襲防御14→剣破損15→窮地17→風の舞21→ルー22→古代石25→誓い32→契約33→解放/戦闘37の順（ページ番号は1始まり）。指定順序と一致。
- **エイダン「……もう、目の前で誰かを失うのは嫌だ。」** は1回、一字一句一致。契約は直後33ページ。武器は15ページで空、33ページでoath_sword、風の舞は21ページで習得。37ページ後のクリックでRaider HP1250/RUNE25の開始を確認。
- 旧「剣が裂け目へ落ちる」はactive altarLinesから消えている。古い台本 `scenario_handoff_for_chatgpt.md:166` には残存。別の「空の黒い裂け目」は砦の物語で、剣喪失とは区別する。少年剣士の木剣台詞も新設定と整合するため削除対象ではない。
- 視覚演出は依然としてA/F/ルーと異形4体の旧placeholder主体。異形は祭壇1ページ目から表示され、Raider登場のページにも巨大Raiderの絵は出ない。剣表示は26ページ、33ページで異形が薄くなり剣の発光。新順序の文章と武器/習得状態は連動するが、Raider出現/奇襲/剣破損/風の舞の画面演出が専用素材で完成したとは言えない。採用素材は変更しない。

## 1ページの長さと縦横表示

390×844 / 844×390のmobile/touch contextで、祭壇全37ページ×2を撮影。文字のRange rectを測り、全ページの文字/箱が画面内に収まり、文字の切断なし。約2行という目安には縦画面の12/30/33ページが3行で外れる。砦は支給7ページを撮影し、全9ページの文字領域も計測。縦の4/5/7/8/9ページは3行。横の砦は全て1行。

横画面の祭壇 **2/5/12/19/30/33ページ** は2行となり、文章箱がAidan/Fiona/下側異形の足元に重なる（DOM矩形重なりと原寸画像で確認）。文字自体は読めるが人物の下部が隠れる。縦画面では文章箱と人物の重なりなし。縦ではAidan/Fionaのplaceholder同士の横方向の重なりが残る。

EQUIPは両画面で5スロット、横はみ出し0。縦scroll44px/横scroll265pxで候補説明まで到達。横の初期画面では候補が下へ続くがsystemMenuの縦スクロールで読める。`?dev=1`のDEVボタン/バッジがメニューと重なるので、QA証跡上は開発用overlayと区別する。一般公開版のoverlay無しの撮影は未実施。

| 祭壇ページ | 字数 | 縦の行数 | 横の行数 | 横の人物重なり |
|---|---|---|---|---|
| 1 | 30 | 2 | 1 | なし |
| 2 | 43 | 2 | 2 | あり |
| 3 | 30 | 2 | 1 | なし |
| 4 | 25 | 2 | 1 | なし |
| 5 | 49 | 2 | 2 | あり |
| 6 | 38 | 2 | 1 | なし |
| 7 | 16 | 1 | 1 | なし |
| 8 | 32 | 2 | 1 | なし |
| 9 | 16 | 1 | 1 | なし |
| 10 | 33 | 2 | 1 | なし |
| 11 | 27 | 2 | 1 | なし |
| 12 | 55 | 3 | 2 | あり |
| 13 | 24 | 1 | 1 | なし |
| 14 | 35 | 2 | 1 | なし |
| 15 | 27 | 2 | 1 | なし |
| 16 | 15 | 1 | 1 | なし |
| 17 | 28 | 2 | 1 | なし |
| 18 | 14 | 1 | 1 | なし |
| 19 | 47 | 2 | 2 | あり |
| 20 | 21 | 1 | 1 | なし |
| 21 | 38 | 2 | 1 | なし |
| 22 | 20 | 1 | 1 | なし |
| 23 | 28 | 2 | 1 | なし |
| 24 | 24 | 1 | 1 | なし |
| 25 | 37 | 2 | 1 | なし |
| 26 | 27 | 2 | 1 | なし |
| 27 | 17 | 1 | 1 | なし |
| 28 | 11 | 1 | 1 | なし |
| 29 | 40 | 2 | 1 | なし |
| 30 | 59 | 3 | 2 | あり |
| 31 | 34 | 2 | 1 | なし |
| 32 | 25 | 1 | 1 | なし |
| 33 | 55 | 3 | 2 | あり |
| 34 | 28 | 2 | 1 | なし |
| 35 | 18 | 1 | 1 | なし |
| 36 | 14 | 1 | 1 | なし |
| 37 | 40 | 2 | 1 | なし |

原寸画像: `night-verify-20261013/independent-run/independent-screenshots/` に祭壇74枚、砦支給2枚、EQUIP初期/スクロール4枚。指定m20が撮った14枚も `night-verify-20261013/screenshots/` に保持。計94PNG。全ページの文、文字数、矩形、行数、武器、習得、異形表示をindependent-results.jsonに保存。

## 旧セーブ互換

各caseは別browser contextで、本物のv30 serializeからfixtureを作成。木剣装備・バッグ木剣2/鉄剣1/指輪1・旧accessoryにemma_charm・wind_dance無し・equipment.unlocked無しを設定。

| fixture stage | 復元stage | 武器 | 装飾品 | 解放/風の舞 | 支給/再ロード |
|---|---|---|---|---|---|
| 0 | 0 | 父の剣 | accessory1へ | 未解放/未習得 | 支給なし。繰返しロード/再保存で個数維持 |
| 12 | 12 | 父の剣 | accessory1へ | 未解放/未習得 | 支給なし。舞のキー無しの旧stage12のため、習得前と扱われる |
| 15 | 15 | 誓いの剣 | accessory1へ | 解放/習得 | 帽子/鎧を各1補完、既存指輪1維持。重複支給なし |
| 18 | 15 | 誓いの剣 | accessory1へ | 解放/習得 | 同上。**既存PrologueProgress.loadの最大15 clamp**により18→15。未来stageの保持を保証しない |

全caseでバッグ木剣2→父の剣2、鉄剣1はバッグに維持、他の装備/アクセサリ保持、v30再保存/再ロードで支給個数維持。ロードのみでは元localStorageを上書きしない。fixtureの原文と結果/再保存をJSONに保存。

### 失敗1: 風の舞が序盤の旧セーブへ残る

再現: 同じcontextでstage15・キー無し旧セーブをロードしてWindDance.learned()==trueになった後、stage0・キー無しの旧セーブをロード。stageは0、EQUIPは未解放に戻るが、**WindDance.learned()==trueのまま**。

原因: index loadGrowthDataのmembers復元はObject.assignで、保存側にlearnedがないと既存learnedを削除しない。WindDance.syncはstage>=13でlearnするだけで、低stageではクリアしない。m21は各読込前にdelete learnedを行うため、この実際のロード切替を検出しない。デフォルトfeature OFFでは戦闘コマンドは隠れるが、習得状態自体は不正に残る。feature ON時の実コマンド操作での波及は未検証。

Claudeへの修正案（未適用）: members復元時に「保存にないlearned」の扱いを明示して現在の状態を引き継がない。保存内の初回発動済みstage12のwind_dance:trueは維持し、キー無しstage0は未習得、キー無しstage>=13は補完する。検証は同一セッションで後半→序盤→後半をロードし、テスト側でdeleteを挟まない。

### 失敗2・3: 旧Aidan装備の鉄剣/鋼剣が消失

旧mainではAidanにも装備可能だった `iron_sword` / `steel_sword` をAidanのweaponにし、バッグ空・stage15の旧セーブを各1件ロード。結果は誓いの剣になったが、**元の武器のownedは0**（期待1）。

原因: 最新equipment-dataはequipBy:['liam']。equipment.loadのwhyでAidanの旧装備を拒否してスロットから破棄し、バッグへ返さない。その後syncStoryEquipmentが誓いの剣を設定する。新しい固定武器の仕様そのものではなく、所持品を守る互換処理の不足。次の通常セーブで欠落状態が保存される可能性がある。

Claudeへの修正案（未適用）: 旧保存のAidan武器が鉄剣/鋼剣なら、equipment.loadで拒否される前の移行でバッグへ1個返し、物語武器へ同期する。数量99上限の衝突は切り捨てず安全に停止/要確認。木剣の既存変換と同様、元保存を破壊しない。

## 旧記述・回帰の穴

| 箇所 | 残存/不一致 | 対応依頼 |
|---|---|---|
| scenario_handoff_for_chatgpt.md:40 / :51 / :99 / :166 | 古い順路、古い祭壇journal、Aidan木剣、裂け目落下 | 末尾の新設定追記だけでなく旧章を同期するか旧版と明示 |
| 同:1201 | 祭壇32ページ/契約27ページ | 実37/契約33へ同期 |
| system-equipment.md:3 / :12 / :13 / 最新節 | 4スロット、崖宝箱iron_sword、契約27ページの古い記述 | 実5スロット・魔力の雫・契約33へ同期 |
| index mainQuestData stage12 | 父の剣破損/誓い契約の新文言に更新済み | 古い裂け目文言なし。祭壇冒頭から契約まで同じstage12なので進行前の内容も表示される点は既存設計 |
| AGENTS §15 | 古い武器喪失→ルー→祭壇→Raiderの経路 | 新設定の設計文書と同期要。基本数値は調査Iの召喚差も参照 |
| equipment_test.py:38 / :42 | `if False else True` / `or True`で実検証しないassert | 本来の検証に戻す依頼、今回未編集 |
| 同:65 | `A and B and C or D`でDだけでもsave検証が通る | version/武器/両アクセサリを全て明示的にANDで確認する依頼 |
| m18末尾 | 失敗を出力してもsys.exitしない | FAILS>0 / errors>0で非0終了を依頼 |

## 実行コマンド / 証跡

```sh
PATH=/workspace/.cloud-setup/venv/bin:$PATH PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python3 -u tools/qa/run_night_tests.py --port 8783  --out docs/qa/night-verify-20261013

PATH=/workspace/.cloud-setup/venv/bin:$PATH PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python3 -u tools/qa/run_night_tests.py --port 8783 --independent-only  --out docs/qa/night-verify-20261013/independent-run
```

前者exit1（m18の1失敗）、後者exit1（上記3失敗）。実行log、test-results.json、fixture/全ページのindependent-results.json、server.logを同ディレクトリへ保存。独立検証の初回はメニューbodyをスクロールしていたため、実際のscroll containerのsystemMenuへ修正して再実行し、鉄剣/鋼剣ケースを追加。報告値はその最終実行。ゲームソースの変更による再試行ではない。

未検証: 全回帰、実戦回避効果（未実装/null）、全ルート徒歩、Android実機、全旧save世代/破損データ、旧saveバッグ上限全組合せ、採用素材の不足コマ。PC Chromiumのmobile contextはAndroid実測ではない。

変更ファイル: 新規tools/qa/run_night_tests.py・night_verify_sword.py、本QAと証跡、新規handoff。CLAIMS追記のみ既存ファイル変更。main未更新。対象実装の修正後には関連5本と旧saveケースの再検証が必要。現失敗を解決済みとして統合しない。

## PLAYER QA / 戻し方

修正/作者の統合後: 父の剣破損→風の舞→ルー→誓い→契約の読みやすさ、37ページのテンポ、横の人物隠れ、砦支給と5スロット、旧所持品/風の舞のロード切替。誓いの台詞は変更しない。

本作業はmain未変更なのでmainロールバック不要。Claudeが将来採用時は直前mainのrollback branch/目印をpush、機能単位merge --no-ff、回帰後通常push。戻す場合 `git revert -m 1 <merge commit>`。force pushしない。
