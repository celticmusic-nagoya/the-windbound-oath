# Production-First v5 規約移植台帳

基点は main `118daf552f39b963362d98d4709304bad4dcd5b8` と PR #501 の開始時 HEAD `2c18a35de1682f447c3be7d02512bf1e7828402d`。正本に依存する制作実績は個別に確認する。

以下は本文単位の対応表。各原文の全条件は SHA-256 付きの `PRODUCTION_FIRST_V5_SOURCES.json` と現行 registry に保持する。対応表中の個別 QA や証跡レビューは自動判定への移植残であり、単体テストは実運用の資格や独立承認を付与しない。

| 移植元 | 条件・適用範囲 | 移植先・検証方法 |
| --- | --- | --- |
| QUALIFIED_SHARED_ENGINES_V45 | 既存所有者の可逆範囲。短時間 native・隔離補正・復元に限定。長時間、deadline 復旧、自動引継ぎ、未資格 write は保留。各環境の署名・版・ライセンス・操作資格を確認 | Production OS / session controller・fenced session 回帰。実環境資格と承認の真正性は証跡レビュー |
| AUTONOMOUS_AUTHORITY_AND_SAFE_HANDOFF_V5 | c/ok の可逆限定。競合時は全 writer 停止確認、STOP_ACK、有効な解放または資格付き期限切れ、CAS 新 fence、復元、独立 QA。強制回収・不可逆操作は別承認 | Production OS / readiness・lease・checkpoint 回帰。STOP_ACK 等の真正性は所有者証跡と照合 |
| TWO_PRODUCTION_OS_V1 | 全工程。正本・承認優先順位、所有権、単一 writer、可逆作業、設計先行、G1–G4、成果物と検証、15 施策の段階展開 | Production OS / dispatch・controller、Blueprint Engine / target・residual 回帰。採用、資産別 QA、運用施策は証跡レビュー |
| CAUSAL_RETRY_AND_METHOD_SWITCH_V3 | 同因二回は再評価。固定打切りや同一失敗リプレイ禁止。仮説・予算・台帳・証跡を保持。独立工程を継続 | Production OS / ledger・classifier の回帰。構造的な改善仮説は証跡レビュー |
| CONTINUOUS_3D_AUTHORING_AND_WORLD_EXPANSION | native 連続制作、補正、チェックポイント、区画単位の独立進行、座標・接続・シーン・歩行 QA | Production OS / controller、Blueprint Engine / geometry・measurement。実シーンと歩行は個別 QA |
| ART_DIRECTED_HYBRID_WORLD_PRODUCTION_V2 | 世界・エリア。意図・実寸・地形・建物・自然物の統合、手作業と手続き生成、見た目と衝突・経路・性能 | Blueprint Engine / geometry・bounds。地理・画作り・ランタイムは個別 QA |
| HIGH_END_3D_TECHNOLOGY_REASSESSMENT_AND_PRODUCTION_PIPELINE | キャラ・世界の手法比較、出典・ライセンス、形状・マテリアル・リグ・検証、採用前の独立 QA | Blueprint Engine / source・target、Production OS / eligibility。技術選定と権利は証跡レビュー |
| MORWEN_BLUEPRINT_FIRST_BASE_SELECTION | Layer 0 から計測し、候補を同じ尺度で比較。VRoid、sculpt、ライセンス済みベースの選定と失格条件 | Blueprint Engine / Morwen cases・residual。候補間の視覚比較と採用は個別 QA |
| MORWEN_VISUAL_EQUIVALENCE_REFERENCE | 四面図、実出典・実 SHA、等価性を個別に確認。代替参照で正本ハッシュを代用しない | Blueprint Engine / source・Morwen Layer 0。画像と由来は独立レビュー |
| HIGH_END_3D_CHARACTER_AND_WORLD_PRODUCTION_V1_1 | キャラと世界の品質・設計、仮座標、現行ゲーム保持、QA、停止・再評価 | Blueprint Engine / geometry、Production OS / Retry v3。既存ゲームと資産別 QA |
| ACTIVE_PRODUCTION_DIRECTIVES | 対象資産の制作順序、原典・画像計測・版・保護・運用。共有承認を各工程に適用 | Production OS / stage 契約、Blueprint Engine / 測定。対象固有条件は原文と現行所有 PR を照合 |
| TOKEN_EFFICIENCY_POLICY_V1 | 同一 SHA の再利用、限定取得、必要な QA・承認を維持してバッチ化、実差分の報告 | Production OS / artifact reuse、dispatch 回帰。取得量と報告はレビュー |
| MORWEN_VROID_FIRST_AUTHORING | VRoid ネイティブ到達点まで、その後 VRM/Blender。髪は資格済み HairHarpy を優先。早期切替は director 承認 | Blueprint Engine / Morwen target。工程順序、ツール資格、承認は所有 PR で確認 |
| MULTI_STAGE_PRODUCTION_BATCHES | キャラ・マップ等の納品単位、準備済み工程の連結、viewport 修正、選択 QA、保存復元、実効上限と予備時間、ライブレビューの条件 | Production OS / session plan・factory、Blueprint Engine / target・correction。実運用は個別 QA |
| BLENDER_530_UNIFICATION | 新規 5.3.0、既存再現・復旧 5.2.4、workflow/asset ごとに移行検証 | Production OS / validate_blender_runtime。native 再現は個別 QA |
| CONTINUITY_AND_PRODUCTION_READINESS | 最新 main・所有 PR・全イベント・期限・実 native 復元、陳腐候補拒否、影響工程のみ停止 | Production OS / shared production readiness・dispatch／Actions snapshot 回帰 |
| CROSS_AGENT_OWNERSHIP_AND_QUOTA_FALLBACK | 能力と可用性で選定、同一資産競合の防止、quota 時の証跡付き引継ぎ、不可逆承認 | Production OS / lease・fenced checkpoint。引継ぎは現行 v5 と所有者証跡を照合 |
| MANDATORY_PREWORK_RULE_RECONCILIATION | 変更前に現行規約・canon・所有者・D0–D4/G1–G4・前提と証跡を結合。別工程継続 | Production OS / 今回追加の authority 判定、既存 readiness。Blueprint Engine / target。全 receipt 自動強制は未資格 |
| CROSS_AI_PROGRESS_AND_MAIN_SYNC | 実質差分を所有 PR、main index は承認経路。最新 HEAD・証跡・変更時再同期。重複監視禁止 | Production OS / Actions snapshot と今回追加の authority 判定。PR と index の更新は証跡レビュー |

