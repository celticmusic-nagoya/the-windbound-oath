# CC: 納品ボアとKO終端

main3208079基準。m29 FAILS0、console/page error0。戦闘23枚（静止5+idle4+attack4+damage4+KO6）、field11枚、RGBA/戦闘480×400/field240×160、alpha足元390/154、alpha bbox中心がcanvas中心±1pxを確認。

実field-monstersのposesはwalk1〜4/alert5/windup6〜7/rush8〜10/recover11に対応。実AIの突進中に8/9/10のsrcを観測。戦闘KO1〜6を実際に再生。最終6コマ目は約738msで出現し、約2407msの結果画面開始と3000ms時点でも表示中。結果を閉じた後、img.src自体はKO6のままだが、敵imgは非表示でforestが復帰した。戦闘後に薄れ絵がフィールドへ残る問題は今回再現せず。結果表示中にKO6が長く残る仕様の演出上の妥当性はPLAYER QA。

初回fixtureはstartAttackBattleの必須id/hp不足を修正。再観測時に未処理のfield敵に再接触したため、KOだけの観測ではFieldMonsters.removeAllでfixture敵を除去した。画像/runtime変更なし。実接触戦闘全体は既存m15dでFFに含める。主観的サイズ/薄れ方/Android未測定。main未変更、統合を戻す場合は `git revert -m 1 <統合コミット>`。

要判断の演出案: 結果画面に表示中のKO6残像も消したい場合は、6コマの総時間1050ms（最後320ms）を消化した後に敵nodeを非表示にする案。勝利計算・HP・結果画面の開始時刻と素材は変えず、generation切替でtimerを破棄する必要がある。実装はこの依頼範囲のjs変更禁止により行わない。現在のhold-lastを採用するか、消す演出にするかは作者判断。
