# ZAMAN DURAĞI — "oda" seti: kesit (cutaway) minyatür oda dioraması, yıllar içinde değişir.
# Kullanım:  python oda.py <bolum.json> <cikti_klasoru> <F0> <F1> [genislik] [ornek]
#        ya da blender -b -P oda.py -- <aynı argümanlar>
import bpy, math, random, sys, json, os

argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]
BOLUM, OUT, F0, F1 = argv[0], argv[1], int(argv[2]), int(argv[3])
GEN = int(argv[4]) if len(argv) > 4 else 720
ORNEK = int(argv[5]) if len(argv) > 5 else 16
B = json.load(open(BOLUM, encoding="utf-8"))
DON = B["donemler"]
FR = B["kare"]
random.seed(11)

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.frame_start, sc.frame_end = 1, FR
sc.render.fps = B.get("fps", 30)
sc.render.resolution_x, sc.render.resolution_y = GEN, GEN * 16 // 9
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = ORNEK
sc.cycles.use_adaptive_sampling = True
sc.cycles.adaptive_threshold = 0.05
sc.cycles.use_denoising = True
try:
    sc.cycles.denoiser = "OPENIMAGEDENOISE"
except Exception:
    pass
sc.cycles.max_bounces = 4
sc.cycles.diffuse_bounces = 3
sc.cycles.glossy_bounces = 1
sc.cycles.transmission_bounces = 2
sc.cycles.transparent_max_bounces = 4
sc.cycles.caustics_reflective = sc.cycles.caustics_refractive = False
sc.cycles.blur_glossy = 1.0
sc.render.use_persistent_data = True
sc.view_settings.view_transform = "AgX"
try:
    sc.view_settings.look = "AgX - Medium High Contrast"
except Exception:
    pass
sc.view_settings.exposure = -0.45
sc.render.image_settings.file_format = "PNG"
sc.render.image_settings.color_mode = "RGB"

# ---------------------------------------------------------------- yardımcılar
_M = {}


def mat(ad, col, rough=0.75, emis=None, guc=0.0, metal=0.0, alfa=1.0):
    if ad in _M:
        return _M[ad]
    m = bpy.data.materials.new(ad)
    m.use_nodes = True
    b = m.node_tree.nodes["Principled BSDF"]
    b.inputs["Base Color"].default_value = (*col, 1)
    b.inputs["Roughness"].default_value = rough
    b.inputs["Metallic"].default_value = metal
    if emis:
        b.inputs["Emission Color"].default_value = (*emis, 1)
        b.inputs["Emission Strength"].default_value = guc
    if alfa < 1:
        b.inputs["Alpha"].default_value = alfa
    _M[ad] = m
    return m


def bsdf(m):
    return m.node_tree.nodes["Principled BSDF"]


def _son(o, m, bevel):
    if m:
        o.data.materials.append(m)
    if bevel:
        bv = o.modifiers.new("bv", "BEVEL")
        bv.width = bevel
        bv.segments = 2
        bv.limit_method = "ANGLE"
    return o


def kutu(x, y, z, sx, sy, sz, m=None, bevel=0.025, ust=None, ad=None):
    """(x,y) merkez, z taban; boyutlar tam ölçü."""
    bpy.ops.mesh.primitive_cube_add(location=(x, y, z + sz / 2))
    o = bpy.context.object
    o.scale = (sx / 2, sy / 2, sz / 2)
    bpy.ops.object.transform_apply(scale=True)
    if ad:
        o.name = ad
    if ust:
        o.parent = ust
    return _son(o, m, bevel)


def silindir(x, y, z, r, h, m=None, n=20, bevel=0.015, ust=None, rot=(0, 0, 0)):
    zz = z + h / 2 if tuple(rot) == (0, 0, 0) else z
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=h, location=(x, y, zz), rotation=rot)
    o = bpy.context.object
    if ust:
        o.parent = ust
    o.data.polygons.foreach_set("use_smooth", [True] * len(o.data.polygons))
    return _son(o, m, bevel)


def kure(x, y, z, r, m=None, sub=2, ust=None, olcek=(1, 1, 1)):
    bpy.ops.mesh.primitive_ico_sphere_add(subdivisions=sub, radius=r, location=(x, y, z))
    o = bpy.context.object
    o.scale = olcek
    if ust:
        o.parent = ust
    return _son(o, m, 0)


def bos(ad, x, y, z=0.0, rz=0.0):
    o = bpy.data.objects.new(ad, None)
    sc.collection.objects.link(o)
    o.location = (x, y, z)
    o.rotation_euler = (0, 0, rz)
    return o


def kf(obj, yol, kare, deger, interp=None, kolay=None, indeks=-1):
    setattr_yol(obj, yol, deger)
    obj.keyframe_insert(yol, frame=kare, index=indeks)
    if interp:
        ad = obj.animation_data.action
        for fc in _fcurves(ad):
            if fc.data_path == yol:
                for k in fc.keyframe_points:
                    if abs(k.co[0] - kare) < 0.5:
                        k.interpolation = interp
                        if kolay:
                            k.easing = kolay


def _fcurves(action):
    try:
        return list(action.fcurves)
    except Exception:
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for cb in strip.channelbags:
                    out.extend(cb.fcurves)
        return out


def setattr_yol(obj, yol, deger):
    setattr(obj, yol, deger)


def soket_kf(sok, kare, deger):
    sok.default_value = deger
    sok.keyframe_insert("default_value", frame=kare)


