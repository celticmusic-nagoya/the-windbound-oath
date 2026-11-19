"""Build the provisional Windwaiting Cliff C candidate from authored profiles."""
import argparse
import hashlib
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

# x along shore, seaward edge Y, crest height, abrasion shelf projection.
# The plan alternates headlands and recesses at deliberately uneven intervals.
SECTIONS = (
    (-8.8, -0.42, 5.55, 0.76), (-7.6, -0.93, 5.73, 0.84),
    (-6.1, -1.69, 5.89, 1.04), (-4.9, -1.76, 5.84, 0.78),
    (-3.9, -1.24, 5.91, 0.55), (-2.9, -1.62, 6.05, 0.67),
    (-1.7, -2.57, 6.13, 1.15), (-0.4, -2.83, 6.16, 0.96),
    (0.65, -2.63, 6.08, 0.80), (1.44, -2.18, 5.94, 0.65),
    (2.05, -1.59, 5.14, 0.57), (2.88, -1.52, 4.98, 0.82),
    (3.84, -1.77, 4.58, 0.91), (4.77, -1.43, 4.45, 0.77),
    (5.40, -0.90, 3.60, 0.84), (6.53, -0.65, 3.43, 0.70),
    (7.42, -0.22, 3.05, 0.74), (8.35, 0.25, 2.72, 0.83),
)
# Crest-to-foreshore profile. Positive offsets cut landwards. The negative
# offsets at the two ledges project over a recessed course and the wave notch.
PROFILE = (
    (1.000, 0.00), (0.977, -0.045), (0.941, -0.12), (0.905, -0.10),
    (0.867, 0.02), (0.840, 0.11), (0.793, 0.15), (0.760, 0.16),
    (0.731, 0.03), (0.704, -0.21), (0.672, -0.26), (0.650, -0.08),
    (0.616, 0.24), (0.566, 0.31), (0.504, 0.28), (0.455, 0.24),
    (0.410, 0.13), (0.379, 0.04), (0.350, 0.12), (0.315, 0.25),
    (0.267, 0.31), (0.216, 0.38), (0.184, 0.49), (0.156, 0.62),
    (0.137, 0.65), (0.115, 0.40), (0.098, 0.04), (0.078, -0.43),
    (0.052, -0.82), (0.025, -1.0),
)
FAULTS = (
    (-7.91,.07,.08,.12), (-7.41,-.19,.06,.17), (-6.90,.31,.05,.15),
    (-6.48,.12,.09,.24), (-5.71,-.30,.07,.24), (-5.40,.27,.05,.16),
    (-4.71,-.29,.06,.19), (-4.1,-.11,.092,.27), (-3.52,.38,.07,.17),
    (-3.14,.25,.05,.23), (-2.68,-.31,.08,.23), (-2.11,.22,.07,.21),
    (-1.52,-.25,.06,.16), (-.93,.16,.085,.29), (-.47,-.28,.06,.20),
    (.16,.17,.06,.17), (.68,-.14,.08,.28), (1.21,-.43,.091,.22),
    (1.80,.31,.06,.19), (2.43,.24,.078,.22), (3.04,-.31,.06,.15),
    (3.79,-.27,.075,.26), (4.37,.18,.06,.14), (5.14,-.20,.065,.20),
    (5.81,.32,.077,.18), (6.71,-.30,.065,.21), (7.45,.27,.078,.17),
)
CG = "assets/approved/game/cliff/sunset_background.png"
CG_SHA = "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07"
BODY = "Cliff C | swept bedrock"


def lerp(a, b, t):
    return a + (b - a) * t


def interpolate_section(x):
    for first, second in zip(SECTIONS, SECTIONS[1:]):
        if x <= second[0]:
            t = (x - first[0]) / (second[0] - first[0])
            t = t * t * (3 - 2 * t)
            return tuple(lerp(a, b, t) for a, b in zip(first[1:], second[1:]))
    return SECTIONS[-1][1:]


