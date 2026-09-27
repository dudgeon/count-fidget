"""Blender scene for the Q5A (acrylic lid) renders. Import inside Blender 5.2:

    blender -b --python render_stills.py -- ...

Units are metres (real scale). The CAD frame is used throughout:
X = PCB_X - 21 mm, Y = 27 mm - PCB_Y, Z above the tray underside.
"""
import json
import math
from pathlib import Path

import bpy
from mathutils import Matrix, Vector

ROOT = Path(__file__).resolve().parents[2]
BUILD = ROOT / 'build/render-q5-acrylic'
TEX = BUILD / 'textures'
ASSETS = BUILD / 'assets'
OLED = BUILD / 'oled'
MM = 0.001


def meta():
    return json.loads((ASSETS / 'q5a-parts.json').read_text())


# ------------------------------------------------------------------ helpers
def srgb(h):
    """#rrggbb -> linear RGBA."""
    h = h.lstrip('#')
    out = []
    for i in (0, 2, 4):
        c = int(h[i:i + 2], 16) / 255
        out.append(c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4)
    return (*out, 1.0)


def new_mat(name):
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    return m, nt, out


def principled(name, base, metallic=0.0, rough=0.5, **kw):
    m, nt, out = new_mat(name)
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = base if len(base) == 4 else (*base, 1)
    b.inputs['Metallic'].default_value = metallic
    b.inputs['Roughness'].default_value = rough
    for k, v in kw.items():
        b.inputs[k].default_value = v
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m, nt, b, out


def sock(node, name, kind=None, out=False):
    socks = node.outputs if out else node.inputs
    for s in socks:
        if s.name == name and (kind is None or s.type == kind) and s.enabled:
            return s
    for s in socks:
        if s.name == name and (kind is None or s.type == kind):
            return s
    raise KeyError(name)


def mix(nt, kind, fac, a, b):
    """Mix node (RGBA or FLOAT). a/b/fac may be sockets or constants. Returns the result socket."""
    n = nt.nodes.new('ShaderNodeMix')
    n.data_type = kind
    t = 'RGBA' if kind == 'RGBA' else 'VALUE'
    for s, v in ((sock(n, 'Factor', 'VALUE'), fac), (sock(n, 'A', t), a), (sock(n, 'B', t), b)):
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, s)
        else:
            s.default_value = v
    return sock(n, 'Result', t, out=True)


def math_node(nt, op, a, b=None, c=None, clamp=False):
    n = nt.nodes.new('ShaderNodeMath')
    n.operation = op
    n.use_clamp = clamp
    for i, v in enumerate((a, b, c)):
        if v is None:
            continue
        if isinstance(v, bpy.types.NodeSocket):
            nt.links.new(v, n.inputs[i])
        else:
            n.inputs[i].default_value = v
    return n.outputs[0]


def shadow_transparent(nt, surface_socket, out, also_diffuse=True):
    """Glass that lets shadow (and diffuse) rays through: a standard trick that keeps the
    parts under the acrylic lit without caustics."""
    lp = nt.nodes.new('ShaderNodeLightPath')
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    fac = lp.outputs['Is Shadow Ray']
    if also_diffuse:
        fac = math_node(nt, 'MAXIMUM', fac, lp.outputs['Is Diffuse Ray'])
    ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(fac, ms.inputs[0])
    nt.links.new(surface_socket, ms.inputs[1])
    nt.links.new(tr.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs['Surface'])


def image(path, colorspace='Non-Color', alpha='CHANNEL_PACKED'):
    img = bpy.data.images.load(str(path), check_existing=True)
    img.colorspace_settings.name = colorspace
    try:
        img.alpha_mode = alpha
    except Exception:
        pass
    return img


