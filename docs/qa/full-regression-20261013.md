# V: 最新main全回帰

基準main160bead、固定source313b25a（O runner追加のみ、js/maps/tests差分なし）。work/codex-v-sourceでgit archive snapshotを作り、全62本をport8791/各600秒で直列実行。作業中のbranch切替/元worktree変更なし。

**合格60 / main既存2 / 新規0 / 未実施0**。失敗合計2、runner exit1（既知失敗でも非0にする）。

既存: m13のmorning line、m4_e2eのFiona到着warning期待値のみ。m4は祭壇まで到達、console errors[]。m8 town mapsも約285秒、seal約202秒で完了しtimeoutなし。全testの前後SHA256一致、全owned server終了を確認。

全件表/生ログ/JSON/性能・画像証跡は[full-regression-20261013/results.md](full-regression-20261013/results.md)。追加Uの赤テストはmainに無く別集計（160beadで2失敗）。T benchも別途検証。Android実機は未測定。

変更: 本報告、full-regression-20261013/証跡、status/CLAIMS。O runnerは56f6050版を変更せず利用（source branch313b25aへ保存/push済み）。ゲーム/マップ/既存tests未変更。STATUS READY。

次: Wで台詞2件の未適用patchと検証を提示。main統合はClaude、Codexのmain更新なしでロールバック不要。

## 新main230a29cでの全件再実行

Claudeのaltar短縮/walker/static lift mergeを受け、新規独立source `43b749f50b27f5c95fa1374efae58b4cac22bde8` （230a29c + unchanged O runner）から全63本を再実行。**61合格 / main既存2 / 新規0 / 未実施0**。前後SHA不変・owned server終了を全63件で確認。m24もFAILS0/console0、縦横の上階宝箱tapが合格。

最新runの全件表/JSON/生ログ: [full-regression-latest-20261013/results.md](full-regression-latest-20261013/results.md)。160bead結果は比較として保持。branch work/codex-v-latest のsourceはpush済み。基準をテスト中に変更していない。旧台詞2件はWの提案へ。Androidは未測定。
