# 家02のdefault_spawn_blocked（Q）

基準main88ae6c0、branch work/codex-q。STATUS: READY（小規模修正/検証、main未反映）。
要約: 入口(430,452)の足元22×10がstoolと重なる。ユーザーのQ小規模安全修正許可に従い、生成元で家02の入口だけ(430,472)へ変更。家具/出口/他室/物語/素材/高さは維持。

## 原因

cb_09はstool、矩形[430.4,436,19.2,14]。旧feet(430,452)の22×10 boxはX419..441/Y442..452で、椅子と約10.6×8px重なる。足元の点自体(430,452)は椅子の外なので、build_rilde_village.validateの点ベース検査は旧mapでもerrors=[]を返す。coarse gridだけの問題ではなく、実FieldCollision.compileMapでもblocked=trueを再現した。

runtime.enterのdefault spawn経路は宣言座標をそのまま使うため、正常位置を指定せずに入り、当たり判定内から始まる。修正は高さや椅子の削除で隠さず、1部屋の入口だけ移す。

## 変更ファイル

- tools/moss/build_rilde_village.py: Interiorにoptional sy、既定は従来のh−48−140。house02のみsy472。
- data/maps/rilde_in_house_02.json: 生成元のRoom.docから再生成。default/from_villageのY452→472、spawnに基づくev_arrivalのY332→352のみ。家具/衝突/出口/会話ゾーンは不変。
- 新規tests/field/house02_spawn.test.js: 実FieldCollisionで両spawnの22×10非衝突、出口直上の配置、2px刻みの出口経路、旧点の衝突（椅子保持）を検証。
- 本報告、QA logs/results、status/CLAIMS。

再生成前のhouse02は生成元とJSONが完全一致することを確認。その後の差分はspawnsとeventZones[0]のみ、残りの全top-level値/全eventZones[1:]一致。他の10室も生成元出力と既存JSONが一致。generator.mainは全mapとmanifestを書換えるため実行せず、rooms()からhouse02だけ生成した。採用済み素材/manifestは未編集。

新feetはX419..441/Y462..472で椅子下端450から12px空く。出口rectは[360,518,140,62]なので、入室直後に出口へ再接触せず、X430のまま出口へ歩ける。変更は20world px、歩行速度や保存形式を変更しない。

## 検証と分類

| 検証 | 変更前 | 変更後 |
|---|---|---|
| 新規Node foot collision regression | default overlapsで失敗（期待した再現） | 合格、旧pointは引続きblockedで家具保持 |
| generator validate（点ベース） | errors=[]（見逃し） | errors=[]。これだけで修正合格とは判断しない |
| generator/JSON一致 | 完全一致 | 対象spawn/arrival以外・他全室一致 |
| 実ブラウザ入室/村へ実歩行 | 未実施、Nodeで衝突再現 | (430,472)、blocked=false、height=null、村へ正常遷移、pageerror0 |
| m10_rilde | Oの旧main531で合格、今回同一88で変更前再実行は未実施 | 合格、全13Rilde map/全室の入室/会話/訓練/村の状態/console0 |

関連の変更前後比較は新規Node回帰で実施。追加browser/m10は現在の接触対応main88を基準にした変更後検証。Oの531全回帰を88の変更前結果として混同しない。

実行: `node tests/field/house02_spawn.test.js`、Python importlibでgenerator.rooms/doc比較、`PATH=/workspace/.cloud-setup/venv/bin:$PATH` の外部検証wrapper。各browser testは自前8785serverを起動/終了し、URL/Chromiumだけadapterで設定、原test assert未変更。結果/ログはdocs/qa/rilde-house02-spawn-20261013/。

補助wrapperの初回はm10が出す `FAILS []` を誤判定した。ゲームtestのconsole/FAILは無く、wrapperを `^FAIL `/`^FAILS [1-9]` に直してm10のみ再実行しexit0を確認。ゲームの新規リグレッションではない。

合格: Node、生成元一致、browser入室/実歩行、m10。失敗: 変更前の新規回帰の再現のみ。未実施: 88+Qでの全回帰、Android実機、全旧save位置。main既存m13/m4は今回実行していない。

## 要判断 / 次の提案

Claudeがこの小修正を採用してmainへ統合する際は通常の退避/no-ff/関連回帰を行う。点ベースgenerator validatorを全室の22×10footに統一する追加整備は別提案（今回は全室判定仕様を変更せず、新規regressionで家02を保護）。全室/全mapのspawn検査へ広げるときは他の既存問題も個別に扱う。

Codexはmain未更新。mainロールバック不要。将来統合分を戻すなら `git revert -m 1 <merge>`。force pushなし。
