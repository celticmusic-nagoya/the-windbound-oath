# MORWEN-REAL-CANON-FINAL-ALIGN-01 pipeline

Run from a scratch directory containing `front_src.png`, `right_src.png` (official originals) and the two provided black-background images:

```
python3 matte.py back_provided.png back_matte2.png back
python3 matte.py left_provided.png left_matte2.png left
python3 colormatch.py front_src.png,right_src.png back_matte2.png back_cm2.png
python3 colormatch.py front_src.png,right_src.png left_matte2.png left_cm2.png
python3 leather_fix.py back_cm2.png back_cm2l.png
python3 cape_fix.py left_cm2.png left_cm2c.png 560 280 1000 1420 1.12 1.5
python3 heelfix.py right_src.png right_fix.png
python3 compose.py            # writes final/morwen_{dir}_final.png + compose_meta.json
python3 ../../scripts/qa_morwen_final_align.py --write
```
Originals are read only. Outputs are candidates, not production assets.
