# A02比較資料

- pc/portrait/landscape-matrix.webm:全12条件（90/75×bobON/OFF/25%×06補正0/8）のDEV実表示。画面上に現在条件を表示。実ビューポート1920×1080/390×844/844×390、動画は負荷軽減のため640×360/360×640/640×360で記録。
- measured-pose-feet.png:実ブラウザ静止画から6幾何条件を並べた4コマ比較。measured-wrap06-01.png:同じ条件の全身06→01。コマ境界の幾何は周期に依存しないので90で採取し、75の時間差は動画・連続記録で評価する。原画編集ではない。
- support-boot-rois.png/support-analysis.json:推定支持足の手動ROI、alpha128/200輪郭、全4境界・腰/外套ROI差・速度の独立解析。物理接地の証明ではない。
- predicted-foot-gap.png:解析式による予測。measured-summary.json/measured-edges.csv:実測DOMの登録/輪郭投影との照合（36条件・144境界）。投影が合ったことを接地PASSと扱わない。
- ground-runs.json.gz:全RAFのraw記録を可逆圧縮。raw-integrity.jsonの展開後SHAで検証可能。`gzip.open(...,'rt')`で読む。
- 再集計: `python tools/qa/summarize_down_grounding.py --raw docs/qa/evidence/dev-walk-cycle-a02/ground-runs.json.gz --out /tmp/ground-summary`。再撮影画像も作る場合はm60のQA_OUTを`--screens`に指定。
- 原画解析再現: `python docs/qa/evidence/dev-walk-cycle-a02/analyze_support.py --out /tmp/support-analysis`（Pillow/NumPy/Matplotlib）。元PNGは読取りのみ。
- results.*と個別log:author直列4/4結果。ground-results.json:機能/投影検査。node.json:Node17本。
- protection.json:正式259・既存PNG・本番コード保護。最終独立レビューはDraft PRへ記録。

機能QAと原画の身体表現/Android実機/正式採用の判定を分ける。mainへマージしない。
