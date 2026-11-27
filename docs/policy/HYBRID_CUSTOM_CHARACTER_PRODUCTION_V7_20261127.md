# High-end 3D character hybrid custom production v7.0 — director-approved 2026-11-27

Scope: all TWO 3D characters and all AI agents/automations (Claude, ChatGPT, Codex and others). Registered from the director's explicit v7.0 instruction delivered in a Claude session on 2026-11-27 (16:50 JST). This registration changes production method priority; it does not certify any runtime capability, grant credentials, adopt assets or change canon.

## Director correction — 2026-11-27

Director correction (2026-11-27): Morwen's production target is 6.25 heads nominal, range 6.2–6.3. This supersedes conflicting earlier 7.75 / 7.5–8 targets. W04 is a verified surface-proxy candidate, not an adopted or independently verified anatomical landmark ratio. Retain B01/B02 for comparison; remeasure the 6.25 work copy using neutral anatomical crown/chin/sole, excluding hair, hats and shoe heels. Preserve W99 hair and independent modules. Do not blindly reverse B02. Morwen only; all other requirements remain. [Decision](https://github.com/celticmusic-nagoya/the-windbound-oath/pull/427#issuecomment-7214642613). The originally registered v7 text is retained in merge commit 69411da7998260280561dff70b0c6c103490ba1f; only the conflicting head-count wording is corrected here.

## Precedence and relation to existing policy

- Latest explicit director instruction > this v7.0 > AGENTS.md v6.0 sections and registry > older scoped policies > historical evidence.
- **New-custom-first hybrid production supersedes** VRoid-only completion, preset-modification fixation and Blender-only fixation wherever they conflict (including `MORWEN_VROID_FIRST_AUTHORING_20261121.md` and the "Blender as principal environment" wording of `MORWEN_EARLY_BLENDER_TRANSFER_20261126.md`). Tool choice is per part (VRoid / Blender 5.3.0 / HairHarpy 2.0.0 / XWear / texture tools), by measured quality, editability, compatibility, rights and total effort.
- Unchanged and still mandatory: D0–D4 design maturity, G1–G4 PASS/FAIL/HOLD/BLOCKED/NOT_RUN, canon/protected originals, licensing, single writer, STOP_ACK/CAS/lease/fencing where the route requires them, no forced reclaim, no new spending, private/public boundary, formal-adoption approval, Morwen visual targets (6.25 heads nominal within 6.2–6.3, corrected 2026-11-27; Layer 0 hair shape, official clothed dark-violet hair colour).
- Claude is the current principal production agent; roles are not permanent. Any qualified AI may produce, implement, recover and QA.

## Operative summary

1. Start each task from latest main AGENTS.md, SESSION_CONTINUITY_INDEX, POLICY_REGISTRY, PRODUCTION_RULES, relevant canon/blueprints, owning PR/HEAD/Actions/artifacts/originals/handoff.
2. Build face, hair, body, clothing, equipment, accessories and textures from new empty custom items / layers / meshes where practical. A colour change or minor preset tweak is never a finished part. VRoid base body mesh, skeleton, expressions, garment templates and UVs remain usable as a foundation.
3. Evaluate existing parts (design match, quality, editability, UV/rig compatibility, rights, rework vs new effort, connection quality) and decide reuse / partial rework / new / external-tool migration. Do not discard qualified parts or verified technical originals.
4. Morwen hair: legacy preset-derived hair (W42/W89/W90) is technical proof, comparison and restore only; never inherited into the finished hairstyle. Structure fringe/side/back/crown/nape/flyaways; fix length, root, curvature and guide envelope causally instead of repeating width-only edits.
5. Body shape is managed as a protected-rig .vroid plus measured parameter ledger; `.vroidcustomitem` body type carries skin texture only.
6. Unverified tool functions (HairHarpy, XWear Packager, etc.) are not assumed available; qualify with defined goal and exit condition. XWear use is not reversible to fully editable .vroid; integrate in Blender when XWear is disadvantageous.
7. Preserve editable originals (.vroid, .vroidcustomitem, .blend, .xwear, .vrm, .glb, layered textures, blueprints, scripts, QA, SHA-256 manifests) in existing private preservation routes; Actions artifacts expire. Record format-conversion losses.
8. Every checkpoint updates the owning PR / private handoff with the minimum handoff fields of section 17 below, with retrievable files — not text-only or chat-only links.
9. c/ok must end in actual production or a precise blocker plus an executed independent task. Two same-cause failures require causal change, tool switch or independent stage.

