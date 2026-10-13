# EE: レイダー回避の実エンジン検証

m30は実PrologueCombat.roundでheroRaiderの風の舞を使った後、enemyRoundを通して確認する。private dodgedは公開APIではないため直接呼ばない。BattleStatusのrollだけを0/.99に固定し、通常攻撃のAidan/Fiona双方、破砕斬の両回避/両命中/片側回避を検査。回避時HP減少0、命中時は通常21・破砕斬42/36、DOMのaidan_evade/fiona_evade画像srcが各roll結果に合うことを確認する。

結果は添付m30.logとschema.log/self.logに記録。実機の描画性能や手操作の避けやすさは未測定。数値は既存ルールを検査し、新数値は採用しない。main/ゲーム/採用素材/セーブ構造は未変更。統合後に戻す場合は `git revert -m 1 <統合コミット>`。

実行結果: 8シナリオすべて合格、FAILS0、console/page error0。height schema/self-testもFAILS0。通常攻撃A/F各命中/回避の4、破砕斬は両命中/両回避/片方ずつ回避の4。画像srcとHPの両方を確認。FFでは最新mainに同testを加えて再実行する。
