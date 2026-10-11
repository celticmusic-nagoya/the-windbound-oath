/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=4d362dc1",
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
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=094f81a1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   543,
   321,
   1072,
   909
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=4d362dc1",
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
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=094f81a1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   543,
   321,
   1072,
   909
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=4d362dc1",
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
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=4090b304",
  "width": 2048,
  "height": 1280,
  "bounds": [
   904,
   333,
   1060,
   897
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=77fda7fe",
  "width": 2048,
  "height": 1280,
  "bounds": [
   903,
   340,
   1058,
   890
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=97d56636",
  "width": 2048,
  "height": 1280,
  "bounds": [
   897,
   338,
   1064,
   892
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=4090b304",
  "width": 2048,
  "height": 1280,
  "bounds": [
   904,
   333,
   1060,
   897
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=37731a1d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   899,
   328,
   1067,
   902
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=152c7a40",
  "width": 2048,
  "height": 1280,
  "bounds": [
   85,
   333,
   1060,
   897
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=35add6fa",
  "width": 2048,
  "height": 1280,
  "bounds": [
   87,
   340,
   1058,
   890
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=79656ecd",
  "width": 2048,
  "height": 1280,
  "bounds": [
   87,
   338,
   1064,
   892
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=152c7a40",
  "width": 2048,
  "height": 1280,
  "bounds": [
   85,
   333,
   1060,
   897
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=7475e589",
  "width": 2048,
  "height": 1280,
  "bounds": [
   82,
   328,
   1067,
   902
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=32e65d2e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   679,
   322,
   1072,
   908
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=32e65d2e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   679,
   322,
   1072,
   908
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=c00f84d7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   686,
   336,
   1065,
   894
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=32e65d2e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   679,
   322,
   1072,
   908
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=c00f84d7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   686,
   336,
   1065,
   894
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