def make_section(x, end_weight):
    edge, crest, shelf = interpolate_section(x)
    # Each layer follows the nearly level crest across the main headland; the
    # shorter blocks toward the east step down with the surveyed silhouette.
    ring = []
    for inland in (5.0, 4.1, 3.2, 2.4, 1.64, 1.03, .56, .25, .10):
        roll = .055 * inland + .10 * math.exp(-((inland - 2.0) / 1.4) ** 2)
        ring.append((edge + inland, crest + roll))
    for k, (fraction, offset) in enumerate(PROFILE):
        split = 0.0
        for center, rake, width, depth in FAULTS:
            centerline = center + rake * (fraction - .5) + .045 * (fraction - .5) ** 2
            fade = min(1.0, 14 * (1 - fraction), 5 * fraction)
            split += depth * fade * math.exp(-((x - centerline) / width) ** 2)
        toe = min(1.0, max(0.0, (.15 - fraction) / .11))
        # Small hand-seeded relief varies between courses, bounded to the
        # seaward direction, keeping the section free of vertical foldovers.
        grit = (random.Random(round(x * 100000) + 1543 * k).random() - .5) * .061
        front = edge + offset + .25 * (1 - fraction) - shelf * toe
        front += end_weight * (split + grit * min(1, k / 3))
        z = crest * fraction
        ring.append((front, z))
    ring.extend(((edge - .63 * shelf, -.22), (edge + 5.0, -.22)))
    return ring


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def make_cliff(target, rock, turf, substrate):
    intervals = 340
    vertices, faces, slots = [], [], []
    rings = [
        make_section(lerp(SECTIONS[0][0], SECTIONS[-1][0], i / intervals), min(i, intervals - i, 5) / 5)
        for i in range(intervals + 1)
    ]
    size = len(rings[0])
    for i, ring in enumerate(rings):
        x = lerp(SECTIONS[0][0], SECTIONS[-1][0], i / intervals)
        vertices.extend((x, y, z) for y, z in ring)
    for i in range(intervals):
        for k in range(size):
            following = (k + 1) % size
            faces.append((i * size + k, (i + 1) * size + k,
                          (i + 1) * size + following, i * size + following))
            slots.append(1 if k < 8 else (2 if k >= size - 2 else 0))
    faces.extend((tuple(range(size - 1, -1, -1)),
                  tuple(intervals * size + k for k in range(size))))
    slots.extend((0, 0))
    mesh = bpy.data.meshes.new("Editable coastal sections")
    mesh.from_pydata(vertices, [], faces)
    mesh.update()
    for material in (rock, turf, substrate):
        mesh.materials.append(material)
    for face, slot in zip(mesh.polygons, slots):
        face.material_index = slot
        face.use_smooth = len(face.vertices) == 4 and slot != 2
    bm = bmesh.new()
    try:
        bm.from_mesh(mesh)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    mesh.update()
    obj = bpy.data.objects.new(BODY, mesh)
    target.objects.link(obj)
    obj["geometry_method"] = "authored XY shoreline and multi-valued vertical profile sweep"
    obj["coordinate_space"] = "asset-local-provisional"
    obj["contact_convention"] = "Z=0 provisional shoreline datum; closure descends below datum"
    return obj


def stone(name, colors, grass=False):
    material = bpy.data.materials.new(name)
    material.diffuse_color = (*colors[1], 1)
    material.use_nodes = True
    nodes, links = material.node_tree.nodes, material.node_tree.links
    shader = nodes.get("Principled BSDF")
    shader.inputs["Roughness"].default_value = .89
    position = nodes.new("ShaderNodeTexCoord")
    noise = nodes.new("ShaderNodeTexNoise")
    noise.inputs["Scale"].default_value = 2.4 if grass else 4.1
    noise.inputs["Detail"].default_value = 3
    links.new(position.outputs["Object"], noise.inputs["Vector"])
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].position = .20
    ramp.color_ramp.elements[0].color = (*colors[0], 1)
    ramp.color_ramp.elements[1].position = .77
    ramp.color_ramp.elements[1].color = (*colors[2], 1)
    ramp.color_ramp.elements.new(.50).color = (*colors[1], 1)
    links.new(noise.outputs["Fac"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], shader.inputs["Base Color"])
    grain = nodes.new("ShaderNodeTexNoise")
    grain.inputs["Scale"].default_value = 24 if grass else 34
    grain.inputs["Detail"].default_value = 3
    links.new(position.outputs["Object"], grain.inputs["Vector"])
    bump = nodes.new("ShaderNodeBump")
    bump.inputs["Strength"].default_value = .37
    bump.inputs["Distance"].default_value = .07
    links.new(grain.outputs["Fac"], bump.inputs["Height"])
    links.new(bump.outputs["Normal"], shader.inputs["Normal"])
    return material


