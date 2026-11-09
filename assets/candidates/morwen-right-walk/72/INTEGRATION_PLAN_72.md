# MORWEN-PIXEL-72 PR依存関係と最終統合手順

## 現在の依存関係（mainは`d5c79f4`のまま）
```
main
 └ #204  feature/morwen-pixel-67-lower-body-art     54f3e9d   CI FAIL（既知）
    └ #205  feature/morwen-pixel-68-secondary-motion  51b15ad   CI FAIL（既知）
       └ #206  feature/morwen-pixel-69-qa-prep          a4e6552   CI PASS
          └ #207  feature/morwen-pixel-70-motion-polish  8afa2c5   CI対象外
             └ #208  feature/morwen-pixel-71-detail-polish 68729b4 CI対象外
                └ #72のPR feature/morwen-pixel-72-final-candidate
```

CI修正として別途用意したDraft PR（フォルダ移動のみ、既存PRのブランチは変更していない）：
- **#204用：** `fix/morwen-pixel-204-ci-path`（`2696d25`）→ base #204のブランチ。差分は43ファイル、すべてR100（66・67の移動）。
- **#205用：** `fix/morwen-pixel-205-ci-path`（`f291c8c`）→ base #205のブランチ。#204用の修正をmergeで取り込み、68を移動。差分は75ファイル、すべてR100。
- **監査結果：** 移動後のツリーで`assets/candidates/field-hd-pixel`配下は0ファイル。`right_walk_66/67/68`の内容は#206と完全一致。

## 統合可能条件
1. 第三者美術QA：72でPASS（`qa_preview_72.html`の記録JSON）
2. Android実機QA：PASS（機種・ブラウザを記録）
3. ディレクターが正式採用を承認していること
4. 各段階でCIがPASS、または対象外であることを確認済み

## 手順（条件を満たした後。force pushは禁止）
1. CI修正PR（#204用）を#204のブランチへmerge → #204のCIがPASSになることを確認
2. CI修正PR（#205用）を#205のブランチへmerge → #205のCIがPASS
3. #206のブランチに#205をmergeで取り込み、ツリーが変わらないことを確認（手元の試行では内容差0）。そのまま#207 → #208 → 72へ順に取り込む
4. #204をmainへ統合（merge commit推奨）
5. #205以降のbaseを順にmainへ変更し、各PRの差分がその段階の固有ファイルだけであることを確認
6. #205 → #206 → #207 → #208 → 72の順に、段階ごとに再QA（各`qa_*.py`）を行ってから統合
7. 統合後のmainで、manifest未登録・本番スプライト不変・CIのPASSを確認
8. ブランチの整理（承認後）：66、67、68、69、70、71、72の各作業ブランチと、2本のCI修正ブランチ

**代替案：** 72のPR1本を#204〜#208を含めてmainへ統合する方法もある。CIは最上段だけ評価されるが、段階ごとのレビューの粒度が失われるため推奨しない。

**本番採用は別工程：** スプライトの配置、manifestへの登録、ゲームへの組み込みは、mainへの候補統合とは別にディレクターの承認が必要。
