# ASSET REGISTRY GUIDE（台帳の更新ルールと運用）

## 構成
| ファイル | 役割 |
|---|---|
| `ASSET_REGISTRY.json` | 機械用台帳（生成物）。アリーナ/将来のアセットビューアが参照 |
| `ASSET_REGISTRY.md` | 人間用台帳（生成物） |
| `ASSET_BACKLOG.md` | 未実装・未統合・未採用・修正待ち（生成物、優先度 P0〜P4） |
| `ASSET_CHANGELOG.md` | 納品・採用・修正・実装・main統合・差し戻しの履歴（**手で追記**） |
| `registry_overrides.json` | **人が確定した事実だけ**（採用・QA・Issue・handoff原本・原本SHA）。推測は書かない |
| `inventory_sources.json` | ブランチ/PR/Issue と「未マージブランチだけにある画像」のスナップショット（`snapshot_sources.py` で更新） |
| `reports/` | `audit_report.md` `refs_report.md` `unmerged_assets.md`（チェック結果） |

## 状態は独立して管理する（混同しない）
- 採用 `APPROVED / PENDING / REJECTED / REVISION_REQUIRED / UNKNOWN`（納品≠採用）
- 実装 `IMPLEMENTED / PARTIAL / REGISTERED_ONLY / NOT_IMPLEMENTED / UNKNOWN`（manifest登録≠実装検証済み）
- 統合 `MAIN / BRANCH_ONLY / SOURCE_ONLY / MISSING / UNKNOWN`（ブランチにある≠main）
- QA `PASS / FAIL / CONDITIONAL / NOT_RUN / UNVERIFIED`。Android は `android_status`（実機確認までは UNVERIFIED）。Codex QA と Claude側QAは `notes` に分けて書く。
- 不明は `UNKNOWN`。推測で埋めない。原本が見つからない素材は再生成せず `MISSING` で記録し再納品を依頼する。
- 未使用素材は原本保管/将来用の可能性があるため自動削除しない。

## 生成・更新手順
1. `python3 tools/assets/build_registry.py` — main の `img/` を走査（sha256・サイズ・コマ群・runtime参照）して JSON/MD/BACKLOG を再生成。
2. 採用・QA・Issue・原本SHAなど人が決めた事実は `registry_overrides.json` の `patches`（正規表現で一致するIDに適用）か `extra_assets`（handoff原本など走査対象外）へ追記。
3. 未マージブランチの素材が増減したら `python3 tools/assets/snapshot_sources.py` → 1 を再実行。
4. `python3 tools/assets/audit_registry.py` と `python3 tools/assets/check_asset_refs.py` が exit 0 であること。`report_unmerged_assets.py` で台帳未反映の未マージ素材が 0 であること。
5. `ASSET_CHANGELOG.md` に1行追記（日付・素材・事象・SHA・Issue/PR）。

## アセットPRのルール（更新漏れ検出）
- 画像の追加・差し替え・削除を含むPRは、同じPRで台帳を再生成してコミットする。
- 漏れは `build_registry.py --check`（台帳が古いと exit 1）と `audit_registry.py`（main上の未登録画像を error）が検出する。テスト `tests/system/asset_registry_audit.py` で実行できる。

## 素材が納品されたとき（毎回）
1. 原本を保存（`docs/art/delivered/<名前>/originals` または handoff `assets-originals/`）。原本は上書き・再生成しない。
2. SHA-256 を記録（`SHA256SUMS.txt` と `registry_overrides.json`）。
3. 台帳に登録し、採用状態を記録（ユーザーの採用判断が出るまで `PENDING` / `UNKNOWN`）。
4. 実装ブランチ・PR・Issue を関連付ける。
5. 実装後、runtime参照先（manifest / assets.js / マップ）を確認し台帳を再生成。
6. main統合後、統合SHAを `ASSET_CHANGELOG.md` に記録。
7. アリーナ「モーションテスト」（`?dev=1` → DEV ▶ → MONSTER ARENA）で再生確認し、Android確認結果を `android_status` に反映。**アリーナでの再生確認を戦闘アセットの標準受け入れ検証とする。**

## アリーナとの関係
再生の正本は `img/battle/motion-manifest.json`（本編 `BattleMotion`）。アリーナは台帳ではなく本編データから状態を計算して表示する。台帳は採用・実装・検証状況の管理用で、アリーナ専用の素材を重複管理しない。`ASSET_REGISTRY.json` の `arena_available` / `motion_gaps` は、アリーナの表示と食い違わないことを `audit_registry.py` の目視確認項目とする。
