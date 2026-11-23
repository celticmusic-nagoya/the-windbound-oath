"""Morwen Layer0 hair: manually placed 2D lock centrelines on the verified four-view originals (artifact 14602858760,
run 44679568515; 384x1024 px, origin top-left, x right, y down, unmirrored). Placement on 4x/8x enlarged crops.
IDs are character-side: CR = character right (front image-left, back image-right, 'right' view 7807),
CL = character left. Points are root -> tip. unc = estimated placement radius in px (not a statistical interval).
w_mid = projected visible width at mid-length where both lock boundaries are drawn; None = boundary not visible."""

VIEWS = {"front": ("7809.png", "b0a5d9f6c77c4a73a9f8bcca3dd2d8acad62403f374e04ebb2b0cb9b1b1199ed"),
         "right": ("7807.png", "9f4873cf331f55b72510159412bd0bfc4c606499f792626e03cffcdace7bf737"),
         "back": ("7810.png", "b9d6d6667be8d9bbed1538a42cbaea0e51bab68371366962e43463fbe394976f"),
         "left": ("7808.png", "69f23ce23cf9c56228e1e4d9a23fbab6b6607456a35239c853718a84da2298fa")}

# id: (region, {view: (points, unc_px, w_mid_px or None)})
LOCKS = {
 # fringe: fans from the forehead parting point (front 213,33) under the crown notch (213,21)
 "BG_C":   ("fringe", {"front": ([(213, 33), (211, 75), (203, 116)], 3, 22)}),
 "BG_C2":  ("fringe", {"front": ([(216, 34), (222, 70), (222, 104)], 3, 12)}),
 "BG_CR1": ("fringe", {"front": ([(205, 35), (197, 60), (192, 90), (190, 112)], 3, 14)}),
 "BG_CR2": ("fringe", {"front": ([(198, 36), (182, 55), (172, 85), (167, 112)], 4, 16),
                       "right": ([(228, 30), (262, 48), (282, 78), (264, 113)], 5, None)}),
 "BG_CL1": ("fringe", {"front": ([(222, 36), (232, 60), (236, 85), (232, 104)], 3, 12)}),
 "BG_CL2": ("fringe", {"front": ([(229, 38), (246, 58), (254, 85), (258, 112)], 4, 16),
                       "left": ([(165, 30), (132, 48), (114, 78), (120, 109)], 5, None)}),
 # face-framing locks in front of the ear
 "FF_CR":  ("temple", {"front": ([(170, 62), (160, 100), (162, 140), (178, 184)], 4, 16),
                       "right": ([(220, 62), (212, 110), (213, 150), (228, 190)], 4, 20)}),
 "FF_CL":  ("temple", {"front": ([(254, 62), (264, 100), (262, 140), (248, 178)], 4, 16),
                       "left": ([(160, 62), (154, 100), (147, 140), (136, 190)], 4, 20)}),
 # side mass behind the ear (outer contour in the front view)
 "SD_CR":  ("side", {"front": ([(180, 28), (146, 75), (128, 130), (134, 182)], 6, None),
                     "right": ([(200, 40), (188, 100), (186, 150), (196, 190)], 5, None)}),
 "SD_CL":  ("side", {"front": ([(240, 28), (274, 75), (292, 130), (288, 182)], 6, None),
                     "left": ([(180, 40), (190, 100), (192, 150), (186, 190)], 5, None)}),
 # loose outer strands / hem flicks (correspondence across views is probable, not certain)
 "FL_CR":  ("flick", {"front": ([(122, 100), (116, 150), (124, 175)], 4, 4),
                      "right": ([(110, 110), (96, 150), (100, 182)], 5, 5),
                      "back": ([(248, 95), (258, 130), (262, 160)], 5, 5)}),
 "FL_CL":  ("flick", {"front": ([(288, 140), (300, 165), (296, 185)], 4, 5),
                      "left": ([(255, 100), (270, 140), (268, 165)], 5, 5),
                      "back": ([(84, 110), (74, 150), (80, 172)], 6, 5)}),
 # back: radiates from the whorl (back 170,28); centre pair forms the nape V notch (171,197)
 "BK_C_CL": ("back", {"back": ([(168, 32), (164, 90), (164, 150), (168, 197)], 4, 14)}),
 "BK_C_CR": ("back", {"back": ([(173, 32), (176, 90), (177, 150), (172, 197)], 4, 14)}),
 "BK_CR1": ("back", {"back": ([(178, 32), (198, 90), (208, 150), (206, 190)], 5, 26)}),
 "BK_CR2": ("back", {"back": ([(186, 32), (222, 85), (238, 140), (234, 188)], 5, 26)}),
 "BK_CR3": ("back", {"back": ([(196, 30), (240, 75), (262, 130), (258, 182)], 5, 24),
                     "right": ([(165, 28), (125, 85), (104, 140), (112, 185)], 5, None)}),
 "BK_CL1": ("back", {"back": ([(163, 32), (146, 90), (136, 150), (136, 190)], 5, 26)}),
 "BK_CL2": ("back", {"back": ([(156, 32), (122, 85), (106, 140), (108, 188)], 5, 26)}),
 "BK_CL3": ("back", {"back": ([(146, 30), (104, 75), (82, 130), (84, 180)], 5, 24),
                     "left": ([(205, 28), (245, 80), (265, 130), (258, 182)], 5, None)}),
 # nape under-layer at the hem (side views)
 "NP_CR":  ("nape", {"right": ([(150, 70), (138, 130), (143, 170), (151, 191)], 5, None)}),
 "NP_CL":  ("nape", {"left": ([(225, 70), (238, 130), (240, 170), (245, 189)], 5, None)}),
}

POINTS = {  # single observed features
 "crown_notch_front": ("front", (213, 21), 2), "parting_point_front": ("front", (213, 33), 3),
 "whorl_back": ("back", (170, 28), 3), "nape_notch_back": ("back", (171, 197), 3),
 "crown_right": ("right", (196, 16), 2), "crown_left": ("left", (181, 16), 2),
 "ear_right": ("right", (195, 125), 3), "ear_left": ("left", (182, 125), 3),
 "hem_front_CR": ("front", (148, 190), 4), "hem_front_CL": ("front", (277, 189), 4),
 "fringe_tip_front": ("front", (203, 116), 4), "chin_front": ("front", (214, 180), 3),
}
