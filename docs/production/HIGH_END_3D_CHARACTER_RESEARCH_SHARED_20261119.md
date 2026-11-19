# TWO｜高品質3Dキャラクター制作・技術研究と全AI共通制作判断（2026-11-19）

**区分:** 技術研究／制作運用ガイド（正式キャラクターデザインの変更ではない）  
**対象:** ChatGPT / Codex / Claude / Gemini / GitHub Actions、特にモルウェン。  
**優先順位:** 最新 main の AGENTS.md、SESSION_CONTINUITY_INDEX.md、後発承認済み方針、private canon、正式 Layer 0 四方向画像を優先。本書はそれらを上書きしない。

## 1. 結論と制作方法

- **第一候補：正式四方向画像を基準とするアートディレクション主導の新規ヘッド／髪／衣装スカルプト。** シルエット→頭蓋・顔面の面構成→眼窩・まぶた→髪束の大中小の流れ→材質→表情・変形の順に、各段階で正面・側面・背面・斜めを確認。
- **代替：ライセンスを検証した未変形の人体素体をデザインスカルプト。** MPFB / MakeHuman 等を比較し、造形上の改善が実証された場合のみ採用。標準素体そのものを完成モデルと呼ばない。
- **限定利用：VRoid/VRM・旧VRoid派生モデル。** Humanoid、表情、視線、SpringBone、髪・衣装の揺れの技術参照と、検証済み独立部品の提供候補。正式デザインとの不一致がある旧顔全体を最終品質の基礎として再利用しない。
- **禁止する失敗ループ:** 既に美術FAILしたリング断面による顔・毛束の単純量産、Bezier管状髪、変形済みquad patch、旧まぶた環状メッシュの再試行を改善仮説なく繰り返さない。方式変更は構造差・QA仮説を記録する。
- **既存成果物の位置付け:** PR #427の旧顔分離メッシュはトポロジー・UV・ウェイト・58 Shape Keysの保持とCycles CPUレンダリングを確認済み。ただし顔全体G2 FAIL。候補の保護と新規スカルプトは両立する。

## 2. 分野別に取り入れる制作ノウハウ

| 参照分野 | 採用する工程・技術 | 注意点 |
| --- | --- | --- |
| ハイエンドゲーム（原神、NTE、アークナイツ：エンドフィールド等） | 立体シルエット、顔面の法線と陰影、髪束のボリューム、材質差、遠景での視認性、ゲーム内NPR | 固有キャラクター・デザインを複製しない。Blenderと実ゲームの見た目は別途QA |
| フィギュア原型 | イラストを立体化する際の正面印象と斜め整合、髪先・衣装・小物の厚み、原型のクレイレビュー | 静止原型の造形だけでは変形・ゲーム性能は保証されない |
| VTuber / VRM | 目線・まばたき・口形・表情合成・髪や衣装の揺れ・Humanoid | VRM規格とBlender/glTFの機能差、ライセンス、再配布条件を確認 |
| ボカロ系3D/MMD | 顔・髪・衣装のアニメ的形状、表情モーフ、ウェイト調整、見栄えのするポーズ | モデル固有の利用規約・商用可否・変換可否を個別に確認 |
| 造形・リトポ | スカルプトを先に評価、目口・肩・肘・膝のエッジフロー、UVとPBR/NPRを分離 | リトポで不十分なスカルプトを隠さない |

## 3. 環境構築とレンダリング

- **制作原本:** Blender 5.2.4固定版。インストーラー、SHA-256、ソース画像SHA、カメラ、軸、暫定縮尺、依存を記録。仮ローカル座標で独立造形GO、正式ワールド配置は別QA。
- **CI/headless:** GitHub ActionsのUbuntu環境ではEeveeのEGLライブラリ不足で失敗した実績がある。既存の成功構成である **Cycles CPU** を基本にし、Eeveeは環境が整った場合のみ別途検証。Blender Pythonの失敗は `--python-exit-code 1` で伝播させ、PNG実在・サイズ・マニフェスト・再オープンを検査する。
- **二段階レンダリング:** 低サンプルの造形レビュー→承認候補の高品質レンダリング。入力・設定・SHAが同じ成功成果物は再利用。無関係なワークフロー起動を避ける。
- **出力:** .blend原本、正面・左右・背面・斜めの比較PNG、構造QA JSON、原本/出力SHA、出典・ライセンス、必要に応じてGLB。WebGL/AndroidはG4で実測。
- **品質ゲート:** G1正式参照整合、G2独立美術、G3トポロジー・UV・ウェイト・実変形・再オープン、G4ゲーム表示・Android性能。CI成功とG2 PASSを混同しない。

