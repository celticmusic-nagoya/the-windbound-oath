/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=7ad6002d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   746,
   158,
   566,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=ccfadc6e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   747,
   141,
   556,
   1089
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=7ad6002d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   746,
   158,
   566,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=49b8f626",
  "width": 2048,
  "height": 1280,
  "bounds": [
   746,
   150,
   554,
   1080
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=e71a25da",
  "width": 2048,
  "height": 1280,
  "bounds": [
   746,
   148,
   566,
   1082
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_05": {
  "path": "img/field/characters/aidan/aidan_walk_down_05.png?v=29607ddf",
  "width": 2048,
  "height": 1280,
  "bounds": [
   746,
   152,
   562,
   1078
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_06": {
  "path": "img/field/characters/aidan/aidan_walk_down_06.png?v=5a35663f",
  "width": 2048,
  "height": 1280,
  "bounds": [
   746,
   158,
   574,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=7f69bd3c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   931,
   166,
   587,
   1064
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=86fca76f",
  "width": 2048,
  "height": 1280,
  "bounds": [
   931,
   152,
   619,
   1078
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=7f69bd3c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   931,
   166,
   587,
   1064
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=04a56b98",
  "width": 2048,
  "height": 1280,
  "bounds": [
   931,
   149,
   592,
   1081
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=a15864bb",
  "width": 2048,
  "height": 1280,
  "bounds": [
   931,
   145,
   610,
   1085
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_05": {
  "path": "img/field/characters/aidan/aidan_walk_left_05.png?v=50851ad3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   932,
   147,
   668,
   1083
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_06": {
  "path": "img/field/characters/aidan/aidan_walk_left_06.png?v=f5edb942",
  "width": 2048,
  "height": 1280,
  "bounds": [
   931,
   168,
   592,
   1062
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=690e6a10",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   166,
   587,
   1064
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=c52b5cfe",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   152,
   619,
   1078
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=690e6a10",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   166,
   587,
   1064
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=97cce417",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   149,
   592,
   1081
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=9ff77724",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   145,
   610,
   1085
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_05": {
  "path": "img/field/characters/aidan/aidan_walk_right_05.png?v=e465ba02",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   147,
   668,
   1083
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_06": {
  "path": "img/field/characters/aidan/aidan_walk_right_06.png?v=0fb332bf",
  "width": 2048,
  "height": 1280,
  "bounds": [
   530,
   168,
   592,
   1062
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=fbcece16",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   137,
   625,
   1093
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=fbcece16",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   137,
   625,
   1093
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=3ae66509",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
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
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=34110895",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   149,
   618,
   1081
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=c5d162a5",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   172,
   655,
   1058
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_05": {
  "path": "img/field/characters/aidan/aidan_walk_up_05.png?v=7797b09f",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   152,
   655,
   1078
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_06": {
  "path": "img/field/characters/aidan/aidan_walk_up_06.png?v=86ceff8a",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   172,
   719,
   1058
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
