/* Aidan standalone field assets (tools/field/install_hero_frames.py): one shared scale + feet anchor. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
 "aidan_idle_down": {
  "path": "img/field/characters/aidan/aidan_idle_down.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   360,
   36,
   490,
   704
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_01": {
  "path": "img/field/characters/aidan/aidan_walk_down_01.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   356,
   161,
   633,
   579
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_02": {
  "path": "img/field/characters/aidan/aidan_walk_down_02.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   360,
   36,
   490,
   704
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_03": {
  "path": "img/field/characters/aidan/aidan_walk_down_03.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   356,
   161,
   633,
   579
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_down_04": {
  "path": "img/field/characters/aidan/aidan_walk_down_04.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   360,
   36,
   490,
   704
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_idle_left": {
  "path": "img/field/characters/aidan/aidan_idle_left.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   569,
   168,
   626,
   572
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_01": {
  "path": "img/field/characters/aidan/aidan_walk_left_01.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   568,
   173,
   625,
   567
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_02": {
  "path": "img/field/characters/aidan/aidan_walk_left_02.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   565,
   171,
   628,
   569
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_03": {
  "path": "img/field/characters/aidan/aidan_walk_left_03.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   569,
   168,
   626,
   572
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_left_04": {
  "path": "img/field/characters/aidan/aidan_walk_left_04.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   566,
   165,
   630,
   575
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_idle_right": {
  "path": "img/field/characters/aidan/aidan_idle_right.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   85,
   168,
   626,
   572
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_01": {
  "path": "img/field/characters/aidan/aidan_walk_right_01.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   87,
   173,
   625,
   567
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_02": {
  "path": "img/field/characters/aidan/aidan_walk_right_02.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   87,
   171,
   628,
   569
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_03": {
  "path": "img/field/characters/aidan/aidan_walk_right_03.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   85,
   168,
   626,
   572
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_right_04": {
  "path": "img/field/characters/aidan/aidan_walk_right_04.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   84,
   165,
   630,
   575
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_idle_up": {
  "path": "img/field/characters/aidan/aidan_idle_up.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   436,
   161,
   633,
   579
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_01": {
  "path": "img/field/characters/aidan/aidan_walk_up_01.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   436,
   161,
   633,
   579
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_02": {
  "path": "img/field/characters/aidan/aidan_walk_up_02.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   440,
   170,
   629,
   570
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_03": {
  "path": "img/field/characters/aidan/aidan_walk_up_03.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   436,
   161,
   633,
   579
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 },
 "aidan_walk_up_04": {
  "path": "img/field/characters/aidan/aidan_walk_up_04.png",
  "width": 1280,
  "height": 800,
  "bounds": [
   440,
   170,
   629,
   570
  ],
  "anchor": [
   640,
   740
  ],
  "scale": 0.0625
 }
};
  Object.values(frames).forEach(Object.freeze);
  window.AidanFieldAssets = Object.freeze({frames:Object.freeze(frames)});
})();
