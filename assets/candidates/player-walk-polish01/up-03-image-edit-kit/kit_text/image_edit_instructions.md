# ChatGPT 画像編集の依頼方法

## 最小限の添付セット（この3枚）

1. `05_crops/right_leg_crop.png`（編集する画像。280×480、正式03の右脚まわり）
2. `05_crops/right_leg_crop_mask.png`（編集してよい範囲。白＝編集可）
3. `04_references/right_boot_details.png`（本人の右足の靴のデザイン）

必要に応じて、`04_references/push_off_motion_reference.png`（姿勢の参考。左足）と `03_guides/right_leg_pose_guide.png` も添付します。

**全身の画像（2048×1280）は渡さないでください。** 全身を渡すと、髪・外套・装備まで描き直されやすくなります。切り出し画像だけを渡し、戻ってきた画像は Claude が元の座標 (940,760) に貼り戻して合成します。マスク外は正式03に戻します。

## 依頼文（英語。そのまま貼り付け可）

> Edit only the white area of the mask (image 2) in image 1. Image 1 is a 280×480 crop of a back-view game sprite (transparent background). Keep every pixel outside the white area unchanged, keep the canvas size 280×480, the transparent background, and the exact art style, colors and line weight.
> In the white area, redraw the character's anatomical RIGHT leg (the leg on the RIGHT side of the image) as a push-off step seen from behind: the leg extends backward toward the viewer, knee slightly bent, heel raised, the sole of the boot faces the viewer, and the toe touches the ground line, which is the bottom of the boots in image 1 (y = 469 in the crop). The boot is a RIGHT boot with the bronze armor design shown in image 3; do not mirror or copy the left boot. The right thigh comes out from under the existing hem and cloak; do not change the hem or cloak. The left leg (left side of the image) stays planted and unchanged; the right boot may overlap only the right edge of the left boot. No ground, shadow, text or background. Output a 280×480 PNG with transparency.

## 日本語での要点

- マスクの白い範囲だけを編集する。
- 本人の右脚（画像の右側）を、後ろへ伸ばした蹴り出しの姿勢にする。膝は軽く曲げ、踵を上げ、靴底は見る人の方向、つま先は接地線（切り出し画像の y=469、元画像の y=1229）。
- 右足用の靴（`right_boot_details.png`）で描く。左足の靴を反転・コピーしない。
- 裾・外套は変えない。腿は裾の下から出す。
- 左脚は変えない（右足が左ブーツの右端に重なるのは可）。
- 背景・地面・影・文字は入れない。透過 PNG・280×480 のまま。

## 戻ってきた画像の受け渡し

PR のブランチに追加するか、チャットに添付してください。Claude が以下を行います。
1. 貼り戻し
2. マスク外を正式03に戻す合成
3. 寸法・接地線・透過・差分の検査
4. 5コマ（蹴り出し→03→04→01→06、周期90、bob 25%）の連続再生比較
5. Codex による独立QA
