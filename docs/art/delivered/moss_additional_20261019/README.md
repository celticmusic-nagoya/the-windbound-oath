# モスの森 追加フィールドアセット納品記録 (2026-10-19)
受領: zip 10ファイル（複合7＋単体3）。複合7枚（fern/bush/rock/root/stump/mushroom/ruins）を17個の独立透過PNGへ分離、単体3本(tree_ancient_great_01 / tree_ancient_sentinel_01 / tree_log_hollow_A3_01)はそのまま。計20種。
- 原本: `originals/`（無加工・保持）。分離結果: `img/field/moss/art/<id>.png`（20）。分離ツール: `tools/art/split_moss_additional.py`、記録: `split_report.json`、台帳: `docs/art/moss_asset_ledger.{md,csv}`。
- 分離方法: 連結成分で各オブジェクトを判定し、全不透明ピクセルをちょうど1つのオブジェクトに割当（合計一致をassert）。ピクセルは無加工コピー（再サンプル・色変更なし）。各PNGに16px透明余白。
- 配置順序: 画像内の左→右 = ID昇順。制作指示書の説明と照合（fern 01=コンパクト/02=横長/03=大小混在、rock 01=単体/02=群/03=低横長、root 01=放射状/02=横方向、stump 01=縦長/02=空洞の低い、mushroom 01=茶橙/02=クリーム、ruins 01=紋様石碑/02=石材残骸、bush 02=横長）。**不確実: bush_forest 01 と 03**（左=丸み/右=背の高い不整形、どちらも黄緑の若葉を含むため「若葉が混ざる」が決め手にならない。左=01・右=03で仮割当）。要確認。
- 重なり: 各オブジェクト間に重なり・接触なし（6px膨張後も別連結成分）。bbox が横方向に重なる組(mushroom/root/ruins/stump)があるが、ピクセルは混在しない。
- 検証: 全PNG RGBA、四隅透明、外周アルファ0（17分離分）。**注意**: 元画像は完全透過でなく、alpha 1〜8 の薄いもや（全体の約2〜6%）を含む（ほぼ不可視）。指示により加工せず原本どおり保持。必要なら閾値クリーニングを別途提案。tree_log_hollow_A3_01 は下端のalpha最大62・四隅alpha 1（薄い影/もや。オブジェクト自体は端に接していない）。
- マニフェスト/マップ: 未登録・未配置・main未反映（指示どおり）。**A3マップは tree_ancient_great_01 / sentinel_01 / tree_log_hollow_A3_01 を既にノードとして参照**しており（現在は^tree_(log|ancient|dead)規則でファイル無し=仮表示）、manifest登録するとA3の見た目が変わるため承認待ち。rock_moss_01-03 は manifest の `^rock_` 規則（standin/rock_small.png）に当たるIDだが、マップ未使用。
- 既存との重複: 同名なし。類似カテゴリ既存: veg_mushroom_brown/red_01-02, anc_*（別ID）。上書き・削除なし。
- Android/実機: UNVERIFIED。Codex QA: 未実施。