## Director-provided full text (authoritative wording)

### THE WINDBOUND OATH
### ハイエンド3Dキャラクター・ハイブリッド自律制作指示書 v7.0

2026年11月27日
対象：Claude／ChatGPT／Codex／その他制作AI

#### 1. 使命・最終目標

オリジナルファンタジーRPG『THE WINDBOUND OATH（TWO）』のアートディレクター、キャラクターモデラー、テクニカルアーティスト、衣装・装備制作担当、アニメーター、技術開発担当として行動する。

原神、NTE、アークナイツ：エンドフィールド、NIKKE等の商業ハイエンド作品を品質比較の基準とし、TWO独自のケルト・アイルランド系ファンタジーの美術表現を確立する。

既存作品の固有デザインを複製せず、正式設定・正式イラストを忠実に反映した、ゲーム内で実際に運用可能な高品質3Dキャラクターを完成させる。

技術実証や管理基盤の構築自体を目的とせず、完成成果物の制作を最優先する。

#### 2. 共通正本・制作規約

共通リポジトリ：

`celticmusic-nagoya/the-windbound-oath`

非公開正本・引継ぎリポジトリ：

`celticmusic-nagoya/the-windbound-oath-handoff`

毎タスク開始時に最新mainから以下を実際に取得する。

- AGENTS.md
- docs/production/SESSION_CONTINUITY_INDEX.md
- docs/policy/POLICY_REGISTRY.json
- docs/policy/PRODUCTION_RULES.json
- 関連する正式設定、精密設計図、制作仕様、非公開正典
- 担当PR、最新HEAD、Actions、Artifacts、制作原本、QA、引継ぎ記録

ユーザーの最新明示指示を最優先する。旧規約、過去の会話、旧担当、未完成の管理基盤を理由に承認済み制作を停滞させない。

本指示の新規カスタム優先・ハイブリッド制作方針は、旧来のVRoid完結主義、プリセット修正への固執、Blender固定主義より優先する。

#### 3. AI非依存・担当交代可能な制作体制

当面はClaudeを主制作担当とする。ただし、Claude・ChatGPT・Codexの担当を恒久的に固定しない。

すべてのAIが制作、設計、実装、技術調査、障害復旧、QAを実行できるものとし、利用制限、実行環境、得意分野、制作効率に応じて担当を切り替える。

特定AIの会話履歴だけに重要な情報を残してはならない。

制作途中でも、別のAIが最新原本と引継ぎ記録から直ちに作業を再開できる状態を維持する。

同一原本への競合書込みは禁止するが、独立した顔・髪型・衣装・装備・テクスチャ等の制作は並行可能とする。

利用制限発生時は、実行中ジョブ、保存済みcheckpoint、所有権、停止証跡を確認し、安全に担当を移管する。

STOP_ACK、CAS、lease、fencing等の既存保護方式が必要な経路では必ず遵守する。自動移管が未資格の場合は隔離コピーによる作業や独立工程を進め、無断で強制奪取しない。

#### 4. 自律制作・実行指示

- `c`：実制作・実装・改善・QAを行い、次の実行可能な工程へ進む。
- `ok`：直前の承認対象を実行する。
- `qa`：独立品質検証。
- `sync`：最新正本・制作状況の同期。
- `status`：実証済みの進捗報告。

c・okに対して、計画、確認、説明、報告だけで終了してはならない。

承認済みの通常制作、隔離コピー編集、非破壊修正、検証、保存、再読込、既存環境での実行を自律的に進める。

正式採用、正本置換、破壊的削除、新規公開、追加課金、権限拡張、強制的な所有権奪取は別途明示承認を要する。

通常の承認済みコード・資料変更は、適切なQA後、現行規約に従ってmainへ統合する。

#### 5. 新規カスタム制作を基本とする

顔・髪型・身体・衣装・装備・アクセサリー・テクスチャは、可能な限り空のカスタムアイテム、新規レイヤー、新規メッシュから制作する。

既存プリセットの色変更や軽微な形状変更だけで完成品としない。

ただし、ゼロから作ること自体を目的としない。既存制作済みパーツについて以下を評価する。

- 正式デザインとの一致度
- 造形・材質品質
- 編集可能性と再現性
- UV・リグ・変形の互換性
- ライセンス・来歴
- 修正工数と新規制作工数
- 他パーツとの接続品質

評価結果に基づき、再利用、部分改修、新規制作、外部ツールへの移行を自律判断する。

既存の高品質なパーツや技術実証済み原本を不必要に廃棄しない。

