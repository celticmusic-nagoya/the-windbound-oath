"""Build the provisional Windwaiting Cliff C candidate from authored profiles."""
import argparse
import hashlib
import math
import random
from pathlib import Path

import bpy
import bmesh
from mathutils import Vector

CG = "assets/approved/game/cliff/sunset_background.png"
CG_SHA = "db0b1f6ae12892047c0def8af53c2bab54b294b76afc08565bf1670252d94a07"
BODY = "Cliff C3 | inland-linked bedrock"


def lerp(a, b, t):
    return a + (b - a) * t


# Each block has separate limits, face yaw, setback and profile assignment.
BLOCKS = (
    (-8.5, -6.6, -8, .18, 0), (-6.6, -3.7, 8, .26, 2),
    (-3.7, -1.9, -11, .49, 1), (-1.9, .05, 6, .16, 3),
    (.05, 1.8, -10, .55, 0), (1.8, 3.35, 9, .22, 2),
    (3.35, 5.10, -6, .33, 1), (5.10, 7.85, 11, .12, 3),
    (7.85, 9.50, -8, .40, 2), (9.50, 11.30, 7, .25, 0),
    (11.30, 13.40, -7, .50, 1), (13.40, 15.0, 9, .15, 3),
)
# Major joints are irregularly clustered. Minor joints taper out by course.
DEEP = (-6.6, -3.7, 7.85)
# Three rounded headlands and two coves, in near-to-far sunset view order.
HEADLANDS = ((-6.3, 5.2, 3.36, 6.30), (2.6, 4.3, 2.89, 5.55), (10.6, 3.25, 2.59, 4.80))
COAST = ((-17., 0.), (23., 0.))
PROFILE_SAMPLES = 64
# Lower courses carry a low, short upward-facing rubble shelf. Two thin
# sandstone ledges project above more recessed silty faces.
COURSES = (
    (0., -.22), (.055, -.31), (.073, -.29), (.098, .055), (.111, .13),
    (.19,.085), (.208,-.036), (.24,-.016), (.32,.055),
    (.352,.066), (.362,-.15), (.387,-.20), (.402,-.12), (.413,.025),
    (.52,.035), (.583,.052), (.60,-.13), (.627,-.19), (.652,-.11),
    (.669,.02), (.77,.041), (.847,.09), (.943,.036), (1.,0.),
)


def smooth(t):
    t = max(0., min(1., t))
    return t*t*(3-2*t)


def end_fade(x):
    return smooth((x+17)/8.15)*smooth((23-x)/8.45)


def crest_height(x):
    slope = 5.97 - .061*(x+6.3)
    crowns = sum(.19*math.exp(-((x-center)/width)**2) for center,_,width,_ in HEADLANDS)
    return lerp(-.62, slope+crowns, end_fade(x))


def shoreline(x):
    return 1.48 - sum(depth*math.exp(-.5*((x-center)/width)**2) for center,depth,width,_ in HEADLANDS)


def crown_radius(center):
    step = .001
    y = shoreline(center)
    slope = (shoreline(center+step)-shoreline(center-step))/(2*step)
    curvature = (shoreline(center+step)-2*y+shoreline(center-step))/(step**2)
    return (1+slope*slope)**1.5 / abs(curvature)


def course(profile, f):
    for a,b in zip(profile,profile[1:]):
        if f <= b[0]:
            return lerp(a[1],b[1],(f-a[0])/(b[0]-a[0]))
    return profile[-1][1]


