# 依頼G：品質・基盤

開始main: `bbfec606b5295c25432e5d7c8cda0212e92b7c03`。
作業ブランチ: `work/codex-quality-foundation`。main/Pagesへの反映なし。

## 移動速度

mainに既存のdt補正があり、Mossのキーボード・ポインタと旧Lindのポインタは共有時計を使用する。
旧Lindのキーボードはkeydown入力単位の移動なので、rAFのHz補正を重ねていない。
既存の`frameScale >= .1`は600Hzを超えるuncappedブラウザで過剰移動になる。
正の最小値をNumber.EPSILONへ変更し、60Hzの歩幅・50ms上限・collision sweepは維持。
実rAFコールバックを呼ぶNodeテストで30/60/120/144/240/1000Hzの2秒移動量=600pxを検証。
`m55_hz.py`は既存のpointer試験にMossのheld keyboardとJS例外確認を追加。

## m6_quest

変更前に「reward page shown and granted」が失敗し、その次の#msgクリックがtimeout。
開始1秒後にfixtureをresetしているため、約1.1秒後のNEW GAME開始がクエスト会話に割り込む。
冒頭会話を待ちcloseDialogueしてからfixtureを開始すると全assertionが合格。
クエスト報酬（ether+1/護符）、会話データ、保存処理は変更していない。

## 全回帰の実行

```sh
# Playwright標準Chromiumがある環境
./tests/run_all.sh

# このクラウド環境のインストール済みChromiumを使う場合
PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium ./tests/run_all.sh
```

Python Playwright/Pillow、Node、GNU timeoutが必要。
全standalone Pythonテストと*.test.jsを逐次実行。テストごとの終了コードをresults.tsvに保存し、失敗時も残りを継続。
HTTPサーバは8765でランナーが所有し、終了時にそのPIDのみ停止。既存サーバが使っていれば開始を拒否。
結果ディレクトリは既定で/tmp/windbound-regression.*、TEST_RESULTS_DIRで変更可能。
各テストの上限は900秒、TEST_TIMEOUT_SECONDSで変更可能。timeout=124は失敗として記録。
引数なしで全件、ファイル名を渡すと対象だけ再実行する。引数が必要なwalk_map.pyはA2を指定（A1/A3には専用回帰あり）。
ランナー実行中はランナー自体を編集しない。
`tests/run_python.py`は任意のChromium実行ファイル指定だけを行い、assertion/待ち時間/ブラウザオプションを変更しない。

## 素材棚卸し

[仮素材一覧](../art/placeholder-inventory.md)は既存manifestと全マップから再生成可能。
node/layer合計でstandin=48、placeholder=51（asset ID単位）。既存check_assets.pyのfirst-matchと同じ分類。
manifestでreal扱いの手続き生成素材も、gen指定を別表で棚卸し。完成画像と保証されるわけではない点を明記。
画像・manifest・生成済みmapの変更なし。

## 検証結果

初回全件では41件合格・2件失敗。seal_a3はDEV harnessのfavicon.ico 404、walk_mapはランナーのマップ引数不足。
DEV harnessへ既存PNGのfavicon参照を追加し、walk_mapをA2指定で起動するよう修正。
初回は実行中のランナー編集により終了処理にもエラーが出たため、修正版を固定して全件を再実行。
最終全回帰: **43/43 PASS、ランナー終了コード0**。
サーバ停止後の8765への接続が拒否されることも確認。
[終了コード一覧](quality-foundation-results/results.tsv)と代表ログを保存。
高Hzブラウザの移動量比: 旧Lind pointer 1.02、Moss pointer 1.00、Moss held keyboard 1.02。
Moss速度は通常約300px/s、uncapped約299px/s（測定時57Hz / 242Hz）。
Node実時計は30/60/120/144/240/1000Hzすべて2秒600px。
DEV結界/A2全経路もerrors=[]、failures=0。
旧Lind pointerは到着前の0.5秒（約150px）を測定し、速すぎる移動による偽合格を防ぐ。
Moss keyboardは固定座標ではなく、collisionとイベント領域を避けた空き通路を検索して測定する。
素材checkerは0 errors / 13 warnings（既存baselineと同じ）。
Android実機120Hzは作者PLAYER QAが必要。ブラウザのuncapped計測は環境負荷でHzが変動する。

終了時のremote mainは `e3565b68acc581759d24c7f6154cdeb51d58f049` へ進行。
本ブランチの検証は開始main（bbfec60）を基準とする。main統合前に最新mainとの再検証が必要。
