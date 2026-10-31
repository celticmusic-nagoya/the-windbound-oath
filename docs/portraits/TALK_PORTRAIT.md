# 会話立ち絵・表情・瞬き 共通システム（Phase 3）

会話（FieldTalk）中に、キャラクターの立ち絵を表示し、表情を切り替え、自然な間隔で瞬きさせる共通の仕組み。キャラクターごとの専用コードは持たない。新しいキャラクターは、レジストリへの登録 1 件と画像だけで追加できる。

- **移植元：** `feature/asset-emma-01` @ `f4456a82`（`talk-portrait.js`、`field-talk.js` の立ち絵接続部、TalkPortrait の CSS、テスト m30・m31）。
  - Issue #16 P2 の表示管理（所有者＋世代番号、`fix/fiona-lou-portrait-lifecycle-p2` @ `5d915ed9`）をそのまま引き継いでいる。
  - 移植はファイル単位。フィオナ・ルー・エマの画像は持ち込んでいない。
- **瞬きの基準：** フィオナ戦闘待機 v3（`feature/fiona-idle-v3`）の目元重ね方式とタイミング。
  - エイダンの瞬き素材は Phase 2 Rev2（2026-10-27 正式採用）。

## ファイル

| ファイル | 役割 |
|---|---|
| `js/field/portrait-registry.js` | キャラクター登録。画像の場所・表情・切り出し・既定の表示位置・瞬き素材を持つ唯一の場所（ほかのコードは画像パスを組み立てない） |
| `js/field/portrait-blink.js` | 瞬きの時間制御。キャラクターにも DOM にも依存しない（Node で単体テスト） |
| `js/field/talk-portrait.js` | 表示：所有者管理・表情や話者の切り替え・canvas での合成・瞬きの開始と停止・後片付け |
| `js/field/field-talk.js` | 会話から立ち絵への受け渡し（開始・ページ・終了・取り消し・LOAD） |
| `css/style.css`（末尾の TalkPortrait 部分） | 会話ボックスの直上に置く枠、画面の左右、画面サイズ別の大きさ |
| `assets/images/characters/portraits/{characterId}/` | 正式採用の立ち絵（無加工）と瞬きの重ね画像。`SHA256SUMS` 付き |
| `dev/talk-portrait-preview.html` | 開発用プレビュー（ゲームの状態に触れない） |

## キャラクターの登録

```js
PortraitRegistry.define('aidan', {
  name: 'エイダン',
  src: {w: 1024, h: 1536},                                   // 元画像の大きさ。座標はすべてこの px
  base: 'assets/images/characters/portraits/aidan/',
  file: f => 'aidan_' + f + '.png',
  crop: {x: 190, y: 0, w: 800, h: 760},                      // 会話で見せる範囲（胸から上）。枠はこの縦横比
  side: 'left',                                              // 既定の表示位置
  faces: ['normal', 'smile', 'angry', 'worried', 'sad', 'surprised'],
  blink: {                                                   // 書かなければ瞬きなし（静止立ち絵）
    seq: BLINK_V3.seq, gap: BLINK_V3.gap,                    // 30/30/35/70/35/30/30ms（計 260ms）、3〜6 秒間隔
    faces: [...],                                            // 瞬きする表情（閉じ目の表情などは外す）
    file: (f, eye, s) => 'blink/' + f + '_' + eye + '_s' + s + '.png',
    eyes: {L: [570, 268, 654, 320], R: [672, 314, 716, 350]} // 重ね画像の位置（元画像の座標）。表情ごとに違う場合は eyesByFace
  }
});
```

### 表情 ID

- 共通の語彙は `normal smile angry sad surprised worried determined relieved`（`01`〜`08` も可）。
- 各キャラクターの `faces` にない ID、未知の ID、読み込めない画像は `normal` で表示する。`normal` も読めない場合は立ち絵なしで、会話は止まらない。
- エイダンは `normal smile angry worried(困り顔) sad(伏し目) surprised`。

### 表示位置の決め方（優先順）

1. ページで指定された `side`。
2. 会話全体で指定された `side`。
3. レジストリの `side`。
4. 共通の既定値 `right`。

## 会話データからの使い方

```js
{id: 'example', lines: [{char: 'aidan', face: 'normal', side: 'left', pages: [
  'エイダン「……ここは？」',
  {speaker: 'エイダン', text: '「誰かいるのか！」', face: 'surprised'},  // 表情だけ変える
  {speaker: '', text: '（風が止んだ）', char: null},                 // このページは立ち絵を隠す
  {speaker: 'エイダン', text: '「行こう。」', char: 'aidan', face: 'smile'}
]}]}
```

- 会話またはページの `char` と `face` で、明示的に指定する。話者名から自動で推測はしない。
- `char` のないページは、前のページの立ち絵をそのまま使う。`char: null` で隠す。
- 既存の会話（`char` の指定なし）は、今までどおり立ち絵なしで表示される。

## 描画