def make_section(x):
    edge, crest = shoreline(x), crest_height(x)
    end = end_fade(x)
    block_index = next((i for i,b in enumerate(BLOCKS) if x<=b[1]),len(BLOCKS)-1)
    start, stop, _, _, _ = BLOCKS[block_index]
    near_left = block_index > 0 and x < start + .075
    near_right = block_index < len(BLOCKS)-1 and x > stop - .075
    alternate = BLOCKS[block_index-1] if near_left else (BLOCKS[block_index+1] if near_right else None)
    blend = .5*(1-smooth((x-start)/.075 if near_left else (stop-x)/.075)) if alternate else 0.

    # Gentle inland ramp fades below datum. Its closure is below the sea,
    # leaving no upward-exposed rear wall. Inner plateau continues in +Y.
    outer = 31.0
    ring = []
    for fraction, target in ((1,-.71),(.93,-.22),(.86,.38),(.78,1.28),(.69,2.52),
                             (.59,3.67),(.50,4.62),(.43,5.13),(.36,5.56)):
        ring.append((edge+outer*fraction,lerp(-.68,target, end)))
    for fraction in (.29,.23,.177,.126,.084,.052,.026,.012):
        inland = outer*fraction
        ring.append((edge+inland,crest + (.077*inland + .035*math.exp(-((inland-2.2)/1.5)**2))*end))
    for i in range(PROFILE_SAMPLES+1):
        f = 1-i/PROFILE_SAMPLES
        def face_depth(block):
            lo,hi,angle,back,kind = block
            face_x = max(lo,min(hi,x))
            yaw_shift = math.tan(math.radians(angle))*(face_x-(lo+hi)/2)
            strata = course(COURSES, max(0.,min(1.,f+(.011,-.016,.018,-.008)[kind]*math.sin(math.pi*f))))
            return strata + (back*.50+yaw_shift)*min(1.,(1-f)*12)*min(1.,f*11)
        offset = lerp(face_depth(BLOCKS[block_index]),face_depth(alternate),blend) if alternate else face_depth(BLOCKS[block_index])
        for seam in DEEP:
            offset += .26*math.exp(-((x-seam-.14*(f-.5))/.102)**2)*min(1.,f*8,(1-f)*11)
        # Local shoulders and short mid-scale fractures stay below facet amplitude.
        offset += .075*math.exp(-((x-start-.30-.34*f)/.135)**2)*math.exp(-((f-.53)/.24)**2)
        offset += .020*math.sin(x*6.3+f*19)*math.sin(math.pi*f)**2
        z = lerp(min(crest-.21,-.32),crest,f)
        ring.append((edge+offset*end,z))
    projection = .065 + .19*math.exp(-((x-9.8)/1.05)**2) + .16*math.exp(-((x+6.2)/1.25)**2)
    ring.extend(((edge-projection*end,min(crest-.26,-.43)),(edge+.18,-1.65),(edge+outer,-1.65)))
    return ring


def collection(name):
    result = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(result)
    return result


def make_cliff(target, rock, turf, substrate):
    intervals = 610
    vertices, faces, slots = [], [], []
    rings = [
        make_section(lerp(COAST[0][0], COAST[-1][0], i / intervals))
        for i in range(intervals + 1)
    ]
    size = len(rings[0])
    for i, ring in enumerate(rings):
        x = lerp(COAST[0][0], COAST[-1][0], i / intervals)
        vertices.extend((x, y, z) for y, z in ring)
    for i in range(intervals):
        for k in range(size):
            following = (k + 1) % size
            faces.append((i * size + k, (i + 1) * size + k,
                          (i + 1) * size + following, i * size + following))
            slots.append(1 if k < 17 and max(ring[k][1] for ring in rings[i:i+2]) > .38 else (2 if k >= size - 3 else 0))
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
    mesh.set_sharp_from_angle(angle=math.radians(26))
    for polygon in mesh.polygons:
        if polygon.material_index == 1 and (polygon.normal.z < .83 or polygon.center.z < 1.4):
            polygon.material_index = 0
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


