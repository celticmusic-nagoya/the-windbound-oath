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
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=744fdb45",
  "width": 2048,
  "height": 1280,
  "bounds": [
   729,
   155,
   830,
   1075
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=8fb04068",
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
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=d2722e16",
  "width": 2048,
  "height": 1280,
  "bounds": [
   766,
   162,
   772,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=093f6152",
  "width": 2048,
  "height": 1280,
  "bounds": [
   782,
   162,
   740,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_05": {
  "path": "img/field/characters/aidan/aidan_walk_left_05.png?v=f5763c3d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   740,
   162,
   813,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_06": {
  "path": "img/field/characters/aidan/aidan_walk_left_06.png?v=0544b56b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   782,
   161,
   756,
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
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=66dff837",
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
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=bf72d2a3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   532,
   158,
   798,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=4d0d48c1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   534,
   162,
   787,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=30067b09",
  "width": 2048,
  "height": 1280,
  "bounds": [
   572,
   162,
   651,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_05": {
  "path": "img/field/characters/aidan/aidan_walk_right_05.png?v=4853c76e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   529,
   158,
   773,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_06": {
  "path": "img/field/characters/aidan/aidan_walk_right_06.png?v=64e2bcb6",
  "width": 2048,
  "height": 1280,
  "bounds": [
   522,
   161,
   853,
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
