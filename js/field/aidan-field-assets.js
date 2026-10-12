/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=123461fb",
  "width": 2048,
  "height": 1280,
  "bounds": [
   599,
   158,
   745,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=7ce54991",
  "width": 2048,
  "height": 1280,
  "bounds": [
   596,
   157,
   755,
   1073
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=f4a9a1ff",
  "width": 2048,
  "height": 1280,
  "bounds": [
   588,
   156,
   783,
   1074
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=5ae337cc",
  "width": 2048,
  "height": 1280,
  "bounds": [
   590,
   159,
   787,
   1071
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=c1c73ee3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   578,
   159,
   798,
   1071
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=8fb04068",
  "width": 2048,
  "height": 1280,
  "bounds": [
   817,
   154,
   748,
   1076
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=171b7e11",
  "width": 2048,
  "height": 1280,
  "bounds": [
   906,
   160,
   562,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=8b7b9056",
  "width": 2048,
  "height": 1280,
  "bounds": [
   967,
   160,
   408,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=c51c154b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   971,
   161,
   389,
   1069
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=2f4c4257",
  "width": 2048,
  "height": 1280,
  "bounds": [
   887,
   160,
   566,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_05": {
  "path": "img/field/characters/aidan/aidan_walk_left_05.png?v=0b39c895",
  "width": 2048,
  "height": 1280,
  "bounds": [
   897,
   161,
   475,
   1069
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_06": {
  "path": "img/field/characters/aidan/aidan_walk_left_06.png?v=2d98f5aa",
  "width": 2048,
  "height": 1280,
  "bounds": [
   952,
   161,
   397,
   1069
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=66dff837",
  "width": 2048,
  "height": 1280,
  "bounds": [
   547,
   155,
   746,
   1075
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=1a04ecd3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   607,
   160,
   562,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=4edcf188",
  "width": 2048,
  "height": 1280,
  "bounds": [
   699,
   160,
   408,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=301a1711",
  "width": 2048,
  "height": 1280,
  "bounds": [
   714,
   161,
   389,
   1069
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=f602f1a2",
  "width": 2048,
  "height": 1280,
  "bounds": [
   621,
   160,
   566,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_05": {
  "path": "img/field/characters/aidan/aidan_walk_right_05.png?v=22ae8ddb",
  "width": 2048,
  "height": 1280,
  "bounds": [
   702,
   161,
   475,
   1069
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_06": {
  "path": "img/field/characters/aidan/aidan_walk_right_06.png?v=943f3e70",
  "width": 2048,
  "height": 1280,
  "bounds": [
   726,
   161,
   397,
   1069
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=5071a53c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   664,
   164,
   766,
   1066
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=b5c433d1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   658,
   157,
   776,
   1073
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=5071a53c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   664,
   164,
   766,
   1066
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=e9a4435c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   662,
   150,
   765,
   1080
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=671a23c1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   664,
   159,
   762,
   1071
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
