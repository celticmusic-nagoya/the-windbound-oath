# Codex 向け作業指示書（並行開発用）

前提: まず `docs/handoff/HANDOFF.md` と `AGENTS.md` §0 / `docs/lore/README.md`（公式設定資料集 v5.0 の所在と参照ルール）を読むこと。v5.0 全文は非公開の引継ぎリポジトリ管理で、読めない場合は推測で補わない。旧 `docs/story/WORLD_STORY_BIBLE_v1.1.txt` は旧版（履歴参照のみ・正典ではない）。報告は日本語・簡潔に。

## 0. 衝突を避ける分担（ファイル所有）
| 領域 | 主担当 | 備考 |
|---|---|---|
| `tools/moss/build_town_maps.py`, `build_rilde_village.py`, `js/field/moss-forest-story.js`, `index.html` のストーリー部, `talk-data-*.js` | Claude | Codex が触る必要が出たら先に相談（ブランチ別でも conflict しやすい） |
| 新規ツール/新規ファイル（例 `tools/moss/build_capital_districts.py`, `js/field/<新機能>.js`）, 画像/音声素材, 戦闘まわり(`js/battle-*.js`) | Codex | 既存ファイルへの追記は最小限、`index.html` は `<script>` 行と `?v=` のみ |
| `data/maps/*.json` | 生成物 | **手で編集しない**。生成元ツールを直す。既存生成物を再生成して差分が出たら理由を報告 |
- ブランチ: `work/codex-<topic>`。main へのマージは作者承認後（Claude は ff-merge を許可されているが Codex 分は作者確認）。
- 共通の完了条件: 該当テスト＋既存回帰が通る / `check_assets.py` が 0 error / `?v=` 更新 / 作者向けに「変更点・未実装・テスト結果」を報告。
- テスト実行: `python3 -m http.server 8765 &` → `python3 tests/moss/<name>.py`（終了コードで判定）。

---
## 依頼A: 仲間のフィールド/戦闘スプライト（リアム・ブラム）
- 目的: 現在の仮チビ絵（`tools/moss/make_npcs.py` の `liam` / `dwarf_drunk`）を、エイダン/フィオナ（`tools/field/install_hero_frames.py`, `docs/art/walk_delivery_brief_2.md`）と同等のフィールド歩行（4方向×待機+歩行）に置き換える素材パイプライン整備。
- 仕様: リアム=バイブル35（アッシュブロンド/ウルフヘア/額を出す/赤い柄入りバンダナ/ゴーグル/赤黒レザー+アンティークゴールド/コンパス・ロープ・地図/ショートソード+弓）。ブラム=バイブル39（ドワーフ・鍛冶師・タンク、戦闘用ヘルメット、酒場では「酔っ払いのドワーフ」）。**明るい黄色髪・短髪・垂れ前髪は禁止**。
- 成果物: 画像 + 取り込みツール + manifest ルール + 単体テスト。NPC スロット(`npc_slot_liam`)は互換で残す。
- 受け入れ: DEV メニュー M8（酒場）で見た目が差し替わる / m11_road_tavern, m8_town_maps が通る。

## 依頼B: リアムを戦闘パーティに入れる
- 目的: `liam_joined` 後、戦闘（`js/battle-party-layout.js` ほか）に参加。役割=盗賊/探索（SPD高, `CHARACTER_DB.liam`）。武器=ショートソード+弓。
- スコープ: パーティ編成(`PartyManager.active`, maxActive 4)・戦闘レイアウト・コマンド(攻撃/スキル/アイテム)・簡易スキル1〜2個（バイブル記載の探索系は後回し可）。戦闘シーンは固定シーンなので既存の呼び出しを壊さない。
- 受け入れ: ゴブリン戦などの既存戦闘が従来どおり動く（`tests/battle/*`, `m55_mobile.py`, `m4_e2e.py`）/ リアム参加時の新テスト。

## 依頼C: 王都の追加地区マップ（新ツールで）
- 目的: バイブル12〜、**騎士団地区・大聖堂地区・魔法学術地区（王立魔法研究院）・職人地区（ブラムの工房 `BRAM'S FORGE`）・裏路地**のマップ生成。
- 方法: 新規 `tools/moss/build_capital_districts.py` を作り、`build_town_maps.py` の `Map` クラスを import して再利用（**同ファイルは編集しない**。必要なら `Map` を別モジュールに切り出す提案を先に）。出力は `data/maps/royal_*.json`、到達性検証つき。
- 接続: 現在 TBD の出口 — 市場東(`tr_r1_to_craft`→職人)、広場東(`tr_r2_to_east`→騎士団/大聖堂/学術)、広場北(`tr_r2_castle_gate`→王城) — の `toMap/toSpawn` 差し替えは Claude に依頼（`build_town_maps.py` 側）。Codex は受け側の spawn 名と ID を報告書に明記。
- 見た目: 白〜淡灰の石造/青緑屋根/アンティークゴールド（`make_town_art.py` の `STW/ROOFT/GOLD`）。大聖堂=「英雄が魔王を封印する姿」の壁画/ステンドグラス（バイブル）。職人地区は工房兼自宅（店舗/受付・鍛冶場・倉庫・居住スペース）。
- 受け入れ: `m8_town_maps` 相当の遷移テスト追加 / 到達性 OK / DEV に `map:` 入口（`js/prologue-dev.js` と `index.html` の entries）。

