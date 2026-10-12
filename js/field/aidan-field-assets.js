/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=8f68deed",
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
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=0a212c37",
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
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=8f68deed",
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
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=e2ecb7e1",
  "width": 2048,
  "height": 1280,
  "bounds": [
   756,
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
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=3bb217c8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   750,
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
  "path": "img/field/characters/aidan/aidan_walk_down_05.png?v=45536fec",
  "width": 2048,
  "height": 1280,
  "bounds": [
   752,
   152,
   563,
   1078
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_06": {
  "path": "img/field/characters/aidan/aidan_walk_down_06.png?v=f8405a11",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   158,
   575,
   1072
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=59587de7",
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
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=261ee6c4",
  "width": 2048,
  "height": 1280,
  "bounds": [
   884,
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
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=59587de7",
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
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=6c30a13c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   930,
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
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=552f74fa",
  "width": 2048,
  "height": 1280,
  "bounds": [
   932,
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
  "path": "img/field/characters/aidan/aidan_walk_left_05.png?v=b2e8ed16",
  "width": 2048,
  "height": 1280,
  "bounds": [
   868,
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
  "path": "img/field/characters/aidan/aidan_walk_left_06.png?v=607b4307",
  "width": 2048,
  "height": 1280,
  "bounds": [
   925,
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
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=4f5664a0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   529,
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
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=d1d1140d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   545,
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
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=4f5664a0",
  "width": 2048,
  "height": 1280,
  "bounds": [
   529,
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
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=770703cd",
  "width": 2048,
  "height": 1280,
  "bounds": [
   526,
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
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=eb76184d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   506,
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
  "path": "img/field/characters/aidan/aidan_walk_right_05.png?v=4a9902e2",
  "width": 2048,
  "height": 1280,
  "bounds": [
   512,
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
  "path": "img/field/characters/aidan/aidan_walk_right_06.png?v=2dd95f9c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   531,
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
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=6b171125",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   138,
   625,
   1092
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=6b171125",
  "width": 2048,
  "height": 1280,
  "bounds": [
   743,
   138,
   625,
   1092
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=57fc7a83",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
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
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=d332160b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   756,
   149,
   617,
   1081
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=774322ec",
  "width": 2048,
  "height": 1280,
  "bounds": [
   747,
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
  "path": "img/field/characters/aidan/aidan_walk_up_05.png?v=59eb3d72",
  "width": 2048,
  "height": 1280,
  "bounds": [
   738,
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
  "path": "img/field/characters/aidan/aidan_walk_up_06.png?v=2a52431e",
  "width": 2048,
  "height": 1280,
  "bounds": [
   708,
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
