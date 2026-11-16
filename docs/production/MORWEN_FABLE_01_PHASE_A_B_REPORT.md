# MORWEN-FABLE-01 — Phase A 監査 / Phase B 方式選定（2026-11-16）
Status: Phase A 完了 / Phase B 提案 / Phase C–E 未実行。詳細・ハッシュ・設定値は `MORWEN_FABLE_EVAL_REPORT.json`。

## Phase A 結果
- 候補 `.blend` SHA-256 一致（9bff525e…）。読み取り専用で検査、実行後も不変。
- 既存候補の可視メッシュは **VRoid β版 CC0 `base_female` 素体そのまま**（青緑の髪・紺の制服・ローファー・Tポーズ）。モルウェンの髪・帽子・マント・衣装・眼鏡・小物のジオメトリは存在しない。証跡: `assets/candidates/morwen-fable-eval-01/baseline_A/A_BASELINE_SHEET.png`
- シルエット頭身 6.57（髪・靴底込み）。目標 7.5–8 に未達。
- 承認済み3DターゲットPNG（7640822c…、`feature/morwen-reference-binary-01`）はバイト照合 PASS。ただし v5.61 シート（47d58…）と Layer 0 シート（7e122…）の実体は GitHub に無く、**どれが3DのG1正本かが未確定** → G1 BLOCKED。
- 承認PNG内の Layer 0 正面図は目測で約6.1頭身（±0.3、非校正）。7.5–8頭身目標と不一致。
- 軸: 候補は正面 +Y・キャラ左 −X、ボーンL/Rと一致（鏡像なし）。レジストリ（正面 −Y・左 +X）は同じ右手系のZ軸180°回転で矛盾ではない。実際の矛盾は `MORWEN_GARTER_RIGHT_ONLY_CANON.json`（character_right=+X かつ正面で画面右）にあり、承認PNG自体も正面=画面左／背面=なし／両側面=あり、と不整合。
- AGENTS.md §5「long dark hair」と 11/08 ロック（短いぱっつんボブ＋魔女帽子）が不整合。後者を採用。

## Phase B 方式比較
| 方式 | 判定 | 要点 |
|---|---|---|
| A 既存Blender＋Fable | 単独では不可 | 流用可はリグ骨格命名と表情キー一覧のみ。顔・髪・帽子・衣装・小物・材質・体型は作り直し。まぶた系は同系統2回失敗で既に停止済み |
| B TRELLIS.2 | 未実行 | MIT。約24GB VRAM必須、本セッションはGPUなし。ホスト版は承認画像の外部送信が必要 |
| B Hunyuan3D 2.1 | 未実行・要法務確認 | 独自ライセンス（EU/UK/韓国を地域除外）。全世界公開のGitHub Pagesと衝突の恐れ。VRAM 10/21/29GB |
| C Blender精密モジュラー | **中核として推奨** | 決定頭身のクアッド素体＋顔/髪/帽子/衣装/小物の独立モジュール、トゥーン＋輪郭、VRM互換リグ |

選定: **C を中核、A はリグ/表情テンプレートのみ、B は権利と送信承認後に参考形状として任意利用。**
注意: ヘッドレスのPythonスクリプトだけでは本リポジトリで有機的な顔造形が繰り返し停滞している。商業水準には対話的スカルプト/リトポ工程（アーティストまたはBlender GUIセッション）が現実的に必要。

## ゲート
G1 BLOCKED / G2 FAIL（ベースラインAの自己評価。独立美術QAは NOT_RUN）/ G3 PARTIAL / G4 NOT_RUN

## 承認・判断が必要な事項
1. 3DのG1正本はどの画像か（不足バイトの提供を含む）
2. 頭身: 7.5–8 を維持するか、承認シート（約6–6.5）に合わせるか
3. ガーター: 解剖学的右脚か、正面図の画面右か
4. 承認画像の外部生成サービスへの送信可否
5. 対話的スカルプト/リトポの担当

## 再実行
```
pip install bpy==5.3.0
python3 -I tools/character_blender/morwen_fable_eval_inspect_render.py -- <blend> <out_dir> --samples 16
python3 tools/character_blender/morwen_fable_eval_make_sheet.py <out_dir>
```
2回実行でピクセル完全一致を確認（PNGファイルSHAは埋め込みメタデータ差のみ）。
