# GG キーボード独立QA (2026-10-13)

基準main `31a5f5e`。ブランチ `work/codex-gg-kk`（commitはgit log参照）。新規 `tests/input/kb_audit.py` と本報告/証跡のみ。ゲームコードは未修正。

## 結果

42項目: 合格40 / 失敗2 / 未実施0。pageerror 0。失敗は基準mainで再現した既存の挙動（追加監査による新規発見、Codex変更の回帰ではない）。

| 指摘 | 重大度 | 再現手順 / 実測 | 原因と提案 |
|---|---|---|---|
| 旧宿屋の店主にEnterで話せない | 中 | `?legacyVillage=1`、`room='inn';dressRoom()`、店主の35〜40px手前へ移動、Enter。keeper click=0。マウスのonclickは登録済み | `oldWorldInteract` は `.furn/.door/.npc` のみ。`#innKeeper` は対象外。旧店主等を含めるか作者判断 |
| 同一フレーム非repeat Enterが2ページ進める | 低・要判断 | `startAltarScene()` 後、同じJS task内で `repeat:false` のkeydown Enterを2回dispatch。scene click=2 | 長押しのrepeat抑止は合格。非repeatの独立イベントには時間/フレーム抑止なし。合成イベントによる経路監査であり、実機の二重物理入力を再現したとはしない。必要なら1フレーム内の確認入力を抑止 |

手帳Q/Tab、リルド・砦のショップEnter/Space購入、入力欄ショートカット除外、旧NPC/家具/扉、全8シーン、セーブ、宝箱、戦闘行動とアイテム消費、マップ読み込み中の確認入力、戦闘開始ログ表示中のTab、blur/メニュー/シーン/戦闘による押下中断、モバイル縦横のCOMMANDタップを確認した。

Spaceスクロールは実キーでscrollY不変、cancelableイベントのpreventDefaultも確認。TabはDOM上のフォーカスがパネル内に留まることを確認した。headlessではアドレスバー等のブラウザUI自体は計測できない。

ショップ/旧世界/シーンはDEVまたは公開関数で開始状態を準備し、確認操作は実キーを使用。アイテムは選択時でなく両者の行動確定後に消費されるため、キュー1件とターン後残数5→4の両方を検査。マップ遷移は読み込み直前/直後のFieldTalk状態を比較し、自然な到着メッセージを偽失敗としない。

## 証跡と再実行

[結果JSON](keyboard-audit-20261013/results.json)、[ログ](keyboard-audit-20261013/run.log)、同ディレクトリのシーン8枚/モバイル2枚。

`PW_CHROMIUM_EXECUTABLE=/usr/bin/chromium python tests/input/kb_audit.py`。自身の8811サーバーを起動/終了、PORT指定時は既存runnerへ委譲。指摘が未修正なのでFAILS 2 / exit1を維持する。期待値を緩めて合格にしない。

Android実機は未測定。保護対象を変えず、Claude側で修正・採用を判断する。次: HH。mainへのマージなし。将来統合する場合は退避branch→no-ff、戻し方 `git revert -m 1 <merge>`。