def gurultu(id_data, yol, olcek=6, guc=1.0, indeks=None):
    ad = id_data.animation_data.action if id_data.animation_data else None
    if not ad:
        return
    for fc in _fcurves(ad):
        if fc.data_path.endswith(yol) and (indeks is None or fc.array_index == indeks):
            n = fc.modifiers.new("NOISE")
            n.scale = olcek
            n.strength = guc
            n.phase = random.uniform(0, 50)


# ---------------------------------------------------------------- dönem yardımcıları
def donem_ar(ad):
    """Eşyanın bulunduğu ardışık dönem aralıkları -> [(bas, bit), ...]"""
    out = []
    for d in DON:
        var = ad in d["esyalar"]
        if var and out and out[-1][1] == d["bas"] - 1:
            out[-1] = (out[-1][0], d["bit"])
        elif var:
            out.append((d["bas"], d["bit"]))
    return out


GECIS = 14  # pop süresi (kare)


def belir_kaybol(kok, ad, gecikme=0):
    """Kök boşluğunu dönemlere göre 'zıplayarak' getir/götür."""
    ar = donem_ar(ad)
    kok.scale = (0.0001,) * 3
    kok.keyframe_insert("scale", frame=1)
    for bas, bit in ar:
        g = 0 if bas == 1 else gecikme
        a = max(1, bas + g)
        if bas == 1:
            kf(kok, "scale", 1, (1, 1, 1), "CONSTANT")
        else:
            kf(kok, "scale", a, (0.0001,) * 3, "BACK", "EASE_OUT")
            kf(kok, "scale", a + GECIS, (1, 1, 1), "CONSTANT")
        if bit < FR:
            c = bit - GECIS - 6 + gecikme // 2
            kf(kok, "scale", c, (1, 1, 1), "BACK", "EASE_IN")
            kf(kok, "scale", c + GECIS - 2, (0.0001,) * 3, "CONSTANT")


# ---------------------------------------------------------------- malzemeler
siyah = mat("soba", (0.05, 0.05, 0.055), 0.45, metal=0.6)
ahsap = mat("ahsap", (0.42, 0.24, 0.12), 0.6)
ahsap_ac = mat("ahsap_ac", (0.62, 0.42, 0.24), 0.6)
beyaz = mat("beyaz", (0.92, 0.91, 0.88), 0.7)
dantel = mat("dantel", (0.97, 0.96, 0.92), 0.9)
kirmizi = mat("kirmizi", (0.62, 0.09, 0.08), 0.85)
krem = mat("krem", (0.88, 0.80, 0.64), 0.85)
cay = mat("cay", (0.55, 0.12, 0.04), 0.1, emis=(0.6, 0.15, 0.03), guc=0.3)
cam_m = mat("cam", (0.8, 0.85, 0.9), 0.2)
ates = mat("ates", (1, 0.4, 0.1), emis=(1.0, 0.38, 0.08), guc=12)
celik = mat("celik", (0.7, 0.7, 0.72), 0.35, metal=0.9)
ortu = mat("ortu", (0.93, 0.93, 0.91), 0.95)

# ---------------------------------------------------------------- oda iskeleti
ODA = 2.55  # yarım genişlik
YUK = 3.1

taban = mat("taban_toprak", (0.36, 0.25, 0.17), 0.95)
cim = mat("cim", (0.30, 0.52, 0.26), 0.9)
kutu(0, 0, -0.75, 6.1, 6.1, 0.55, taban, bevel=0.06)
kutu(0, 0, -0.22, 6.1, 6.1, 0.12, cim, bevel=0.04)
# döşeme: tahta şeritler
for i in range(10):
    ton = 0.36 + 0.05 * ((i * 7) % 3)
    kutu(-ODA + 0.255 + i * 0.51, 0, -0.1, 0.5, 2 * ODA, 0.1,
         mat(f"tahta{i%3}", (ton + 0.12, ton - 0.02, ton - 0.16), 0.55), bevel=0.012)

duvar_m = mat("duvar", tuple(DON[0]["duvar"]), 0.9)
for d in DON:
    soket_kf(bsdf(duvar_m).inputs["Base Color"], max(1, d["bas"] + 4), (*d["duvar"], 1))
    soket_kf(bsdf(duvar_m).inputs["Base Color"], d["bit"] - 8, (*d["duvar"], 1))
