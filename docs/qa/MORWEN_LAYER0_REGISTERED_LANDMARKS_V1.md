# Morwen Layer 0 四方向ランドマーク v1

Draft PR #427、入力 HEAD `f3e60c5d7cab782adf6330b6c8e0354e6503e77d`。添付 blueprint v1 の ZIP SHA-256 は `95078f8296e18a822ebebc18408499beec6d4e83ec29331bfc7b45222b8d0388`。内部 PNG 4枚は [PR #419 の参照パス](https://github.com/celticmusic-nagoya/the-windbound-oath/tree/feature/morwen-rebuild-01/tools/blender/production_mesh_08/references) の実体とバイト一致。[既存の測定結果](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44679568515) のアルファ境界と一致。参照原本の複製は追加していない。

`tools/morwen_authored_sculpt/layer0_landmarks_v1.json` に46点の元画像座標、不確かさ、可視状態および遮蔽箇所を記録。座標は手動読取値で、肩と首の位置は推定。正面と背面で反対側に見える留め具を鏡像補完せず、左側面では遮蔽として扱った。アルファ最下端と上下のアルファ境界間隔を登録に使用し、水平アンカーは足元を目視で推定。正規化座標は図面上の比較用。正投影、姿勢差、実寸、三四分角の奥行きは未校正。

実行（Pillow、入力は原本4枚を置いたディレクトリ）

```sh
python3 tools/morwen_authored_sculpt/render_layer0_landmarks.py INPUT_DIR OUTPUT_DIR
```

出力は四方向の注記付きPNGおよび `registered_landmarks.json`。ローカルで二度実行し、全出力のバイト一致を確認。G1は参照ハッシュと登録処理を確認済み、独立注記レビューと投影校正は未実施。G2 / G3 / G4 は NOT_RUN。

次工程は編集可能な比較用モデルの権利・出所・SHAの確認。MakeHumanのCC0インポート証跡は [既存の成果物](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44553193163) を再利用できる。VRMの[往復試験](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44678376702)はフィクスチャの互換性確認。利用権を確認済みの候補または独立スカルプトの実体が揃うまで、三方式の採否判定は保留。過去の局所パッチとリング方式の失敗証跡を継承する。
