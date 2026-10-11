/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=4c339e36",
  "width": 2048,
  "height": 1280,
  "bounds": [
   550,
   126,
   830,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=2b98241e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   554,
   287,
   1116,
   943
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=125a458b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   543,
   274,
   1128,
   956
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=72607669",
  "width": 2048,
  "height": 1280,
  "bounds": [
   551,
   286,
   1115,
   944
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=125a458b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   543,
   274,
   1128,
   956
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=99ee6516",
  "width": 2048,
  "height": 1280,
  "bounds": [
   731,
   287,
   1068,
   943
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=4484094f",
  "width": 2048,
  "height": 1280,
  "bounds": [
   705,
   278,
   1094,
   952
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=99ee6516",
  "width": 2048,
  "height": 1280,
  "bounds": [
   731,
   287,
   1068,
   943
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=7d223c3e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   687,
   274,
   1112,
   956
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=99ee6516",
  "width": 2048,
  "height": 1280,
  "bounds": [
   731,
   287,
   1068,
   943
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=6e884d0d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   36,
   286,
   1115,
   944
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=df339490",
  "width": 2048,
  "height": 1280,
  "bounds": [
   38,
   294,
   1113,
   936
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=b7f099c9",
  "width": 2048,
  "height": 1280,
  "bounds": [
   38,
   292,
   1119,
   938
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=6e884d0d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   36,
   286,
   1115,
   944
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=32451ecf",
  "width": 2048,
  "height": 1280,
  "bounds": [
   33,
   281,
   1123,
   949
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=705376a0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   661,
   275,
   1128,
   955
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=705376a0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   661,
   275,
   1128,
   955
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=89cd15a4",
  "width": 2048,
  "height": 1280,
  "bounds": [
   668,
   289,
   1120,
   941
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=705376a0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   661,
   275,
   1128,
   955
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=89cd15a4",
  "width": 2048,
  "height": 1280,
  "bounds": [
   668,
   289,
   1120,
   941
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 }
};
  Object.values(frames).forEach(Object.freeze);
  window.AidanFieldAssets = Object.freeze({frames:Object.freeze(frames)});
})();