def loose_rock(target, name, location, dimensions, material, seed, kind):
    rng = random.Random(seed)
    sides = (5, 7, 9)[kind]
    levels = (0., .16, .31, .355, .48, .62, .662, .81, 1.)
    vertices = []
    angles = [2*math.pi*(i+rng.uniform(-.23,.23))/sides for i in range(sides)]
    radii = [rng.uniform(.71,1.12) for _ in angles]
    for level, z in enumerate(levels):
        taper = (1.,1.08,.87,1.03,.89,.74,.93,.82,.47)[level]
        for i, angle in enumerate(angles):
            r = radii[i]*taper*rng.uniform(.88,1.12)
            vertices.append((dimensions[0]*(r*math.cos(angle)+.28*z),
                             dimensions[1]*r*math.sin(angle), dimensions[2]*(z + (rng.uniform(-.09,.09) if level == len(levels)-1 else 0))))
    faces = [tuple(reversed(range(sides)))]
    for n in range(len(levels)-1):
        for i in range(sides):
            j = (i+1)%sides
            faces.append((n*sides+i,n*sides+j,(n+1)*sides+j,(n+1)*sides+i))
    faces.append(tuple((len(levels)-1)*sides+i for i in range(sides)))
    mesh = bpy.data.meshes.new(name)
    mesh.from_pydata(vertices,[],faces)
    mesh.update()
    obj = bpy.data.objects.new(name, mesh)
    target.objects.link(obj)
    obj.location = location
    obj.rotation_euler.z = rng.uniform(-.65,.65)
    obj["shape_family"] = sides
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
    body = make_cliff(collection("01 | Continuous cliff body"), rock, turf, substrate)
    stacks = collection("02 | Detached sea stacks")
    loose_rock(stacks, "Detached stack 01", (10.2, -3.85, -.62), (.90,.66,3.45), rock, 524, 2)
    loose_rock(stacks, "Detached stack 02", (-6.8, -5.48, -.62), (.77,.55,2.95), rock, 526, 1)
    talus = collection("03 | Talus modules")
    rng = random.Random(937)
    for i in range(15):
        x = (-6.2, -2.15, 2.9, 9.75)[i % 4] + rng.uniform(-.48,.48)
        scale = .16 + .34 * rng.random() ** 2.2
        contacts = []
        for dx in (0, -.07, .07, -.14, .14, -.27, .27):
            sample_x = x + dx
            for step in range(101):
                sample_y = shoreline(sample_x) - .30 + .018 * step
                hit, point, normal, _ = body.ray_cast(
                    Vector((sample_x,sample_y,.48)),Vector((0,0,-1)),distance=.55)
                if hit and normal.z >= .5 and -.06 <= point.z <= .34:
                    score = abs(point.z-.10) + abs(dx)*.5
                    contacts.append((score, sample_x, sample_y, point.z))
        if not contacts:
            raise RuntimeError(f"Missing upward cliff-foot support at {x}")
        _, x, support_y, support_z = min(contacts)
        loose_rock(talus, f"Talus {i+1:02d}", (x,support_y,support_z-.055),
                   (1.35*scale, .88*scale, scale), rock, i + 33, i % 3)
        talus.objects[f"Talus {i+1:02d}"]["support_z"] = support_z

    reefs = collection("05 | Waterline reef modules")
    for i, (x, y, d, h) in enumerate((
        (-7.5,-5.29,.48,.51),(-7.05,-5.86,.34,.45),(-6.40,-5.92,.24,.36),
        (-5.90,-5.25,.31,.43),(-2.5,-1.73,.48,.52),(-2.0,-1.92,.26,.35),
        (1.9,-4.26,.43,.51),(2.55,-4.18,.36,.54),(3.27,-3.99,.27,.39),
        (9.65,-3.49,.53,.61),(10.8,-3.98,.36,.57),(11.12,-3.56,.31,.41),
    )):
        loose_rock(reefs, f"Reef {i+1:02d}", (x,y,-.22), (d,.78*d,h), rock, 710+i, i%3)
    review = collection("04 | Review cameras and lighting")
    water = bpy.data.materials.new("Provisional sea | review only")
    water.diffuse_color = (.024,.077,.105,1)
    water.use_nodes = True
    shader = water.node_tree.nodes.get("Principled BSDF")
    shader.inputs["Base Color"].default_value = (.019,.072,.09,1)
    shader.inputs["Roughness"].default_value = .34
    size = 400
    mesh = bpy.data.meshes.new("Provisional sea at Z=0")
    mesh.from_pydata([(-size,-size,0),(size,-size,0),(size,size,0),(-size,size,0)],[],[(0,1,2,3)])
    sea = bpy.data.objects.new(mesh.name, mesh)
    review.objects.link(sea)
    mesh.materials.append(water)
    world = bpy.data.worlds.new("Cool maritime fill")
    world.use_nodes = True
    world.node_tree.nodes.get("Background").inputs[0].default_value = (.31,.40,.59,1)
    world.node_tree.nodes.get("Background").inputs[1].default_value = .42
    scene.world = world
    sun = bpy.data.lights.new("Grazing warm key", "SUN")
    sun.energy = 2.45
    sun.angle = math.radians(9)
    sun.color = (1,.82,.65)
    light = bpy.data.objects.new(sun.name, sun)
    review.objects.link(light)
    light.location = (9,-6,6)
    aim(light, (0,0,1))
    cameras = {}
    for name, position, scale in (
        ("front", (1,-65,19), 47), ("left", (-45,-47,19), 51),
        ("right", (49,-52,18), 52), ("elevated", (20,-42,53), 63),
        ("sunset", (-29,-7,16), 31),
    ):
        data = bpy.data.cameras.new(name)
        data.type, data.ortho_scale = "ORTHO", scale
        data.clip_end = 1500
        camera = bpy.data.objects.new(name, data)
        review.objects.link(camera)
        camera.location = position
        aim(camera, (2,11,2.6) if name != "sunset" else (1,1.8,3.4))
        cameras[name] = camera
    scene.camera = cameras["front"]
    # CPU studio views run without a window-system or GPU dependency.
    scene.render.engine = "CYCLES"
    scene.cycles.samples = 12
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
    bpy.ops.wm.save_as_mainfile(filepath=str(output / "windwaiting_cliff_C3_UNAPPROVED.blend"), compress=True)
    for name, camera in cameras.items():
        scene.camera = camera
        if name == "sunset":
            sun = bpy.data.objects["Grazing warm key"]
            sun.location = (16, 9, 4)
            aim(sun, (0,0,1))
            sun.data.color = (1,.52,.23)
        scene.render.filepath = str(output / (name + ".png"))
        bpy.ops.render.render(write_still=True)


if __name__ == "__main__":
    main()
