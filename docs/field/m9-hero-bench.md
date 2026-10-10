# 主人公ビジュアル(フィオナ/エイダン) と 断崖ベンチイベント (M9)

## フィオナ field スプライト
- 生成: `python3 tools/field/make_fiona.py`（決定的）→ `img/field/moss/real/fiona/fiona_{idle_<dir>|walk_<dir>_01..06}.png`（4方向 × (待機+6コマ歩行) = 28枚）と `js/field/fiona-field-assets.js`（`window.FionaFieldAssets.frames`、AidanFieldAssets と同形式）。
- 仕様: 512×640 透過RGBA、足元アンカー(256,600)、scale 0.1（約46 world px、エイダンと同クラス）。3倍スーパーサンプリング→LANCZOS。1コマ=1透過PNG。
- 設定: 人間の耳（エルフ耳・翼なし）、薄い栗色の長いウェーブ髪、緑の瞳、花と葉の髪飾り、アイボリー＋深緑＋アンティークゴールド、麻のブラウス・革コルセット・蔓の杖(緑の宝石)。
- ランタイム: `moss-forest-runtime.js` の `mountFionaSprite/updateFiona`。追従で動くと歩行コマ(105ms/コマ)、止まれば待機。向きは移動方向、停止時はプレイヤー方向。`FieldChoreo` の移動でも同様に歩く。
- 差し替え: 手描き素材が届いたら同名PNGを置き換えるだけ（キャンバス/アンカーが同じなら `fiona-field-assets.js` の bounds だけ更新）。
- エイダン: 既存の高精細な4方向×4コマ素材を維持し、歩行中に 1.5px のステップ上下動を加えて滑らかに。リメイク(新規描き下ろし)は手描き/画像生成素材の到着待ち。

## 風見の断崖のベンチ（選択肢イベント）
1. stage 3 で頂上のベンチを調べる → `FieldTalk.talk('cliff_bench')`（`talk-data-scenes.js`、`when: stage 3`）。
2. 会話の末尾に **はい / いいえ**。
   - はい: フラグ `cliff_bench_sat` を立て、選択肢効果 `scene:'cliff_sunset_to_fire'` でシーン開始。エイダンとフィオナがベンチ前に歩み寄って（着席の代わり）夕景→夜→村の炎上→stage 4 へ進行。
   - いいえ: 返答のみで通常状態へ戻る（何も進まない。何度でも再選択可）。
3. 頂上トリガーは stage 3 ではヒント表示のみ（シーン自動開始はしない）。stage 15 以降は従来どおり時間帯切替。
- 新しい選択肢効果: `scene:'<FieldScene id>'`（field-talk.js）。
- テスト: `tests/moss/m7_cliff.py`（いいえ→変化なし、はい→フラグ+シーン）、`tests/moss/m9_hero.py`。
