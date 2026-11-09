# MORWEN-PIXEL-69 PR統合計画（#204・#205・69）

実行条件：第三者美術QA・Android実機QA・必要な再QAがPASSし、ディレクターが正式採用を承認していること。**本タスクではマージ・PRのクローズ・ブランチ削除・force pushを一切行っていない。**

## 1. 監査結果（2026-11-09時点）
| 項目 | 結果 |
|---|---|
| main | `d5c79f4e8dc9a8e20f1d427b7fff595f64de66a6` |
| PR #204（Draft、base main） | `feature/morwen-pixel-67-lower-body-art` @ `54f3e9d61b88321f990d9b2591657e2c042c4fd7` |
| PR #205（Draft、base #204） | `feature/morwen-pixel-68-secondary-motion` @ `51b15addcaec02680d7dd8677ec48ad456645e66` |
| 66ブランチ（PRなし） | `feature/morwen-pixel-66-walk-rebuild` @ `a4d6eb9`。その2コミットは#204に含まれる |
| マージ先 | 正しい（#204→main、#205→#204） |
| mainとの差分 | #204は43ファイル、#205は75ファイル。すべて`assets/candidates/field-hd-pixel/morwen/`配下で、それ以外のファイルの変更は0 |
| 本番素材・manifest・コードへの変更 | なし |
| 重複コミット | なし（直線履歴：90587a8 → a4d6eb9 → 54f3e9d → 51b15ad） |
| mainとのコンフリクト | なし（mainはmerge-baseのまま進んでいない。GitHub上のmergeableもtrue） |
| 他のopenなPR（#203、#154、#153、#145、#144、#140、#139）との競合 | 同じパス・manifest・正本を触るものは0件 |
| **CI** | **FAIL**：#204・#205とも`Official HD pixel candidate QA / validate`がfailure（下記） |
| ブランチ保護の設定 | UNVERIFIED（Pages・保護設定のAPIはこのセッションから参照不可） |

### CIのFAILの原因（69で特定・修正）
`.github/workflows/field-hd-pixel-qa.yml`は、`assets/candidates/field-hd-pixel/*`配下の各ディレクトリを「4方向の静止画セット（down/left/right/up.png）」として検証する。66〜68で歩行候補を`field-hd-pixel/morwen/right_walk_*`に置いたため、`Missing required direction: morwen/down.png`で失敗していた（ローカルでも同じ失敗を再現済み）。66〜68の報告ではCIの状態を確認しておらず、この見落としはClaude側の不備。

**69での修正：** 66・67・68の3ディレクトリを`assets/candidates/morwen-right-walk/`へ移した（コミット`f3816a3`）。
- 移動のみで中身は変えていない（75ファイルすべてR100、ファイル実体のハッシュも完全一致）。
- 移動後、ワークフローと同じ手順（単体テストと候補ディレクトリの走査）をローカルで実行し、PASSを確認。
- 前例：`assets/candidates/goblin-field-20f`も、このワークフローの対象外の場所に置かれている。
- 別案として、QAスクリプトを歩行候補を対象外にするよう改修する方法もあるが、共有のCIを変更するため採らなかった。

## 2. マージ手順（承認後）
**事前準備：#204・#205のCIを通す（ディレクターの承認が必要）。** force pushはしない。

| 手順 | 対象 | 内容 |
|---|---|---|
| 0a | #204 | ブランチ末尾に移動のみのコミット（66・67）を追加する |
| 0b | #205 | #204の更新をマージコミットで取り込み、68の移動のみのコミットを追加する |
| 0c | 69 | #205をマージコミットで取り込む |

上記0a〜0cはローカルの一時ブランチで試し、コンフリクト0、69の最終ツリーが現行69と完全一致することを確認済み（同じ移動が重なっても衝突しない）。

| 手順 | 内容 |
|---|---|
| 1 | #204をmainへ統合（merge commit推奨。squashすると66・67の履歴の粒度が失われる） |
| 2 | #205のbaseをmainに変更 |
| 3 | 差分が68固有のファイルだけであることを確認する（試行では32ファイル、`right_walk_68/`のみ） |
| 4 | 68固有の再QA：`qa_morwen68.py`を再実行し技術QAがPASSか、CIがPASSか確認 |
| 5 | #205をmainへ統合 |
| 6 | 統合後のmainで、候補のパスに何も参照していないこと、manifestに未登録であること、本番スプライトが不変であることを確認 |
| 7 | ブランチを整理（下記） |

## 3. 69のPRをどこに積むか
- 69のPR（QA資料と移動の修正）は**#205のブランチ**に積む（現在のbase）。
- 手順0を採らない場合は、69を#205へ取り込んだうえで#204〜69を一括統合する代替案もある（CIは最上段だけPASS）。ただしPRごとのレビューの粒度が失われるため推奨しない。
- 第三者QAで不具合が出た場合（70）の修正PRは、69ブランチ（最上段）に積む。

## 4. リスク
| リスク | 対策 |
|---|---|
| CIが失敗したまま、または保護設定によってはマージできない | 手順0を先に行う |
| baseを変更したときに67の差分が#205に重なって表示される | 手順3で差分を確認する |
| 移動したパスを外部資料が参照している | 候補内のREADMEに旧パスの記載はない（確認済み）。#204・#205のPR本文にある旧パスは、手順0を行うときに更新する |
| 候補がmainに入ることを本番反映と誤認される | 「mainにあること≠本番採用」を明記。本番採用は別工程（manifest登録・ゲームへの接続）で、ディレクターの承認が必要 |
| AGENTS.mdの「`field-hd-pixel/`に追加」との関係 | この規則は4方向静止画の制作規約。歩行候補をその外に置くことをディレクターに確認してもらう |

## 5. 統合後のQA
- `qa_morwen66/67/68.py`の再実行（12枚の形式・保護画素・接地・歩行構造）
- CI（field-hd-pixel QA）がPASSすること
- `git diff main~ main --stat`で候補ディレクトリ以外に変更がないこと
- 本番スプライト・manifestのハッシュが統合前と同じであること

## 6. 整理対象のブランチ（統合と承認の後。今回は削除していない）
- `feature/morwen-pixel-66-walk-rebuild`（#204に含まれる）
- `feature/morwen-pixel-67-lower-body-art`（#204のマージ後）
- `feature/morwen-pixel-68-secondary-motion`（#205のマージ後）
- `feature/morwen-pixel-69-qa-prep`（69のPRのマージ後）
