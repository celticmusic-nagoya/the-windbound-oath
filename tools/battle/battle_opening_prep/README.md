戦闘開始モーション(エイダン draw / フィオナ ready)の前処理手順。原本シートは docs/art/delivered/battle_start_20261013/ に保存。
1. split2.py <aidan|fiona>  : 6コマ分割(連結成分+最近傍。エイダン2〜3コマ目は接触しているため x=690..760 の最小コスト継ぎ目で切る) → <name>_raw.pkl
2. clean2.py <name>         : 薄いもやの除去と暖色(赤/黄/茶)縁の色補正。緑〜黄緑(魔法の光・葉)は不変(フィオナ) → <name>_clean.pkl
3. norm2.py <name> <本体px> <足中心比> : 足元・足中心を統一し、戦闘表示枠(158x198 基準)で本体が既存の待機と同じ大きさになるキャンバスへ配置 → out_<name>/
   (aidan 96 0.41 / fiona 101 0.58)
4. python3 tools/battle/install_motion_frames.py out_<name> --ms ... を実行し、manifest の hitFrame を削除。
入出力パスは各スクリプトの先頭定数(アップロード先/カレント)を環境に合わせて調整する。

第3納品(2026-10-13: エイダン抜刀/待機・フィオナ待機)は split3.py <aidan_idle|aidan_draw|fiona_idle> → clean2.py相当(clean()) → norm3.py。
  norm3.py aidan_idle 0 100 81 / aidan_draw 5 101.3 86.2 / fiona_idle 0 101 89.5