- **canvas の中身：** 切り出し範囲と同じ大きさの canvas（元画像の解像度）に、採用画像を 1:1 で描く。補間なし。
  - 開眼時は採用画像そのもの（テストで全画素一致を確認）。
  - 瞬きの段階があるときは、その段階の目元の重ね画像を元の座標にそのまま重ねる。
- **拡大・縮小：** canvas の表示倍率の変更は CSS で 1 回だけ。画像と目元を別々に拡大しないので、ずれや境目の線が出ない。
- **描き直す時：** 段階が変わったとき（1 回の瞬きで 7 回）と、表情や話者が変わったときだけ。常時の描画ループはない。
- **表情を変えるとき：** 新しい表情の画像と重ね画像がすべて読み込めてから、1 回で描き替える（空白のコマを出さない）。同じキャラクターの瞬き中なら、まず開眼に戻す。

## 瞬きと後片付け

| 状況 | 動作 |
|---|---|
| 立ち絵の表示完了 | 3〜6 秒後に最初の瞬きを予約する（タイマーは 1 本だけ） |
| 表情の変更（瞬き中を含む） | 瞬きを止めて開眼に戻し、新しい表情の表示完了後に予約し直す。古い表情の重ね画像は残らない |
| 話者の変更 | 前の立ち絵を消してタイマーを止める。新しい立ち絵の表示完了後に開始する |
| 会話の終了・スキップ・取り消し（`FieldTalk.cancel`）・`say()` での置き換え・LOAD（`FieldTalk.load`）・戦闘開始・会話ボックスが閉じたとき | 立ち絵を取り消し、タイマーを止める。読み込み中の古い要求は、世代番号で無視される |
| 物語の場面（`#louIntroScene`・`#altarScene`。イベント CG はこの中に出る）が開いたとき | 立ち絵を取り消す（重ならない） |
| 画面が非表示になったとき | 瞬きを止めて開眼に戻す。再表示で予約し直す |
| 視覚効果を減らす設定（`prefers-reduced-motion: reduce`） | 瞬きしない。途中で切り替わっても追従する |
| 瞬き素材がない・読み込めない | その表情は静止立ち絵で表示を続ける |

確認用に、`TalkPortrait.status`（表示中のキャラクター・表情・位置・目の段階・タイマー数）と、`TalkPortrait.frame(s)`（段階 s の描画結果の読み取り専用のコピー）を用意している。

## 画面レイアウト

- 枠は会話ボックス（`#msg`）の直上に置き、会話ボックスと選択肢には重ならない。`pointer-events: none` なので、操作を妨げない。
- 高さの目安：PC は最大 52vh・560px、スマホ縦は 34vh まで、スマホ横は 60vh まで。会話ボックスの上の空きに収まるよう、実測で調整する。

## 新しいキャラクターを追加する手順

1. 立ち絵（同じキャンバス・同じ位置の表情差分）と瞬き素材を作り、ユーザーの採用承認を得る。
2. `assets/images/characters/portraits/{id}/` に無加工で置き、`SHA256SUMS` を作る。
3. `docs/ASSET_INVENTORY.md` に記帳する。
4. `portrait-registry.js` に `define()` を 1 件追加する。瞬き素材がまだなければ `blink` を書かない。
5. テスト m40〜m42 を流す。

## 未対応（Phase 4 以降）

- フィオナ・ルー・エマの登録：表情ごとの採用判断の後。
- 複数の立ち絵の同時表示、話していない人物を暗くする表示。
- 実際のシナリオへの表情の割り当て（Phase 5）。

## ゲーム内DEV検証（DIRECTIVE-18C / 18D）

ゲーム開始後、会話を閉じて `DEV ▶` → `立ち絵・モーションテスト`。正式登録済みのキャラクター・表情だけを選べる。未登録のフィオナ・ルー・エマは「未実装」で無効。

- `今すぐ瞬き` は既存の `blinkNow()` で1回再生し開眼で停止。`自動瞬き` は通常の3〜6秒間隔。`連続テスト` はDEV専用の短い間隔。
- `停止・開眼` でタイマーを解除。`フレーム 0〜4` は実際の本編canvasに開眼〜閉眼を静止表示する。
- 状態欄は素材READY/MISSING、実行タイマー、目の段階、次回までの時間、reduced-motion・hiddenを表示。読み込み失敗時はファイルパスと取得/復号失敗を表示する。
- reduced-motion有効時は手動・自動・連続のアニメーションを停止する。フレームの静止確認は可能。設定を尊重し、無理に再生しない。
- パネルは人物の反対側に置き、スマホ横は折りたたんで開く。操作欄はスクロール可能。左右切替・画面回転でも本編と同じ切り出しとcanvasを使う。
- 会話・イベント・読み込み中は起動しない。閉じる/LOAD/戦闘/本編会話による所有権変更で、DEVの描画・瞬き・状態更新タイマーを解放する。セーブやイベントフラグには書き込まない。

`TalkPortrait.devControl(mode, state)` はDEV有効かつ専用所有者 `__devPortrait` のときだけ使える。通常会話の瞬き間隔や描画は変更しない。

