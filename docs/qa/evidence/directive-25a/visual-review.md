# Visual review — Chromium captures, not Android hardware

rootが実際のcaptureを確認。

- `screenshots/25a_normal_fiona.png`: NEW GAMEから実walk/touchした通常会話。Fionaの顔・上半身が見え、台詞と操作領域は読める。259正式素材を無変更で使用。
- `screenshots/portrait_touch_390x844_cg3.png`: 正式縦CGと台詞の可読性を確認。ルー/魔法/Fiona/敵と台詞表示が欠けず、立ち絵重複なし。
- `screenshots/landscape_915x412_altar_cg01.png`: 横CGはfull-art contain、顔/剣/敵を切らず台詞を前面表示。横長画面では高さによる左右余白が残る既存方針であり、幅100%達成と偽らない。
- `25a_normal_training_won.png`は訓練終了直後のcapture。非同期portrait画像のreadyを待つ完成描画の判定には使用しない。ready後の全115ページcanvas/瞬きはm53のpixel判定を正本とする。
- `25a_seeded_capital.png`は隔離seeded fixture。通常NEW GAMEから王都まで歩いた証拠ではない。

全battle/menu controlのtap最小寸法・全mapの全edge・実指での押しやすさを網羅したとは判定しない。端末OS/画面/Chrome固有の最終確認はユーザー実機が必要。

- `screenshots/25a_normal_attack.png`: 通常到達stage5で旧DOM field（F/騎等の文字・CSS図形）が表示される。台詞とAidan portraitは前面表示。平和時pixel mapとの差はM08/P6-FIELD-01のPARTIALとして記録する。
