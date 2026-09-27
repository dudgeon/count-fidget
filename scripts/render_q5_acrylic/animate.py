"""Build the Q5A assembly film (animation + cameras) and save it as a .blend.

blender -b --python scripts/render_q5_acrylic/animate.py -- [--out build/render-q5-acrylic/film.blend]

24 fps. Shots (frames):
  1   1-120   macro glide over the component side of the ordered board
  2 121-228   pull back; the board rolls over to show the display side
  3 229-336   the board settles into the printed tray
  4 337-420   the clicky switches press into the hot-swap sockets
  5 421-540   the acrylic lid, spacers and screws come down as one
  6 541-672   screws driven home (macro, then wide)
  7 673-744   keycaps
  8 745-876   display wakes; three presses count 0 -> 3
  9 877-984   final orbit and hold
"""
import json
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

sys.path.insert(0, str(Path(__file__).resolve().parent))
import scene as S  # noqa: E402

MM = S.MM
FPS = 24
SHOTS = [(1, 120), (121, 228), (229, 336), (337, 420), (421, 540), (541, 672), (673, 744), (745, 876), (877, 984)]
END = SHOTS[-1][1]


def key(obj, path, frame, value, index=-1, interp='BEZIER', ease='AUTO'):
    if index >= 0:
        getattr(obj, path)[index] = value
    else:
        setattr(obj, path, value)
    obj.keyframe_insert(path, frame=frame, index=index)
    fc = None
    ad = obj.animation_data
    if ad and ad.action:
        for f in _fcurves(ad.action):
            if f.data_path == path and (index < 0 or f.array_index == index):
                for kp in f.keyframe_points:
                    if int(round(kp.co.x)) == frame:
                        kp.interpolation = interp
                        kp.easing = ease


def _fcurves(action):
    try:
        return action.fcurves
    except AttributeError:          # layered actions (Blender 4.4+)
        out = []
        for layer in action.layers:
            for strip in layer.strips:
                for bag in strip.channelbags:
                    out.extend(bag.fcurves)
        return out


def keyv(obj, path, frame, vec, interp='BEZIER'):
    setattr(obj, path, vec)
    obj.keyframe_insert(path, frame=frame)
    for f in _fcurves(obj.animation_data.action):
        if f.data_path == path:
            for kp in f.keyframe_points:
                if int(round(kp.co.x)) == frame:
                    kp.interpolation = interp


def hide(obj, frame, hidden):
    for o in [obj] + list(obj.children_recursive):
        o.hide_render = hidden
        o.keyframe_insert('hide_render', frame=frame)
        for f in _fcurves(o.animation_data.action):
            if f.data_path == 'hide_render':
                for kp in f.keyframe_points:
                    kp.interpolation = 'CONSTANT'


def shot_camera(name, lens, keys, fstop=None, focus_keys=None):
    """keys: [(frame, location, target)], focus_keys: [(frame, point)]"""
    cam = S.camera(name, lens=lens)
    tgt = bpy.data.objects.new(name + '_target', None)
    bpy.context.scene.collection.objects.link(tgt)
    c = cam.constraints.new('TRACK_TO')
    c.target = tgt
    c.track_axis = 'TRACK_NEGATIVE_Z'
    c.up_axis = 'UP_Y'
    for f, loc, t in keys:
        keyv(cam, 'location', f, Vector(loc))
        keyv(tgt, 'location', f, Vector(t))
    if fstop:
        cam.data.dof.use_dof = True
        cam.data.dof.aperture_fstop = fstop
        foc = bpy.data.objects.new(name + '_focus', None)
        bpy.context.scene.collection.objects.link(foc)
        cam.data.dof.focus_object = foc
        for f, p in (focus_keys or [(k[0], k[2]) for k in keys]):
            keyv(foc, 'location', f, Vector(p))
    return cam


def oled_sequence(folder, schedule):
    """Write one 128 x 64 PNG per frame from [(first_frame, png or None)] and return the first file."""
    from shutil import copyfile
    folder.mkdir(parents=True, exist_ok=True)
    black = folder / 'black.png'
    if not black.exists():
        img = bpy.data.images.new('black', 128, 64)
        img.pixels = [0.0, 0.0, 0.0, 1.0] * (128 * 64)
        img.filepath_raw = str(black)
        img.file_format = 'PNG'
        img.save()
    sched = sorted(schedule)
    for f in range(1, END + 1):
        src = black
        for start, png in sched:
            if f >= start:
                src = black if png is None else S.OLED / png
        copyfile(src, folder / f'oled_{f:04d}.png')
    return folder / 'oled_0001.png'