kesit = mat("kesit", (0.80, 0.76, 0.70), 0.9)
T = 0.22
# arka duvar (y = +ODA)
kutu(0, ODA + T / 2, 0, 2 * ODA + 2 * T, T, YUK, duvar_m, bevel=0.02)
# sol duvar (x = -ODA) pencere boşluklu
PY0, PY1, PZ0, PZ1 = -1.45, 0.15, 1.0, 2.4
kutu(-ODA - T / 2, (-ODA + PY0) / 2, 0, T, PY0 + ODA, YUK, duvar_m, bevel=0.02)
kutu(-ODA - T / 2, (PY1 + ODA) / 2, 0, T, ODA - PY1, YUK, duvar_m, bevel=0.02)
kutu(-ODA - T / 2, (PY0 + PY1) / 2, 0, T, PY1 - PY0, PZ0, duvar_m, bevel=0.02)
kutu(-ODA - T / 2, (PY0 + PY1) / 2, PZ1, T, PY1 - PY0, YUK - PZ1, duvar_m, bevel=0.02)
# duvar üst kesitleri (maket hissi)
kutu(0, ODA + T / 2, YUK, 2 * ODA + 2 * T, T + 0.01, 0.04, kesit, bevel=0.0)
kutu(-ODA - T / 2, 0, YUK, T + 0.01, 2 * ODA, 0.04, kesit, bevel=0.0)
# süpürgelik
kutu(0, ODA - 0.03, 0, 2 * ODA, 0.06, 0.14, ahsap_ac, bevel=0.01)
kutu(-ODA + 0.03, 0, 0, 0.06, 2 * ODA, 0.14, ahsap_ac, bevel=0.01)
# pencere çerçevesi
cerceve = mat("cerceve", (0.95, 0.95, 0.93), 0.5)
kutu(-ODA - T / 2, (PY0 + PY1) / 2, PZ0 - 0.06, T + 0.16, PY1 - PY0 + 0.1, 0.07, cerceve, bevel=0.01)
kutu(-ODA - T / 2, (PY0 + PY1) / 2, PZ1, T, PY1 - PY0, 0.06, cerceve, bevel=0.01)
kutu(-ODA - T / 2, PY0 + 0.03, PZ0, T, 0.06, PZ1 - PZ0, cerceve, bevel=0.01)
kutu(-ODA - T / 2, PY1 - 0.03, PZ0, T, 0.06, PZ1 - PZ0, cerceve, bevel=0.01)
kutu(-ODA - T / 2, (PY0 + PY1) / 2, PZ0, T * 0.5, 0.05, PZ1 - PZ0, cerceve, bevel=0.0)
kutu(-ODA - T / 2, (PY0 + PY1) / 2, (PZ0 + PZ1) / 2, T * 0.5, PY1 - PY0, 0.05, cerceve, bevel=0.0)

# dışarıdaki ağaç (yıllar içinde büyür)
agac = bos("agac", -2.85, -2.6)
silindir(0, 0, 0, 0.09, 1.2, ahsap, n=8, ust=agac)
yap_m = mat("yaprak", (0.22, 0.5, 0.2), 0.8)
for (x, y, z, r) in [(0, 0, 1.45, 0.55), (0.15, -0.3, 1.2, 0.4), (-0.1, 0.3, 1.8, 0.38)]:
    kure(x, y, z, r, yap_m, sub=1, ust=agac)
kf(agac, "scale", 1, (0.75, 0.75, 0.75))
kf(agac, "scale", FR, (1.35, 1.35, 1.35))
for d, c in zip(DON, [(0.22, 0.5, 0.2), (0.75, 0.45, 0.12), (0.25, 0.55, 0.22), (0.62, 0.5, 0.22)]):
    soket_kf(bsdf(yap_m).inputs["Base Color"], d["bas"] + 6, (*c, 1))
    soket_kf(bsdf(yap_m).inputs["Base Color"], d["bit"] - 6, (*c, 1))

# ---------------------------------------------------------------- eşyalar
ESYA = {}


def esya(ad, gecikme=0):
    def sar(fn):
        ESYA[ad] = (fn, gecikme)
        return fn
    return sar


@esya("soba", 0)
def _soba(k):
    silindir(0, 0, 0, 0.36, 0.95, siyah, n=24, ust=k)
    silindir(0, 0, 0.95, 0.42, 0.06, siyah, n=24, ust=k)
    for a in range(3):
        aci = a * 2 * math.pi / 3
        kutu(0.3 * math.cos(aci), 0.3 * math.sin(aci), -0.1, 0.06, 0.06, 0.12, siyah, ust=k)
    # alev penceresi (titrer)
    kutu(0.31, 0.0, 0.3, 0.12, 0.26, 0.18, ates, bevel=0.0, ust=k)
    # boru: yukarı, sonra duvara
    silindir(0, 0, 1.0, 0.08, 1.45, siyah, n=12, ust=k)
    silindir(-0.28, 0, 2.38, 0.08, 0.6, siyah, n=12, ust=k, rot=(0, math.pi / 2, 0))
    # çaydanlık + demlik
    silindir(0.05, 0.05, 1.01, 0.15, 0.17, celik, n=18, ust=k)
    silindir(0.05, 0.05, 1.19, 0.1, 0.13, mat("demlik", (0.85, 0.85, 0.82), 0.4, metal=0.5), n=18, ust=k)
    # soba ışığı
    bpy.ops.object.light_add(type="POINT", location=(0.6, 0, 0.45))
    l = bpy.context.object
    l.parent = k
    l.data.color = (1.0, 0.5, 0.2)
    l.data.shadow_soft_size = 0.3
    ISIKLAR.append(dict(veri=l.data, enerji=70, emat=ates, eguc=12, ad=CUR[0], tip="surekli", titre=0.35))


@esya("sedir", 2)
def _sedir(k):
    kutu(0, 0, 0, 3.0, 0.85, 0.38, ahsap, ust=k)
    kutu(0, 0, 0.38, 3.0, 0.85, 0.12, kirmizi, bevel=0.05, ust=k)
    desen = mat("kilim_desen", (0.85, 0.65, 0.2), 0.85)
    for i in range(5):
        kutu(-1.2 + i * 0.6, -0.43, 0.06, 0.18, 0.02, 0.22, desen, bevel=0.0, ust=k)
    for i in range(3):
        y = kutu(-1.0 + i, 0.3, 0.5, 0.85, 0.22, 0.55, mat(f"yastik{i}", [(0.7, 0.12, 0.1), (0.8, 0.55, 0.15), (0.7, 0.12, 0.1)][i], 0.9), bevel=0.08, ust=k)
        y.rotation_euler = (-0.18, 0, 0)


