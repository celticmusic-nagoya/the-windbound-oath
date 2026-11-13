# モルウェン Blender制作進捗｜MORWEN-PRODUCTION

> **最終確認：2026-11-13 JST**｜この文書は自動更新ではありません。GitHub Actionsの実行状況は下記リンクから確認してください。

## 現在の状態

| 工程 | 状態 | 確認内容 |
|---|---|---|
| 正式四面図・衣装参照の整理 | DONE | MORWEN-PRODUCTION-06参照資料／ハッシュ照合 |
| Layer 0：素体候補 | SCRIPT_READY | メッシュ生成コードあり。正式品質未達 |
| Layer 1：インナー・ニーソックス | SCRIPT_READY | レイヤー別試作。正式品質未達 |
| Layer 2：制服・スカート・ブーツ | SCRIPT_READY | レイヤー別試作。正式品質未達 |
| Layer 3：帽子・マント・鞄・装飾 | SCRIPT_READY | レイヤー別試作。正式品質未達 |
| ガーターベルト | CANON_LOCKED | 本人の右脚のみ／正面画面右・背面画面左 |
| 16枚のBlenderレイヤー別実レンダリング | **NOT_VERIFIED** | 実行成功と成果物の確認待ち |
| 正式四面図との独立美術QA | NOT_RUN | 16枚の実画像が必要 |
| 本番採用・mainマージ | NOT_DONE | 承認前に実施しない |

**重要：** 既存のMVP Blockout成功は、Layer 0〜3の正式衣装レンダリング成功を意味しません。

## GitHubで進捗を確認する

- [GitHub Actions 実行一覧](https://github.com/celticmusic-nagoya/the-windbound-oath/actions)
- [既存MVP Blockoutの成功実行（参考、正式品質ではない）](https://github.com/celticmusic-nagoya/the-windbound-oath/actions/runs/43362808451)
- [今回の制作ブランチ](https://github.com/celticmusic-nagoya/the-windbound-oath/tree/feature/mvp-blockout-01)
- [Layer 0メッシュ生成候補](../../tools/blender/production_mesh_07/build.py)
- [Layer別制作仕様](MORWEN_PRODUCTION_08_LAYER_RENDER_PLAN.md)
- [右脚ガーターの正本](MORWEN_GARTER_RIGHT_ONLY_CANON.json)

## 次の完了条件

1. GitHub Actions上でBlenderを実際に起動し、Layer 0〜3×4方向の16枚を出力
2. PNG16枚と編集可能な.blend、SHA-256/QA記録をArtifactsへ保存
3. 四面図と照合し、右脚ガーター、ニーソックス、左右非対称の装飾を確認
4. 美術QA PASS後のみ完成品質と表示

**更新ルール：** 成功の証拠（実行URL、コミットSHA、Artifact名）が揃った工程だけDONEに変更。未実行や未検証をPASSにしない。