def build(args):
    ctx = S.build()
    sc = bpy.context.scene
    sc.render.fps = FPS
    sc.frame_start, sc.frame_end = 1, END
    L = S.studio_lights()
    G, P, md = ctx['G'], ctx['parts'], ctx['meta']
    lid_top, pcb_top = md['lid_top'] * MM, md['pcb_top'] * MM

    # ---------------- display: per-frame firmware frames + wake-up ramp
    first = oled_sequence(S.BUILD / 'oled_seq', [(1, None), (752, 'oled_0_none.png'), (806, 'oled_1_none.png'),
                                                  (830, 'oled_2_none.png'), (854, 'oled_3_none.png')])
    nt = ctx['mats']['oled_active'].node_tree
    tex = nt.nodes['frame']
    img = bpy.data.images.load(str(first))
    img.source = 'SEQUENCE'
    img.colorspace_settings.name = 'sRGB'
    tex.image = img
    tex.image_user.frame_duration = END
    tex.image_user.frame_start = 1
    tex.image_user.frame_offset = 0
    tex.image_user.use_auto_refresh = True
    em = nt.nodes['emission']
    strength = [l for l in nt.links if l.to_socket == em.inputs['Strength']][0].from_node
    k = strength.inputs[1]
    k.default_value = 0.0
    k.keyframe_insert('default_value', frame=751)
    k.default_value = 6.0
    k.keyframe_insert('default_value', frame=764)

    # ---------------- board: shots 1-3 (G_PCB pivots about the board centre)
    pcb, H = G['pcb'], ctx['home']
    h = H['pcb']
    hi = h.z + 0.036                      # component side up, high above the (hidden) tray
    keyv(pcb, 'rotation_euler', 1, (0, math.pi, math.radians(-14)))
    keyv(pcb, 'location', 1, (0.002, 0.0, hi))
    keyv(pcb, 'rotation_euler', 146, (0, math.pi, math.radians(-3)))
    keyv(pcb, 'location', 146, (0.0, 0.0, hi + 0.004))
    keyv(pcb, 'rotation_euler', 206, (0, 0.0, 0.0))                   # rolls over its short axis
    keyv(pcb, 'location', 206, (0.0, 0.0, hi + 0.006))
    keyv(pcb, 'location', 240, (0.0, 0.0, h.z + 0.034))
    keyv(pcb, 'rotation_euler', 240, (0, 0.0, 0.0))
    keyv(pcb, 'location', 318, (0.0, 0.0, h.z))
    keyv(pcb, 'location', END, (0.0, 0.0, h.z))
    hide(G['tray'], 1, True)
    hide(G['tray'], 121, False)

    # ---------------- switches: shot 4
    for i, (start, land) in ((1, (344, 382)), (2, (356, 394))):
        g = G[f'sw{i}']
        hide(g, 1, True)
        hide(g, 337, False)
        keyv(g, 'location', 1, (0, 0, 0.030))
        keyv(g, 'location', start, (0, 0, 0.030))
        keyv(g, 'location', land - 4, (0, 0, 0.0004))
        keyv(g, 'location', land, (0, 0, 0.0))
    # ---------------- lid assembly: shot 5 (screws ride 4.4 mm high until shot 6)
    lid = G['lid']
    hide(lid, 1, True)
    hide(lid, 421, False)
    keyv(lid, 'location', 1, (0, 0, 0.045))
    keyv(lid, 'location', 432, (0, 0, 0.045))
    keyv(lid, 'location', 516, (0, 0, 0.0))
    raise_ = 0.0044
    turns = 5.5
    drive = {1: (560, 632), 2: (636, 668), 3: (638, 670), 4: (640, 672)}
    for i in range(1, 5):
        s = P[f'screw-{i}']
        base = s.location.copy()
        keyv(s, 'location', 1, (base.x, base.y, base.z + raise_))
        keyv(s, 'rotation_euler', 1, (0, 0, 0))
        a, b = drive[i]
        keyv(s, 'location', a, (base.x, base.y, base.z + raise_))
        keyv(s, 'rotation_euler', a, (0, 0, 0))
        keyv(s, 'location', b, (base.x, base.y, base.z))
        keyv(s, 'rotation_euler', b, (0, 0, -turns * 2 * math.pi))
    # ---------------- keycaps: shot 7
    for i, (start, land) in ((1, (684, 716)), (2, (694, 726))):
        g = G[f'key{i}']
        hide(g, 1, True)
        hide(g, 673, False)
        keyv(g, 'location', 1, (0, 0, 0.028))
        keyv(g, 'location', start, (0, 0, 0.028))
        keyv(g, 'location', land, (0, 0, 0.0))
    # ---------------- three presses on COUNT: shot 8
    travel = md['travel'] * MM * 0.93
    stem = [P['switch-1-pom_cyan'], P['switch-1-pom_white']]
    for press in (800, 824, 848):
        for obj in [G['key1']] + stem:
            z0 = 0.0 if obj is G['key1'] else obj.location.z
            keyv(obj, 'location', press - 4, (obj.location.x, obj.location.y, z0))
            keyv(obj, 'location', press, (obj.location.x, obj.location.y, z0 - travel))
            keyv(obj, 'location', press + 5, (obj.location.x, obj.location.y, z0))

    # ---------------- cameras
    cams = []
    zc = H['pcb'].z + 0.036 + 0.0015           # small parts on the flipped board's component side
    cams.append(shot_camera('cam1', 90, [(1, (-0.052, -0.070, zc + 0.070), (-0.005, -0.004, zc)),
                                         (120, (0.046, -0.078, zc + 0.064), (0.006, 0.003, zc))], fstop=36,
                            focus_keys=[(1, (-0.005, -0.004, zc)), (120, (0.006, 0.003, zc))]))
    cams.append(shot_camera('cam2', 70, [(121, (0.030, -0.140, 0.120), (0.0, 0.0, H['pcb'].z + 0.034)),
                                         (228, (-0.070, -0.215, 0.160), (0.0, 0.0, H['pcb'].z + 0.022))], fstop=22))
    cams.append(shot_camera('cam3', 70, [(229, (-0.120, -0.185, 0.150), (0.0, 0.0, 0.016)),
                                         (336, (-0.060, -0.215, 0.150), (0.0, 0.0, 0.010))], fstop=18))
    cams.append(shot_camera('cam4', 90, [(337, (0.058, -0.105, 0.070), (0.0, -0.014, 0.018)),
                                         (420, (0.028, -0.118, 0.078), (0.0, -0.014, 0.016))], fstop=14))
    cams.append(shot_camera('cam5', 60, [(421, (-0.170, -0.215, 0.180), (0.0, 0.0, 0.026)),
                                         (540, (-0.130, -0.235, 0.165), (0.0, 0.0, 0.015))], fstop=20))
    cams.append(shot_camera('cam6', 100, [(541, (-0.062, -0.078, 0.052), (-0.0185, -0.025, 0.0175)),
                                          (618, (-0.055, -0.083, 0.047), (-0.0185, -0.025, 0.0172))], fstop=11,
                            focus_keys=[(541, (-0.0185, -0.025, 0.0190)), (618, (-0.0185, -0.025, 0.0180))]))
    cams.append(shot_camera('cam6b', 85, [(619, (0.0, -0.110, 0.230), (0.0, 0.0, 0.012)),
                                          (672, (0.010, -0.098, 0.232), (0.0, 0.0, 0.012))], fstop=22))
    cams.append(shot_camera('cam7', 85, [(673, (0.110, -0.150, 0.080), (0.0, -0.008, 0.020)),
                                         (744, (0.085, -0.165, 0.090), (0.0, -0.008, 0.018))], fstop=16))
    cams.append(shot_camera('cam8', 90, [(745, (0.016, -0.098, 0.128), (0.0, 0.0020, 0.0150)),
                                         (876, (0.006, -0.090, 0.122), (0.0, 0.0030, 0.0150))], fstop=22,
                            focus_keys=[(745, (0.0, 0.0060, 0.0170)), (876, (0.0, 0.0060, 0.0170))]))
    orbit = []
    for j, f in enumerate(range(877, END + 1, 12)):
        t = j / ((END - 877) / 12)
        a = math.radians(-140 + 50 * (1 - (1 - t) ** 2))
        r = 0.215
        orbit.append((f, (r * math.cos(a), r * math.sin(a), 0.205 - 0.02 * t), (0.0, 0.0015, 0.0115)))
    cams.append(shot_camera('cam9', 85, orbit, fstop=16, focus_keys=[(877, (0.0, -0.002, 0.017)), (END, (0.0, -0.002, 0.017))]))
    starts = [1, 121, 229, 337, 421, 541, 619, 673, 745, 877]
    for cam, f in zip(cams, starts):
        m = sc.timeline_markers.new(cam.name, frame=f)
        m.camera = cam
    sc.camera = cams[0]
    # A slow light sweep across the acrylic while the lid lands.
    sweep = S.area_light('sweep', (-0.25, 0.05, 0.10), (0, 0, 0.015), 0.0, 0.04, 0.45)
    sweep.visible_diffuse = False          # highlight on the acrylic only; no wash on the backdrop
    for f, x, e in ((421, -0.25, 0.0), (440, -0.20, 2.2), (540, 0.22, 2.2), (560, 0.25, 0.0)):
        sweep.location.x = x
        sweep.keyframe_insert('location', frame=f)
        sweep.data.energy = e
        sweep.data.keyframe_insert('energy', frame=f)
    # Anchors for the explainer labels (world points that move with their parts).
    anchors = {
        'mcu': ('pcb', (0.0004, -0.0048, md['pcb_z'] * MM - 0.0014)),
        'fram': ('pcb', (0.0, -0.0206, md['pcb_z'] * MM - 0.0016)),
        'cell': ('pcb', (md['bt1_center'][0] * MM, md['bt1_center'][1] * MM, md['pcb_z'] * MM - 0.0048)),
        'usb': ('pcb', (0.0213, 0.0004, md['pcb_z'] * MM - 0.0016)),
        'socket': ('pcb', (-0.0110, -0.0166, md['pcb_z'] * MM - 0.0019)),
        'oled': ('pcb', (md['oled_active_center'][0] * MM, md['oled_active_center'][1] * MM, md['oled_active_z'] * MM)),
        'tray': ('tray', (-0.0227, -0.010, 0.008)),
        'switch': ('sw1', (-0.0095, -0.0138, pcb_top + 0.009)),
        'lid': ('lid', (0.016, 0.018, lid_top)),
        'spacer': ('lid', (-0.0185, -0.025, pcb_top + 0.003)),
        'screw': ('lid', (-0.0185, -0.025, lid_top + 0.0016)),
        'keycap': ('key1', (-0.0095, -0.0138, md['keycap_top'] * MM)),
    }
    local = {}
    for name, (grp, p) in anchors.items():
        hz = H[grp]
        local[name] = (grp, (p[0] - hz.x, p[1] - hz.y, p[2] - hz.z))
    sc['anchors'] = json.dumps(local)
    return ctx