def _kanepe(k, renk, ad):
    m = mat(ad, renk, 0.95)
    kutu(0, 0, 0.08, 2.6, 0.9, 0.38, m, bevel=0.06, ust=k)
    kutu(0, 0.32, 0.4, 2.6, 0.26, 0.6, m, bevel=0.1, ust=k)
    for s in (-1, 1):
        kutu(s * 1.22, -0.02, 0.4, 0.22, 0.86, 0.3, m, bevel=0.08, ust=k)
    for s in (-1, 0, 1):
        kutu(s * 0.78, -0.05, 0.46, 0.74, 0.7, 0.12, m, bevel=0.06, ust=k)
    for s in (-1, 1):
        for t in (-1, 1):
            kutu(s * 1.2, t * 0.35, 0, 0.08, 0.08, 0.08, ahsap, bevel=0.0, ust=k)


@esya("kanepe_kahve", 2)
def _kk(k):
    _kanepe(k, (0.36, 0.2, 0.12), "kadife_kahve")
    kutu(0.0, 0.25, 0.75, 0.7, 0.04, 0.45, dantel, bevel=0.0, ust=k)


@esya("kanepe_bej", 2)
def _kb(k):
    _kanepe(k, (0.72, 0.64, 0.52), "kumas_bej")
    kutu(0.75, 0.12, 0.55, 0.42, 0.18, 0.42, mat("kirlent", (0.55, 0.62, 0.7), 0.9), bevel=0.08, ust=k)


@esya("masa_dantel", 4)
def _masa(k):
    silindir(0, 0, 0, 0.06, 0.62, ahsap, n=10, ust=k)
    silindir(0, 0, 0, 0.25, 0.04, ahsap, n=16, ust=k)
    silindir(0, 0, 0.62, 0.5, 0.05, ahsap, n=28, ust=k)
    silindir(0, 0, 0.67, 0.56, 0.012, dantel, n=28, bevel=0, ust=k)
    for i, (x, y) in enumerate([(0.2, 0.1), (-0.15, 0.2), (0.05, -0.22)]):
        silindir(x, y, 0.682, 0.07, 0.012, beyaz, n=14, bevel=0, ust=k)
        silindir(x, y, 0.69, 0.035, 0.12, cay, n=10, bevel=0, ust=k)
    kutu(-0.2, -0.05, 0.682, 0.16, 0.12, 0.06, mat("seker", (0.95, 0.95, 0.95), 0.6), bevel=0.01, ust=k)


@esya("sehpa", 4)
def _sehpa(k):
    cam = mat("sehpa_cam", (0.75, 0.82, 0.85), 0.15)
    kutu(0, 0, 0, 1.0, 0.6, 0.36, ahsap_ac, bevel=0.02, ust=k)
    kutu(0, 0, 0.36, 1.1, 0.7, 0.04, cam, bevel=0.01, ust=k)
    kutu(0.25, 0.05, 0.4, 0.22, 0.14, 0.03, mat("kumanda", (0.1, 0.1, 0.1), 0.5), bevel=0.01, ust=k)
    silindir(-0.25, -0.05, 0.4, 0.06, 0.1, beyaz, n=12, ust=k)


@esya("saat", 0)
def _saat(k):
    # duvar saati: kasa + kadran + akrep/yelkovan + sarkaç
    kutu(0, 0, -0.95, 0.5, 0.1, 1.35, ahsap, bevel=0.03, ust=k)
    silindir(0, -0.06, 0.2, 0.19, 0.02, beyaz, n=28, bevel=0, ust=k, rot=(math.pi / 2, 0, 0))
    kadran = bos("kadran", 0, -0.1, 0.2)
    kadran.parent = k
    akrep = kutu(0, 0, 0, 0.025, 0.01, 0.11, siyah, bevel=0, ust=kadran)
    yelkovan_k = bos("yelk", 0, -0.005, 0)
    yelkovan_k.parent = kadran
    kutu(0, 0, 0, 0.018, 0.01, 0.16, siyah, bevel=0, ust=yelkovan_k)
    son = next((d["bas"] for d in DON if d.get("son")), FR)
    # zaman akıyor: yelkovan hızla döner, son dönemde durur
    for o, tur in ((kadran, 6), (yelkovan_k, 70)):
        kf(o, "rotation_euler", 1, (0, 0, 0), "LINEAR", indeks=1)
        kf(o, "rotation_euler", son, (0, -tur * 2 * math.pi, 0), "CONSTANT", indeks=1)
    # sarkaç (sürücü ile salınır; genlik son dönemde sıfıra iner)
    sar = bos("sarkac", 0, -0.07, -0.25)
    sar.parent = k
    silindir(0, 0, -0.55, 0.012, 0.55, celik, n=6, bevel=0, ust=sar)
    silindir(0, 0, -0.62, 0.07, 0.02, mat("pirinc", (0.85, 0.65, 0.25), 0.3, metal=1.0), n=20, bevel=0, ust=sar, rot=(math.pi / 2, 0, 0))
    sar["genlik"] = 0.32
    sar.keyframe_insert('["genlik"]', frame=1)
    sar.keyframe_insert('["genlik"]', frame=max(2, son - 1))
    sar["genlik"] = 0.0
    sar.keyframe_insert('["genlik"]', frame=son + 45)
    d = sar.driver_add("rotation_euler", 1).driver
    d.type = "SCRIPTED"
    v = d.variables.new()
    v.name = "g"
    v.targets[0].id = sar
    v.targets[0].data_path = '["genlik"]'
    d.expression = "g*sin(frame*0.21)"


