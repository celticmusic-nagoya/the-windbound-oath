# DEV-WALK-CYCLE-A01 evidence

- visual-REVIEW.md /visual-measurements.json /visual-six-vs-four-feet.png:独立の原画評価・ROIと限界・6/4足元比較。原本を変更した画像ではない。
- visual-analyze.py:リポジトリrootを自動検出。`python docs/qa/evidence/dev-walk-cycle-a01/visual-analyze.py --out /tmp/down-cycle-visual`で計測/比較を再現（Pillow/NumPy）。
- down-results.json /down-cadence.json /*-raw.json:低負荷録画実行の実画像フレーム・実測周期（author d671f7b）。
- pc-comparison.webm /portrait-comparison.webm /landscape-comparison.webm:旧6/90、4/60・75・90、補正・上下動・他方向等を操作した動画。PC表示1920×1080でもエンコードは720×405、縦は表示390×844/エンコード360×640、横は表示844×390/エンコード720×405。録画の解像度が表示条件やPNG解像度を変えたわけではない。
- *-four-90-06.png:同実行の補正なし06のDEV表示。
- initial/:ffmpeg未導入・台帳参照追跡の初回FAILを保持。他の回帰の成功と区別。
- highres/:高解像度録画下の4/60順序FAILを保持（失敗60の生データなし、原因断定不可）。同headで既存4回帰はPASS。
- measured/:d671f7b、ビューポート不変で録画エンコードを軽量化、生データを記録し同じ厳格な順序検査PASS。
- protection.json /node.json:原本・本番コード・正式259SHA保護とNode17出力。

最終固定HEADの独立QAはDraft PRに別記する。全体の接地品質や本番採用をPASSとした証拠ではない。Android実機は未実施。
