# PROLOGUE-RETURN-01｜実装前の現行コード監査・受入条件

状態: **PARTIAL / 実装前監査**。本資料はゲームのイベント実装・正式シナリオ改変を行わない。

## 目的
正式採用した「レイダー討伐→ルー案内で荒廃したリルド村に再訪→エマと再会→コナーの息子と認識する増援騎士との会話→フィオナが同行を決断→ドゥンヴァル砦」を既存進行へ安全に組み込む。

正典: 非公開 `the-windbound-oath-handoff/reference/lore/SCENARIO_CANON_20261108.md`（ADD-003）。公開リポジトリに非公開正典の全文を複製しない。

## mainの現状（直接確認）
- `index.html`: `startRaiderAftermath()` は storyStage=13、`aftermathScene` 終了時に `PartyManager.support.joined=true`、storyStage=14へ変更して **650ms後に直接 `startFortFinale()`**。
- `index.html`: `fortLines` の冒頭は「夜明け。長い森を抜けた先に、王国軍の小さな砦が見えた。」。エマとの再会が入らない。
- `index.html`: `startFortFinale()` は storyStage=14、`showPrologueEnd()` で storyStage=15。装備支給は `fortIndex===6` で実行。これらの副作用を保護する。
- `js/field/rilde-village.js`: 平和/廃墟の切替は `storyStage>=5` または `rilde_ruined` フラグで判定。砦からの自由探索は `afterPrologue()`。
- DEVジャンプの `aftermath`、`fort`、`prologueEnd` と SAVE/CONTINUE は既存のstoryStageに依存する。ステージ番号の全体繰り下げは避ける。

## 実装設計（承認済みシナリオを尊重した提案、未実装）
1. レイダー戦後の `aftermathScene` を維持し、ルーの加入フラグも既存タイミングで設定する。
2. 従来の「森→砦」の直行遷移を「森→リルド村再訪シーン→砦」に置き換える。**storyStage=14を遷移用に再利用**し、新たなstageを無断で追加しない。シーン完了フラグはSAVEとの関係を調査して設計。
3. リルド村の廃墟を見せる。ルーの案内、エマ生存とフィオナの再会、村の救助・復興、増援騎士によるコナーの息子の認識、フィオナの自発的同行決定を描く。エマは村に残る。
4. エマの護符は**任意クエスト**として別の状態管理を維持。再会時の自動付与禁止。
5. 再訪シーンの完了後のみ `startFortFinale()` に進める。砦での装備支給、ルー加入、誓いの剣、風の舞、エンディングの一度きり実行を保護。
6. 台詞・立ち絵は正式採用された脚本に合わせ、既存の `FieldTalk`/CG管理を優先。仮台詞を正式採用として登録しない。

## 実装前に必要な調査
- `index.html` のSAVE/CONTINUE復帰処理とstoryStage=13/14/15の再入条件。
- `aftermathScene`/砦/村の表示切替と `MossForest`、`RildeVillage.enter()` の呼出条件。
- エマの立ち絵・既存の再会CG/脚本ID・騎士の立ち絵の可用性。
- 旧SAVEの「stage14=砦」からの復帰互換。新SAVEの「stage14=村再訪中」と衝突しない設計。
- 正典にある固定台詞と別チャット採用脚本全文の一致。

## 受入基準（実装時）
- 新規開始から襲撃→川へ跳躍→森→レイダー→村再訪→砦が連続進行し、シーンスキップ・タップ連打で重複しない。
- エマの生存と再会が描写され、フィオナが自分の意思で同行。騎士はコナー生存設定と整合。
- 旧SAVE stage13/14/15、既存装備支給、ルー支援、エマ護符の一度きり受注/報酬、襲撃後村マップが退行しない。
- 画面表示切替時の背景露出・二重表示なし。Android縦横とブラウザで確認。
- 独立QA完了までDraft。mainマージ・公開なし。

## QA判定
**現行コード差分の特定: PASS**。
**イベント実装・自動回帰・Android実機・旧SAVE互換: NOT_RUN**。
PR #169（脱出修正）は別ブランチで進行中。依存関係の調整前に両ブランチを同時マージしない。