@esya("radyo", 3)
def _radyo(k):
    kutu(0, 0, 0, 0.3, 1.1, 0.05, ahsap, bevel=0.01, ust=k)   # raf
    kutu(0.02, 0.1, 0.05, 0.26, 0.55, 0.32, mat("radyo", (0.55, 0.32, 0.15), 0.4), bevel=0.04, ust=k)
    kutu(0.15, 0.0, 0.1, 0.02, 0.28, 0.2, mat("hoparlor", (0.85, 0.78, 0.6), 0.9), bevel=0.0, ust=k)
    for z in (0.15, 0.27):
        silindir(0.16, 0.28, z, 0.03, 0.02, krem, n=10, bevel=0, ust=k, rot=(0, math.pi / 2, 0))


def _foto(k, renk):
    kutu(0, 0, 0, 0.05, 0.42, 0.52, ahsap_ac, bevel=0.01, ust=k)
    kutu(0.03, 0, 0.05, 0.01, 0.32, 0.42, mat("foto_" + str(renk), renk, 0.6), bevel=0, ust=k)


@esya("foto1", 1)
def _f1(k):
    _foto(k, (0.55, 0.45, 0.32))


@esya("foto2", 3)
def _f2(k):
    _foto(k, (0.45, 0.5, 0.55))


@esya("foto3", 5)
def _f3(k):
    _foto(k, (0.6, 0.55, 0.5))


def _saksi(k, kuru):
    silindir(0, 0, 0, 0.12, 0.18, mat("saksi", (0.7, 0.35, 0.2), 0.8), n=14, ust=k)
    sap = mat("sap_kuru" if kuru else "sap", (0.45, 0.33, 0.18) if kuru else (0.2, 0.45, 0.18), 0.8)
    for i in range(7):
        a = i / 7 * 2 * math.pi
        kure(0.07 * math.cos(a), 0.07 * math.sin(a), 0.25 + (i % 2) * 0.05, 0.07, sap, sub=1, ust=k)
    if not kuru:
        ciceK = mat("sardunya", (0.9, 0.12, 0.15), 0.6)
        for i in range(4):
            a = i / 4 * 2 * math.pi + 0.4
            kure(0.06 * math.cos(a), 0.06 * math.sin(a), 0.36, 0.055, ciceK, sub=1, ust=k)


@esya("saksi", 6)
def _s(k):
    _saksi(k, False)


@esya("saksi_kuru", 6)
def _sk(k):
    _saksi(k, True)


@esya("ampul", 0)
def _ampul(k):
    silindir(0, 0, -0.75, 0.008, 0.75, siyah, n=6, bevel=0, ust=k)
    amp = mat("ampul", (1, 0.9, 0.7), emis=(1.0, 0.72, 0.4), guc=0.0)
    kure(0, 0, -0.82, 0.07, amp, sub=2, ust=k)
    bpy.ops.object.light_add(type="POINT", location=(0, 0, -0.85))
    l = bpy.context.object
    l.parent = k
    l.data.color = (1.0, 0.7, 0.4)
    l.data.shadow_soft_size = 0.08
    ISIKLAR.append(dict(veri=l.data, enerji=220, emat=amp, eguc=25, ad=CUR[0], tip="gece", titre=0.0))


@esya("avize", 0)
def _avize(k):
    silindir(0, 0, -0.4, 0.01, 0.4, celik, n=6, bevel=0, ust=k)
    silindir(0, 0, -0.55, 0.32, 0.12, mat("avize_kapak", (0.95, 0.95, 0.92), 0.6), n=28, ust=k)
    amp = mat("led", (1, 1, 1), emis=(1.0, 0.92, 0.82), guc=0.0)
    silindir(0, 0, -0.57, 0.28, 0.02, amp, n=28, bevel=0, ust=k)
    bpy.ops.object.light_add(type="AREA", location=(0, 0, -0.6))
    l = bpy.context.object
    l.parent = k
    l.data.size = 0.5
    l.data.color = (1.0, 0.9, 0.8)
    l.rotation_euler = (0, 0, 0)
    ISIKLAR.append(dict(veri=l.data, enerji=260, emat=amp, eguc=10, ad=CUR[0], tip="gece", titre=0.0))


@esya("kilim", 0)
def _kilim(k):
    m = mat("hali", (0.6, 0.15, 0.12), 0.95)
    kutu(0, 0, 0, 2.8, 2.0, 0.025, m, bevel=0.005, ust=k)
    kenar = mat("hali_kenar", (0.9, 0.75, 0.45), 0.95)
    for s in (-1, 1):
        kutu(0, s * 0.85, 0.02, 2.5, 0.08, 0.008, kenar, bevel=0, ust=k)
        kutu(s * 1.25, 0, 0.02, 0.08, 1.7, 0.008, kenar, bevel=0, ust=k)
    kutu(0, 0, 0.02, 0.5, 0.5, 0.008, kenar, bevel=0, ust=k).rotation_euler = (0, 0, math.pi / 4)
    renk = {"kirmizi": (0.6, 0.13, 0.1), "mavi": (0.15, 0.25, 0.5), "bej": (0.72, 0.62, 0.48)}
    for d in DON:
        c = renk.get(d.get("hali", "kirmizi"))
        soket_kf(bsdf(m).inputs["Base Color"], d["bas"] + 6, (*c, 1))
        soket_kf(bsdf(m).inputs["Base Color"], d["bit"] - 6, (*c, 1))