VRoidの基礎人体メッシュ、骨格、表情機能、衣装型紙、UV等は制作基盤として利用してよい。空カスタムとは、利用可能な制作基盤まで破壊することではない。

#### 6. ハイブリッド制作方式

VRoidだけで全パーツを完成させることに固執しない。部位ごとに最適なツールを選択する。

##### VRoid Studio

人体基盤、顔パラメーター、表情、髪の自由造形、肌・目・衣装テクスチャ、カスタムアイテム制作を担当する。

顔パーツ、髪型、衣装等は可能な限り新規カスタムから開始する。標準機能の限界を確認し、無理な再現を続けない。

体型は肌テクスチャのカスタムアイテムと、身体形状を保持する.vroid原本・パラメーター台帳を分けて管理する。

##### Blender

VRoidで十分な精度を得られない顔、耳、身体形状、毛束、衣装、立体装飾、装備品を制作する。

スカルプト、精密モデリング、リトポロジー、UV、スキニング、シェイプキー、材質、物理挙動、レンダリング、ゲーム向け最適化に活用する。

現行の標準環境はBlender 5.3.0。既存規約に従い、5.2.4は必要時の復旧経路とする。

##### HairHarpy

VRoidで十分に再現できない複雑な毛束、曲線、立体的な髪の造形に使用を検討する。

HairHarpy v2.0.0の実行・入出力・Blender互換性を確認し、実証済みの操作範囲で採用する。

未検証の機能を利用可能と仮定しない。

##### XWear／XWear Packager

Blender等で制作した衣装・装備・アクセサリーを、対応する着せ替え環境へ取り込む経路として活用する。

必要に応じてUnity、XWear Packager等の公式対応環境を利用する。

素体との適合、ウェイト、ボーン、材質、貫通、保存・再読込、書出しを検証する。

XWear形式の利用と、元の.vroid形式への完全な編集可能状態での逆変換を混同しない。

XWearを経由することが品質や工数面で不利な場合は、Blender内で統合する。

##### その他

Krita、GIMP、その他のテクスチャ制作ツール、Cascadeur、Mesh2Motion等も、必要性・互換性・ライセンス・品質を確認して利用する。

無料または既契約の範囲を基本とし、未承認の追加課金を行わない。

#### 7. 正式資料・精密設計図

正式四面図、衣装設定画、人物設定、材質指定を最優先する。

制作前に関連部位を詳細分析し、D0〜D4に準拠した精密設計を行う。

必要に応じて以下を定義する。

- 正面・背面・左右側面・斜め方向の設計
- 頭身、シルエット、主要ランドマーク
- 部位ごとの寸法・比率・断面
- 頂点・面・曲線・輪郭の構造
- 毛束の根元、方向、湾曲、厚さ、毛先
- 衣装の型紙、重なり、縫い目、装飾
- 色、材質、UV、テクスチャ構成
- ボーン、ウェイト、可動範囲
- 許容誤差、計測不確かさ、接続条件

2D画像から見えない奥行きや内部構造を確定値として扱わない。推定値、未確定値、実測値を区別する。

生成AIによる補助設定画や実写風画像は、質感・構造検討用とし、正式資料を無断で置き換えない。

#### 8. 顔の制作

顔の輪郭、顎、頬、額、鼻、口、耳、目、眉、まつ毛を個別に設計・制作する。

可能な限り新規カスタムアイテムや独自テクスチャレイヤーを用いる。

目の形状、虹彩、瞳孔、白目、透明感、まつ毛、眉、肌の色調を精密に調整する。

VRoidのパラメーター限界を超える形状はBlenderで補正する。

正面だけでなく側面・斜めからの立体的な自然さと、正式イラストへの一致度を重視する。

瞬き、視線、口形、表情変化、口腔内、表情時の形状崩れも検証する。

#### 9. 髪型の制作

原則として空のカスタム髪型から個別の毛束を制作する。

モルウェンについて、旧プリセット由来の髪型は技術実証・比較・復元用途に限定し、完成髪型へ安易に継承しない。

前髪、側頭部、後頭部、頭頂部、襟足、浮き毛を構造的に分離する。

各毛束について、根元、曲線、断面、厚さ、重なり、毛先の収束、色、光沢を設計する。

板状の前髪、均一すぎる毛束、過剰な顔の遮蔽、不自然な頭皮露出、貫通を避ける。

VRoid自由描画、個別毛束編集、HairHarpy、Blender曲線・メッシュ等を適宜組み合わせる。

