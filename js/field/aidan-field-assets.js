/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=cf64943b",
  "width": 1792,
  "height": 1152,
  "bounds": [
   489,
   76,
   713,
   1024
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=82636f00",
  "width": 1792,
  "height": 1152,
  "bounds": [
   483,
   257,
   921,
   843
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=cf64943b",
  "width": 1792,
  "height": 1152,
  "bounds": [
   489,
   76,
   713,
   1024
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=82636f00",
  "width": 1792,
  "height": 1152,
  "bounds": [
   483,
   257,
   921,
   843
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=cf64943b",
  "width": 1792,
  "height": 1152,
  "bounds": [
   489,
   76,
   713,
   1024
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=fef669bd",
  "width": 1792,
  "height": 1152,
  "bounds": [
   793,
   268,
   910,
   832
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=0c791f9e",
  "width": 1792,
  "height": 1152,
  "bounds": [
   792,
   275,
   909,
   825
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=f018ee44",
  "width": 1792,
  "height": 1152,
  "bounds": [
   787,
   273,
   914,
   827
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=fef669bd",
  "width": 1792,
  "height": 1152,
  "bounds": [
   793,
   268,
   910,
   832
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=d92d196c",
  "width": 1792,
  "height": 1152,
  "bounds": [
   788,
   263,
   916,
   837
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=7ed00773",
  "width": 1792,
  "height": 1152,
  "bounds": [
   89,
   268,
   910,
   832
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=bf9a867e",
  "width": 1792,
  "height": 1152,
  "bounds": [
   91,
   275,
   909,
   825
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=fcbe8991",
  "width": 1792,
  "height": 1152,
  "bounds": [
   91,
   273,
   914,
   827
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=7ed00773",
  "width": 1792,
  "height": 1152,
  "bounds": [
   89,
   268,
   910,
   832
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=73bcfe3d",
  "width": 1792,
  "height": 1152,
  "bounds": [
   87,
   263,
   916,
   837
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=c33c3bf0",
  "width": 1792,
  "height": 1152,
  "bounds": [
   600,
   258,
   921,
   842
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=c33c3bf0",
  "width": 1792,
  "height": 1152,
  "bounds": [
   600,
   258,
   921,
   842
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=2875f162",
  "width": 1792,
  "height": 1152,
  "bounds": [
   605,
   271,
   914,
   829
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=c33c3bf0",
  "width": 1792,
  "height": 1152,
  "bounds": [
   600,
   258,
   921,
   842
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=2875f162",
  "width": 1792,
  "height": 1152,
  "bounds": [
   605,
   271,
   914,
   829
  ],
  "anchor": [
   896,
   1100
  ],
  "scale": 0.0625
 }
};
  Object.values(frames).forEach(Object.freeze);
  window.AidanFieldAssets = Object.freeze({frames:Object.freeze(frames)});
})();
