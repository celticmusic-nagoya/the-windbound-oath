# MORWEN-PRODUCTION-73 本番組み込み調査・Draft実装計画

- **状態：** 調査と計画のみ。コード・本番素材・manifestは未変更。
- **入力：** mainの`assets/candidates/morwen-right-walk/72/`（MORWEN-PIXEL-72、正式採用済み。Android 4/4 PASS、第三者美術QA PASS）。
- **調査時点のmain：** `8e67dc25`（#204〜#209の統合後）。

## 1. 現行ランタイムの調査結果（main）
| 項目 | 事実 |
|---|---|
| モルウェンのフィールド表示 | **未実装**。`index.html`（と`dev-fresh-20261108.html`）にパーティのデータ（`morwen:{joined:false,...}`）があるだけ。フィールド用アセットのレジストリやJSからの参照は0件 |
| 仲間の素材の形式 | `js/field/<hero>-field-assets.js`の`frames`（`path`・`width`・`height`・`bounds`・`anchor`・`scale`）。`tools/field/install_hero_frames.py`が素材を正規化してmanifestのJSを生成する（エイダンとフィオナのみ対応） |
| 必要なコマ | 4方向（下・左・右・上）それぞれに待機1枚と歩行4〜6枚。フィオナは左右に横向きの専用6枚（`fiona_side_*`）がある |
| 歩行コマの選択 | `js/field/walk-motion.js`の`ally()`。`id`は`aidan`/`fiona`の2択で固定。コマは移動距離で切り替わる（`STRIDE=90`、`MossForest.walkStride(id,dir)`で上書き可） |
| 仲間の追従 | `moss-forest-runtime.js`にフィオナとルー専用の処理（`el.fiona`、`fionaVisible`）。3人目の追従者を置く汎用の仕組みはない |
| 表示上の揺れ | `field-sprite-motion.js`の`companion`の設定（bounce 2.5、sway 1.2） |
| 方針 | AGENTS.md（2026-11-08）のフィールド刷新では「各方向の静止画＋JS/CSSの揺れ」が既定で、歩行アニメーションは保留扱い。72の採用は、その例外としての正式採用と解釈する（要確認） |

## 2. 組み込みに不足しているもの（実装前に解消が必要）
1. **右向き以外の方向：** あるのは右向きの歩行6コマのみ。待機、下・左・上の歩行はない。
   - 左右反転で左向きを作ると、鞄の側と装飾の左右が入れ替わる → 公式デザイン上の判断が必要。
2. **縮尺と接地点：**
   - 72は96×128のキャンバス、足の最下行124、48×64版は最下行61。
   - canonical JSON（48×64・原点(24,63)）とは2〜3行ずれる。
   - フィオナの基準（`height` 62・`anchor`(640,790)）にどう合わせるか決める必要がある。
3. **足の滑り：**
   - 72は立脚の足が1コマごとに6px（96px基準）進む。1歩3コマ、1周期6コマで36pxになる。
   - `walkStride('morwen','right')`を「36px×表示倍率」に合わせないと、足が滑る（既定のSTRIDE 90では大きくずれる）。
4. **ランタイム側の対応：** `walk-motion.js`の`ally()`、`labels`、仲間の追従、加入フラグの処理がモルウェンに対応していない。
5. **シナリオとの整合：** 加入時期（`joined:false`）は物語の進行に従う。プロローグでは表示しない想定（要確認）。

## 3. Draft実装の範囲（次のPRで行う。本番切り替えはしない）
| 手順 | 内容 | 検証 |
|---|---|---|
| A | `tools/field/install_hero_frames.py`に`morwen`の設定を追加（ドット絵用の`--dot`、`--mixed-walk-counts`を利用）。出力は候補用のフォルダ`img/field/characters/morwen/`（未参照） | 候補の72のPNGと画素が一致すること（最近傍のみ、補間なし） |
| B | `js/field/morwen-field-assets.js`を生成する。読み込み・参照はDEVフラグの背後に限定 | 既存のエイダン・フィオナのmanifestのハッシュが不変 |
| C | `walk-motion.js`の`ally()`にmorwenの分岐を追加（DEVゲート付き）。`walkStride`は上記3の値 | 距離あたりのコマ進行と足の位置の比較テスト（滑り1px未満） |
| D | DEVのイベントジャンプで、右向き歩行だけを表示する確認ページ（本番のUIには出さない） | PC・Android（実機はNOT_RUNから開始） |
| E | 未作成の方向（待機・下・左・上）はBLOCKEDとして記録。制作タスクを別途起票 | — |

## 4. 禁止・保留
- 本番マップへの配置、本番manifestへの登録、本番公開（GitHub Pagesの通常デプロイで露出させない）は行わない。
- 正本・既存の仲間の素材・SAVEの形式は変更しない。

## 5. 判断が必要な事項
1. 左向きを左右反転で作ってよいか（鞄の側が入れ替わる）。
2. 表示の高さ（フィオナの46〜62と同じ尺度にするか）と、原点(24,63)との整合。
3. 歩行アニメーション方式を、2026-11-08の「静止画＋揺れ」方針の例外として正式に扱うか。
4. フィールドでの加入時期と表示条件。

## 6. 統合作業の記録（MORWEN-INTEGRATION-72）
| PR | mainへのmerge commit | mainに入った差分 | 画像の再現確認 |
|---|---|---|---|
| #204 | `ec47df1b` | `right_walk_66/67` | 24枚一致 |
| #205 | `d8d20401` | `right_walk_68` | 12枚一致 |
| #206 | `9f7b780c` | `qa_69` | 画像なし（資料） |
| #207 | `e62ede9a` | `70` | 70と70/art/ART-70Bで24枚一致 |
| #208 | `34196cba` | `71` | 12枚一致 |
| #209 | `8e67dc25` | `72` | 12枚一致 |

- `assets/candidates/morwen-right-walk/`以外のツリーのハッシュは、統合前後で同一（正本・`img/`・`data/`・manifest・JSは不変）。
- **CI：** `Official HD pixel candidate QA`は、パスの条件により#204〜#209とmainのいずれでも起動しない（NOT_RUN）。同じ手順（単体テスト・候補ディレクトリの走査）をローカルで実行し、#204・#205のHEADでPASS。
- **GitHub Pages：** mainへのpushでPagesのビルドが自動で走った。中間のコミットのビルドはキャンセル（後続に置き換え）され、最終の`8e67dc25`のビルドが実行された。追加されたのは参照されない候補ファイルだけで、ゲームの動作に変更はない。