## 依頼D: 地下エリア（第七封鎖区画）とモルウェン導線の下地
- 目的: バイブル56の「魔法学術地区→研究院→第七封鎖区画→地下ボス→魔王の紋章の矛盾→モルウェン加入」に使う **旧水路/地下墓所/古代都市遺構/第七封鎖区画** のマップ群と地下ボス戦の枠（戦闘シーンは仮敵で可）。
- 注意: ストーリー台詞・フラグ接続は Claude 側（`talk-data-*`, `moss-forest-story.js`）。Codex はマップ・仮戦闘・出入口・フラグ名の提案（命名: `seventh_*`）まで。
- 受け入れ: DEV から入れる/戻れる、天候・暗めの時間帯、遷移テスト。

## 依頼E: 音（BGM/SE）
- 目的: 手続き生成 BGM（`js/field/field-bgm.js` の `PROFILES`）を拡張し、砦(山岳・夕暮れ)/街道/王都昼・夜・祭(Reel/Jig 風・速いアレンジ)/ギルド酒場/地下 の曲を追加。バイブルの BGM 方針に従う（CAERDYN DAY→NIGHT は同主旋律をテンポダウン）。
- 方法: `PROFILES[id]` を追加、マップの `audio.bgm.id` は生成ツール側（Claude）で切替。録音ファイル方式に変える場合は `FieldBgm` 内に loader を足し、設定タブのミュート(`windbound.bgm`)を維持。
- 受け入れ: ミュート/初回ジェスチャ後再生、マップ間のフェード、`m10_rilde.py` が通る。

## 依頼F: 時間帯・宿屋・周年祭の基盤
- 目的: ① 宿屋の「朝/昼/夕/夜まで休む」選択（`FieldTimeOfDay.set`、`restAtBed` 周辺、`party-rest`）② 王都の時間帯バリエーション（昼夜で NPC・ライト・BGM が変わる）③ 周年祭状態（flag `caerdyn_festival`）で広場が祭り会場に変わる装飾レイヤ。
- 注意: 物語トリガー（祭りの開始条件）は Claude 側。Codex は「flag で切り替わる」仕組みと素材まで。
- 受け入れ: 時間帯切替が保存/復帰で崩れない、`m9_env.py` が通る。

## 依頼G: 品質・基盤（優先度高め、短期）
1. **120Hz 端末の移動速度**: 移動量を dt 基準に（`field-movement.js`, `moss-forest-runtime.js`）。`tests/moss/m55_hz.py` を拡張。
2. **`m6_quest.py` の恒常失敗**の原因調査と修正（変更前から失敗。テスト側かゲーム側かを切り分けて報告）。
3. **全回帰ランナー**: `tests/run_all.sh`（サーバ起動→全テスト→終了コード一覧→停止）。
4. 仮絵の棚卸し: `check_assets.py` の standin/placeholder 一覧を `docs/art/` に表で出力（差し替え優先度つき）。
- 受け入れ: 上記それぞれのテスト/ドキュメント。

## 依頼H: 仮絵の本番化（継続）
- 対象: 建物（`town_house_*`, `guild_front`, `inn_front`, `castle_front`, `caer_gate`, `keep_front`）・兵士/商人/町人 NPC・家具。作者の承認した画風（リルド村 Lind 画像のドット/イラスト調）に合わせる。
- 方法: PNG を作る → `img/field/moss/town/` に置き、manifest ルールを維持（アスペクトと足元中央アンカー、1ドット=2px）。`make_town_art.py` の生成は上書きされるので、**差し替えたものは `gen` を外す**/生成対象から外す。
- 受け入れ: `check_assets.py` 0 error、実機でのサイズ感（エイダン身長 69px 基準）。

---
## 優先順位の提案
1. 依頼G（基盤・短期）→ 2. 依頼A+B（リアムを戦力化）→ 3. 依頼C（地区マップ）→ 4. 依頼D（地下・モルウェン）→ 5. 依頼E/F/H（継続）。
Claude 側は並行して: 台詞/フラグ/導線の接続、TBD 出口の接続、長老の本実装、襲撃の戦闘・目的の FieldTalk 化、バイブル整合の維持。

---
## 付録: 王都の未接続出口の接続手順（依頼C の受け側マップ確定後）
出口は `tools/moss/capital_exits.json` で管理（今は全て null = TBD のまま）。
| 出口ID | 場所 | 行き先（想定） | 戻りで使う spawn（既存） |
|---|---|---|---|
| `tr_r1_to_craft` | 市場の東端 | 職人地区（ブラムの工房側） | 市場 `from_craft` (4400,1500 左向き) |
| `tr_r2_to_east` | 広場の東端 | 騎士団/大聖堂/魔法学術地区への分岐 | 広場 `from_east` (3640,1700 左向き) |
| `tr_r2_castle_gate` | 広場北の王城門 | 王城（前庭/高台） | 広場 `from_castle` |
手順: Codex が受け側マップID・spawn名を共有 → Claude が json の null を `{"toMap": "...", "toSpawn": "..."}` に置換 → `python3 tools/moss/build_town_maps.py`（接続先の `data/maps/<id>.json` と spawn の存在を検証、無ければ exit 1）。受け側マップ側の「戻りドア」は Codex が上記の既存 spawn へ `toMap/toSpawn` を張る。
