# 断崖〜リルド村襲撃・復旧：CG登録台帳（2026-11-07）

**登録状況:** 原本15点をローカルZIPに保全。**GitHubへのPNGバイナリ登録は未完了**。この文書だけでは素材はゲームから参照できない。原本を別の絵に再生成・置換しない。

## 対象と正式採用の区別

| 使用場面 | ZIP内パス | 状態 |
|---|---|---|
| 断崖・夕陽 背景のみ | `assets/approved/game/cliff/sunset_background.png` | 過去の正式採用アーカイブ |
| 断崖・夕陽 二人の後ろ姿 | `assets/approved/game/cliff/sunset_two_characters_back_view.png` | 過去の正式採用アーカイブ |
| 星空 二人着座 | `assets/approved/game/cliff/stargazing_seated.png` | 過去の正式採用アーカイブ |
| 星空 二人立位・見上げる | `assets/approved/game/cliff/stargazing_standing_final.png` | 過去の正式採用アーカイブ |
| 星空・立ち絵会話用背景 | `assets/approved/game/rilde_story/cliff/stargazing_dialogue_background.png` | 正式採用 |
| カーブした未舗装の坂道・村炎上発見 | `assets/approved/game/rilde_story/road/curve_reveal_candidate_a.png`、`curve_reveal_candidate_b.png` | どちらが最終採用か要照合。未舗装・カーブ後に村が見える版を優先 |
| 炎上村・人物ゴブリンあり | `assets/approved/game/rilde_story/raid/attack_with_characters.png` | 会話中に採用された版との最終画像照合待ち |
| 炎上村・立ち絵用背景のみ | `assets/approved/game/rilde_story/raid/attack_background_only.png` | 会話中に採用された版との最終画像照合待ち |
| 鎮火後・荒廃した村 背景のみ | `assets/approved/game/rilde_story/aftermath/ruins_background_only.png` | 会話中に採用された版との最終画像照合待ち |
| 兵士による救援・村人の復旧 | `assets/approved/game/rilde_story/recovery/relief_with_characters.png` | 最終採用版。ポニーテール女性兵士 |
| 参考・未採用候補 | `*_alternate.png` | 保全のみ。ゲーム組込禁止 |

## 絶対条件
- 断崖から村は見えない。村の炎は坂道のカーブを抜けたところで初めて視認。
- 村の風の石・石橋・建物の地理的整合性を保護。
- 異常化ゴブリンは紫の魔力を帯び、奪った酒を手に指揮。通常ゴブリンは村人襲撃、破壊、略奪。
- 襲撃 → 脱出 → モスの森 → レイダー撃破 → ドゥンヴァル砦で報告 → 村に一時帰還・復旧。
- ゲーム本体専用。公式サイトへの公開は禁止。
- PNG原本のバイト列を保持し、SHA-256照合後に素材マニフェストを確定。
- 正式採用版が特定できない箇所は候補のまま保留し、誤登録を防ぐ。

## 次工程
1. 同梱 `MANIFEST.json` にある15点のSHA-256と寸法を確認。
2. PNGバイナリをGitHubのこのブランチにアップロード。既存ファイルの上書き・削除禁止。
3. GitHub上の原本を再取得してSHA-256照合。
4. 最終採用の対応が未確定な画像を視覚照合し、正式採用分だけ実装用リストに昇格。
5. CG表示・背景＋立ち絵会話の遷移をイベント実装。Android実機QAとSAVE互換QA後にmainへ。
