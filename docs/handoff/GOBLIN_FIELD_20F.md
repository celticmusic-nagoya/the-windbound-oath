# ゴブリン・フィールド20コマ統合

STATUS: READY_FOR_REVIEW。Owner: Codex。ブランチ: `feature/goblin-field-20f`。
基準main: `2276c3c693cce9ea215dd68d51e1725bfb4e51fb`。
実装・最終ブラウザ検証HEAD: `a1ba70a576b2f504f9bc03bffb881ddfc5c58c83`。
main変更・マージ・Pages公開は行わない。画像は**候補・採用判断待ち**で、正式採用へ自動昇格させていない。

## 画像と照合

正本: `img/battle/enemies/goblin/goblin_battle_idle.png`、1312×1199、SHA-256 `c4702d8292505d7e84b307cdf9096d16d0a9690c796060a129eea9d15c3cec01`。緑の肌、黄橙の目、尖った耳、長い鼻、継ぎ接ぎの茶フード、革帯・腰布、腕の包帯、湾曲した刃を照合。正式画像を上書きしていない。外見の最終的な一致・採用判断は人間のレビューに残す。

アップロード20PNGには低解像度の背景片残留と足元位置のばらつきがあった。正式画像とアップロードを参照して画像編集ツールで20姿勢を描き直し、透明背景へ修正。原本は`assets/candidates/goblin-field-20f/source/`にバイト不変で保存。旧`feat/goblin-field-art`3535a24の2枚WIPは別物であり、マージ・採用・上書きしていない。

- [入力比較](../art/candidates/goblin-field-20f/input-contact.png)
- [修正後・足元基準線](../art/candidates/goblin-field-20f/packed-contact.png)
- 編集出力: `docs/art/candidates/goblin-field-20f/generated-sheet.png`
- ゲーム用: `img/field/monsters/goblin/`、20PNG、各320×320 RGBA。
- manifest: 同ディレクトリ`manifest.json`。全SHA、編集出力SHA、参照SHA、切出し位置・平行移動を記録。

`tools/art/pack_goblin_field20.py`は切出し・共通キャンバスへのパディングのみ。人物の再描画・拡縮はしない。>32-alphaの全前景と2pxの縁を保持し、空領域の低alphaマットノイズを切出し範囲外に除外。完全透明画素のRGBを0に正規化。足元anchor=(160,288)、表示scale=.25、キャンバス80×80world、可視高さ約49.75～61.25world（横向きは身をかがめた姿勢）。頭や武器に合わせて毎コマ拡縮する方式は使わない。

## コード

`js/field/field-monsters.js`の既存基盤を再利用。通常ゴブリンのplaceholderを待機4枚＋上下左右各4枚へ接続。待機は受領仕様の正面3/4姿勢4枚、3fps。歩行は実際に進んだ距離から48world/周期で4コマ選択し、実移動方向を使う。上下左右の専用画像を使い、鏡像反転はしない。方向転換／再始動で位相をリセット、移動不能なら待機。既存tickを使い、rAF／intervalを新設しない。

AI・索敵・速度・接触半径・戦闘ID・報酬・マップ・シナリオ・SAVE形式は不変。通常ゴブリンは既存A1/A2配置・既存story gateに従う。異形ゴブリンやレイダー、イベントCGには適用しない。他3種の描画分岐は維持。`index.html`は当該JSのキャッシュキー1行のみ更新。

台帳は新規5系列だけPENDING / BRANCH_ONLY / Android UNVERIFIED。履歴の旧2枚は維持。台帳監査はcheckout上のBRANCH_ONLYファイルにもSHA・参照・登録検査を適用し、MAINに偽装せず整合性を検査する。正常・改変SHA・欠落ファイルの独立した故障注入を実施。

## QA

- 関連回帰 **7ファイル、9実行PASS**。m54実描画、SAVE/CONTINUE、m17配置・接触、m15スライム、m9既存キャラクター、素材台帳、候補素材保護。[実行結果初回](../qa/goblin-field20/qa/results.json)／[最終3本](../qa/goblin-field20/final-qa/results.json)。終了コードとログ中FAILを確認。
- 新規Node **10ケースPASS**、既存を含むNode **16ファイルPASS**。停止・再開、四方向、障害物、freeze/clear、他3種の既存描画を検査。
- PC1920×1080、Android相当390×844・844×390で **20/20×3画面**。実DOM画像をcanvasへ描画し、完全不透明画素のSHAを各PNGと照合。全方向4コマ、画面内表示、左右非反転、freeze/clear、通常設定ゴブリンの接触→既存戦闘開始PASS。[描画結果](../qa/goblin-field20/actual-render-results.json)。
- 素材20枚のSHA・透明性・参照一致、台帳5系列の候補状態維持。故障注入2件（壊れたSHA／欠落フレーム）でFAIL検出。正式259PNG、既存1298画像の不変を独立確認。
- 構文`node --check` PASS。vanilla JSのため別途bundle buildはない。console/pageerror/HTTP4xx5xxはm54で0。Android**実機はNOT_RUN**。

四方向・全コマの検証では既存DEVアリーナと決定的なAI fixtureを使用した。通常のストーリー到達性を証明するテストではなく、26Cの連続プレイ履歴は触っていない。SAVE/CONTINUEは既存原版回帰の結果を別に扱う。既知の本編進行課題の解消やゲーム全体の完走PASSを意味しない。

再検証中の失敗も隠していない。編集出力の低alpha空領域で最初のパディング検査が失敗し、前景を保持した切出しに修正した。素材fixtureは履歴の旧2枚も数えて失敗したため、対象manifestの20枚へ限定して修正し、旧資料は維持した。`node --test`の外側1件表示や誤って旧checkoutを対象にした実行は新規10件／16本のPASSに使わず、正しいブランチを直接Node実行して回収した。

## レビュー操作

本ブランチで`python3 -m http.server 8000`→ブラウザで`http://localhost:8000/`。既存DEVメニュー→モンスター配置アリーナ→種類「ゴブリン」→配置。移動・追跡・freezeで外見と足元を確認。新しいDEV専用表示システムは追加していない。公開Pagesは本ブランチへ更新していない。

次の判断: 候補20枚の見た目の採用可否。採用・mainマージは別の明示承認後。自律リトライは素材の正式採用権限や既存のmain変更禁止を拡張しない。
