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
`tests/run_python.py`は任意のChromium実行ファイル指定だけを行い、assertion/待ち時間/ブラウザオプションを変更しない。

## 素材棚卸し

[仮素材一覧](../art/placeholder-inventory.md)は既存manifestと全マップから再生成可能。
node/layer合計でstandin=48、placeholder=51（asset ID単位）。既存check_assets.pyのfirst-matchと同じ分類。
manifestでreal扱いの手続き生成建物/NPCも完成画像と保証されるわけではない点を明記。
画像・manifest・生成済みmapの変更なし。

## 検証結果

全回帰の終了後に終了コード一覧を記録する。
素材checkerは0 errors / 13 warnings（既存baselineと同じ）。
Android実機120Hzは作者PLAYER QAが必要。ブラウザのuncapped計測は環境負荷でHzが変動する。
