# モルウェン Layer 0（BASE_BODY）候補 v0.7（CHARACTER-ASSET-STUDIO-10 TASK D／F）

**状態: 未承認の候補。正式な素体ではない。** 正式な素体は、この後の画像生成、骨格の比較、ディレクターの承認を経て決める。

- 入力: v0.6 の計測結果（変更していない）と、v0.7 で正規化した4方向の作業用コピー（`normalized/morwen-final-canon-20261111/`）。
- 作り方: `python3 tools/character-asset-studio/pipeline/cas.py layer0-candidate --character morwen --age-category minor --evidence <v0.6 measurement_evidence.json> --transforms <view_transforms.json> --out-dir <このフォルダ> [--overwrite]`
- 体のガイドの方針: モルウェンは17歳のため `minor_neutral_structure`。マネキンのように中立的な構造ガイドで、解剖学的な細部は描かず、年齢と体格も変えない。

## ファイル
| ファイル | 内容 |
|---|---|
| `BASE_BODY_SPEC.candidate.json` | BASE_BODY_SPEC v2.0（形式は変更なし）の未承認候補。座標は正規化後のもの（接地点は (600, 1540)） |
| `front／back／left／right_body_guide.png` | 透明背景のガイド（○ = VERIFIED、□ = ESTIMATED、破線 = DESIGNED_CANDIDATE）。測定不能（UNKNOWN）の関節は点を描かず、名前だけを書く。`_preview` は正規化した正本を薄く重ねた確認用 |
| `landmark_evidence.json` | 方向・ランドマークごとの計測状態と根拠。設計した候補値は `designedCandidates` に分けて記録する |
| `production_brief.json` | ChatGPT が画像を作るための制作指示（`cas/production-brief/0.5`）。VERIFIED／ESTIMATED の点だけを載せ、UNKNOWN の関節は「設計して DESIGNED_CANDIDATE として返す」よう指示している。画像の生成は別の工程 |
| `BODY_QA_REPORT.json` | QA結果 |

## 計測状態（40点）
| 状態 | 件数 | 内容 |
|---|---|---|
| VERIFIED | 10 | 接地4、足の接地点6（靴底から自動で計測） |
| ESTIMATED | 7 | 膝6（目視、人間の確認なし）、首1（推定） |
| UNKNOWN | 23 | 頭頂、肩、骨盤、首（背面・側面）、側面の奥の膝・足 |

- UNKNOWN の23点は、正本から計測した値として登録していない。BASE_BODY_SPEC v2.0 は全項目に値が必要なため、テンプレートの値を `template_default`／`provisional` として仮に入れているだけで、QA では BLOCKED にしている。テンプレートの値を正式な骨格の値として採用することはない。
- 設計した候補値（DESIGNED_CANDIDATE）は、共通の膝の高さ y = 1076 の1つだけ。正規化後の膝の高さ（ESTIMATED）の平均で、方向ごとに 1059〜1093 と34px の幅がある。BASE_BODY_SPEC には入れず、`landmark_evidence.json` にだけ記録した。

## QA（`BODY_QA_REPORT.json`、全体 BLOCKED、採用不可）
- PASS（69件）:
  - 4方向の接地点が (600, 1540) で一致する
  - 正規化座標とピクセル座標が一致する（17点）
  - UNKNOWN を計測値として登録していない（23点）
  - 設計値を仕様ファイルに混ぜていない
  - 仕様ファイルと制作指示がスキーマを満たす
  - 自動採用しない
  - R2.1 が BLOCKED のまま
  - 正本17件の SHA-256 が変わっていない
- BLOCKED（23件）: UNKNOWN の関節。
- NOT_RUN（22件、人間の確認待ち）:
  - モルウェンのデザイン保護12項目（`profiles/morwen_design_protection.json`）
  - ESTIMATED 7点の確認
  - 方向ごとの膝の高さの違い
  - 4方向の骨格の整合
  - ディレクターの承認