毛束数を先に固定せず、四方向のシルエットと美術品質から必要な構造を判断する。

毛束幅だけの微修正を繰り返さず、長さ、根元、曲率、ガイド包絡を含めて原因を修正する。

#### 10. 身体・体型制作

頭部、首、肩、胸郭、胴体、骨盤、腕、手、脚、足の比率と自然な人体構造を設計する。

モルウェンの現行正式目標は6.25頭身を基準とした6.2〜6.3頭身とする（2026-11-27 ディレクター訂正。旧7.75／7.5〜8指定に優先）。

頭身計測時は髪のボリューム、帽子、靴のヒールを除外した人体ランドマークを使用する。

単純な胴体・脚の引伸ばしではなく、全身バランスと関節位置を調整する。

基礎リグ、骨格、ウェイトを保護し、必要に応じてBlenderで形状補正を行う。

歩行、走行、座り、戦闘姿勢等における変形と衣装貫通も確認する。

#### 11. 衣装・装備制作

衣装を完成プリセットの流用だけで済ませない。

インナー、レッグウェア、上衣、外衣、ベルト、靴、手袋、立体装飾等を独立した構成として制作する。

新規カスタム型紙、独自UV・テクスチャ、Blenderによる立体造形、XWear等を組み合わせる。

既存制作済みの衣装型紙、レッグウェア、ガーター等は正式設計との適合を確認し、有用なら再利用する。

布の厚さ、縫製、折返し、刺繍、金属、革、留め具、重なり、身体との接続を精密に表現する。

眼鏡、装飾品、魔法具、武器、防具等も個別の編集可能なアセットとして制作する。

VRoidの機能限界を超える部分はBlenderで新規制作し、必要に応じてXWearで適合を確認する。

装備着脱、可動、身体・衣装との干渉、ゲーム側の装備仕様を考慮する。

#### 12. 材質・テクスチャ品質

セルルック・NPRと高精細な材質表現を融合させ、アニメ調の造形を維持する。

権利確認済みの写真素材、PBR素材、独自描画、プロシージャル材質を使用する。

必要な材質ではBase Color、Normal、Roughness、Metallic、AO、透過、発光等を適切に分離する。

Base Colorへの過剰な照明焼込みを避ける。

肌、髪、瞳、布、革、金属等の質感差を明確にする。

高解像度の制作原本を維持し、ゲーム向けテクスチャは実測した負荷に基づいて最適化する。

#### 13. 実行環境・制作技術

既存の成功済み実行環境を優先して再利用する。

現時点の確認済み経路：

- macOS GitHub Actions
- 署名・SHA確認済みVRoid Studio 2.16.0
- CoreGraphics／VisionによるGUI操作
- VRoid原本の編集・保存・再読込
- VRM 1.0書出し
- 非公開の成果物転送・保存
- Linux Blender 5.3.0
- VRM Add-on 4.10.5
- Blender原本の保存・再読込・レンダリング

VRoidからBlenderへの成功実行記録：

`45779704407`

参照資料：

`docs/production/VERIFIED_VROID_BLENDER_EXECUTION_AND_RECOVERY_20261126.md`

スマートフォンやブラウザのみでも制作継続できる既存経路を優先する。

AIのコネクター権限、GitHubの操作権限、実際のGUI実行能力は区別する。

必要な権限や機能がない場合は、既存の資格確認済み担当・実行経路へ引き継ぐ。権限不足を理由に全制作を停止しない。

XWear、HairHarpy等の未実証部分は、目的と終了条件を定めて実際に動作検証する。

#### 14. 連続制作・障害復旧

作業は可能な範囲で複数工程を連続実行する。

精密設計、実制作、計測、比較、補正、再計測、保存、再読込、QAを一連の制作工程として扱う。

単一のパラメーター変更やスクリーンショット撮影だけを理由に、制作を毎回終了しない。

同一原因で2回失敗した場合は、原因分析、操作方式変更、別ツールへの移行、独立工程への切替を実施する。

不明なGUI状態では無条件クリックを行わない。対象ラベル、操作領域、選択状態、画面SHA等を確認する。

同一入力・設定による成功済みレンダーや実証を不必要に繰り返さない。

失敗履歴も保存し、別AIが同じ失敗を繰り返さないようにする。

#### 15. 品質ゲート

設計成熟度D0〜D4と、成果物品質G1〜G4を分けて管理する。

**G1：正式設定・設計・来歴**

正式資料との整合、設計根拠、利用権、原本SHAを確認する。

**G2：美術品質**

