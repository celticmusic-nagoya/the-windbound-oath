/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=b111bd98",
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
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=ac18d630",
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
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=49b8dbf6",
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
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=2198052a",
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
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=bf230b15",
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
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=9b3f8ef5",
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
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=aef6db0e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   765,
   162,
   733,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=93c1d490",
  "width": 2048,
  "height": 1280,
  "bounds": [
   864,
   160,
   638,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=b2e07787",
  "width": 2048,
  "height": 1280,
  "bounds": [
   925,
   160,
   534,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=86709ec7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   838,
   160,
   678,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=4a3be66f",
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
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=28b1cc3b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   576,
   162,
   733,
   1068
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=a360d5fd",
  "width": 2048,
  "height": 1280,
  "bounds": [
   573,
   160,
   638,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=73656fbf",
  "width": 2048,
  "height": 1280,
  "bounds": [
   616,
   160,
   534,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=10cdd07f",
  "width": 2048,
  "height": 1280,
  "bounds": [
   558,
   160,
   678,
   1070
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=d72e5ec5",
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
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=9d0c49a7",
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
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=d72e5ec5",
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
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=30c90b88",
  "width": 2048,
  "height": 1280,
  "bounds": [
   663,
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
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=083ae706",
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
