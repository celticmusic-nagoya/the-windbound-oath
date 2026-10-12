/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=c23d16b8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   278,
   502,
   952
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=3fd08ef3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   778,
   263,
   494,
   967
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=c23d16b8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   278,
   502,
   952
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=1095dc3c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   271,
   492,
   959
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=5abdf1c6",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   269,
   502,
   961
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_05": {
  "path": "img/field/characters/aidan/aidan_walk_down_05.png?v=b1927d0a",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   272,
   499,
   958
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_06": {
  "path": "img/field/characters/aidan/aidan_walk_down_06.png?v=ce5d05c3",
  "width": 2048,
  "height": 1280,
  "bounds": [
   777,
   278,
   510,
   952
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=8c60a0e2",
  "width": 2048,
  "height": 1280,
  "bounds": [
   942,
   285,
   522,
   945
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=12c2525b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   942,
   272,
   549,
   958
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=8c60a0e2",
  "width": 2048,
  "height": 1280,
  "bounds": [
   942,
   285,
   522,
   945
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=50539788",
  "width": 2048,
  "height": 1280,
  "bounds": [
   942,
   270,
   525,
   960
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=db8638ef",
  "width": 2048,
  "height": 1280,
  "bounds": [
   942,
   266,
   542,
   964
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_05": {
  "path": "img/field/characters/aidan/aidan_walk_left_05.png?v=a517f5dd",
  "width": 2048,
  "height": 1280,
  "bounds": [
   943,
   268,
   593,
   962
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_06": {
  "path": "img/field/characters/aidan/aidan_walk_left_06.png?v=f35e435b",
  "width": 2048,
  "height": 1280,
  "bounds": [
   942,
   287,
   525,
   943
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=9d07852c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   285,
   522,
   945
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=ef2439d7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   272,
   549,
   958
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=9d07852c",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   285,
   522,
   945
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=08bb9e6d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   270,
   525,
   960
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=a34335f8",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   266,
   542,
   964
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_05": {
  "path": "img/field/characters/aidan/aidan_walk_right_05.png?v=fceca528",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   268,
   593,
   962
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_06": {
  "path": "img/field/characters/aidan/aidan_walk_right_06.png?v=aef85640",
  "width": 2048,
  "height": 1280,
  "bounds": [
   585,
   287,
   525,
   943
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=b164b5c5",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   260,
   555,
   970
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=b164b5c5",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   260,
   555,
   970
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=c6efc450",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   269,
   526,
   961
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=5581f5e9",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   270,
   548,
   960
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=c959850d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   290,
   582,
   940
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_05": {
  "path": "img/field/characters/aidan/aidan_walk_up_05.png?v=49c28e1d",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   272,
   582,
   958
  ],
  "anchor": [
   1024,
   1230
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_06": {
  "path": "img/field/characters/aidan/aidan_walk_up_06.png?v=456da3f7",
  "width": 2048,
  "height": 1280,
  "bounds": [
   775,
   290,
   639,
   940
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
