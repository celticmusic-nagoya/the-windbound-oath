/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=0af6b2e7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   733,
   126,
   738,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=7f909159",
  "width": 2048,
  "height": 1280,
  "bounds": [
   844,
   126,
   541,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=885c51b8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   869,
   127,
   558,
   1103
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=dd8c6814",
  "width": 2048,
  "height": 1280,
  "bounds": [
   888,
   126,
   547,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=7909b152",
  "width": 2048,
  "height": 1280,
  "bounds": [
   876,
   126,
   514,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_05": {
  "path": "img/field/characters/aidan/aidan_walk_down_05.png?v=4b31861a",
  "width": 2048,
  "height": 1280,
  "bounds": [
   887,
   126,
   540,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_06": {
  "path": "img/field/characters/aidan/aidan_walk_down_06.png?v=55e69c60",
  "width": 2048,
  "height": 1280,
  "bounds": [
   888,
   126,
   537,
   1104
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
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=0c5711d5",
  "width": 2048,
  "height": 1280,
  "bounds": [
   862,
   126,
   623,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=87c87672",
  "width": 2048,
  "height": 1280,
  "bounds": [
   932,
   126,
   512,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=483da079",
  "width": 2048,
  "height": 1280,
  "bounds": [
   905,
   126,
   557,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=822bfa2b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   960,
   126,
   492,
   1104
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
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=4d211bee",
  "width": 2048,
  "height": 1280,
  "bounds": [
   646,
   126,
   622,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=eea0d238",
  "width": 2048,
  "height": 1280,
  "bounds": [
   686,
   126,
   553,
   1103
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=dd423665",
  "width": 2048,
  "height": 1280,
  "bounds": [
   676,
   126,
   531,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=95d11f9f",
  "width": 2048,
  "height": 1280,
  "bounds": [
   669,
   126,
   626,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=d626c812",
  "width": 2048,
  "height": 1280,
  "bounds": [
   794,
   126,
   670,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=1d527f86",
  "width": 2048,
  "height": 1280,
  "bounds": [
   831,
   126,
   606,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=1bd6c65e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   861,
   126,
   600,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=bcb96807",
  "width": 2048,
  "height": 1280,
  "bounds": [
   880,
   126,
   583,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=8cdfd050",
  "width": 2048,
  "height": 1280,
  "bounds": [
   864,
   126,
   585,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_05": {
  "path": "img/field/characters/aidan/aidan_walk_up_05.png?v=f64dc488",
  "width": 2048,
  "height": 1280,
  "bounds": [
   860,
   126,
   637,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_06": {
  "path": "img/field/characters/aidan/aidan_walk_up_06.png?v=b1eb8ef8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   873,
   126,
   661,
   1104
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