## 参照競合

- 高品質 3D v1.1 の Retry v2 参照を現行 v3 の因果再評価に修正した。
- Field RO の旧デザイン参照を履歴出典として明示した。計画状態、既存参照素材、保留 PR を保持する。
- 引継ぎの競合は v5 の停止・解放・CAS・復元・独立 QA を優先する。60–120 分は計画の目安。実行時間枠と native 長時間経路の資格は別条件。
- D0–D4 は設計成立、G1–G4 は制作 QA。緑 CI や短時間の隔離実証では代替しない。
- クロスドメイン設計完了、精密計測、共有配布、地理 canon などの適用条件は現行 AGENTS と関連規約から引き続き解決する。

## 独立 QA

`python3 tools/production_qa/shared_production_readiness.py` で 19 件の台帳、原文バイト、現行・履歴の分類を検査する。`--extract` は検証済み原文を SHA-256 と行番号付きで全件出力する。任意の参照パスを引数に渡すと、そのパスが registry に基づく実行根拠となるかも検査する。Registry の明示的な active 一覧と一致する正規パスのみ許可する。既存の dispatch、writer lease、Blueprint Engine の経路は別途回帰する。

移植台帳の網羅性レビュー、適用範囲ごとの証跡確認と runtime 資格確認が残る。現行 19 規約の正式失効と main への統合には別途承認が必要。