def export_anchors(ctx, path):
    from bpy_extras.object_utils import world_to_camera_view
    sc = bpy.context.scene
    anchors = json.loads(sc['anchors'])
    markers = sorted(((m.frame, m.camera) for m in sc.timeline_markers), key=lambda t: t[0])
    out = {}
    for f in range(1, END + 1):
        sc.frame_set(f)
        cam = [c for start, c in markers if start <= f][-1]
        row = {}
        for name, (grp, p) in anchors.items():
            g = ctx['G'][grp]
            w = g.matrix_world @ Vector(p)
            co = world_to_camera_view(sc, cam, w)
            row[name] = [round(co.x, 4), round(1 - co.y, 4), round(co.z, 4)]
        out[f] = dict(camera=cam.name, points=row)
    Path(path).write_text(json.dumps(out))


def main():
    argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
    out = Path(argv[argv.index('--out') + 1]) if '--out' in argv else S.BUILD / 'film.blend'
    ctx = build(argv)
    S.configure_render(samples=16, res=(1920, 1080), threshold=0.05)
    cy = bpy.context.scene.cycles
    cy.max_bounces, cy.diffuse_bounces, cy.glossy_bounces, cy.transmission_bounces = 6, 1, 2, 6
    cy.denoising_prefilter = 'FAST'
    cy.adaptive_min_samples = 8
    for m in bpy.data.materials:
        if m.node_tree:
            for n in m.node_tree.nodes:
                if n.type == 'BSDF_PRINCIPLED':
                    n.inputs['Subsurface Weight'].default_value = 0.0
    export_anchors(ctx, S.BUILD / 'anchors.json')
    bpy.context.scene.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(out), compress=True)
    print('saved', out)


if __name__ == '__main__':
    main()
