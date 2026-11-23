"""Evidence classes. Every value in a blueprint carries exactly one."""

NATIVE_MEASURED = "NATIVE_MEASURED"                    # measured in the native file (Blender/VRoid)
OFFICIAL_SOURCE_MEASURED = "OFFICIAL_SOURCE_MEASURED"  # pixel-exact on an SHA-verified official source
RECONSTRUCTED = "RECONSTRUCTED"                        # derived from >=2 registered views by a named method
ESTIMATED = "ESTIMATED"                                # manual/visual estimate with stated uncertainty
PROVISIONAL_DESIGN = "PROVISIONAL_DESIGN"              # design decision, not measured, not canon
UNDETERMINED = "UNDETERMINED"                          # unknown; no value may be asserted

CLASSES = (NATIVE_MEASURED, OFFICIAL_SOURCE_MEASURED, RECONSTRUCTED, ESTIMATED,
           PROVISIONAL_DESIGN, UNDETERMINED)
TARGET_ELIGIBLE = frozenset(CLASSES) - {UNDETERMINED}
OBSERVATION_ELIGIBLE = frozenset({NATIVE_MEASURED, OFFICIAL_SOURCE_MEASURED})
MEASURED = OBSERVATION_ELIGIBLE

ROLES = ("OFFICIAL_CANON", "APPROVED_REFERENCE", "CANDIDATE", "REFERENCE", "VERIFICATION",
         "NATIVE_WORKING")
PROJECTIONS = {"orthographic-2d": 2, "perspective-2d": 2, "image-2d-uncalibrated": 2,
               "native-3d": 3, "data": 0}
VISIBILITY = ("visible", "partial", "estimated", "occluded", "hidden")
