# TWO｜マップ開発チーム引き継ぎ（制作環境再構築／2026-11-18）

**状態: PREPARATION / NO-GO。新規マップ3D造形を再開しない。** 本書は既存正式設定を変更しない作業引き継ぎ。再開にはディレクターの明示承認が必要。詳細版はChatGPT Library `/THE_WINDBOUND_OATH/TWO_MAP_TEAM_HANDOFF_PRODUCTION_RESET_20261118.md`（他AIから自動閲覧可能とは限らない）。

## 1. 正式制作方式と対象
- 正式採用済み **Art-Directed Hybrid World Production** を維持。正式CG・世界設定を基準に、主要崖・岩盤・張り出し・亀裂はスカルプト／精密メッシュ。Heightfieldは緩斜面・農地・遠景など限定。Geometry Nodesは植生／小物配置。適法なスキャン・CC0・PBRはライセンス・構造・美術適合性を検証。
- 単一Heightfield、プリミティブ石積み反復、既に失敗した方式の無根拠な再試行を禁止。
- 最初の完成品質マスター候補は **風待ちの崖**。正式世界地図を実寸設計図として扱わない。橋・道路・港・崖の移動可能性は独立QA。
- 原神、NTE、アークナイツ：エンドフィールド、NIKKEは品質比較のみ。固有意匠は模倣しない。

## 2. チーム
- ディレクター: 正式採用・再開・削除・マージ・公開承認。
- ChatGPT: 正本、PR/ブランチ統制、技術選定、再開判定、独立QA。
- マップ制作担当（実際に利用可能なCodex等）: 実際の編集可能Blender原本、崖・建築・地形・植生・水・VFX、レンダリング。
- キャラクター制作担当: キャラクター側を独立所有。共通座標・縮尺・カメラ・接地・影・遮蔽を契約化。
- 独立美術QA（実際に利用可能なClaude等）: 形状・素材・CG適合性を判定。
- GitHub Actions: Blender実行、SHA、原本再オープン、構造QA、レンダリング、Artifacts。**CI成功はG2合格ではない**。
AIは実際に起動・成果物を検証するまで「稼働中」と報告しない。

## 3. PR増殖停止
- 2026-11-18 GitHub検索で未完了「LIND」関連PR **64件**（キーワード検索であり総数確定ではない）。未完了PR全体は少なくとも100件。
- 既存PRのHEAD、対象、所有者、原本、SHA、ライセンス、QA、Artifacts、依存関係、失敗履歴を棚卸し。**1対象・1工程・1担当につき原則アクティブ実装PR1本**。
- 新規ブランチは既存PRを検索し、再利用不能を証明できる場合のみ。ブランチ名変更・微調整で失敗回数をリセットしない。
- 関連PR: #421（CC0岩盤3方向候補、現時点G1 BLOCKED/G2 NOT_RUN）、#415（packed .blend候補）、#416（トポロジーガード）、#403（独立QA）、#365（地質・ライセンス）、#353（キャラ／マップ接続契約）。これらの実物・最新HEADを確認せず同種PRを新設しない。
- クローズ、削除、mainマージ、正式置換、公開は明示承認まで行わない。

## 4. 先に実行する安全な作業
1. mainの`AGENTS.md`、正式CG・世界設定・採用素材・原本SHA・失敗台帳を再照合。原本不明はG1 BLOCKED。
2. #421/#415等の実際の`.blend`、3方向PNG、PBR、ライセンス、Artifactsの所在と再オープン可否を検証。G2合格は独立レビューまで主張しない。
3. GitHub ActionsのBlenderバージョン固定、取得失敗、キャッシュ、タイムアウト、Artifact保存・ダウンロードを実証。無意味な再試行はしない。
4. 風待ちの崖の正式CGに対するシルエット、層理・亀裂、接地、風化、植生、水、夕景／星空、探索経路の評価項目を整理。
5. Blender制作マスターとWebGL/Android出力を分離。LOD、メモリ、ドローコール、ロード時間、Android実機の評価方法を定める。数値予算は未承認の推測値で固定しない。
6. PR #353等の共通座標・カメラ・縮尺・遮蔽・ライティング契約を確認。

## 5. 再開ゲート
A 正本CG／原本／SHA／ライセンス照合、B PR統制と担当確定、C Blenderによる実原本再オープン＋実レンダリング＋Artifacts取得、D 完成品質に向けた造形方式の実証、E 利用可能なAI間の実際の新規セッション引き継ぎ検証、F G1正本・G2美術・G3構造・G4 WebGL/Androidの独立QA基準、G ディレクターの再開承認。**未充足はNO-GO**。
- 同原因・同方式の失敗2回でその方式を停止し、因果的に異なる方式へ切り替える。独立工程まで止める必要はない。

## 6. 正本参照
- main: `docs/policy/HIGH_END_3D_CHARACTER_AND_WORLD_PRODUCTION_V1_1.md`
- main: `docs/policy/CAUSAL_RETRY_AND_METHOD_SWITCH_V2.md`
- 既存Draft PRブランチ: `docs/production/PRODUCTION_RESET_READINESS_GATE_20261118.md`
- リポジトリ: https://github.com/celticmusic-nagoya/the-windbound-oath
- PR #421 https://github.com/celticmusic-nagoya/the-windbound-oath/pull/421
- PR #415 https://github.com/celticmusic-nagoya/the-windbound-oath/pull/415
- PR #353 https://github.com/celticmusic-nagoya/the-windbound-oath/pull/353

報告は(1)対象ファイル・仕様・実装内容 (2)QAと未検証・デグレ (3)次工程・実行結果の3項目。未実行を完了扱いしない。
