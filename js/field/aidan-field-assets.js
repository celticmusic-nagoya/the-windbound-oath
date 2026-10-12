/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=4e75f464",
  "width": 2048,
  "height": 1280,
  "bounds": [
   564,
   158,
   806,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=bd9b4340",
  "width": 2048,
  "height": 1280,
  "bounds": [
   423,
   315,
   1084,
   915
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=b9389374",
  "width": 2048,
  "height": 1280,
  "bounds": [
   415,
   302,
   1096,
   928
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=1c19bfae",
  "width": 2048,
  "height": 1280,
  "bounds": [
   389,
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
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=b9389374",
  "width": 2048,
  "height": 1280,
  "bounds": [
   415,
   302,
   1096,
   928
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
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=219fe120",
  "width": 2048,
  "height": 1280,
  "bounds": [
   671,
   303,
   1096,
   927
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=219fe120",
  "width": 2048,
  "height": 1280,
  "bounds": [
   671,
   303,
   1096,
   927
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=f413f796",
  "width": 2048,
  "height": 1280,
  "bounds": [
   992,
   148,
   593,
   1082
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=219fe120",
  "width": 2048,
  "height": 1280,
  "bounds": [
   671,
   303,
   1096,
   927
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=a3fcbe12",
  "width": 2048,
  "height": 1280,
  "bounds": [
   952,
   152,
   655,
   1078
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