@esya("kedi", 8)
def _kedi(k):
    tuy = mat("kedi", (0.85, 0.5, 0.2), 0.95)
    govde = kure(0, 0, 0.15, 0.25, tuy, sub=2, ust=k, olcek=(1.35, 0.85, 0.6))
    kure(0.3, -0.05, 0.2, 0.14, tuy, sub=2, ust=k)
    for s in (-1, 1):
        bpy.ops.mesh.primitive_cone_add(vertices=4, radius1=0.05, depth=0.1, location=(0.32, -0.05 + s * 0.08, 0.34))
        o = bpy.context.object
        o.parent = k
        o.data.materials.append(tuy)
    kuyruk = silindir(-0.1, -0.22, 0.1, 0.035, 0.4, tuy, n=8, ust=k, rot=(0, math.pi / 2, 0.4))
    # nefes alıyor
    for f in range(1, FR, 50):
        kf(govde, "scale", f, (1.35, 0.85, 0.6))
        kf(govde, "scale", f + 25, (1.38, 0.9, 0.66))


@esya("tv_tuplu", 3)
def _tvt(k):
    kutu(0, 0, 0, 0.9, 0.55, 0.55, ahsap, bevel=0.02, ust=k)
    kutu(0, 0.02, 0.55, 0.78, 0.66, 0.62, mat("tv_kasa", (0.18, 0.17, 0.16), 0.5), bevel=0.06, ust=k)
    ekran = mat("ekran", (0.6, 0.7, 0.8), 0.2, emis=(0.55, 0.7, 0.95), guc=0.0)
    kutu(0, -0.3, 0.62, 0.56, 0.04, 0.46, ekran, bevel=0.04, ust=k)
    kutu(0.0, 0.05, 1.17, 0.55, 0.4, 0.008, dantel, bevel=0, ust=k)
    silindir(0.12, 0.1, 1.33, 0.012, 0.35, celik, n=6, bevel=0, ust=k, rot=(0.4, 0.3, 0))
    silindir(-0.12, 0.1, 1.33, 0.012, 0.35, celik, n=6, bevel=0, ust=k, rot=(0.4, -0.3, 0))
    bpy.ops.object.light_add(type="AREA", location=(0, -0.6, 0.85), rotation=(math.pi / 2, 0, 0))
    l = bpy.context.object
    l.parent = k
    l.data.size = 0.5
    l.data.color = (0.6, 0.75, 1.0)
    ISIKLAR.append(dict(veri=l.data, enerji=40, emat=ekran, eguc=3.5, ad=CUR[0], tip="gece", titre=0.4))


@esya("tv_duz", 3)
def _tvd(k):
    kutu(0, 0, 0, 1.5, 0.45, 0.42, mat("tv_unite", (0.95, 0.94, 0.9), 0.4), bevel=0.02, ust=k)
    kutu(0, 0.05, 0.42, 0.2, 0.15, 0.08, siyah, bevel=0.01, ust=k)
    kutu(0, 0.05, 0.5, 1.3, 0.05, 0.75, siyah, bevel=0.01, ust=k)
    ekran = mat("ekran2", (0.1, 0.1, 0.12), 0.2, emis=(0.5, 0.65, 1.0), guc=0.0)
    kutu(0, 0.02, 0.53, 1.24, 0.02, 0.69, ekran, bevel=0, ust=k)
    bpy.ops.object.light_add(type="AREA", location=(0, -0.4, 0.9), rotation=(math.pi / 2, 0, 0))
    l = bpy.context.object
    l.parent = k
    l.data.size = 1.0
    l.data.color = (0.6, 0.75, 1.0)
    ISIKLAR.append(dict(veri=l.data, enerji=35, emat=ekran, eguc=3.0, ad=CUR[0], tip="gece", titre=0.4))


@esya("telefon", 4)
def _tel(k):
    kutu(0, 0, 0, 0.4, 0.4, 0.55, ahsap_ac, bevel=0.02, ust=k)
    kutu(0, 0, 0.55, 0.42, 0.42, 0.01, dantel, bevel=0, ust=k)
    kutu(0, 0, 0.56, 0.2, 0.24, 0.08, mat("telefon", (0.85, 0.75, 0.45), 0.4), bevel=0.03, ust=k)
    kutu(0, 0, 0.64, 0.24, 0.06, 0.05, mat("telefon", (0.85, 0.75, 0.45), 0.4), bevel=0.02, ust=k)


@esya("dikis", 5)
def _dikis(k):
    kutu(0, 0, 0, 0.8, 0.45, 0.7, ahsap, bevel=0.02, ust=k)
    gov = mat("dikis", (0.08, 0.08, 0.09), 0.35)
    kutu(0, 0, 0.7, 0.5, 0.18, 0.1, gov, bevel=0.03, ust=k)
    kutu(-0.18, 0, 0.8, 0.1, 0.16, 0.22, gov, bevel=0.03, ust=k)
    kutu(0, 0, 0.97, 0.45, 0.14, 0.09, gov, bevel=0.03, ust=k)
    kutu(0.18, 0, 0.82, 0.07, 0.07, 0.16, gov, bevel=0.01, ust=k)
    silindir(-0.25, 0, 0.98, 0.07, 0.03, mat("pirinc", (0.85, 0.65, 0.25), 0.3, metal=1.0), n=16, ust=k, rot=(0, math.pi / 2, 0))
    silindir(0.1, -0.08, 0.7, 0.03, 0.05, mat("makara", (0.8, 0.2, 0.3), 0.6), n=10, ust=k)


