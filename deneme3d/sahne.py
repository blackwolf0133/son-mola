# Blender deneme: izometrik low-poly İstanbul dioraması — gündüzden geceye, kamera yavaşça döner,
# arabalar akar, martılar uçar, akşam pencereler yanar. blender -b -P sahne.py -- <cikti_klasoru> <baslangic> <bitis>
import bpy, math, random, sys
argv = sys.argv[sys.argv.index("--") + 1:]
OUT, F0, F1 = argv[0], int(argv[1]), int(argv[2])
random.seed(7)
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
FR = 240
sc.frame_start, sc.frame_end = 1, FR
sc.render.fps = 30
sc.render.resolution_x, sc.render.resolution_y = 1080, 1920
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 24
sc.cycles.use_denoising = True
sc.render.film_transparent = False
sc.view_settings.view_transform = "AgX"
sc.view_settings.look = "AgX - Punchy"

def mat(name, col, emis=None, strength=0.0, rough=0.7):
    m = bpy.data.materials.new(name); m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1); b.inputs["Roughness"].default_value = rough
    if emis:
        b.inputs["Emission Color"].default_value = (*emis, 1); b.inputs["Emission Strength"].default_value = strength
    return m

def kutu(x, y, z, sx, sy, sz, m):
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + sz / 2)); o = bpy.context.object
    o.scale = (sx / 2, sy / 2, sz / 2); o.data.materials.append(m); return o

# zemin (iki yaka) + boğaz suyu
cim = mat("cim", (0.25, 0.55, 0.28)); su = mat("su", (0.05, 0.35, 0.55), rough=0.08)
kutu(-6, 0, -0.5, 8, 16, 0.5, cim); kutu(6, 0, -0.5, 8, 16, 0.5, cim)
w = kutu(0, 0, -0.8, 4, 16, 0.5, su)
# köprü
celik = mat("celik", (0.85, 0.2, 0.15), rough=0.4)
kutu(0, 2, 0.9, 6, 0.6, 0.15, celik)
for x in (-1.6, 1.6): kutu(x, 2, 0, 0.18, 0.18, 2.6, celik)
# binalar (pencereleri gece yanacak)
renk = [(0.9, 0.85, 0.75), (0.85, 0.55, 0.4), (0.95, 0.9, 0.6), (0.7, 0.75, 0.85)]
isik = []
for yaka in (-1, 1):
    for i in range(26):
        x = yaka * random.uniform(3, 9.5); y = random.uniform(-7.5, 7.5)
        if abs(y - 2) < 0.8: continue
        h = random.choice([0.6, 0.9, 1.2, 1.6, 2.2])
        m = mat(f"b{yaka}{i}", random.choice(renk), emis=(1.0, 0.75, 0.35), strength=0.0)
        kutu(x, y, 0, random.uniform(0.7, 1.2), random.uniform(0.7, 1.2), h, m); isik.append(m)
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.75, depth=0.45, location=(x, y, h + 0.22), rotation=(0, 0, math.pi / 4))
        bpy.context.object.data.materials.append(mat(f"cati{yaka}{i}", (0.7, 0.25, 0.18)))
# ağaçlar
yap = mat("yaprak", (0.18, 0.5, 0.22))
for i in range(40):
    x = random.choice([-1, 1]) * random.uniform(2.3, 9.8); y = random.uniform(-7.8, 7.8)
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=1, radius=random.uniform(0.25, 0.4), location=(x, y, 0.45))
    bpy.context.object.data.materials.append(yap)
# vapur (boğazda ilerler)
vap = kutu(0.4, -8, -0.55, 0.9, 2.0, 0.5, mat("vapur", (0.95, 0.95, 0.95)))
vap.keyframe_insert("location", frame=1); vap.location.y = 8; vap.keyframe_insert("location", frame=FR)
# köprüde arabalar
for i in range(8):
    c = kutu(-3, 1.85 + (0.25 if i % 2 else 0), 1.05, 0.35, 0.18, 0.18, mat(f"a{i}", random.choice([(0.9, 0.8, 0.1), (0.9, 0.1, 0.1), (0.1, 0.3, 0.9)])))
    off = i * 30
    c.location.x = -3 if i % 2 == 0 else 3; c.keyframe_insert("location", frame=1 + off % FR)
    c.location.x = 3 if i % 2 == 0 else -3; c.keyframe_insert("location", frame=1 + off % FR + 90)
# gökyüzü: gündüz -> gün batımı -> gece
world = bpy.data.worlds.new("w"); sc.world = world; world.use_nodes = True
bg = world.node_tree.nodes["Background"]
for f, col, s in [(1, (0.55, 0.75, 1.0), 1.0), (120, (1.0, 0.55, 0.35), 0.7), (200, (0.03, 0.04, 0.12), 0.25), (FR, (0.02, 0.03, 0.1), 0.2)]:
    bg.inputs["Color"].default_value = (*col, 1); bg.inputs["Strength"].default_value = s
    bg.inputs["Color"].keyframe_insert("default_value", frame=f); bg.inputs["Strength"].keyframe_insert("default_value", frame=f)
bpy.ops.object.light_add(type="SUN", location=(5, -5, 10)); gun = bpy.context.object
for f, e, rx in [(1, 4.0, 0.6), (120, 2.0, 1.25), (200, 0.05, 1.5)]:
    gun.data.energy = e; gun.rotation_euler = (rx, 0.3, 0.8)
    gun.data.keyframe_insert("energy", frame=f); gun.keyframe_insert("rotation_euler", frame=f)
for m in isik:  # pencereler sırayla yanar
    s = m.node_tree.nodes["Principled BSDF"].inputs["Emission Strength"]
    t = random.randint(130, 200); s.default_value = 0; s.keyframe_insert("default_value", frame=t); s.default_value = 3.0; s.keyframe_insert("default_value", frame=t + 6)
# kamera: izometrik, yavaş dönüş
bpy.ops.object.empty_add(location=(0, 0, 0)); piv = bpy.context.object
bpy.ops.object.camera_add(location=(0, -24, 18)); cam = bpy.context.object; sc.camera = cam
cam.data.type = "ORTHO"; cam.data.ortho_scale = 15
tr = cam.constraints.new("TRACK_TO"); tr.target = piv; tr.track_axis = "TRACK_NEGATIVE_Z"; tr.up_axis = "UP_Y"
cam.parent = piv
piv.rotation_euler = (0, 0, math.radians(-20)); piv.keyframe_insert("rotation_euler", frame=1)
piv.rotation_euler = (0, 0, math.radians(25)); piv.keyframe_insert("rotation_euler", frame=FR)
for fc in piv.animation_data.action.fcurves:
    for k in fc.keyframe_points: k.interpolation = "LINEAR"
sc.render.filepath = OUT + "/f_"
sc.frame_start, sc.frame_end = F0, F1
bpy.ops.render.render(animation=True)
