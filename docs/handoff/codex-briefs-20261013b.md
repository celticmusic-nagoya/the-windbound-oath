# Codex 作業指示(第2弾) 2026-10-13
前提: `AGENTS.md` と `docs/handoff/codex-standing-orders.md` に従う。ブランチは各 `work/codex-<topic>`。完了/停止時は standing-orders §4/§5 の形式で報告。Claude側は同時に「接触判定のレベル対応(js/moss-forest-runtime.js 他)」を実装するため、該当ファイルは触らない。

## L: マップ別高さ計画書
- 入力: `docs/qa/map-survey-20261013.md`, `docs/qa/field-height-proto/phase1-report.md`, `js/field/field-height.js`, `data/maps/dev_height_proto.json`。
- 成果: `docs/design/height-plan-per-map.md`。優先順(崖/夕日の丘→ダンヴァル砦→モスA1→A2→A3→リルデ→他)に、マップ毎に ①高低差の候補箇所 ②必要なコネクタ(階段/坂/梯子) ③影響する接触物(NPC/敵/宝箱/イベント/出入口) ④リスク(性能・スポーン・既存テスト) ⑤必要アセット を表で。実装はしない。
- 禁止: データ/コードの変更、メインマップでの高さ有効化。

## M: 祭壇ページの短縮案(縦画面3行ページ)
- 対象: `index.html` の `altarLines` のうち縦画面で3行になる12/30/33ページ(ページ番号は tests/moss/m18 のログ参照)。
- 成果: `docs/handoff/altar-shorten-proposal.md` に現文・短縮案(各2行/約60全角以内)・意図の保持確認。コード変更なし。
- 不変: 誓いの台詞「……もう、目の前で誰かを失うのは嫌だ。」逐語、複数話者の改行ルール、イベント順序。

## N: 風の舞 数値比較シミュレーション
- 入力: `docs/handoff/wind-dance-proposal-20261013.md`, `js/data/support-magic-data.js`, 戦闘ダメージ/命中式(該当コード)。
- 成果: `docs/handoff/wind-dance-sim.md` と再現スクリプト `tools/sim/wind_dance_sim.py`(保守/標準/強の3案で、モス森ボス戦・レイダー戦の被弾率/被ダメ期待値/MP消費効率を比較)。
- 禁止: ゲームコードへの数値反映、`proposal`の確定。

## O: 全テスト一括実行スクリプト
- 成果: `tools/qa/run_all.sh`(直列・サーバ自前起動停止・`^FAIL `/`^FAILS [1-9]` grep・exit判定・結果表を `docs/qa/` に出力・既知失敗m13/m4_e2eを「main既存」表記)。
- 検証: 実際に全実行して結果表を添付。

## P: 剣付きエイダン歩行素材の受入検品
- 成果: `tools/field/check_aidan_walk_assets.py`(18フレームの枚数/サイズ/透過/足元基準線/接地位置のズレ/左右対称性を検査し合否表を出力)と `docs/art/aidan_walk_acceptance.md`。素材未着の間はダミーでテスト。
- 禁止: 採用済み素材の差し替え。

## Q: rilde_in_house_02 default_spawn_blocked
- 調査して原因と修正案を `docs/qa/rilde-house02-spawn.md` に。データ修正が小さく安全なら `work/codex-q` で修正+テストまで可(要報告)。