@esya("petek", 2)
def _petek(k):
    for i in range(8):
        kutu(0, -0.5 + i * 0.14, 0, 0.1, 0.1, 0.6, beyaz, bevel=0.02, ust=k)


@esya("perde", 5)
def _perde(k):
    tul = mat("tul", (0.98, 0.97, 0.94), 0.9, alfa=0.55)
    for s in (-1, 1):
        o = kutu(0, s * 0.72, 0, 0.03, 0.5, 1.55, tul, bevel=0, ust=k)
    silindir(0, 0, 1.6, 0.015, 2.2, celik, n=6, bevel=0, ust=k, rot=(math.pi / 2, 0, 0))


@esya("ortu_kanepe", 6)
def _ok(k):
    kutu(0, 0, 0, 2.7, 0.95, 0.5, ortu, bevel=0.15, ust=k)
    kutu(0, 0.3, 0.45, 2.7, 0.35, 0.45, ortu, bevel=0.15, ust=k)
    kutu(0, -0.4, 0, 2.6, 0.2, 0.25, ortu, bevel=0.08, ust=k)


@esya("ortu_tv", 10)
def _ot(k):
    kutu(0, 0, 0, 1.5, 0.5, 0.45, ortu, bevel=0.1, ust=k)
    kutu(0, 0.05, 0.45, 1.25, 0.25, 0.7, ortu, bevel=0.12, ust=k)


@esya("toz", 0)
def _toz(k):
    tm = mat("toz", (1, 0.9, 0.7), emis=(1.0, 0.85, 0.6), guc=6)
    for i in range(46):
        x, y, z = random.uniform(-1.2, 1.8), random.uniform(-2.2, 0.6), random.uniform(0.5, 2.3)
        p = kure(x, y, z, random.uniform(0.008, 0.016), tm, sub=1, ust=k)
        for f, dx in ((1, 0), (FR, 1)):
            kf(p, "location", f, (x + dx * random.uniform(-0.4, 0.4), y + dx * random.uniform(-0.3, 0.3), z + dx * random.uniform(-0.5, 0.3)))
        gurultu(p, "location", 60, 0.12)


# Eşyaların odadaki yerleri (x, y, z, dönüş)
YER = {
    "soba": (-2.00, 1.49, 0, 0), "sedir": (0.34, 2.08, 0, 0), "kanepe_kahve": (0.34, 2.04, 0, 0),
    "kanepe_bej": (0.34, 2.04, 0, 0), "ortu_kanepe": (0.34, 2.04, 0, 0),
    "masa_dantel": (0.42, 0.26, 0, 0), "sehpa": (0.38, 0.77, 0.02, 0),
    "saat": (1.91, 2.49, 1.9, 0), "radyo": (-2.42, 0.85, 1.55, 0),
    "foto1": (-2.51, -1.95, 1.6, 0), "foto2": (-2.51, 1.10, 1.95, 0), "foto3": (-2.51, -1.95, 2.3, 0),
    "saksi": (-2.51, -0.64, 0.97, 0), "saksi_kuru": (-2.51, -0.64, 0.97, 0),
    "ampul": (0.34, 0.34, YUK, 0), "avize": (0.34, 0.34, YUK, 0),
    "kilim": (0.34, 0.42, 0, 0), "kedi": (-0.42, 1.91, 0.5, 0.3),
    "tv_tuplu": (1.70, -1.36, 0, math.radians(110)), "tv_duz": (1.83, -1.02, 0, math.radians(100)),
    "ortu_tv": (1.83, -1.02, 0, math.radians(100)),
    "telefon": (-1.78, -1.87, 0, 0), "petek": (-2.42, -0.59, 0.2, 0), "perde": (-2.40, -0.59, 0.85, 0),
    "toz": (0.00, 0.00, 0, 0),
}
for _a, _dx in (("radyo", 0.15), ("foto1", 0.05), ("foto2", 0.05), ("foto3", 0.05), ("saksi", 0.05), ("saksi_kuru", 0.05), ("petek", 0.15), ("perde", 0.18)):
    _v = YER[_a]; YER[_a] = (-ODA + _dx, _v[1], _v[2], _v[3])
YER["saat"] = (YER["saat"][0], ODA - 0.06, YER["saat"][2], 0)
YER["dikis"] = (-1.75, -1.75, 0, math.radians(30))
# kedi ikinci dönemde kanepenin üstünde biraz yükseğe
ISIKLAR = []
CUR = [None]

for ad, (fn, gec) in ESYA.items():
    if not donem_ar(ad):
        continue
    x, y, z, rz = YER[ad]
    k = bos("k_" + ad, x, y, z, rz)
    CUR[0] = ad
    fn(k)
    belir_kaybol(k, ad, gec)

# ---------------------------------------------------------------- ışık & gökyüzü (gün döngüsü)
world = bpy.data.worlds.new("w")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bpy.ops.object.light_add(type="SUN", location=(0, 0, 10))
gunes = bpy.context.object
gunes.data.angle = math.radians(3)
gunes.data.color = (1.0, 0.95, 0.85)

# dolgu ışığı (kamera tarafından yumuşak)
bpy.ops.object.light_add(type="AREA", location=(6, -7, 7))
dolgu = bpy.context.object
dolgu.data.size = 8
dolgu.data.energy = 900
dolgu.rotation_euler = (math.radians(55), 0, math.radians(40))


