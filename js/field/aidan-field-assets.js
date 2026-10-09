/* A1 standalone field assets. Explicit foot registration; no battle paths. */
(function () {
  "use strict";
  if (!window.WINDBOUND_DEV) return;
  const frames = {
  "aidan_idle_down": {
    "path": "img/field/characters/aidan/aidan_idle_down.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      468,
      144,
      601,
      759
    ],
    "anchor": [
      768,
      903
    ],
    "scale": 0.057971014492753624
  },
  "aidan_idle_left": {
    "path": "img/field/characters/aidan/aidan_idle_left.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      490,
      82,
      592,
      854
    ],
    "anchor": [
      768,
      936
    ],
    "scale": 0.05152224824355972
  },
  "aidan_idle_right": {
    "path": "img/field/characters/aidan/aidan_idle_right.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      470,
      90,
      598,
      857
    ],
    "anchor": [
      768,
      947
    ],
    "scale": 0.051341890315052506
  },
  "aidan_idle_up": {
    "path": "img/field/characters/aidan/aidan_idle_up.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      436,
      115,
      642,
      794
    ],
    "anchor": [
      768,
      909
    ],
    "scale": 0.055415617128463476
  },
  "aidan_walk_down_01": {
    "path": "img/field/characters/aidan/aidan_walk_down_01.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      463,
      144,
      610,
      773
    ],
    "anchor": [
      768,
      917
    ],
    "scale": 0.056921086675291076
  },
  "aidan_walk_down_02": {
    "path": "img/field/characters/aidan/aidan_walk_down_02.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      471,
      144,
      595,
      772
    ],
    "anchor": [
      768,
      916
    ],
    "scale": 0.05699481865284974
  },
  "aidan_walk_down_03": {
    "path": "img/field/characters/aidan/aidan_walk_down_03.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      437,
      103,
      666,
      816
    ],
    "anchor": [
      768,
      919
    ],
    "scale": 0.05392156862745098
  },
  "aidan_walk_down_04": {
    "path": "img/field/characters/aidan/aidan_walk_down_04.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      467,
      144,
      614,
      781
    ],
    "anchor": [
      768,
      925
    ],
    "scale": 0.056338028169014086
  },
  "aidan_walk_left_01": {
    "path": "img/field/characters/aidan/aidan_walk_left_01.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      483,
      82,
      643,
      845
    ],
    "anchor": [
      768,
      927
    ],
    "scale": 0.05207100591715976
  },
  "aidan_walk_left_02": {
    "path": "img/field/characters/aidan/aidan_walk_left_02.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      489,
      79,
      596,
      848
    ],
    "anchor": [
      768,
      927
    ],
    "scale": 0.05188679245283019
  },
  "aidan_walk_left_03": {
    "path": "img/field/characters/aidan/aidan_walk_left_03.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      464,
      82,
      726,
      851
    ],
    "anchor": [
      768,
      933
    ],
    "scale": 0.05170387779083431
  },
  "aidan_walk_left_04": {
    "path": "img/field/characters/aidan/aidan_walk_left_04.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      495,
      69,
      587,
      846
    ],
    "anchor": [
      768,
      915
    ],
    "scale": 0.05200945626477541
  },
  "aidan_walk_right_01": {
    "path": "img/field/characters/aidan/aidan_walk_right_01.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      428,
      91,
      617,
      846
    ],
    "anchor": [
      768,
      937
    ],
    "scale": 0.05200945626477541
  },
  "aidan_walk_right_02": {
    "path": "img/field/characters/aidan/aidan_walk_right_02.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      467,
      88,
      592,
      842
    ],
    "anchor": [
      768,
      930
    ],
    "scale": 0.052256532066508314
  },
  "aidan_walk_right_03": {
    "path": "img/field/characters/aidan/aidan_walk_right_03.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      427,
      75,
      582,
      864
    ],
    "anchor": [
      768,
      939
    ],
    "scale": 0.05092592592592592
  },
  "aidan_walk_right_04": {
    "path": "img/field/characters/aidan/aidan_walk_right_04.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      467,
      88,
      570,
      841
    ],
    "anchor": [
      768,
      929
    ],
    "scale": 0.052318668252080855
  },
  "aidan_walk_up_01": {
    "path": "img/field/characters/aidan/aidan_walk_up_01.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      458,
      93,
      620,
      841
    ],
    "anchor": [
      768,
      934
    ],
    "scale": 0.052318668252080855
  },
  "aidan_walk_up_02": {
    "path": "img/field/characters/aidan/aidan_walk_up_02.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      427,
      51,
      674,
      907
    ],
    "anchor": [
      768,
      958
    ],
    "scale": 0.04851157662624035
  },
  "aidan_walk_up_03": {
    "path": "img/field/characters/aidan/aidan_walk_up_03.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      403,
      95,
      669,
      821
    ],
    "anchor": [
      768,
      916
    ],
    "scale": 0.0535931790499391
  },
  "aidan_walk_up_04": {
    "path": "img/field/characters/aidan/aidan_walk_up_04.png",
    "width": 1536,
    "height": 1024,
    "bounds": [
      431,
      71,
      647,
      872
    ],
    "anchor": [
      768,
      943
    ],
    "scale": 0.05045871559633028
  }
};
  Object.values(frames).forEach(Object.freeze);
  window.AidanFieldAssets = Object.freeze({frames:Object.freeze(frames)});
})();
