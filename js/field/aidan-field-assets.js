/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=002b5f63",
  "width": 2048,
  "height": 1280,
  "bounds": [
   824,
   158,
   389,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=689c4436",
  "width": 2048,
  "height": 1280,
  "bounds": [
   644,
   158,
   736,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=002b5f63",
  "width": 2048,
  "height": 1280,
  "bounds": [
   824,
   158,
   389,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=b0c6dd2d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   646,
   158,
   736,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=002b5f63",
  "width": 2048,
  "height": 1280,
  "bounds": [
   824,
   158,
   389,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=9fe14938",
  "width": 2048,
  "height": 1280,
  "bounds": [
   737,
   315,
   1037,
   915
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=2e60407c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   692,
   306,
   1062,
   924
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=9fe14938",
  "width": 2048,
  "height": 1280,
  "bounds": [
   737,
   315,
   1037,
   915
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=b509fa89",
  "width": 2048,
  "height": 1280,
  "bounds": [
   692,
   302,
   1080,
   928
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=9fe14938",
  "width": 2048,
  "height": 1280,
  "bounds": [
   737,
   315,
   1037,
   915
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=66f0574b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   65,
   313,
   1083,
   917
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=c1deb269",
  "width": 2048,
  "height": 1280,
  "bounds": [
   81,
   321,
   1081,
   909
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=1bd12480",
  "width": 2048,
  "height": 1280,
  "bounds": [
   96,
   319,
   1087,
   911
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=66f0574b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   65,
   313,
   1083,
   917
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=69c306d6",
  "width": 2048,
  "height": 1280,
  "bounds": [
   86,
   308,
   1090,
   922
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=c94ba03c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   660,
   158,
   702,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=7e0c4efd",
  "width": 2048,
  "height": 1280,
  "bounds": [
   447,
   158,
   1069,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=bb9083a6",
  "width": 2048,
  "height": 1280,
  "bounds": [
   492,
   158,
   1012,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=c94ba03c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   660,
   158,
   702,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=ae206b39",
  "width": 2048,
  "height": 1280,
  "bounds": [
   580,
   158,
   845,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_05": {
  "path": "img/field/characters/aidan/aidan_walk_up_05.png?v=83232452",
  "width": 2048,
  "height": 1280,
  "bounds": [
   728,
   158,
   705,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_06": {
  "path": "img/field/characters/aidan/aidan_walk_up_06.png?v=bd86f172",
  "width": 2048,
  "height": 1280,
  "bounds": [
   679,
   158,
   689,
   1072
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