def gok(f, renk, guc, g_enerji, g_yuk, g_az, g_renk=(1, 0.95, 0.85), dolgu_e=900):
    soket_kf(bg.inputs["Color"], f, (*renk, 1))
    soket_kf(bg.inputs["Strength"], f, guc)
    gunes.data.energy = g_enerji
    gunes.data.keyframe_insert("energy", frame=f)
    gunes.data.color = g_renk
    gunes.data.keyframe_insert("color", frame=f)
    gunes.rotation_euler = (math.radians(90 - g_yuk), 0, math.radians(g_az))
    gunes.keyframe_insert("rotation_euler", frame=f)
    dolgu.data.energy = dolgu_e
    dolgu.data.keyframe_insert("energy", frame=f)


SABAH = ((0.45, 0.62, 0.88), 0.8)
OGLE = ((0.50, 0.70, 0.95), 0.9)
AKSAM = ((0.98, 0.62, 0.42), 0.75)
GECE = ((0.03, 0.045, 0.11), 0.35)
SAFAK = ((0.30, 0.36, 0.55), 0.5)
G_BAS, G_BIT = 0.70, 0.90   # dönem içinde gece aralığı

for d in DON:
    a, b = d["bas"], d["bit"]
    L = b - a
    if d.get("son"):
        # uzun, altın ikindi ışığı; sonra yavaş kararma
        gok(a, (0.95, 0.75, 0.55), 0.7, 4.5, 18, -95, (1.0, 0.72, 0.45), 700)
        gok(b - 90, (0.85, 0.55, 0.42), 0.55, 3.2, 10, -100, (1.0, 0.62, 0.38), 500)
        gok(b, (0.25, 0.2, 0.25), 0.3, 0.8, 4, -104, (1.0, 0.55, 0.35), 250)
        continue
    gok(a, SABAH[0], SABAH[1], 3.0, 22, -120, (1.0, 0.88, 0.75), 900)
    gok(a + int(L * 0.32), OGLE[0], OGLE[1], 4.2, 55, -60, (1.0, 0.96, 0.9), 1000)
    gok(a + int(L * 0.58), AKSAM[0], AKSAM[1], 2.6, 12, -10, (1.0, 0.6, 0.35), 700)
    if d.get("gece"):
        gok(a + int(L * G_BAS), GECE[0], GECE[1], 0.0, -5, 10, (1.0, 0.6, 0.35), 180)
        gok(a + int(L * G_BIT), GECE[0], GECE[1], 0.0, -5, 10, (1.0, 0.6, 0.35), 180)
        gok(b, SAFAK[0], SAFAK[1], 0.6, 2, -125, (1.0, 0.7, 0.55), 500)


def donem(f):
    for d in DON:
        if d["bas"] <= f <= d["bit"]:
            return d
    return DON[-1]


def gece_mi(f):
    d = donem(f)
    L = d["bit"] - d["bas"]
    return bool(d.get("gece")) and d["bas"] + int(L * G_BAS) - 6 <= f <= d["bas"] + int(L * G_BIT)


def var_mi(ad, f):
    return any(a <= f <= b - 18 for a, b in donem_ar(ad))


rnd = random.Random(5)
for I in ISIKLAR:
    son = None
    for f in list(range(1, FR + 1, 2)) + [FR]:
        on = var_mi(I["ad"], f) and (I["tip"] == "surekli" or gece_mi(f))
        t = 1 + I["titre"] * rnd.uniform(-1, 1) if on else 0
        if on or son != on:
            I["veri"].energy = I["enerji"] * t
            I["veri"].keyframe_insert("energy", frame=f)
            soket_kf(bsdf(I["emat"]).inputs["Emission Strength"], f, I["eguc"] * t)
        son = on

# ---------------------------------------------------------------- kamera (yavaş yörünge + nefes alan zoom)
hedef = bos("hedef", 0.0, 0.0, 0.7)
pivot = bos("pivot", 0, 0, 0)
cam_d = bpy.data.cameras.new("kam")
cam_d.lens = 36
cam_d.sensor_width = 36
cam_d.dof.use_dof = True
cam_d.dof.focus_object = hedef
cam_d.dof.aperture_fstop = 1.4
kam = bpy.data.objects.new("kam", cam_d)
sc.collection.objects.link(kam)
kam.parent = pivot
kam.location = (10.2, -10.2, 9.0)
tr = kam.constraints.new("TRACK_TO")
tr.target = hedef
tr.track_axis = "TRACK_NEGATIVE_Z"
tr.up_axis = "UP_Y"
sc.camera = kam
kf(pivot, "rotation_euler", 1, (0, 0, math.radians(-14)), "SINE", "EASE_IN_OUT")
kf(pivot, "rotation_euler", FR, (0, 0, math.radians(22)), "SINE", "EASE_IN_OUT")
# açılış: yakından geri çekil; final: yavaşça yaklaş
kf(pivot, "scale", 1, (0.9, 0.9, 0.9), "SINE", "EASE_OUT")
kf(pivot, "scale", 75, (1.0, 1.0, 1.0), "SINE", "EASE_IN_OUT")
son_bas = next((d["bas"] for d in DON if d.get("son")), FR)
kf(pivot, "scale", son_bas, (1.0, 1.0, 1.0), "SINE", "EASE_IN_OUT")
kf(pivot, "scale", FR, (0.88, 0.88, 0.88), "SINE", "EASE_IN_OUT")

# ---------------------------------------------------------------- render
os.makedirs(OUT, exist_ok=True)
for f in range(F0, F1 + 1):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, f"{f:05d}.png")
    bpy.ops.render.render(write_still=True)
    print("KARE", f, flush=True)
