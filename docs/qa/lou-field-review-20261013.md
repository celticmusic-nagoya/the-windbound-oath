# HH フィールドルー検品 / 軽量化案

基準main `31a5f5e`、ブランチ `work/codex-gg-kk`。テスト/新規生成tool/docsのみ。縮小画像は `/tmp/lou-field-proposal` に生成し採用しない。

## 結果

37項目すべて合格、FAILS0、pageerror0。合流前後、屋内非表示、FieldChoreo中の6コマ循環、マップ切替、高さlift、戦闘突入/結果→復帰、実saveGrowthData/loadGrowthDataをPC・縦・横で確認。DEVジャンプによるセーブ抑止を避け、enterMossForestで準備した。

rootのforestLouは幅/高さ0の配置用要素であり、Playwrightのis_visibleはfalseになる。表示中のimgで可視性を判断する（テスト初回の復帰/復元失敗6件はこの判定ミス、修正後0件）。

## 提案

| 6枚合計 | 元PNG | 高さ120px PNG | 高さ120px lossless WebP |
|---|---:|---:|---:|
| bytes | 2303132 | 93723 | 81936 |

表示52pxに対して120px（約2.3倍）を候補とした。RGBA/縦横比を維持。battle torso anchorsを各フレームの実幅/高さ比で変換したmanifestを生成し、足元基準と胴体基準を混同しない。現field実装は画像bottom+hoverを使用しており、manifest anchorを反映する仕様変更は未実施。

`python tools/field/make_lou_field_frames.py --output /tmp/lou-field-proposal` で再生成できる。img配下への出力は拒否する。比較はブラウザの画像リクエストを候補PNGへrouteするだけで本体ファイルは不変。

## PC Chromium参考計測

各条件3秒のrAF、decodeは6枚同時・3回の中央値。decode値はローカルHTTP読込込み、ネットワーク/実機の負荷ではない。順次実行・小標本で性能改善の断定不可。

| 表示 | 素材 | decode median ms | mean frame ms | p99 ms | 移動距離px |
|---|---|---:|---:|---:|---:|
| pc | original | 29.00 | 28.04 | 50.00 | 910.0 |
| pc | proposal | 14.90 | 30.47 | 66.70 | 905.0 |
| pc | hidden | 26.40 | 26.55 | 50.00 | 910.0 |
| portrait | original | 26.50 | 16.67 | 16.80 | 904.9 |
| portrait | proposal | 14.00 | 16.67 | 16.80 | 905.0 |
| portrait | hidden | 36.40 | 16.76 | 16.80 | 905.0 |
| landscape | original | 27.10 | 16.67 | 16.80 | 904.9 |
| landscape | proposal | 15.60 | 16.67 | 16.80 | 910.0 |
| landscape | hidden | 30.50 | 16.67 | 16.80 | 910.0 |

hidden条件も元画像はロードされるため、描画非表示の比較であり「画像未ロード」のメモリ削減比較ではない。移動は実キーを使用し、変位を記録。停止した区間/衝突は数値の制約として扱う。Android性能は未測定。

## 見た目 / 要判断

PC・縦・横の追従と高さスクショは [証跡](lou-field-20261013/) に保存。高さ1ではFionaと同じ-56px lift。背後2.4倍という計算はFionaが演出で前へ動く場合はルーを更に前方へ置く。通常追従では空中22pxを確保するが、狭い位置/演出時はキャラの輪郭が重なり得る。独立したLouの演出位置指定やオフセット制限は作者判断、変更していない。画面外や一瞬のチラつきを全経路で否定するテストではない。

縮小版は読込量を約96%削減する候補。52px表示の縮小版の見た目をPLAYER QAしてから採用判断する。採用素材の差替えはClaude担当。

変更: tests/moss/m33_lou_field_review.py、tools/field/make_lou_field_frames.py、本報告/証跡。再実行は `python tests/moss/m33_lou_field_review.py`（既定では一時候補を自動生成して終了時削除、LOU_PROPOSAL指定時だけ既存候補を使用）。自身の8812サーバーを終了。次II。main未統合、将来の戻し方は `git revert -m 1 <merge>`。
