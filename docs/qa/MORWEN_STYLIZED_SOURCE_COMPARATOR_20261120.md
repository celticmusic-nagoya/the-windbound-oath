# Morwen｜Blender Studio 素体 C のレンダー検証

入力 `487c822`、既存 Draft PR #427 の実行差分 `fc80b45`。最初の Actions は [公式ZIPへのHTTP 403](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/44684399381) で、Blender 起動前に停止した。取得方式を既存監査と同じ User-Agent に合わせ、公式ミラーと固定SHA検証を追加した。

[公式配布ZIP v1.4.1](https://download.blender.org/demo/asset-bundles/human-base-meshes/human-base-meshes-bundle-v1.4.1.zip) のSHA-256は `811f43accbb31a88266d932f8f5563b2d13586fca0ba2693aad1f5fe582b3515`。内蔵READMEの “All provided assets are public domain under the CC0 license.” を確認した。Rain Rig の別ライセンス文は該当2コレクションに適用せず、Rain Rig は出力に含めない。

| ソースコレクション | 主メッシュ | 頂点 / 辺 / 面 |
|---|---|---:|
| Head - Stylized | GEO-head_stylized | 4,118 / 8,250 / 4,134 |
| Body Female - Stylized | GEO-body_female_stylized | 12,502 / 25,000 / 12,500 |

各コレクションには元の左右眼球があり、それぞれ802頂点、1,632辺、832面。引き継ぎ文書の数値に代えて、固定SHAの実ファイルから得たデータブロックの実測を記録した。Blender 5.3.0で各5方向、クレイ、透過、CPU Cyclesを実行し、保存した両 .blend を開き直してメッシュの件数と変換行列が一致した。材質はビュー層で上書きし、メッシュを変更せずカメラと照明を高さに合わせた。左右のファイル名はLayer 0の横顔の向きに対応する。ワイヤー画像はCyclesのレンダー時の三角化を表示する。

Layer 0との形状比較は `NOT_COMPARABLE`。頭部単体で全身を登録できず、全身素体も参照画像と姿勢や外形が異なる。IoUと解剖学ランドマーク誤差は出していない。G1は素材の同定・権利確認済み、キャラクターの設計整合未判定。G2 / G3（モルウェンとして）/ G4 は NOT_RUN。Aの権利・SHA確認済みVRoid/VRM入力とBの新規編集可能スカルプトを得られた時点で共通条件の比較に進む。
