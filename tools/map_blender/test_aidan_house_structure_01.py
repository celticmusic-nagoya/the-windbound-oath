"""Static structural-cage invariants, no Blender installation required."""
import ast,pathlib
p=pathlib.Path(__file__).with_name("aidan_house_structural_cage_01.py")
tree=ast.parse(p.read_text())
d=next(n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=="D" for t in n.targets))
values=ast.literal_eval(d.value)
assert values["length"]>2*values["wall_thickness"]
assert values["width"]>2*values["wall_thickness"]
assert values["wall_top"]>values["door_height"]>0
assert values["ridge_z"]>values["wall_top"]
assert values["door_width"]<values["length"]-2*values["wall_thickness"]
assert values["roof_overhang"]>0
assert any(isinstance(n,ast.FunctionDef) and n.name=="build" for n in tree.body)
# Eave beams must run along the X ridge, not the gable ends.
source=p.read_text()
assert 'for y in (-W,W):' in source
assert 'box(c,"eave beam %s"%y,-L-.30,L+.30' in source
print("PASS: structural cage dimensions and eave/ridge alignment (not mesh/render QA)")