本編への初接続は風見の断崖・頂上ベンチの夕日会話（DIRECTIVE-18B）。18Cではsmile/normal各3回の自然な瞬きで、両目の実canvas画素が開眼/半目/閉眼の正式素材合成と一致することを確認した。通常設定で描画不具合は再現せず、端末固有の原因は未確定。[診断と目元比較](../qa/DIRECTIVE-18C.md)。

## Phase4通常3枚 (DIRECTIVE-19B)

2026-10-29、ユーザーがフィオナ・ルー・エマのnormal3枚をSHA指定で正式採用。登録はnormalのみ・blinkなし。他21表情は未承認。[承認・原本照合・本編接続](PHASE4_ADOPTED_NORMALS.md)。DEVでは3人とも選択でき、「未実装・静止画」と表示し、瞬き操作は無効。

既存の専用会話欄では `TalkPortrait.open(owner,{scene,anchor})` を使い、同じcanvasをanchor直上に置ける。sceneはanchorを含む要素。page/closeと世代管理はFieldTalkと共通。scene非表示、CG・戦闘、LOAD、FieldTalk.cancel()で解放する。通常のFieldTalk.open(owner)の挙動は維持。

### DIRECTIVE-20D provisional Android QA

The19 revised20C expressions and24normalblink overlays are now provisionally authorized; see [scope/usage](PHASE4_PROVISIONAL_20C.md) and [per-PNG SHA ledger](PHASE4_PROVISIONAL_20C.json). `PortraitRegistry.get(id).provisionalFaces` and `.provisionalBlink` expose adoption scope for DEV labels. Normal file/crop is unchanged, all expressions reuse that crop; `blink.faces` includes only normal. Fiona8/Lou6/Emma8 faces, Lou smile/relieved excluded. Registration does not mean formal asset adoption.

### Android eyelid correction (20E)

Fiona/Lou use versioned `provisional-20e/` eye-only assets: normalblink16PNG and12expression variants, with the user-approved curved lid shape. Normal images/crops and shared renderer/timing are unchanged. Emma retains20C paths/geometry and all approved-for-QA PNG bytes; user declared its Android result PASS. See [provenance/protection ledger](PHASE4_EYELID_REVISION_20E.json). New derived art remains Android-QA provisional, not formal adoption.

### DIRECTIVE-21A formal adoption

Phase4 current46runtimePNG are now **APPROVED** after user Android QA all4items PASS: Fiona8/Lou6/Emma8 expressions(including normal3) +normalblink24. Exactly the bytes resolved by the PR91 registry are adopted. See [the current formal record/lock](PHASE4_FORMAL_ADOPTION_21A.md). Historical provisional ledgers, path names and DEV QA labels remain unchanged; they record history/UI behavior and are not the authoritative current adoption state. No images or display code changed in21A.

### DIRECTIVE-21C expression blink extension

The5faces angry/sad/surprised/worried/determined now have provisional blink overlays for all3 Phase4 characters. Source bytes and boxes: [21C ledger](PHASE4_EXPRESSION_BLINK_21C.json). Normal overlays remain formally adopted21A files. Fiona/Emma smile+relieved stay still; Lou smile+relieved remain unregistered. Shared renderer/timing unchanged. New120files are provisional, not a change to the formal21A image lock.

### DIRECTIVE-22A expression blink formal adoption

PR93's120expression blink PNGs are now formallyAPPROVED after user Android QA acceptance. [Pinned22Arecord/120SHA](PHASE4_EXPRESSION_BLINK_FORMAL_22A.md) supplements the unchanged21A46file lock; all144normal/expression blink originals stay immutable. No timing/draw changes. Fiona brow repair candidates remain a separate provisional QA workflow; current5fa3532 delivery is CHANGES_REQUESTED and not registered.

## Current status — DIRECTIVE-23A (2026-10-31)

Phase4 COMPLETE; Fiona double-brow repair CLOSED after user PR95 Android all5itemsPASS. R4static3/R3static2/R2blink24 are now formal exactPR95bytes, supplementing prior21A/22A locks. Total259protectedPNG including Aidan/CG; no runtime or image changes. [Current completion/adoption audit](PHASE4_COMPLETION_23A.md). Earlier normal-only/unregistered/provisional sections document earlier phases, not current registration. Fiona8/Lou6/Emma8; normal3+15expression blinks; closedeye4faces intentionally static; Lou smile/relieved still excluded. Phase5 dialogue-expression assignments remain separate scope.

## Phase5 explicit page metadata (DIRECTIVE-24A)

Existing conversations may set `portraits:[{char,face,side}, {char:null}, ...]` beside `pages`. Indexes correspond exactly to the original rendered pages. FieldTalk copies only these three presentation fields; speaker/text, page count, choices/effects/conditions stay unchanged. Narration, unsupported speakers and intentionally mixed pages explicitly hide the portrait. Existing page/conversation metadata still works; explicit per-page metadata wins. This supports the escape scene's shared string array without rewriting its words or pagination. Legacy `say(text, portrait)` and scene-owned text sinks only forward explicitly authored metadata to existing TalkPortrait ownership/anchors; no speaker inference or new renderer is added.