def loose_rock(target, name, location, dimensions, material, seed):
    rng = random.Random(seed)
    bm = bmesh.new()
    try:
        bmesh.ops.create_icosphere(bm, subdivisions=2, radius=1)
        for vertex in bm.verts:
            co = vertex.co
            scale = rng.uniform(.77, 1.17)
            co.x *= dimensions[0] * scale
            co.y *= dimensions[1] * scale
            co.z *= dimensions[2] * scale
            co.x += .24 * co.z
        mesh = bpy.data.meshes.new(name)
        bm.to_mesh(mesh)
    finally:
        bm.free()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler.z = rng.uniform(-.65, .65)
    mesh.materials.append(material)


def aim(obj, point):
    obj.rotation_euler = (Vector(point) - obj.location).to_track_quat("-Z", "Y").to_euler()


def build_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene["coordinate_space"] = "asset-local-provisional"
    scene["unit_scale_status"] = "UNAPPROVED"
    scene["forward_axis"] = "-Y (sea)"
    scene["up_axis"] = "+Z"
    scene["visual_reference"] = CG
    scene["visual_reference_sha256"] = CG_SHA
    scene["production_status"] = "CANDIDATE_G2_REVIEW_PENDING"
    rock = stone("Slate and weathered limestone", ((.053,.061,.075),(.171,.164,.157),(.32,.282,.224)))
    turf = stone("Windward olive turf", ((.024,.049,.012),(.106,.145,.030),(.27,.25,.075)), grass=True)
    substrate = stone("Damp lower bedrock", ((.028,.039,.048),(.074,.087,.092),(.17,.155,.127)))
    make_cliff(collection("01 | Continuous cliff body"), rock, turf, substrate)
    stacks = collection("02 | Detached sea stacks")
    loose_rock(stacks, "Detached stack 01", (7.1, -3.42, .74), (.62,.48,1.10), rock, 524)
    loose_rock(stacks, "Detached stack 02", (8.44, -2.36, .33), (.54,.41,.65), rock, 526)
    talus = collection("03 | Talus modules")
    rng = random.Random(937)
    for i in range(15):
        x = rng.uniform(-7.5, 6.2)
        edge, _, shelf = interpolate_section(x)
        scale = rng.uniform(.12, .37)
        loose_rock(talus, f"Talus {i+1:02d}", (x, edge - 1.03 - shelf - rng.uniform(.04,.48), .34 * scale),
                   (1.35*scale, .88*scale, scale), rock, i + 33)

    review = collection("04 | Review cameras and lighting")
    world = bpy.data.worlds.new("Cool maritime fill")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs[0].default_value = (.29,.39,.57,1)
    world.node_tree.nodes.get("Background").inputs[1].default_value = .36
    scene.world = world
    sun = bpy.data.lights.new("Grazing warm key", "SUN")
    sun.energy = 2.35
    sun.angle = math.radians(11)
    sun.color = (1,.79,.53)
    light = bpy.data.objects.new(sun.name, sun)
    review.objects.link(light)
    light.location = (9,-6,6)
    aim(light, (0,0,1))
    cameras = {}
    for name, position, scale in (
        ("front", (0,-27,8), 21), ("left", (-20,-24,10), 20.5),
        ("right", (22,-25,9), 20.5), ("elevated", (12,-18,24), 22),
    ):
        data = bpy.data.cameras.new(name)
        data.type, data.ortho_scale = "ORTHO", scale
        camera = bpy.data.objects.new(name, data)
        review.objects.link(camera)
        camera.location = position
        aim(camera, (0,.5,2.6))
        cameras[name] = camera
    scene.camera = cameras["front"]
    # CPU studio views run without a window-system or GPU dependency.
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 16
    scene.cycles.use_denoising = True
    scene.render.threads_mode = "FIXED"
    scene.render.threads = 3
    scene.render.resolution_x, scene.render.resolution_y = 1200, 760
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.view_settings.view_transform = "AgX"
    return scene, cameras


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    assert tuple(bpy.app.version) == (5, 2, 4), bpy.app.version_string
    output = args.out.resolve()
    output.mkdir(parents=True, exist_ok=True)
    scene, cameras = build_scene()
    scene["producer_script_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "windwaiting_cliff_C_swept_UNAPPROVED.blend"), compress=True)
    for name, camera in cameras.items():
        scene.camera = camera
        scene.render.filepath = str(output / (name + ".png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