造形、シルエット、顔の再現性、毛束、人体比率、衣装、材質、全方向の外観を評価する。

**G3：技術品質**

メッシュ、UV、法線、リグ、ウェイト、表情、貫通、変形、テクスチャ、保存・再読込、書出しを検証する。

**G4：ゲーム統合品質**

実際のゲームエンジン、WebGL、Android、操作、描画負荷、アニメーション、既存機能との互換性を検証する。

各ゲートをPASS／FAIL／HOLD／BLOCKED／NOT_RUNで個別管理する。

自己評価、機械検査、独立QAを区別する。

Actions成功、保存成功、画像の見栄えだけで、全品質ゲートをPASSとしない。

#### 16. 成果物・原本保全

完成品だけでなく制作途中の編集可能原本を保全する。

該当するものを保存する。

- .vroid
- .vroidcustomitem
- .blend
- .xwear／対応する着せ替え原本
- .vrm
- .glb／.gltf
- 編集可能なテクスチャ・レイヤー原本
- 精密設計図・パラメーター台帳
- 制作スクリプト・実行設定
- 比較画像・レンダリング・QA記録
- SHA-256マニフェスト

形式変換によって失われる情報を記録する。VRMやGLBのみを編集原本の代替としない。

Actions Artifactsの期限切れを前提に、重要なcheckpointは既存の非公開保全経路へ保存し、実際の取得・SHA照合・復元を確認する。

正式原本、採用済みパーツ、過去の復元可能なcheckpointは無断で上書き・削除しない。

#### 17. AI間の完全引継ぎ

制作checkpointごとに、担当PRまたは適切な非公開共有場所へ引継ぎ記録を更新する。

最低限、以下を残す。

- 対象キャラクター・制作部位・工程ID
- 現在の担当者・担当PR・branch・HEAD
- 正式資料・設計図の参照先とSHA
- 使用ツール・バージョン・依存環境
- 入力原本・出力原本の取得先・SHA
- 再利用パーツ・新規制作パーツ・選定理由
- 実施済み操作と再現手順
- Actions run／job／artifact ID
- Artifact有効期限・長期保全状況
- G1〜G4・D0〜D4の状態
- 失敗履歴・解決方法・未解決障害
- 実行中ジョブ・所有権・停止状況
- 次に実行する具体的な作業
- 復元方法・ロールバック条件

引継ぎ先が実ファイルを取得できることを確認する。文章だけ、ファイル名だけ、別チャット内のリンクだけで引継ぎ完了としない。

担当交代時に既に完了した制作や技術実証を最初からやり直さない。

利用制限が解除された旧担当者も、現在の担当・所有権を確認せず再開してはならない。

#### 18. モルウェン制作の開始位置

担当PR：#427

2026年11月27日時点の既存証跡：

- W89：Hair39の幅編集・保存・再読込成功
- W90：Hair40の幅編集・保存・再読込、制御点モード確認成功
- W92：正式四面図に基づく新規毛束設計
- W93：空カスタム髪型・身体・衣装の独立制作検証

W90までは復元・比較・技術実証用として保護する。旧プリセット由来の髪型を完成品としない。

W93の実行結果、保存原本、最新担当PRを確認し、未完了部分から再開する。起動済みの同一作業を重複実行しない。

正式目標：

- 頭身：6.25基準（6.2〜6.3）
- 顔：正式デザインへの精密な一致
- 髪型：正式Layer 0四面図
- 髪色：正式衣装付きデザインの暗い紫系
- 衣装・装備：最新正式設定

顔・髪型・身体・衣装・装備を独立管理し、必要に応じてVRoid、Blender、HairHarpy、XWearを組み合わせる。

#### 19. 継続的な技術研究

3dnchu、公式技術資料、専門家による制作解説、ハイエンドゲーム、VTuber、フィギュア、アニメーション制作等から有益な技術を継続収集する。

新技術は実用性、品質向上、商用利用条件、再現性、互換性、総工数を評価して導入する。

調査やツール導入を繰り返すだけで、実制作を停滞させない。

#### 20. 最終原則

最優先事項は、高品質なTWOキャラクターを完成させることである。

使用するAI、ツール、制作方式は目的達成のための手段であり、固定しない。

制作済みの有用な成果物は最大限活用し、必要なら新規制作へ切り替える。

常に別AIへ引き継げる状態を維持する。

完成品質、正本整合性、再現性、安全性、総開発工数の最適化を図り、承認済みの制作を自律的に進める。

未実行の作業を完了と報告してはならない。
