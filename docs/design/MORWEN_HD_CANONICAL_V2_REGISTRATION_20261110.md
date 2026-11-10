# MORWEN HD 正本 v2 — 登録記録（2026-11-10）

STATUS: REGISTERED_ON_DRAFT_BRANCH ／ 本番（index.html・フィールド・戦闘・SAVE）は未接続 ／ ディレクターの視覚確認とAndroid実機確認は未実施（NOT_RUN）

- 受け取ったファイル：`MORWEN_CANONICAL_V2_LEFT_REPLACED_NORMALIZED_20261110.zip`（ユーザー添付）
- 登録先：`assets/official/characters/morwen/hd-v2/`
- 参照の設定：`data/morwen-hd-canonical-v2.json`（正）、`js/field/morwen-hd-canonical.js`（読み取り専用。index.htmlからは読み込まない）
- 確認用の画面：`dev/morwen-hd-v2-preview/`（DEV専用・noindex）
- 技術QA：`scripts/qa_morwen_hd_v2.py`、`tests/field/morwen_hd_canonical.test.js`
- QA報告：`docs/qa/MORWEN_HD_CANONICAL_V2_QA_20261110.md`

## 方針
- 最新のドット絵の左向き（`originals/pixel/left.png`、SHA-256 `5d0608bf2d60708325b0cdbb0a75a160e7153365cb402d5b33183c608c7eccf8`）を、左向きの唯一の正本とする。
- 旧左向き（MORWEN-3Vの左 `d858c428…`、PR #219の左候補）は参照対象から外す。ファイルと履歴は削除せず残す。
- 原本9点はバイト単位で保存する。表示用の4点（1200×1600、足元アンカー(600,1540)）は派生物で、マスターではない。
- 74I/75/76/77のちびキャラ歩行候補とは混ぜない。

## 登録結果（ZIP内のMANIFEST.jsonで照合し、SHA-256は13/13一致）
| ファイル | SHA-256 | 結果 | 登録先 |
|---|---|---|---|
| originals/pixel/front.png | d6fe876b…2c2b5a | 新規登録 | hd-v2/originals/pixel/front.png |
| originals/pixel/left.png（左の新正本） | 5d0608bf…7eccf8 | 新規登録 | hd-v2/originals/pixel/left.png |
| originals/pixel/right.png | f2a485d2…c060c7 | 新規登録 | hd-v2/originals/pixel/right.png |
| originals/pixel/back.png | 64bc5cbe…91e03f | 新規登録 | hd-v2/originals/pixel/back.png |
| originals/real/front.png | f9a0272c…1d13ec | 新規登録 | hd-v2/originals/real/front.png |
| originals/real/left.png | a48ab1bc…645279 | 新規登録 | hd-v2/originals/real/left.png |
| originals/real/right.png | b435dde0…f50850 | 新規登録 ※1 | hd-v2/originals/real/right.png |
| originals/real/back.png | 66bc519d…dad8ab | 新規登録 ※1 | hd-v2/originals/real/back.png |
| originals/real/portrait.webp | 141a6955…74581b | **登録済み（再登録なし）** | 既存の `web/companions/morwen.webp` |
| display/pixel/front_1200x1600.png | a1cec16d…45ac9c | 新規登録 | hd-v2/display/pixel/ |
| display/pixel/left_1200x1600.png | e0fe4050…a8d7e7 | 新規登録 | hd-v2/display/pixel/ |
| display/pixel/right_1200x1600.png | 531c4ee0…d68144 | 新規登録 | hd-v2/display/pixel/ |
| display/pixel/back_1200x1600.png | 047fb26b…db7f64 | 新規登録 | hd-v2/display/pixel/ |

※1 3Vの右（`7eeff76a…`）・背面（`9cf2f274…`）とは、αが完全に一致し、乗算済みの色の差も1/255未満で、見た目は同一。ただしバイトが異なる（SHA-256が違う）ため、指示どおり別ファイルとして登録した。

照合の範囲：ゲーム本体のmain、公式サイトのmain、両リポジトリのMorwen/companions系のブランチ（ゲーム11本・サイト11本）。SHA-256が一致したのはportrait.webpのみだった。

## 表示用派生4点の確認結果（要判断）
- 4点とも、MANIFESTのbbox・倍率・貼り付け位置から原本を最近傍法で処理すると、完全に一致する画像が再現できた。
- 接地行はy=1539（アンカーの1px上）で、4方向とも揃っている。
- **左右の位置**：派生4点は「帽子を含む外接矩形」を中央に置いているため、ブーツの中心は前611.5／左499／右712.5／背面600.5で、左右の向きで約100px ずれる。画像は加工せず、計測した補正値 `anchor_dx` をデータに記録した（プレビューで補正のオン・オフを切り替えられる）。
- **縮尺**：目の高さは前330／左290／右368（目視計測、±8px）。左と右で約6〜7%の大きさの差がある。
- **α値**：原本は体の部分のαがおおむね253（約1%透けている）。原本は変更していない。

## 次の工程
MORWEN-HD-WALK-01の左向き6コマ：`data/sprite-rig/morwen_hd_left_walk6_v2_recheck.json`、`docs/design/morwen-hd-walk/MORWEN_HD_WALK_01_V2_RECHECK.md`