## 4. 優先参考資料（外部資料の転載ではなくリンク・研究用途）

一次資料・公式の導線を優先する。動画の提供範囲、利用規約、更新日、Blender版差分は利用時に再確認する。

1. Blender Studio — Stylized Character Workflow: https://studio.blender.org/training/stylized-character-workflow/ — デザイン→スカルプト→リトポ→材質→表情の一連工程
2. Blender Studio — Toon Character Workflow: https://studio.blender.org/training/toon-character-workflow/ — アニメ調の造形、シェーディング、リグ、アニメーション
3. Blender Studio — Realistic Human Research: https://studio.blender.org/training/realistic-human-research/ — 解剖・顔面形状・変形研究
4. Blender Manual: https://docs.blender.org/manual/en/latest/ — Sculpt、Retopology、Shape Keys、Cycles、glTF export、Geometry Nodesの一次仕様
5. Blender Developer: https://developer.blender.org/ — Blenderバージョン間の変更確認
6. MPFB documentation: https://www.makehumancommunity.org/mpfb/docs/getting_started.html — 素体生成・導入の検証入口
7. MakeHuman Community: https://www.makehumancommunity.org/ — 素体・アセットのライセンスを素材ごとに確認
8. VRM specification and implementation guide: https://vrm.dev/ — Humanoid、Expressions、LookAt、SpringBone
9. VRoid Studio: https://vroid.com/studio — アニメ調アバターの制作ワークフローと利用規約
10. Khronos glTF 2.0: https://www.khronos.org/gltf/ — ゲーム用データ形式・相互運用
11. 3dnchu: https://3dnchu.com/ — Blender、ZBrush、アセット、CG制作技術の新着情報探索。記事は二次情報のため原典を追跡
12. 3dtotal Japan: https://3dtotal.jp/ — キャラクタースカルプト、造形、材質、リトポのチュートリアル探索
13. Good Smile Company: https://www.goodsmile.com/ — フィギュア原型・製品の造形観察（画像・モデルの転載や模倣はしない）
14. Unity Toon Shader documentation: https://docs.unity3d.com/ — NPRの技術参照。TWOの実描画環境への移植可否は別検証

**調査運用:** 参考資料は日付・URL・著者・ライセンス・技術の適用条件を記録。YouTube等の制作動画は公式発信元・実演・公開日を確認し、紹介記事だけで成功を断定しない。有料教材・API・モデルの購入・課金は事前承認が必要。

## 5. モルウェン次工程（既存PR #427で実施）

1. 正式 Layer 0 四方向画像と現在の原本SHA・寸法・ランドマークを確認。視覚同一性とバイト同一性を区別。
2. 旧顔のG2 FAIL原因（白い眼周囲・斜めの不自然さ・髪欠落）を記録済みとして、**旧顔の再修復ではなく新規ヘッドスカルプト**に移る。既存 `build_head_study.py` のリング断面方式は正式制作の基盤として反復しない。
3. まず新方式の実編集可能な頭部原本を作り、ニュートラルなクレイレンダーで正面・斜め・側面を比較。G2未合格ならリトポ・リグへ進めない。
4. 髪・顔・身体・衣装・装備をモジュール制作し、表情・接地・陰影を検証。正式採用・main統合・本番組込みは各QAと承認条件に従う。

**本書のmain収録は「研究知見の全AI共有」であり、モデル・素材の正式採用、PR #427全体のマージ、G1〜G4 PASSを意味しない。**