# ------------------------------------------------------------------ materials
def pcb_material():
    """Green LPI soldermask over FR-4, ENIG pads, SAC solder on pasted pads, white silk,
    driven by the rasterised KiCad layers of the ordered board."""
    m, nt, out = new_mat('pcb')
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    u = math_node(nt, 'MULTIPLY_ADD', sep.outputs['X'], 1 / 0.042, 0.021 / 0.042)
    v = math_node(nt, 'MULTIPLY_ADD', sep.outputs['Y'], 1 / 0.054, 0.027 / 0.054)
    uv = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(u, uv.inputs[0])
    nt.links.new(v, uv.inputs[1])

    def tex(name, interp='Linear'):
        n = nt.nodes.new('ShaderNodeTexImage')
        n.image = image(TEX / name)
        n.interpolation = interp
        n.extension = 'CLIP'
        nt.links.new(uv.outputs[0], n.inputs['Vector'])
        return n
    top, bot, hgt, drl = tex('top_rgba.png'), tex('bot_rgba.png'), tex('height_rgba.png', 'Cubic'), tex('drill_rgba.png')
    nsep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Normal'], nsep.inputs[0])
    nz = nsep.outputs['Z']
    is_top = math_node(nt, 'GREATER_THAN', nz, 0.5)
    is_side = math_node(nt, 'LESS_THAN', math_node(nt, 'ABSOLUTE', nz), 0.5)
    ch = mix(nt, 'RGBA', is_top, bot.outputs['Color'], top.outputs['Color'])
    cs = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(ch, cs.inputs[0])
    cu, opening, silk = cs.outputs[0], cs.outputs[1], cs.outputs[2]
    paste = mix(nt, 'FLOAT', is_top, bot.outputs['Alpha'], top.outputs['Alpha'])
    hs = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(hgt.outputs['Color'], hs.inputs[0])
    cu_h = mix(nt, 'FLOAT', is_top, hs.outputs[1], hs.outputs[0])
    silk_h = mix(nt, 'FLOAT', is_top, hgt.outputs['Alpha'], hs.outputs[2])
    ds = nt.nodes.new('ShaderNodeSeparateColor')
    nt.links.new(drl.outputs['Color'], ds.inputs[0])
    plated = math_node(nt, 'GREATER_THAN', math_node(nt, 'MAXIMUM', ds.outputs[0], ds.outputs[2]), 0.02)
    mask_fr4, mask_cu = srgb('#0f4a26'), srgb('#2f7a3c')
    enig, solder, silk_c = (0.93, 0.74, 0.40, 1), (0.80, 0.80, 0.82, 1), (0.86, 0.87, 0.84, 1)
    fr4_edge = srgb('#b9b48a')
    col = mix(nt, 'RGBA', cu, mask_fr4, mask_cu)
    metal = mix(nt, 'RGBA', paste, enig, solder)
    col = mix(nt, 'RGBA', opening, col, metal)
    col = mix(nt, 'RGBA', silk, col, silk_c)
    side = mix(nt, 'RGBA', plated, fr4_edge, enig)
    col = mix(nt, 'RGBA', is_side, col, side)
    metallic = mix(nt, 'FLOAT', is_side, math_node(nt, 'MULTIPLY', opening, math_node(nt, 'SUBTRACT', 1.0, silk)), plated)
    rough = mix(nt, 'FLOAT', opening, 0.30, mix(nt, 'FLOAT', paste, 0.26, 0.14))
    rough = mix(nt, 'FLOAT', silk, rough, 0.62)
    rough = mix(nt, 'FLOAT', is_side, rough, mix(nt, 'FLOAT', plated, 0.7, 0.3))
    coat = math_node(nt, 'MULTIPLY', math_node(nt, 'SUBTRACT', 1.0, opening), math_node(nt, 'SUBTRACT', 1.0, is_side))
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    nt.links.new(col, b.inputs['Base Color'])
    nt.links.new(metallic, b.inputs['Metallic'])
    nt.links.new(rough, b.inputs['Roughness'])
    nt.links.new(math_node(nt, 'MULTIPLY', coat, 0.55), b.inputs['Coat Weight'])
    b.inputs['Coat Roughness'].default_value = 0.08
    b.inputs['Coat IOR'].default_value = 1.52
    # Height: copper under the mask, silk on top, mask openings recessed, faint orange peel.
    noise = nt.nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value = 900.0
    noise.inputs['Detail'].default_value = 3.0
    nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
    h = math_node(nt, 'MULTIPLY_ADD', cu_h, 1.0, math_node(nt, 'MULTIPLY', silk_h, 0.55))
    h = math_node(nt, 'SUBTRACT', h, math_node(nt, 'MULTIPLY', opening, 0.45))
    h = math_node(nt, 'MULTIPLY_ADD', noise.outputs['Fac'], 0.05, h)
    h = math_node(nt, 'MULTIPLY', h, math_node(nt, 'SUBTRACT', 1.0, is_side))
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Distance'].default_value = 3.5e-5
    bump.inputs['Strength'].default_value = 1.0
    nt.links.new(h, bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    nt.links.new(b.outputs[0], out.inputs['Surface'])
    return m


def acrylic_material(name='acrylic', ior=1.49, rough=0.0, tint=(1, 1, 1, 1)):
    m, nt, out = new_mat(name)
    g = nt.nodes.new('ShaderNodeBsdfPrincipled')
    g.inputs['Base Color'].default_value = tint
    g.inputs['Transmission Weight'].default_value = 1.0
    g.inputs['Roughness'].default_value = rough
    g.inputs['IOR'].default_value = ior
    shadow_transparent(nt, g.outputs[0], out)
    return m


def printed_material(name, colour, rough=0.52, layer=0.00016, layer_depth=1.0):
    """3D-printed plastic: satin base, fine horizontal layer lines on walls."""
    m, nt, b, out = principled(name, colour, rough=rough)
    b.inputs['Specular IOR Level'].default_value = 0.42
    if layer:
        tc = nt.nodes.new('ShaderNodeTexCoord')
        sep = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Object'], sep.inputs[0])
        wave = math_node(nt, 'SINE', math_node(nt, 'MULTIPLY', sep.outputs['Z'], 2 * math.pi / layer))
        wave = math_node(nt, 'POWER', math_node(nt, 'ABSOLUTE', wave), 0.6)
        noise = nt.nodes.new('ShaderNodeTexNoise')
        noise.inputs['Scale'].default_value = 400.0
        nt.links.new(tc.outputs['Object'], noise.inputs['Vector'])
        hgt = math_node(nt, 'MULTIPLY_ADD', noise.outputs['Fac'], 0.25, wave)
        bump = nt.nodes.new('ShaderNodeBump')
        bump.inputs['Distance'].default_value = 1.2e-5 * layer_depth
        nt.links.new(hgt, bump.inputs['Height'])
        nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def keycap_material(name, colour, legend_colour, top_z):
    """Keycap with a paint-filled engraved legend: faces 0.2 mm or more below the top face are the legend floor."""
    m, nt, b, out = principled(name, colour, rough=0.38)
    b.inputs['Specular IOR Level'].default_value = 0.45
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    nsep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Normal'], nsep.inputs[0])
    floor = math_node(nt, 'MULTIPLY', math_node(nt, 'LESS_THAN', sep.outputs['Z'], top_z - 0.00022),
                      math_node(nt, 'GREATER_THAN', sep.outputs['Z'], top_z - 0.0006))
    walls = math_node(nt, 'MULTIPLY', math_node(nt, 'GREATER_THAN', sep.outputs['Z'], top_z - 0.0006),
                      math_node(nt, 'LESS_THAN', math_node(nt, 'ABSOLUTE', nsep.outputs['Z']), 0.5))
    walls = math_node(nt, 'MULTIPLY', walls, math_node(nt, 'GREATER_THAN', sep.outputs['Z'], top_z - 0.0012))
    fac = math_node(nt, 'MAXIMUM', floor, math_node(nt, 'MULTIPLY', walls, 0.0))
    col = mix(nt, 'RGBA', fac, colour, legend_colour)
    nt.links.new(col, b.inputs['Base Color'])
    return m


def oled_material(frame_png, strength=6.0):
    m, nt, out = new_mat('oled_active')
    md = meta()
    cx, cy = md['oled_active_center']
    w, h = md['oled_active_size']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    u = math_node(nt, 'MULTIPLY_ADD', sep.outputs['X'], 1 / (w * MM), -(cx - w / 2) / w)
    v = math_node(nt, 'MULTIPLY_ADD', sep.outputs['Y'], 1 / (h * MM), -(cy - h / 2) / h)
    uv = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(u, uv.inputs[0])
    nt.links.new(v, uv.inputs[1])
    t = nt.nodes.new('ShaderNodeTexImage')
    t.name = 'frame'
    t.image = image(frame_png, 'sRGB', 'STRAIGHT')
    t.interpolation = 'Closest'
    t.extension = 'CLIP'
    nt.links.new(uv.outputs[0], t.inputs['Vector'])
    gx = math_node(nt, 'LESS_THAN', math_node(nt, 'FRACT', math_node(nt, 'MULTIPLY', u, 128)), 0.88)
    gy = math_node(nt, 'LESS_THAN', math_node(nt, 'FRACT', math_node(nt, 'MULTIPLY', v, 64)), 0.88)
    lit = math_node(nt, 'MULTIPLY', math_node(nt, 'MULTIPLY', gx, gy), sock(t, 'Color', out=True))
    em = nt.nodes.new('ShaderNodeEmission')
    em.inputs['Color'].default_value = (0.86, 0.93, 1.0, 1)
    em.name = 'emission'
    nt.links.new(math_node(nt, 'MULTIPLY', lit, strength), em.inputs['Strength'])
    base = nt.nodes.new('ShaderNodeBsdfPrincipled')
    base.inputs['Base Color'].default_value = (0.004, 0.004, 0.005, 1)
    base.inputs['Roughness'].default_value = 0.12
    add = nt.nodes.new('ShaderNodeAddShader')
    nt.links.new(base.outputs[0], add.inputs[0])
    nt.links.new(em.outputs[0], add.inputs[1])
    nt.links.new(add.outputs[0], out.inputs['Surface'])
    return m


def label_material(name, png, base_colour, ink=(0.08, 0.08, 0.09, 1), metallic=1.0, rough=0.22):
    """Metal face with a printed/laser-marked label from an RGBA image mapped on object XY."""
    m, nt, b, out = principled(name, base_colour, metallic=metallic, rough=rough)
    return m


def decal_mix(nt, b, png, cx, cy, w, h, ink, rough=None, top_only=True, metallic=None):
    """Mix an RGBA decal (alpha = ink) into a Principled BSDF using object XY (metres, CAD frame)."""
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    u = math_node(nt, 'MULTIPLY_ADD', sep.outputs['X'], 1 / (w * MM), -(cx - w / 2) / w)
    v = math_node(nt, 'MULTIPLY_ADD', sep.outputs['Y'], 1 / (h * MM), -(cy - h / 2) / h)
    uv = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(u, uv.inputs[0])
    nt.links.new(v, uv.inputs[1])
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = image(png, 'Non-Color', 'STRAIGHT')
    t.extension = 'CLIP'
    nt.links.new(uv.outputs[0], t.inputs['Vector'])
    fac = t.outputs['Alpha']
    if top_only:
        ns = nt.nodes.new('ShaderNodeSeparateXYZ')
        nt.links.new(tc.outputs['Normal'], ns.inputs[0])
        fac = math_node(nt, 'MULTIPLY', fac, math_node(nt, 'GREATER_THAN', math_node(nt, 'ABSOLUTE', ns.outputs['Z']), 0.5))
    base = b.inputs['Base Color'].default_value[:]
    nt.links.new(mix(nt, 'RGBA', fac, base, ink), b.inputs['Base Color'])
    if rough is not None:
        nt.links.new(mix(nt, 'FLOAT', fac, b.inputs['Roughness'].default_value, rough), b.inputs['Roughness'])
    if metallic is not None:
        nt.links.new(mix(nt, 'FLOAT', fac, b.inputs['Metallic'].default_value, metallic), b.inputs['Metallic'])
    return fac


def build_materials(opts):
    mats = {}
    mats['pcb'] = pcb_material()
    mats['acrylic'] = acrylic_material()
    mats['pc_clear'] = acrylic_material('pc_clear', ior=1.585, rough=0.035, tint=(0.97, 0.985, 1.0, 1))
    mats['tray'] = printed_material('tray', opts['tray_colour'])
    top = 0.0          # keycap origins are moved to the top face (build(): set_origin), so object z = 0 there
    mats['keycap_count'] = keycap_material('keycap_count', opts['count_colour'], opts['legend_colour'], top)
    mats['keycap_reset'] = keycap_material('keycap_reset', opts['reset_colour'], opts['legend_colour'], top)
    mats['brass'] = principled('brass', (0.93, 0.72, 0.42, 1), 1.0, 0.24)[0]
    mats['steel_screw'] = principled('steel_screw', (0.66, 0.66, 0.65, 1), 1.0, 0.2, **{'Anisotropic': 0.3})[0]
    mats['plastic_black'] = principled('plastic_black', srgb('#141517'), 0.0, 0.5)[0]
    mats['pom_cyan'] = principled('pom_cyan', srgb('#29a9e1'), 0.0, 0.34, **{'Subsurface Weight': 0.15, 'Subsurface Radius': (0.001, 0.001, 0.001)})[0]
    mats['pom_white'] = principled('pom_white', srgb('#eeeeea'), 0.0, 0.4)[0]
    mats['steel_spring'] = principled('steel_spring', (0.7, 0.7, 0.7, 1), 1.0, 0.22)[0]
    mats['gold'] = principled('gold', (1.0, 0.77, 0.36, 1), 1.0, 0.22)[0]
    md = meta()
    m, nt, b, _ = principled('pcb_blue', srgb('#12448f'), 0.0, 0.24, **{'Coat Weight': 0.5, 'Coat Roughness': 0.06})
    mx, my = md['oled_module_center']
    decal_mix(nt, b, ASSETS / 'oled_silk.png', mx, my, 27.3, 27.8, (0.86, 0.87, 0.85, 1), rough=0.6)
    mats['pcb_blue'] = m
    mats['tin_pads'] = principled('tin_pads', (0.86, 0.86, 0.87, 1), 1.0, 0.16)[0]
    mats['glass_edge'] = principled('glass_edge', (0.012, 0.015, 0.016, 1), 0.0, 0.03, **{'Specular IOR Level': 0.6})[0]
    mats['glass_top'] = principled('glass_top', (0.006, 0.006, 0.008, 1), 0.0, 0.02, **{'Specular IOR Level': 0.6})[0]
    mats['polariser'] = principled('polariser', (0.004, 0.004, 0.005, 1), 0.0, 0.07)[0]
    mats['oled_active'] = oled_material(opts['oled_frame'])
    mats['cog_die'] = principled('cog_die', (0.16, 0.16, 0.18, 1), 0.6, 0.25)[0]
    mats['fpc_kapton'] = principled('fpc_kapton', srgb('#d8871f'), 0.0, 0.28, **{'Coat Weight': 0.4, 'Subsurface Weight': 0.1})[0]
    mats['smd_body'] = principled('smd_body', srgb('#8a6c50'), 0.0, 0.5)[0]
    mats['tin_pins'] = principled('tin_pins', (0.82, 0.82, 0.83, 1), 1.0, 0.25)[0]
    mats['solder'] = principled('solder', (0.84, 0.84, 0.86, 1), 1.0, 0.1)[0]
    mats['nylon_ivory'] = principled('nylon_ivory', srgb('#ebe4d2'), 0.0, 0.5, **{'Subsurface Weight': 0.08})[0]
    mats['tin_contacts'] = principled('tin_contacts', (0.82, 0.82, 0.83, 1), 1.0, 0.3)[0]
    mats['steel_cell'] = principled('steel_cell', (0.72, 0.72, 0.73, 1), 1.0, 0.24, **{'Anisotropic': 0.5})[0]
    m, nt, out = new_mat('cell_label')
    b = nt.nodes.new('ShaderNodeBsdfPrincipled')
    b.inputs['Base Color'].default_value = (0.05, 0.05, 0.055, 1)
    b.inputs['Roughness'].default_value = 0.55
    cx, cy = md['bt1_center']
    t = nt.nodes.new('ShaderNodeTexImage')
    t.image = image(ASSETS / 'cell_label.png', 'Non-Color', 'STRAIGHT')
    t.extension = 'CLIP'
    tc = nt.nodes.new('ShaderNodeTexCoord')
    sep = nt.nodes.new('ShaderNodeSeparateXYZ')
    nt.links.new(tc.outputs['Object'], sep.inputs[0])
    uu = math_node(nt, 'MULTIPLY_ADD', sep.outputs['X'], 1 / (20 * MM), -(cx - 10) / 20)
    vv = math_node(nt, 'MULTIPLY_ADD', sep.outputs['Y'], 1 / (20 * MM), -(cy - 10) / 20)
    uvn = nt.nodes.new('ShaderNodeCombineXYZ')
    nt.links.new(uu, uvn.inputs[0])
    nt.links.new(vv, uvn.inputs[1])
    nt.links.new(uvn.outputs[0], t.inputs['Vector'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    ms = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(math_node(nt, 'MULTIPLY', t.outputs['Alpha'], 0.8), ms.inputs[0])
    nt.links.new(tr.outputs[0], ms.inputs[1])
    nt.links.new(b.outputs[0], ms.inputs[2])
    nt.links.new(ms.outputs[0], out.inputs['Surface'])
    mats['cell_label'] = m
    mats['pa_purple'] = principled('pa_purple', srgb('#6b58b4'), 0.0, 0.46)[0]
    mats['steel_satin'] = principled('steel_satin', (0.74, 0.74, 0.75, 1), 1.0, 0.32)[0]
    # KiCad component STEP colours.
    mats['epoxy'] = principled('epoxy', srgb('#1a1a1c'), 0.0, 0.42, **{'Specular IOR Level': 0.45})[0]
    mats['resistor'] = principled('resistor', srgb('#111113'), 0.0, 0.55)[0]
    mats['mlcc'] = principled('mlcc', srgb('#9b7a5a'), 0.0, 0.45)[0]
    mats['tin'] = principled('tin', (0.80, 0.80, 0.80, 1), 1.0, 0.3)[0]
    mats['stainless'] = principled('stainless', (0.72, 0.71, 0.69, 1), 1.0, 0.16)[0]
    mats['plastic_dark'] = principled('plastic_dark', srgb('#26282b'), 0.0, 0.5)[0]
    mats['backdrop'] = principled('backdrop', opts['backdrop_colour'], 0.0, 0.85)[0]
    mats['marking'] = principled('marking', srgb('#8e9092'), 0.0, 0.7)[0]
    return mats


# ------------------------------------------------------------------ import
def bake_to_world(objs, scale=1.0, offset=(0, 0, 0)):
    """Unparent, apply scale/offset in world space and bake into mesh data: object origin = world origin."""
    S = Matrix.Translation(offset) @ Matrix.Scale(scale, 4)
    for o in objs:
        mw = o.matrix_world.copy()
        o.parent = None
        o.matrix_world = S @ mw
    for o in objs:
        if o.type != 'MESH':
            continue
        o.data = o.data.copy() if o.data.users > 1 else o.data
        o.data.transform(o.matrix_world)
        o.matrix_world = Matrix.Identity(4)


def import_glb(path):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.gltf(filepath=str(path), merge_vertices=False)
    return [o for o in bpy.data.objects if o not in before]


def top_parent_name(o):
    while o.parent is not None and o.parent.parent is not None:
        o = o.parent
    return o.name


def classify_kicad(o, ref):
    m = o.material_slots[0].material if o.material_slots and o.material_slots[0].material else None
    if m is None or not m.node_tree:
        return 'epoxy'
    p = m.node_tree.nodes.get('Principled BSDF')
    c = p.inputs['Base Color'].default_value if p else (0.5, 0.5, 0.5, 1)
    metal = p.inputs['Metallic'].default_value if p else 0
    lum = 0.3 * c[0] + 0.5 * c[1] + 0.2 * c[2]
    if ref.startswith('J'):
        return 'stainless' if lum > 0.2 else ('gold' if c[0] > c[2] * 2 and lum > 0.1 else 'plastic_dark')
    if c[0] > 0.6 and c[2] < 0.3 and c[1] > 0.4:
        return 'gold'
    if lum > 0.3:
        return 'tin'
    if c[0] > 0.09 and c[0] > c[2] * 2.2:
        return 'mlcc'
    if ref.startswith('R') and lum < 0.012:
        return 'resistor'
    return 'epoxy'


def load_board(mats):
    """KiCad GLB (metres, board frame) -> CAD frame; PCB body gets the textured shader."""
    md = meta()
    objs = import_glb(TEX / 'board.glb')
    board, parts = None, []
    refs = {}
    for o in objs:
        if o.type != 'MESH':
            continue
        name = top_parent_name(o)
        refs[o.name] = name
    # The board body is the root-level mesh with the 42 x 54 mm footprint.
    def span(o):
        xs = [(o.matrix_world @ Vector(c)) for c in o.bound_box]
        return (max(v.x for v in xs) - min(v.x for v in xs)) * (max(v.y for v in xs) - min(v.y for v in xs))
    body = max((o for o in objs if o.type == 'MESH' and refs[o.name] == o.name), key=span)
    bake_to_world(objs, 1.0, (-0.021, 0.027, md['pcb_z'] * MM))
    for o in objs:
        if o.type != 'MESH':
            continue
        name = refs[o.name]
        if o == body:
            board = o
            o.data.materials.clear()
            o.data.materials.append(mats['pcb'])
            continue
        key = classify_kicad(o, name.split('.')[0].split('_')[0])
        o.data.materials.clear()
        o.data.materials.append(mats[key])
        o['ref'] = name
        parts.append(o)
    for o in objs:
        if o.type == 'EMPTY':
            bpy.data.objects.remove(o)
    assert board is not None, 'PCB body not found in board.glb'
    board.name = 'pcb_body'
    for f in board.data.polygons:
        f.use_smooth = False
    return board, parts


def load_parts(mats):
    objs = import_glb(ASSETS / 'q5a-parts.glb')
    bake_to_world(objs, MM)
    out = {}
    for o in objs:
        if o.type != 'MESH':
            continue
        n = o.name if '|' in o.name else (o.parent.name if o.parent else o.name)
        mat, _, part = n.partition('|')
        part = part.split('.')[0]
        o.name = part
        o.data.materials.clear()
        o.data.materials.append(mats[mat])
        o['mat'] = mat
        out[part] = o
        try:
            for f in o.data.polygons:
                f.use_smooth = True
            o.data.set_sharp_from_angle(angle=math.radians(35))
        except Exception:
            pass
    for o in objs:
        if o.type == 'EMPTY' and o.name in bpy.data.objects:
            bpy.data.objects.remove(o)
    return out


def set_origin(o, point):
    """Move the object origin to a world point without moving the geometry."""
    p = Vector(point)
    o.data.transform(Matrix.Translation(-p))
    o.matrix_world = Matrix.Translation(p) @ o.matrix_world


def group(name, children, origin=(0, 0, 0)):
    """Parent unparented, baked objects to a new empty at `origin` without moving them.
    Uses matrix_basis explicitly: matrix_world is stale until the depsgraph updates."""
    e = bpy.data.objects.new(name, None)
    bpy.context.scene.collection.objects.link(e)
    e.location = origin
    inv = Matrix.Translation(Vector(origin)).inverted()
    for c in children:
        assert c.parent is None
        basis = c.matrix_basis.copy()
        c.parent = e
        c.matrix_parent_inverse = inv
        c.matrix_basis = basis
    bpy.context.view_layer.update()
    return e


def add_markings(board_parts, mats):
    """Laser marks on the two large packages (part numbers only)."""
    marks = []
    for ref, lines, size in (('U1', ['STM32L072', 'CBT6'], 0.00085), ('U8', ['FM25V02A'], 0.00062)):
        objs = [o for o in board_parts if o.get('ref', '').startswith(ref)]
        if not objs:
            continue
        lo = Vector((min(v[0] for o in objs for v in o.bound_box), min(v[1] for o in objs for v in o.bound_box), min(v[2] for o in objs for v in o.bound_box)))
        hi = Vector((max(v[0] for o in objs for v in o.bound_box), max(v[1] for o in objs for v in o.bound_box), max(v[2] for o in objs for v in o.bound_box)))
        c = (lo + hi) / 2
        for i, text in enumerate(lines):
            cu = bpy.data.curves.new(f'mark-{ref}-{i}', 'FONT')
            cu.body = text
            cu.size = size
            cu.align_x = 'CENTER'
            cu.align_y = 'CENTER'
            ob = bpy.data.objects.new(f'mark-{ref}-{i}', cu)
            bpy.context.scene.collection.objects.link(ob)
            dy = (0.5 - i) * size * 1.35 if len(lines) > 1 else 0
            ob.location = (c.x, c.y + dy, lo.z - 0.000004)
            ob.rotation_euler = (0, math.pi, 0)       # bottom-side part: readable from below, and upright once the board rolls over Y
            ob.data.materials.append(mats['marking'])
            marks.append(ob)
    return marks


# ------------------------------------------------------------------ studio
def cyclorama(mat, size=1.2, radius=0.25):
    import bmesh
    bm = bmesh.new()
    prof = [(-size, 0.0)]
    for i in range(17):
        a = -math.pi / 2 + (math.pi / 2) * i / 16
        prof.append((0.35 + radius * math.cos(a) * 1.0, radius + radius * math.sin(a)))
    prof = [(-size, 0.0), (0.35, 0.0)] + [(0.35 + radius * math.sin(math.pi / 2 * i / 16), radius - radius * math.cos(math.pi / 2 * i / 16)) for i in range(1, 17)] + [(0.35 + radius, size)]
    rows = []
    for x in (-size, size):
        rows.append([bm.verts.new((x, y, z)) for y, z in prof])
    for j in range(len(prof) - 1):
        bm.faces.new((rows[0][j], rows[1][j], rows[1][j + 1], rows[0][j + 1]))
    me = bpy.data.meshes.new('cyclorama')
    bm.to_mesh(me)
    ob = bpy.data.objects.new('cyclorama', me)
    bpy.context.scene.collection.objects.link(ob)
    for f in me.polygons:
        f.use_smooth = True
    me.materials.append(mat)
    return ob


def area_light(name, loc, target, power, size, size_y=None, colour=(1, 1, 1)):
    ld = bpy.data.lights.new(name, 'AREA')
    ld.shape = 'RECTANGLE'
    ld.size = size
    ld.size_y = size_y or size
    ld.energy = power
    ld.color = colour
    ob = bpy.data.objects.new(name, ld)
    bpy.context.scene.collection.objects.link(ob)
    ob.location = loc
    d = Vector(target) - Vector(loc)
    ob.rotation_euler = d.to_track_quat('-Z', 'Y').to_euler()
    return ob


def world_hdri(path, strength=0.35, rotation=0.0, background=None):
    w = bpy.data.worlds.new('studio')
    bpy.context.scene.world = w
    try:
        w.use_nodes = True
    except Exception:
        pass
    nt = w.node_tree
    nt.nodes.clear()
    out = nt.nodes.new('ShaderNodeOutputWorld')
    env = nt.nodes.new('ShaderNodeTexEnvironment')
    env.image = bpy.data.images.load(str(path), check_existing=True)
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Rotation'].default_value = (0, 0, rotation)
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nt.links.new(tc.outputs['Generated'], mp.inputs['Vector'])
    nt.links.new(mp.outputs[0], env.inputs['Vector'])
    bg = nt.nodes.new('ShaderNodeBackground')
    bg.inputs['Strength'].default_value = strength
    nt.links.new(env.outputs['Color'], bg.inputs['Color'])
    if background is not None:
        lp = nt.nodes.new('ShaderNodeLightPath')
        flat = nt.nodes.new('ShaderNodeBackground')
        flat.inputs['Color'].default_value = background
        flat.inputs['Strength'].default_value = 1.0
        ms = nt.nodes.new('ShaderNodeMixShader')
        nt.links.new(lp.outputs['Is Camera Ray'], ms.inputs[0])
        nt.links.new(bg.outputs[0], ms.inputs[1])
        nt.links.new(flat.outputs[0], ms.inputs[2])
        nt.links.new(ms.outputs[0], out.inputs['Surface'])
    else:
        nt.links.new(bg.outputs[0], out.inputs['Surface'])
    return w


def configure_render(samples=256, res=(1920, 1080), threshold=0.01, motion_blur=False):
    sc = bpy.context.scene
    sc.render.engine = 'CYCLES'
    cy = sc.cycles
    cy.device = 'CPU'
    cy.samples = samples
    cy.use_adaptive_sampling = True
    cy.adaptive_threshold = threshold
    cy.use_denoising = True
    try:
        cy.denoiser = 'OPENIMAGEDENOISE'
        cy.denoising_input_passes = 'RGB_ALBEDO_NORMAL'
        cy.denoising_prefilter = 'ACCURATE'
        cy.denoising_quality = 'HIGH'
    except Exception:
        pass
    cy.max_bounces = 10
    cy.diffuse_bounces = 3
    cy.glossy_bounces = 4
    cy.transmission_bounces = 10
    cy.transparent_max_bounces = 16
    cy.caustics_reflective = False
    cy.caustics_refractive = False
    cy.blur_glossy = 0.6
    cy.sample_clamp_indirect = 4.0
    cy.film_exposure = 1.0
    try:
        cy.use_light_tree = True
    except Exception:
        pass
    sc.render.resolution_x, sc.render.resolution_y = res
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.use_motion_blur = motion_blur
    sc.render.image_settings.file_format = 'PNG'
    sc.render.image_settings.color_depth = '8'
    vs = sc.view_settings
    vs.view_transform = 'AgX'
    for look in ('AgX - Medium High Contrast', 'Medium High Contrast', 'AgX - Base Contrast'):
        try:
            vs.look = look
            break
        except Exception:
            continue
    sc.render.use_persistent_data = True


def lean_paths():
    """Path depth and material settings shared by stills and film: enough bounces for the lid and
    switch housings, no subsurface (it multiplied CPU render time for no visible gain)."""
    cy = bpy.context.scene.cycles
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 6, 1, 2, 6
    cy.transparent_max_bounces = 12
    cy.denoising_prefilter = 'FAST'
    cy.adaptive_min_samples = 16
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Subsurface Weight'].default_value = 0.0


def camera(name='cam', lens=85, sensor=36):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = sensor
    cd.clip_start = 0.002
    cd.clip_end = 20
    ob = bpy.data.objects.new(name, cd)
    bpy.context.scene.collection.objects.link(ob)
    bpy.context.scene.camera = ob
    return ob


def aim(ob, loc, target, roll=0.0):
    ob.location = Vector(loc)
    d = Vector(target) - Vector(loc)
    q = d.to_track_quat('-Z', 'Y')
    ob.rotation_euler = q.to_euler()
    if roll:
        ob.rotation_euler.rotate_axis('Z', roll)


def dof(cam, focus, fstop):
    cam.data.dof.use_dof = fstop is not None
    if fstop is not None:
        cam.data.dof.focus_distance = focus
        cam.data.dof.aperture_fstop = fstop


# ------------------------------------------------------------------ top level
DEFAULTS = dict(tray_colour=srgb('#3a3b3e'), count_colour=srgb('#f2f1ed'), reset_colour=srgb('#f2f1ed'),
                legend_colour=srgb('#3a3b3e'), backdrop_colour=srgb('#d9d8d4'),
                oled_frame=OLED / 'oled_108_none.png', hdri=ASSETS / 'studio_small_09_4k.exr')


def build(**opts):
    o = dict(DEFAULTS)
    o.update(opts)
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    sc.unit_settings.system = 'METRIC'
    mats = build_materials(o)
    board, kicad_parts = load_board(mats)
    parts = load_parts(mats)
    marks = add_markings(kicad_parts, mats)
    md = meta()
    # Screws rotate about their own axes; give them local origins.
    for i, (x, y) in enumerate(md['mounts'], 1):
        set_origin(parts[f'screw-{i}'], (x * MM, y * MM, md['lid_top'] * MM))
        set_origin(parts[f'spacer-{i}'], (x * MM, y * MM, md['pcb_top'] * MM))
    for i, (x, y) in enumerate(md['keys'], 1):
        set_origin(parts[f'keycap-{i}'], (x * MM, y * MM, md['keycap_top'] * MM))
    pcb_names = [n for n in parts if n.startswith(('oled', 'bt1', 'sw1-socket', 'sw2-socket', 'sw3'))]
    G = {}
    G['pcb'] = group('G_PCB', [board] + kicad_parts + marks + [parts[n] for n in pcb_names], origin=(0, 0, (md['pcb_z'] + 0.8) * MM))
    G['tray'] = group('G_TRAY', [parts['tray']])
    for i in (1, 2):
        G[f'sw{i}'] = group(f'G_SW{i}', [parts[n] for n in parts if n.startswith(f'switch-{i}-')])
        G[f'key{i}'] = group(f'G_KEY{i}', [parts[f'keycap-{i}']])
    G['lid'] = group('G_LID', [parts['lid']] + [parts[f'spacer-{i}'] for i in range(1, 5)] + [parts[f'screw-{i}'] for i in range(1, 5)])
    cyclorama(mats['backdrop'])
    world_hdri(o['hdri'], strength=o.get('hdri_strength', 0.22), rotation=o.get('hdri_rotation', 0.6))
    home = {k: g.location.copy() for k, g in G.items()}
    return dict(G=G, parts=parts, board=board, kicad=kicad_parts, mats=mats, meta=md, opts=o, home=home)


def studio_lights(key=3.2, fill=0.8, rim=2.2, top=1.1, scale=1.0):
    L = {}
    L['key'] = area_light('key', (-0.22 * scale, -0.20 * scale, 0.30 * scale), (0, 0, 0.01), key, 0.22, 0.16)
    L['fill'] = area_light('fill', (0.30 * scale, -0.12 * scale, 0.16 * scale), (0, 0, 0.01), fill, 0.30, 0.30)
    L['rim'] = area_light('rim', (0.05 * scale, 0.32 * scale, 0.12 * scale), (0, 0, 0.012), rim, 0.40, 0.05)
    L['top'] = area_light('top', (0.0, 0.0, 0.45 * scale), (0, 0, 0), top, 0.5, 0.5)
    return L
