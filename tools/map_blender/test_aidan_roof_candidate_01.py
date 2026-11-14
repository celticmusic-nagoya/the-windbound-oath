"""Static safeguards for Aidan roof candidate; does not require Blender."""
from pathlib import Path
s=Path(__file__).with_name("aidan_roof_candidate_01.py").read_text()
assert 'random.Random(SEED)' in s
assert 'RoofShell_' in s and 'Fascia_' in s and 'RidgeCap_' in s
assert 'if bpy.data.collections.get(COLLECTION)' in s
assert 'GEOMETRY_CANDIDATE_NO_PBR_OR_ART_APPROVAL' in s
assert 'rows=15' in s and 'segments=14' in s
assert 'roof_angle_degrees' in s
print("PASS: deterministic candidate, shell+trim, non-overwrite guard, no false art approval")
