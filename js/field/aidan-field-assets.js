/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png?v=8eb8c6cb",
  "width": 1536,
  "height": 1024,
  "bounds": [
   425,
   96,
   601,
   864
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png?v=94105b02",
  "width": 1536,
  "height": 1024,
  "bounds": [
   419,
   249,
   777,
   711
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png?v=8eb8c6cb",
  "width": 1536,
  "height": 1024,
  "bounds": [
   425,
   96,
   601,
   864
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png?v=94105b02",
  "width": 1536,
  "height": 1024,
  "bounds": [
   419,
   249,
   777,
   711
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png?v=8eb8c6cb",
  "width": 1536,
  "height": 1024,
  "bounds": [
   425,
   96,
   601,
   864
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png?v=35a04663",
  "width": 1536,
  "height": 1024,
  "bounds": [
   681,
   258,
   768,
   702
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png?v=8fd08822",
  "width": 1536,
  "height": 1024,
  "bounds": [
   680,
   264,
   767,
   696
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png?v=7ccf4cb7",
  "width": 1536,
  "height": 1024,
  "bounds": [
   676,
   262,
   771,
   698
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png?v=35a04663",
  "width": 1536,
  "height": 1024,
  "bounds": [
   681,
   258,
   768,
   702
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png?v=b4675166",
  "width": 1536,
  "height": 1024,
  "bounds": [
   677,
   254,
   773,
   706
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png?v=6ee8a0af",
  "width": 1536,
  "height": 1024,
  "bounds": [
   87,
   258,
   768,
   702
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png?v=815e555d",
  "width": 1536,
  "height": 1024,
  "bounds": [
   89,
   264,
   767,
   696
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png?v=e49b1cb1",
  "width": 1536,
  "height": 1024,
  "bounds": [
   89,
   262,
   771,
   698
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png?v=6ee8a0af",
  "width": 1536,
  "height": 1024,
  "bounds": [
   87,
   258,
   768,
   702
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png?v=58d1cab2",
  "width": 1536,
  "height": 1024,
  "bounds": [
   85,
   254,
   773,
   706
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png?v=6a06d0a3",
  "width": 1536,
  "height": 1024,
  "bounds": [
   518,
   250,
   777,
   710
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png?v=6a06d0a3",
  "width": 1536,
  "height": 1024,
  "bounds": [
   518,
   250,
   777,
   710
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png?v=5cb8c59f",
  "width": 1536,
  "height": 1024,
  "bounds": [
   523,
   260,
   771,
   700
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png?v=6a06d0a3",
  "width": 1536,
  "height": 1024,
  "bounds": [
   518,
   250,
   777,
   710
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png?v=5cb8c59f",
  "width": 1536,
  "height": 1024,
  "bounds": [
   523,
   260,
   771,
   700
  ],
  "anchor": [
   768,
   960
  ],
  "scale": 0.0625
 }
};
  Object.values(frames).forEach(Object.freeze);
  window.AidanFieldAssets = Object.freeze({frames:Object.freeze(frames)});
})();
