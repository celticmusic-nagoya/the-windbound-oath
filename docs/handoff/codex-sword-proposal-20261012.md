# 剣設定: 依頼G調査 / 依頼H差分案 (2026-10-12)

基準mainコミット: `0d48324e49d3b21d764373126f98df82785df086`
ブランチ: `work/codex-sword-setting`
引継: `docs/codex-sword-handoff` / `1b3b248` / `docs/handoff/codex-sword-setting-20261012.md`
STATUS: READY（調査と未適用差分の提示。採用・main統合ではない）

変更ファイル一覧: 本報告、`codex-sword-proposal-20261012.patch`、`CLAIMS.md`。アプリ・既存テストは直接変更していない。
追加・変更したID・フラグ: 実環境への追加なし。差分案では `father_sword`（仮ID）。新フラグなし。

## G: 影響表（コード変更なし）

| 対象 | 現状の実装 | 新設定への影響 / 提案 |
|---|---|---|
| `index.html` `giveStarterSword/startTraining` | 訓練開始で木剣を配布・装備、木剣所有時は再配布しない | 父の剣は冒頭から所持。起動時の初期装備に移し、訓練から配布を外す。Claude所有なので未適用patchで依頼 |
| `js/data/equipment-data.js` | 木剣は補正なし、Aidan限定、`motionVariant:'wooden'` | 仮ID `father_sword`、表示「父の剣」、補正なし、Aidan限定、variantなし。木剣の定義は互換用に残し、プレイヤー装備を不可にする案 |
| `js/equipment.js` | ID保存、装備/バッグは別管理。武器変更/ロード時にvariant同期 | 読込前に旧IDを移行。装備処理・加算式・equipment v1を変更しない |
| `js/inventory.js` / セーブ読込 | バッグは `inventory.gear`、上限99。v30・同一SAVE_KEY | バッグの木剣も父の剣へ。同名合算の上限超過はロードを中止し元保存を保持。Inventory本体と形式は変更不要 |
| `js/battle-motion.js` / manifest | 装備variant→専用コマ、なければ基本コマ。既存テストは偽の木剣コマを使用 | 父の剣は納品済みAidan基本コマを使用。新しい剣素材やモーション名は追加しない。鉄剣の偽variantで切替検証を維持 |
| `js/prologue-combat.js` | 戦闘進行・中断・世代管理 | 今回変更不要。父の剣の補正0を維持してRaider等の数値に影響を出さない |
| `js/prologue-dev.js` | event jumpとsandbox/save制御 | 今回変更不要。DEVジャンプで父の剣を再配布する案は入れない |
| `js/field/aidan-field-actor.js` | 素材を描画。altは「エイダン · 誓いの剣」固定 | 装備IDで素材を切替えていない。背中の剣を統一する素材作業はClaude担当。altの物語時点との不一致は別途依頼、今回は未変更 |
| `js/field/talk-data-scenes.js` / story | モス会話・演出・進行フラグ | 指定の新順序をClaudeが担当。10ページ/UIを含めCodexは触らない |
| 誓いの剣 | 祭壇表示/物語上の獲得はあるが、EquipmentDataに該当装備IDはない | stageだけで父の剣を自動削除したり誓いの剣を装備したりしない。折れる/契約する時点と装備状態の連携はClaudeとの別作業 |
| `docs/system-equipment.md` | 「初期装備空」と「訓練で木剣」の両記述あり | 初期父の剣・訓練で配布しない・互換処理へ記述更新する差分 |
| 装備テスト2本 | 木剣初期配布、variant、入替、UI、v30 roundtrip | 父の剣の起動時所持、訓練で重複しない、補正0、基本コマ、旧ID移行、保存形式維持へ期待値更新 |
| `scenario_handoff_for_chatgpt.md` / AGENTS §15 | 古い武器喪失→ルー→祭壇の経路説明が残る | 新設定の確定源は引継書。物語資料の同期はClaudeへ依頼し直接編集しない |

## H: 未適用の差分案

隣の `.patch` は上記mainに対するunified diff。変更候補は `index.html`、`js/data/equipment-data.js`、`js/equipment.js`、装備テスト2本、`docs/system-equipment.md` の6ファイル。専用ブランチには資料として保存し、ゲームコードには適用していない。

父の剣は金属の剣を想定するが、能力補正・攻撃フレーム・戦闘ルールは追加しない。`iron_sword` を初期武器に流用するとATK+5となるため、新IDと補正0を提案した。名称/説明/IDは採用前レビュー対象。

