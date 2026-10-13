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
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=c3bc0082",
  "width": 2048,
  "height": 1280,
  "bounds": [
   660,
   126,
   667,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=b26cdaeb",
  "width": 2048,
  "height": 1280,
  "bounds": [
   863,
   126,
   664,
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
 "aidan_walk_dl_01": {
  "path": "img/field/characters/aidan/aidan_walk_dl_01.png?v=c8b97d09",
  "width": 2048,
  "height": 1280,
  "bounds": [
   831,
   122,
   598,
   1107
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_02": {
  "path": "img/field/characters/aidan/aidan_walk_dl_02.png?v=87c239f3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   788,
   123,
   661,
   1106
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_03": {
  "path": "img/field/characters/aidan/aidan_walk_dl_03.png?v=39e276e4",
  "width": 2048,
  "height": 1280,
  "bounds": [
   840,
   128,
   597,
   1101
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_04": {
  "path": "img/field/characters/aidan/aidan_walk_dl_04.png?v=6c80ebd0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   841,
   129,
   612,
   1100
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_05": {
  "path": "img/field/characters/aidan/aidan_walk_dl_05.png?v=d6d28209",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   113,
   679,
   1116
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_06": {
  "path": "img/field/characters/aidan/aidan_walk_dl_06.png?v=b7460dd4",
  "width": 2048,
  "height": 1280,
  "bounds": [
   748,
   108,
   697,
   1121
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_07": {
  "path": "img/field/characters/aidan/aidan_walk_dl_07.png?v=b8ace7dd",
  "width": 2048,
  "height": 1280,
  "bounds": [
   821,
   140,
   620,
   1089
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_08": {
  "path": "img/field/characters/aidan/aidan_walk_dl_08.png?v=7e254314",
  "width": 2048,
  "height": 1280,
  "bounds": [
   788,
   132,
   675,
   1097
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_09": {
  "path": "img/field/characters/aidan/aidan_walk_dl_09.png?v=9b8c7075",
  "width": 2048,
  "height": 1280,
  "bounds": [
   813,
   136,
   635,
   1093
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_10": {
  "path": "img/field/characters/aidan/aidan_walk_dl_10.png?v=e4d82d55",
  "width": 2048,
  "height": 1280,
  "bounds": [
   751,
   110,
   714,
   1119
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_11": {
  "path": "img/field/characters/aidan/aidan_walk_dl_11.png?v=9ad0b063",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   134,
   687,
   1095
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_dl_12": {
  "path": "img/field/characters/aidan/aidan_walk_dl_12.png?v=af251b7e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   805,
   141,
   627,
   1088
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=37139065",
  "width": 2048,
  "height": 1280,
  "bounds": [
   679,
   127,
   832,
   1103
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=bec8540a",
  "width": 2048,
  "height": 1280,
  "bounds": [
   647,
   127,
   924,
   1103
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=b5a88f08",
  "width": 2048,
  "height": 1280,
  "bounds": [
   665,
   126,
   889,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=7a3a64a0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   665,
   126,
   899,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_05": {
  "path": "img/field/characters/aidan/aidan_walk_down_05.png?v=2e1cafe1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   673,
   128,
   904,
   1102
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_06": {
  "path": "img/field/characters/aidan/aidan_walk_down_06.png?v=bfd1db5d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   668,
   126,
   856,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=d453729e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   823,
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
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=336ee5e8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   893,
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
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=9fae61f0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   866,
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
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=852f9183",
  "width": 2048,
  "height": 1280,
  "bounds": [
   921,
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
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=239a2e0c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   733,
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
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=c0474f60",
  "width": 2048,
  "height": 1280,
  "bounds": [
   773,
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
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=6e275fa0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   763,
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
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=4b795b21",
  "width": 2048,
  "height": 1280,
  "bounds": [
   756,
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
 "aidan_walk_ul_01": {
  "path": "img/field/characters/aidan/aidan_walk_ul_01.png?v=5b102933",
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
 "aidan_walk_ul_02": {
  "path": "img/field/characters/aidan/aidan_walk_ul_02.png?v=4cecda50",
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
 "aidan_walk_ul_03": {
  "path": "img/field/characters/aidan/aidan_walk_ul_03.png?v=38f05cfc",
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
 "aidan_walk_ul_04": {
  "path": "img/field/characters/aidan/aidan_walk_ul_04.png?v=195c9a8c",
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
 "aidan_walk_ul_05": {
  "path": "img/field/characters/aidan/aidan_walk_ul_05.png?v=33d5cf9a",
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
 "aidan_walk_ul_06": {
  "path": "img/field/characters/aidan/aidan_walk_ul_06.png?v=282e82a9",
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
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=04655d6d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   621,
   126,
   902,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=1f8d7b36",
  "width": 2048,
  "height": 1280,
  "bounds": [
   590,
   127,
   915,
   1103
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=68ec13e6",
  "width": 2048,
  "height": 1280,
  "bounds": [
   604,
   126,
   893,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=9857415d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   608,
   126,
   919,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_05": {
  "path": "img/field/characters/aidan/aidan_walk_up_05.png?v=131926e7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   597,
   126,
   937,
   1104
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_06": {
  "path": "img/field/characters/aidan/aidan_walk_up_06.png?v=7a835a97",
  "width": 2048,
  "height": 1280,
  "bounds": [
   621,
   126,
   887,
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
