# Asset gaps — DIRECTIVE-25A

基準: PR98 main `5ab60c5db833821744d73080f91ffcd559ebf0a4`。[正式採用台帳](../assets/ASSET_REGISTRY.json)と既存[素材backlog](../assets/ASSET_BACKLOG.md)を保持し、現行の不足／将来の制作候補だけをここに整理する。**画像生成・差し替え・採用変更なし。**

259正式採用PNGは保護対象。会話全28表情、瞬き24表情、意図的静止4表情に不足扱いを追加しない。ルーsmile/relievedは未採用のまま、制作必須リストにも自動追加しない。レイダー元sheet5件はbranch保管でも派生frameがmainで実装済みであり、欠損素材ではない。45未参照、885採用UNKNOWN、179未マージは台帳の異なる軸であり、足して「不足数」にしない。

以下は **10制作／接続検討単位**。現行画面の必須参照切れ10件という意味ではない。pixel寸法・フレーム数・anchorの正式指定がないものはTBDと明示し、制作前に契約する。既存解像度を根拠なく新規の正式仕様へ昇格しない。

| ID | 用途／登場シーン | 不足の種類・必要画像 | サイズ／縦横比 | 透過 | 画風・配置条件 | 優先度／担当／依存 | 代替 |
|---|---|---|---|---|---|---|---|
| ART-01 | リアム加入後の戦闘 | 3人目以降のbattle用standalone sprite・必要poseの契約未確定 | TBD: active人数とHUDから先に決定。既存field絵は112×168 RGBA×7でありbattle仕様ではない | battle spriteは実alpha必要 | 既存高精細アニメ／絵画調、味方左・右向き、顔・採用済み設定の武器を欠かさずanchor統一 | P1開発の依存／ChatGPT仕様・Claude制作・ユーザー採用・Codex接続／PARTY-01 | 加入・field・保証人には既存7fieldPNG。実戦拡張は代替未確定 |
| ART-02 | フィオナ通常戦闘 | windbloom、guard、evade、prayer、item、victory、awaken、low_hpの専用複数frameは未統合／未納品が混在 | TBD: `img/battle/motion-manifest.json`の既存anchor／frame契約を照合して動作ごと決定 | 必要 | 正式Fiona、杖・髪・装飾保持。採用済み風の舞v3と会話瞬きは別系統 | P2／Claude・ユーザー・Codex／対象motion選定 | 現在の静止pose＋共通演出。すべて描画不能という意味ではない |
| ART-03 | ルーSUPPORT戦闘 | charge→heal、rune、evade、victory、low_hpの専用motion | TBD:小型SUPPORT枠と既存flightを基準に契約 | 必要 | 妖精サイズ、羽・魔法・髪保持。通常command actorにしない | P2／Claude・ユーザー・Codex／SUPPORT演出方針 | 現行静止絵＋flight／浮遊・支援効果 |
| ART-04 | エイダン通常戦闘 | victory、guard、evade、itemの専用複数frame | TBD:採用済みbattle motionと同じfeet anchorへ | 必要 | 父の剣／誓いの剣の時期を保持、右向き | P3／Claude・ユーザー・Codex／対象motion選定 | 現行静止poseと共通移動演出 |
| ART-05 | 通常ゴブリン戦闘 | damage、low_hp、guardの専用motion | TBD:既存enemy描画枠と接地線へ | 必要 | 単独monsterPNG、合成参照sheetからの切出し禁止 | P3／Claude・ユーザー・Codex／動作を実際に使う条件確認 | 現行pose＋hit effect |
| ART-06 | 異常化ゴブリン戦闘 | damage、low_hp、guardの専用motion | TBD:既存enemy anchorへ | 必要 | 黒紫ルーンと既存採用デザイン保持 | P3／Claude・ユーザー・Codex／動作選定 | 現行pose＋hit effect |
| AUD-01 | 森、断崖、砦、街道、王都等のfield BGM | map宣言IDの多くにFieldBgm生成profileなし。録音audioファイルは現行treeにない | 音声:画像size/alpha該当なし。codec、loop、尺、LUFSはTBD | 該当なし | ケルト調、各場面の緊張・静けさ。新曲採用は別承認 | P2／ChatGPT・ユーザー方針、Codex接続／AUDIO-01 | リルド3生成profile、非対応IDは停止。架空のmp3参照切れではない |
| MAP-01 | 王都職人地区・東地区・王城内 | 未接続3出口の先のmap／背景／props仕様 | TBD:承認済み次区間のworld／viewport設計後 | layers/props毎にTBD | 既存王都top-down pixel fieldと整合。戦闘絵と別系統 | P1計画／ChatGPT・ユーザー、Claude制作、Codex接続／STORY-01 | 現行出口は未実装通知で留まる。無断接続しない |
| MAP-02 | モスの森深部 | `tr_to_deep`先の未実装領域。制作要否から未決定 | TBD:採用シナリオ・map範囲承認後 | layers毎TBD | 既存森tile／scatter／collision方式と整合 | P2計画／ChatGPT・ユーザー／STORY-01 | 現在は根で閉鎖。現行プロローグの進行には不要 |

| MAP-03 | 本編stage5〜8のlegacy襲撃field | NPC/敵/救助地点に文字・CSS図形の仮表示が残る。正式pixel素材との接続差 | TBD:現行top-down fieldの表示枠/anchorに合わせる。既存正式ruin-map素材の再利用を先に照合 | actor/propは実alpha、map layerは用途別 | 平和/廃墟Rildeと同一村として連続するpixel画風。会話立ち絵と別系統 | P2／Codex・Claude／FIELD-01。シナリオ条件保持 | 正式なRilde peace/ruin mapと既存field素材あり。全身再生成から始めない |

別の実装不足: ルーKO6frameは既に納品・実装側の登録があるが、ルー専用失神triggerは未整備。これは画像再制作依頼に数えず、SUPPORT演出のコード課題として扱う。レイダー`ko_dissolve`／`powered_attack`候補はPENDINGのまま保全し、既存KOに対する必須代替とも扱わない。

実ファイル所在・マップ遷移・BGM宣言・259SHAは[静的証拠](../qa/evidence/directive-25a/static-inventory.json)、採用／未採用分類は正本台帳を参照。現行runtimeのHTTP失敗は総合監査の観測範囲で別集計する。新規制作を始める際は各IDを画像1枚／motion1式に分解し、pixelサイズ・stage数・anchor・命名・承認者を確定してからClaude／ChatGPTへ渡す。