初期化は装備モジュール読込後の一回。父の剣がバッグ/装備にある場合、または別武器を装備中なら配布しない。訓練・DEVジャンプ・セーブロードでは再配布せず、折れた剣を復活させる処理を作らない。セーブ削除は現状どおり保存データ削除だけで、新規ゲームリセット仕様は追加しない。

### 旧セーブ移行案

| 旧保存状態 | 読込後の案 | 留意点 |
|---|---|---|
| Aidanのweaponが `wooden_sword` | 同じスロットで `father_sword` | アクセサリ等・能力補正を維持 |
| バッグに木剣n個 | 父の剣n個に置換、既存父の剣と合算 | 他装備/キー/claimedを維持。合算99超または移行先の不正個数は中止 |
| 鉄剣/鋼剣等を装備 | 装備は維持、バッグの木剣のみ置換 | 武器の強制変更なし |
| equipmentなし / 武器スロット空 / 木剣もない | 空を維持 | 旧進行中の「武器喪失」と未取得を既存データだけで区別できないため、推測して剣を追加しない |
| stage12以降でも木剣が残る | IDだけ置換、stage/フラグ維持 | 誓いの剣の装備IDが現状ないため、後半も父の剣表示が残り得る。Claude側イベント連携の検討が必要 |
| 不正・未知装備ID | 現行loadの検証に従う | 不正データ一般の修復機能は増やさない |

保存オブジェクトをコピーして変換し、localStorageは明示的な次回セーブまで上書きしない。変換後の再変換は同じ結果。既存v30、equipment v1、SAVE_KEY、フィールド構造は維持。移行案の採用はセーブ互換性の変更に当たるため、main反映前に作者レビューが必要。今のブランチは資料だけなので既存セーブへ作用しない。

## 検証

未適用patchを `/tmp/sword-proposal-preview` に展開。変更対象以外は元リポジトリへのリンクで参照し、元のゲームファイルを編集せずChromiumで検証。

- `git apply --check docs/handoff/codex-sword-proposal-20261012.patch`: 合格（基準main上）。
- 新規移行関数のNode検証: 装備/バッグの置換、元オブジェクト不変、冪等性、空/他武器維持、合算、99超過拒否を確認。
- 装備テスト2本: 最終実行2/2合格（各exit 0、失敗0、console error 0）。新規起動、UI入替/キーボード/390px表示、旧セーブ移行、明示保存前の原本維持、v30再保存を含む。
- 高さ・物語・採用素材は未変更。全回帰・Android実機・物語新演出は未検証（今回は差分案まで）。

実行コマンド:

```sh
PATH=/workspace/.cloud-setup/venv/bin:$PATH \
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium TEST_TIMEOUT_SECONDS=180 \
TEST_RESULTS_DIR=/tmp/sword-proposal-results-final \
bash /tmp/sword-proposal-preview/tests/run_all.sh \
 tests/system/equipment_test.py tests/system/equipment_ui_flow_test.py
```

runnerが8765サーバーを起動/停止。最終ログは上記resultsディレクトリ。ここでの合格は提案の局所検証であり、ゲームへの採用・全回帰合格を意味しない。

## 未実装・要確認 / PLAYER QA

- 父の剣の仮ID/表示名と、バッグ木剣を全個数移行する方針をレビューする。数量を勝手に1へ減らさない。
- 折れる瞬間の装備解除、誓いの剣の装備表示、既存後半セーブの整合はClaudeのイベント設計と合わせる。新フラグ/進行推定をこの案に混ぜていない。
- 木剣は互換用のデータを残すが、NPCの描画/訓練演出には手を加えていない。
- 不足18コマと既存素材の背中の剣はClaudeが対応。装備変更だけでは素材の剣有無は変わらない。
- 採用後QA: 冒頭で父の剣を持つ、木剣が装備候補にない、訓練で増えない、鉄剣入替で父の剣がバッグへ戻る、旧セーブのアイテム/進行が保たれる。新物語と剣破損/契約の表示はClaude実装後に確認。

## 戻し方

main未変更なのでロールバックは不要。提案を却下する場合はpatchを適用せずブランチを保持する。将来採用時は直前mainのrollback目印をpushし、機能単位の `merge --no-ff`、関連/全回帰後push、戻す場合は `git revert -m 1 <merge commit>`。force push禁止。
