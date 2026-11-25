"""Q5B option C (simple clear back) design-agreement drawings: plan + three sections, to scale from the generator numbers.
Z datum = underside of the back panel. Board frame: y negative = display end."""
import math, sys
from pathlib import Path
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
S = 3.5625                      # old datum (tray underside) -> new datum (panel underside)
PANEL = (0, 4.7625); FRAME_B = 4.7625
PCB = (7.22 + S, 8.82 + S); PLATE = (12.32 + S, 13.82 + S); WIN = (15.52 + S, 20.282 + S); TOP = WIN[1]
HEAD = (TOP, TOP + 1.75); TIP = TOP - 25.0; NUT = (0, 2.0); POCKET = 2.05
W, Y_TOP, Y_BOT = 47.0, -29.5, 33.75; WALL, BEZEL = 2.0, 1.2
WIN_Y = (-28.05, 32.3); WIN_X = 22.05; WELL_X, WELL_Y = 19.05, (4.2, 23.4)
PLATE_Y = (4.45, 32.3); SPLIT = 4.2
UP, LOW = (18.5, -24.5), (18.5, 29.55); PEG = (18.5, 25.0); FEET = [(8, -24.5), (8, 28.5)]; FOOT = (8.0, 2.0)
KEY = (9.525, 13.8); CAP_B, CAP_T = 19.82 + S, 19.82 + S + 9.4; CAP_W, CAP_D, CAP_TIP = 17.85, 18.0, 13.0
SW_TOP, STEM_TOP = 8.82 + 11.6 + S, 8.82 + 15.2 + S
GUS = FRAME_B + 3.3

C = dict(acr='#bfe6ee', acr_s='#3a8fa3', prt='#9a9ea6', prt_s='#2d3035', pcb='#2f7d4a', comp='#e3dccb', comp_s='#7a705a',
         metal='#c9ced3', metal_s='#4a5058', nut='#7d848c', plate='#3b3e44', cap='#f4f3ef', sw='#cfd8db', foot='#222', top='#e59a3a', top_s='#8a5510', low='#7c8fe0', low_s='#2c3a86',
         hid='#555', txt='#111', dim='#c0392b')


class Fig:
    def __init__(self, title, h0, h1, z0, z1, s=10, left=60, right=440, top=60, bot=60, hlabel='y', flip=False):
        self.s, self.h0, self.z1, self.left, self.top, self.flip = s, h0, z1, left, top, flip
        self.w = left + (h1 - h0) * s + right; self.h = top + (z1 - z0) * s + bot
        self.items, self.labels, self.title = [], [], title
        self.right_x = left + (h1 - h0) * s + 30

    def X(self, h): return self.left + (h - self.h0) * self.s
    def Z(self, z): return self.top + (self.z1 - z) * self.s

    def rect(self, h0, h1, z0, z1, fill, stroke, sw=1.0, dash=None, op=1.0):
        a, b = sorted((h0, h1)); c, d = sorted((z0, z1))
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.items.append(f'<rect x="{self.X(a):.1f}" y="{self.Z(d):.1f}" width="{(b-a)*self.s:.1f}" height="{(d-c)*self.s:.1f}" '
                          f'fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{da}/>')

    def poly(self, pts, fill, stroke, sw=1.0):
        p = ' '.join(f'{self.X(h):.1f},{self.Z(z):.1f}' for h, z in pts)
        self.items.append(f'<polygon points="{p}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')

    def line(self, h0, z0, h1, z1, stroke, sw=1.0, dash=None):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        self.items.append(f'<line x1="{self.X(h0):.1f}" y1="{self.Z(z0):.1f}" x2="{self.X(h1):.1f}" y2="{self.Z(z1):.1f}" stroke="{stroke}" stroke-width="{sw}"{da}/>')

    def label(self, h, z, text, side='r'):
        self.labels.append((h, z, text, side))

    def text(self, x, y, t, size=13, anchor='start', weight='normal', fill=None):
        self.items.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" font-weight="{weight}" fill="{fill or C["txt"]}">{t}</text>')

    def dimz(self, h, z0, z1, t):
        x = self.X(h)
        self.items.append(f'<line x1="{x}" y1="{self.Z(z0)}" x2="{x}" y2="{self.Z(z1)}" stroke="{C["dim"]}" stroke-width="1" marker-start="url(#a)" marker-end="url(#a)"/>')
        self.text(x - 5, (self.Z(z0) + self.Z(z1)) / 2 + 4, t, 12, 'end', fill=C['dim'])

    def dimh(self, h0, h1, z, t):
        y = self.Z(z)
        self.items.append(f'<line x1="{self.X(h0)}" y1="{y}" x2="{self.X(h1)}" y2="{y}" stroke="{C["dim"]}" stroke-width="1" marker-start="url(#a)" marker-end="url(#a)"/>')
        self.text((self.X(h0) + self.X(h1)) / 2, y + 15, t, 12, 'middle', fill=C['dim'])

    def svg(self):
        # labels stacked on the right, leader lines to their points
        ls = sorted(self.labels, key=lambda l: self.Z(l[1]))
        n = len(ls); yy = []
        y0, y1 = self.top - 10, self.h - 30
        for i, (h, z, t, s) in enumerate(ls):
            yy.append(max(self.Z(z), (yy[-1] + 19) if yy else y0))
        over = (yy[-1] - y1) if yy else 0
        if over > 0:
            yy = [y - over for y in yy]
            for i in range(1, n):
                yy[i] = max(yy[i], yy[i - 1] + 19)
        out = []
        for (h, z, t, s), y in zip(ls, yy):
            out.append(f'<polyline points="{self.X(h):.1f},{self.Z(z):.1f} {self.right_x - 8:.1f},{y:.1f} {self.right_x - 2:.1f},{y:.1f}" fill="none" stroke="#666" stroke-width="0.8"/>'
                       f'<circle cx="{self.X(h):.1f}" cy="{self.Z(z):.1f}" r="2.2" fill="#111"/>')
            out.append(f'<text x="{self.right_x:.1f}" y="{y + 4:.1f}" font-size="13" fill="#111">{t}</text>')
        return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{self.w:.0f}" height="{self.h:.0f}" viewBox="0 0 {self.w:.0f} {self.h:.0f}" font-family="DejaVu Sans, sans-serif">'
                f'<defs><marker id="a" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse"><path d="M0,0 L10,5 L0,10 z" fill="{C["dim"]}"/></marker></defs>'
                f'<rect width="100%" height="100%" fill="#fff"/>'
                f'<text x="20" y="30" font-size="18" font-weight="bold">{self.title}</text>'
                + ''.join(self.items) + ''.join(out) + '</svg>')


def acr(f, *a): f.rect(*a, C['acr'], C['acr_s'], 1.2)
def prt(f, *a): f.rect(*a, C['prt'], C['prt_s'], 1.0)
def tp(f, *a): f.rect(*a, C['top'], C['top_s'], 1.0)
def lw(f, *a): f.rect(*a, C['low'], C['low_s'], 1.0)
WEB = FRAME_B + 1.2


def screw_stack(f, h, upper, labels=True):
    """Vertical screw column at section coordinate h."""
    f.rect(h - 2.5, h + 2.5, *HEAD, C['metal'], C['metal_s'])
    f.rect(h - 1.25, h + 1.25, TIP, TOP, C['metal'], C['metal_s'])
    f.rect(h - 2.5, h + 2.5, *NUT, C['nut'], C['metal_s'])
    f.rect(h - 1.25, h + 1.25, TIP, TOP, C['metal'], C['metal_s'])
    z0 = PCB[1] if upper else PLATE[1]
    tp(f, h - 2.5, h - 1.35, z0, WIN[0]); tp(f, h + 1.35, h + 2.5, z0, WIN[0])


# ------------------------------------------------------------------ Section A: x = 18.5 through one side's two screws
def section_a():
    f = Fig('Section A-A: through the two screws on one side (x = 18.5 mm)', Y_TOP - 2, Y_BOT + 2, TIP - FOOT[1] - 1, HEAD[1] + 2, s=11)
    # back panel with the nut pockets
    acr(f, Y_TOP, Y_BOT, *PANEL)
    for y in (UP[1], LOW[1]):
        f.rect(y - 2.575, y + 2.575, 0, POCKET, '#ffffff', C['acr_s'], 1.0)
        f.rect(y - 1.45, y + 1.45, 0, PANEL[1], '#ffffff', C['acr_s'], 0.6)
    # frame: end walls cut, side wall seen behind (dashed)
    prt(f, Y_TOP, Y_TOP + WALL, FRAME_B, TOP); prt(f, Y_BOT - WALL, Y_BOT, FRAME_B, TOP)
    f.rect(Y_TOP + WALL, Y_BOT - WALL, FRAME_B, TOP, 'none', C['prt_s'], 0.8, '4,3')
    # display-end ledge under the acrylic edge, key-end ledge under the plate
    prt(f, Y_TOP + BEZEL, Y_TOP + WALL, FRAME_B + 0.01, WIN[0] - 0.1)
    prt(f, Y_BOT - WALL, Y_BOT - BEZEL, FRAME_B + 0.01, PLATE[0] - 0.1)
    # lower support: a flat web on the back panel with the columns standing on it
    prt(f, Y_TOP + WALL - 0.1, UP[1] + 2.5, FRAME_B, PCB[0]); prt(f, PEG[1] - 2.2, PEG[1] + 2.2, FRAME_B, PCB[0])
    prt(f, LOW[1] - 2.2, Y_BOT - WALL + 0.1, FRAME_B, PLATE[0])
    f.rect(-27, 27, *PCB, C['pcb'], '#173d24')
    f.rect(-4.87, 4.07, PCB[0] - 3.31, PCB[0], C['comp'], C['comp_s'])
    # top piece: switch plate, its side arm to the display end, pegs and spacer bosses, all one print
    tp(f, UP[1], 5.95, PCB[1], PCB[1] + 2.0)                       # arm, lying on the board
    tp(f, 4.45, 22.8, PCB[1], PLATE[1])                           # switch-box wall up to the plate
    tp(f, 22.6, 23.4, PCB[1], PLATE[1])                           # low link
    tp(f, 23.4, Y_BOT - WALL - 0.15, PCB[1], WIN[0])              # key-end spacer block
    tp(f, UP[1] - 2.5, UP[1] + 2.5, PCB[1], WIN[0])
    # M2 self-tapping screw: head recessed in the block, through the board hole, into the grey standoff
    f.rect(PEG[1] - 2.0, PEG[1] + 2.0, PCB[1] + 4.0, WIN[0], '#ffffff', C['top_s'], 0.6)
    f.rect(PEG[1] - 1.9, PEG[1] + 1.9, PCB[1] + 4.0, PCB[1] + 5.4, C['metal'], C['metal_s'])
    f.rect(PEG[1] - 1.0, PEG[1] + 1.0, PCB[1] - 6.0, PCB[1] + 4.0, C['metal'], C['metal_s'])
    acr(f, WIN_Y[0], WELL_Y[0], *WIN); acr(f, WELL_Y[1], WIN_Y[1], *WIN)
    # the screws need clearance holes in the stacks above: draw them over
    for y, up in ((UP[1], True), (LOW[1], False)):
        for z0, z1 in ((PANEL[1], PCB[0] if up else PLATE[0]),):
            f.rect(y - 1.45, y + 1.45, z0, z1, '#ffffff', C['prt_s'], 0.6)
        screw_stack(f, y, up)
    # feet (not in this plane: shown dashed behind) and the table
    for _, y in FEET:
        f.rect(y - 4, y + 4, -FOOT[1], 0, C['foot'], C['foot'], 0.8, op=0.35)
    f.line(Y_TOP - 2, -FOOT[1], Y_BOT + 2, -FOOT[1], '#999', 1.0, '6,4')
    f.text(f.X(Y_TOP - 1.5), f.Z(-FOOT[1]) + 16, 'table', 12, fill='#777')
    f.text(f.X(Y_TOP), f.Z(HEAD[1] + 1.2), 'display end', 12, fill='#555'); f.text(f.X(Y_BOT), f.Z(HEAD[1] + 1.2), 'key end', 12, 'end', fill='#555')
    # labels
    f.label(UP[1] + 1.5, HEAD[1] - 0.5, 'M2.5 × 25 pan-head screw (×4)')
    f.label(-12, WIN[1] - 1, 'TOP ACRYLIC, 3/16 in clear')
    f.label(14, WIN[0] + 1, 'opening for the keycaps')
    f.label(UP[1] + 2.2, (PLATE[1] + WIN[0]) / 2, 'spacer boss to the acrylic (part of print 1)')
    f.label(12, PLATE[1] - 0.6, 'PRINT 1: switch-box wall, plate on top (orange)')
    f.label(-10, PCB[1] + 1.0, 'arm of print 1, beside the display, lying on the board')
    f.label(PEG[1], PCB[1] + 4.7, 'M2 × 10 self-tapping screw: print 1 → board → print 2')
    f.label(PEG[1] - 1.6, PCB[1] + 2.0, 'key-end block of print 1')
    f.label(-20, PCB[1] - 0.6, 'Q5 BOARD (unchanged)')
    f.label(0, PCB[0] - 1.5, 'USB-C receptacle (under the board)')
    f.label(Y_BOT - 0.6, TOP - 8, 'PRINT 2: surround with corner standoffs (grey)')
    f.label(UP[1] + 2.2, PCB[0] - 2.5, 'corner standoff, joined to the wall (part of print 2)')
    f.label(8, FRAME_B + 2.5, 'open under the board: nothing printed here')
    f.label(-5, PANEL[1] - 2.2, 'BACK ACRYLIC, 3/16 in clear')
    f.label(LOW[1] + 2.2, 1.0, 'M2.5 nut in a 2.05 mm lasered hex pocket')
    f.label(LOW[1], TIP + 0.3, 'screw tip, 1.2 mm below the back')
    f.label(FEET[1][1] - 3, -FOOT[1] / 2, '2 mm feet (×4, not in this plane)')
    f.dimz(Y_TOP - 0.6, 0, TOP, f'{TOP:.1f}')
    f.dimz(Y_TOP - 0.6 + 0.0, -FOOT[1], 0, '2.0')
    f.dimh(Y_TOP, Y_BOT, TIP - FOOT[1] + 0.3, f'{Y_BOT - Y_TOP:.2f} mm long')
    return f


# ------------------------------------------------------------------ Section B: x = 9.525 through the right key, along the length
def section_b():
    f = Fig('Section B-B: through one key, along the length (x = 9.5 mm)', Y_TOP - 2, Y_BOT + 2, -FOOT[1] - 1, CAP_T + 2, s=11)
    acr(f, Y_TOP, Y_BOT, *PANEL)
    prt(f, Y_TOP, Y_TOP + WALL, FRAME_B, TOP); prt(f, Y_BOT - WALL, Y_BOT, FRAME_B, TOP)
    prt(f, Y_TOP + BEZEL, Y_TOP + WALL, FRAME_B + 0.01, WIN[0] - 0.1)
    prt(f, Y_BOT - WALL, Y_BOT - BEZEL, FRAME_B + 0.01, PLATE[0] - 0.1)
    f.rect(-27, 27, *PCB, C['pcb'], '#173d24')
    # battery holder (round body chord at x = 9.5) and the OLED module
    ch = math.sqrt(10.15 ** 2 - 9.525 ** 2)
    f.rect(-18.8, -2.6, PCB[0] - 5.52, PCB[0], C['comp'], C['comp_s'])
    f.rect(-14.2, -7.2, PCB[0] - 2.2, PCB[0], C['comp'], C['comp_s'])
    f.rect(-24.4, 3.8, 14.68, 16.48, '#1d3f73', '#0d1f3a'); f.rect(-19.43, -2.33, 16.48, 18.08, '#1d3f73', '#0d1f3a')
    f.rect(-23.95, -21.45, PCB[1], PCB[1] + 2.5, '#222', '#000')
    # MCU (just inside this plane? no: x -5..4.3) -> skip. Hot-swap socket (approx.)
    f.rect(KEY[1] - 7.75, KEY[1] + 7.75, PCB[0] - 1.85, PCB[0], '#444', '#111')
    # plate with the switch cut-out; switch; keycap in the opening
    tp(f, PLATE_Y[0], KEY[1] - 7.0, *PLATE); tp(f, KEY[1] + 7.0, KEY[1] + 9.0, *PLATE)
    tp(f, PLATE_Y[0], KEY[1] - 7.6, PCB[1], PLATE[0]); tp(f, KEY[1] + 7.6, KEY[1] + 9.0, PCB[1], PLATE[0])
    f.rect(KEY[1] - 6.975, KEY[1] + 6.975, PCB[1], PLATE[1], C['sw'], '#555')
    f.poly([(KEY[1] - 7.8, PLATE[1]), (KEY[1] + 7.8, PLATE[1]), (KEY[1] + 6.5, SW_TOP), (KEY[1] - 6.5, SW_TOP)], C['sw'], '#555')
    f.rect(KEY[1] - 0.65, KEY[1] + 0.65, SW_TOP, STEM_TOP, '#2bb673', '#185')
    f.poly([(KEY[1] - CAP_D / 2, CAP_B), (KEY[1] + CAP_D / 2, CAP_B), (KEY[1] + CAP_TIP / 2, CAP_T), (KEY[1] - CAP_TIP / 2, CAP_T)], C['cap'], '#777')
    acr(f, WIN_Y[0], WELL_Y[0], *WIN); acr(f, WELL_Y[1], WIN_Y[1], *WIN)
    f.line(Y_TOP - 2, -FOOT[1], Y_BOT + 2, -FOOT[1], '#999', 1.0, '6,4')
    for _, y in FEET:
        f.rect(y - 4, y + 4, -FOOT[1], 0, C['foot'], C['foot'], 0.8, op=0.35)
    f.text(f.X(Y_TOP), f.Z(CAP_T + 1.0), 'display end', 12, fill='#555'); f.text(f.X(Y_BOT), f.Z(CAP_T + 1.0), 'key end', 12, 'end', fill='#555')
    f.label(KEY[1], CAP_T - 1, 'standard MX keycap (top 8.9 mm above the acrylic)')
    f.label(KEY[1] + 4.5, CAP_B + 0.2, 'cap skirt rests 0.46 mm below the acrylic top')
    f.label(KEY[1] + 7.3, SW_TOP - 3, 'Box Jade, clipped into the plate')
    f.label(-9, WIN[1] - 1.2, 'top acrylic: 1.0 mm over the OLED')
    f.label(-12, 17.5, 'OLED module')
    f.label(-10, PCB[1] - 0.5, 'Q5 board')
    f.label(-16, PCB[0] - 3, 'LIR2032 holder: 0.5 mm over the back panel')
    f.label(KEY[1] + 5, PCB[0] - 1, 'hot-swap socket (under the board)')
    f.label(KEY[1] + 8, PLATE[1] - 0.6, 'print 1: 2 mm ring round each switch')
    f.label(27, PLATE[0], 'open: board visible past the keys')
    f.label(Y_BOT - 0.6, TOP - 8, 'print 2: surround')
    f.label(0, PANEL[1] - 2, 'clear back: battery + engraved warning show through')
    f.dimz(KEY[1] - 10.6, TOP, CAP_T, f'{CAP_T - TOP:.1f}')
    f.dimz(Y_TOP - 0.6, 0, TOP, f'{TOP:.1f}')
    return f


# ------------------------------------------------------------------ Section C: y = 13.8 across both keys
def section_c():
    f = Fig('Section C-C: across both keys (y = 13.8 mm)', -W / 2 - 2, W / 2 + 2, -FOOT[1] - 1, CAP_T + 2, s=12)
    acr(f, -W / 2, W / 2, *PANEL)
    for sgn in (-1, 1):
        prt(f, sgn * W / 2, sgn * (W / 2 - WALL), FRAME_B, TOP)
        prt(f, sgn * (W / 2 - WALL), sgn * (W / 2 - BEZEL), FRAME_B + 0.01, PLATE[0] - 0.1)
    f.rect(-21, 21, *PCB, C['pcb'], '#173d24')
    for kx in (-KEY[0], KEY[0]):
        f.rect(kx - 2.95, kx + 2.95, PCB[0] - 1.85, PCB[0], '#444', '#111')
        f.rect(kx - 6.975, kx + 6.975, PCB[1], PLATE[1], C['sw'], '#555')
        f.poly([(kx - 7.8, PLATE[1]), (kx + 7.8, PLATE[1]), (kx + 6.5, SW_TOP), (kx - 6.5, SW_TOP)], C['sw'], '#555')
        f.rect(kx - 2.0, kx + 2.0, SW_TOP, STEM_TOP, '#2bb673', '#185')
        f.poly([(kx - CAP_W / 2, CAP_B), (kx + CAP_W / 2, CAP_B), (kx + CAP_TIP / 2, CAP_T), (kx - CAP_TIP / 2, CAP_T)], C['cap'], '#777')
    edges = [-KEY[0] - 9.0, -KEY[0] - 7.0, -KEY[0] + 7.0, KEY[0] - 7.0, KEY[0] + 7.0, KEY[0] + 9.0]
    for a, b in zip(edges[::2], edges[1::2]):
        tp(f, a, b, *PLATE)
        tp(f, a + (0.6 if a > -KEY[0] - 8 else 0), b - (0.6 if b < KEY[0] + 8 else 0), PCB[1], PLATE[0])
    acr(f, -WIN_X, -WELL_X, *WIN); acr(f, WELL_X, WIN_X, *WIN)
    f.label(KEY[0], CAP_T - 1, 'keycaps 36.9 × 18.0 (pair, measured)')
    f.label(WELL_X + 0.5, WIN[1] - 0.8, 'top acrylic: 38.1 mm opening, 3.0 mm side rails')
    f.label(W / 2 - 0.5, TOP - 3, 'print 2: surround, 2.0 mm wall, flush with the top')
    f.label(0, FRAME_B + 2.5, 'open under the board')
    f.label(KEY[0] + 6, PLATE[1] - 0.5, 'print 1: switch plate (1.5 mm)')
    f.label(KEY[0] + 2, PCB[0] - 1, 'hot-swap socket')
    f.label(15, PANEL[1] - 2, 'clear back panel')
    f.dimh(-W / 2, W / 2, -0.9, f'{W:.1f} mm wide')
    return f


# ------------------------------------------------------------------ plan view (looking down), with section lines
def plan():
    s = 9
    left, top = 70, 70
    X = lambda x: left + (x + W / 2 + 2) * s
    Y = lambda y: top + (y - Y_TOP + 2) * s
    it = []
    def rr(x0, y0, x1, y1, r, fill, stroke, sw=1.2, dash=None, op=1):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        it.append(f'<rect x="{X(x0):.1f}" y="{Y(y0):.1f}" width="{(x1-x0)*s:.1f}" height="{(y1-y0)*s:.1f}" rx="{r*s:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{da}/>')
    def circ(x, y, r, fill, stroke, sw=1.0, dash=None, op=1):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        it.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r*s:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{da}/>')
    def txt(x, y, t, size=13, anchor='middle', fill='#111'):
        it.append(f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" text-anchor="{anchor}" fill="{fill}">{t}</text>')
    rr(-W / 2, Y_TOP, W / 2, Y_BOT, 3.4, C['prt'], C['prt_s'])                       # frame (= panel outline)
    rr(-WIN_X, WIN_Y[0], WIN_X, WIN_Y[1], 2.2, C['acr'], C['acr_s'])                  # top acrylic
    rr(-21, -27, 21, 27, 0.5, C['pcb'], '#173d24', 1, '5,3', 0.25)                    # board (hidden)
    rr(-13.85, -24.4, 13.85, 3.8, 0.3, '#1d3f73', '#0d1f3a', 1, None, 0.55)          # OLED through the acrylic
    rr(-WELL_X, WELL_Y[0], WELL_X, WELL_Y[1], 1.0, '#ffffff', C['acr_s'])             # key opening
    for kx in (-KEY[0], KEY[0]):
        rr(kx - CAP_W / 2, KEY[1] - CAP_D / 2, kx + CAP_W / 2, KEY[1] + CAP_D / 2, 1.0, C['cap'], '#777')
    for sx in (-1, 1):
        for (x, y) in (UP, LOW):
            circ(sx * x, y, 2.5, C['metal'], C['metal_s'], 1.2)
        for (x, y) in FEET:
            circ(sx * x, y, 4, 'none', '#222', 1.2, '4,3')
    circ(12.6, 24.2, 0.75, '#fff', '#c0392b', 1.2, '2,2')
    rr(W / 2 - 0.6, -0.4 - 6.7, W / 2 + 0.6, -0.4 + 6.7, 0.3, '#fff', '#111', 1.2)  # USB opening in the side wall
    # section lines
    for x, name in ((18.5, 'A'), (9.525, 'B')):
        it.append(f'<line x1="{X(x)}" y1="{Y(Y_TOP - 1.6)}" x2="{X(x)}" y2="{Y(Y_BOT + 1.6)}" stroke="#c0392b" stroke-width="1.4" stroke-dasharray="10,4,2,4"/>')
        txt(X(x), Y(Y_TOP - 1.9), name, 15, fill='#c0392b'); txt(X(x), Y(Y_BOT + 3.2), name, 15, fill='#c0392b')
    it.append(f'<line x1="{X(-W/2 - 1.6)}" y1="{Y(KEY[1])}" x2="{X(W/2 + 1.6)}" y2="{Y(KEY[1])}" stroke="#c0392b" stroke-width="1.4" stroke-dasharray="10,4,2,4"/>')
    txt(X(-W / 2 - 2.6), Y(KEY[1]) + 5, 'C', 15, fill='#c0392b'); txt(X(W / 2 + 2.6), Y(KEY[1]) + 5, 'C', 15, fill='#c0392b')
    # notes on the right
    rx = X(W / 2 + 6)
    notes = [('Plan, from above (to scale)', 16, 'bold'), ('', 8, ''),
             ('● 4 × M2.5 × 25 screws, straight through', 13, ''), ('    top acrylic → spacer → board or plate →', 13, ''),
             ('    corner standoff → back acrylic → nut', 13, ''),
             ('◌ 4 × 2 mm feet on the back (dashed)', 13, ''),
             ('◌ red: reset pinhole through the back', 13, ''), ('▭ USB-C opening in the right wall', 13, ''),
             ('', 8, ''), ('Footprint 47.0 × 63.25 mm', 13, ''), ('Height 23.8 mm (25.8 on its feet),', 13, ''),
             ('plus 1.75 mm screw heads', 13, ''), ('', 8, ''),
             ('The key-end screws sit just past the', 13, ''), ('board edge: the board’s own key-end', 13, ''),
             ('holes are 0.2 mm from the key opening,', 13, ''), ('so they only take the plate’s pegs.', 13, '')]
    yy = top + 10
    for t, sz, wgt in notes:
        it.append(f'<text x="{rx:.1f}" y="{yy:.1f}" font-size="{sz}" font-weight="{wgt or "normal"}">{t}</text>'); yy += sz + 7
    txt(X(0), Y(Y_TOP) - 26, 'display end', 13, fill='#555'); txt(X(0), Y(Y_BOT) + 48, 'key end', 13, fill='#555')
    w, h = rx + 330, Y(Y_BOT + 2) + 60
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" font-family="DejaVu Sans, sans-serif">'
            f'<rect width="100%" height="100%" fill="#fff"/><text x="20" y="32" font-size="18" font-weight="bold">Option C (simple clear back): plan and section lines</text>'
            + ''.join(it) + '</svg>')


def top_piece():
    sc = 11; left, top = 60, 70
    X = lambda x: left + (x + W / 2 + 1) * sc
    Y = lambda y: top + (y - Y_TOP + 1) * sc
    it = []
    def rr(x0, y0, x1, y1, r, fill, stroke, sw=1.2, dash=None, op=1):
        da = f' stroke-dasharray="{dash}"' if dash else ''
        it.append(f'<rect x="{X(x0):.1f}" y="{Y(y0):.1f}" width="{(x1-x0)*sc:.1f}" height="{(y1-y0)*sc:.1f}" rx="{r*sc:.1f}" fill="{fill}" fill-opacity="{op}" stroke="{stroke}" stroke-width="{sw}"{da}/>')
    def circ(x, y, r, fill, stroke, sw=1.0):
        it.append(f'<circle cx="{X(x):.1f}" cy="{Y(y):.1f}" r="{r*sc:.1f}" fill="{fill}" stroke="{stroke}" stroke-width="{sw}"/>')
    HI, LO = '#d9822b', '#f3c184'
    rr(-W / 2, Y_TOP, W / 2, Y_BOT, 3.4, 'none', '#999', 1, '6,4')
    rr(-21, -27, 21, 27, 0.5, C['pcb'], '#173d24', 1, None, 0.30)
    rr(-13.85, -24.4, 13.85, 3.8, 0.3, '#1d3f73', '#0d1f3a', 1, None, 0.35)
    # plate level (light): rings round the switches, centre web, side rails
    rr(-KEY[0] - 9.0, PLATE_Y[0], KEY[0] + 9.0, KEY[1] + 9.0, 0.6, LO, C['top_s'])
    for kx in (-KEY[0], KEY[0]):
        rr(kx - 7, KEY[1] - 7, kx + 7, KEY[1] + 7, 0.3, '#ffffff', C['top_s'])
        rr(kx - CAP_W / 2, KEY[1] - CAP_D / 2, kx + CAP_W / 2, KEY[1] + CAP_D / 2, 1.0, 'none', '#555', 1, '3,3')
    for sx in (-1, 1):
        a, b = sorted((sx * 17.3, sx * 20.5))
        rr(a, UP[1], b, 5.95, 0.3, LO, C['top_s'])                      # arm, on the board
        a, b = sorted((sx * 15.8, sx * 21.2))
        rr(a, 22.6, b, 23.4, 0.1, LO, C['top_s'])
        rr(a, 23.4, b, Y_BOT - WALL - 0.15, 0.5, HI, C['top_s'])        # key-end block
        circ(sx * 18.5, UP[1], 2.5, HI, C['top_s']); circ(sx * 18.5, UP[1], 1.45, '#fff', C['top_s'])
        circ(sx * 18.5, LOW[1], 1.45, '#fff', C['top_s'])
        circ(sx * 18.5, PEG[1], 2.1, '#fff', C['top_s']); circ(sx * 18.5, PEG[1], 1.1, '#c9ced3', '#4a5058')
    rx = X(W / 2 + 4); yy = top + 6
    notes = [('The orange piece, from above', 16, 'bold'), ('', 8, ''),
             ('Dark orange: full height, touches the top', 13, ''), ('acrylic. These are the spacers.', 13, ''),
             ('Light orange: lower parts. The switch box', 13, ''), ('(walls from the board up to the 1.5 mm', 13, ''),
             ('plate) and the arms, 2 mm tall, lying', 13, ''), ('on the board.', 13, ''), ('', 8, ''),
             ('The switch box sits almost entirely', 13, ''), ('under the keycaps (dashed).', 13, ''), ('', 8, ''),
             ('Prints board side down, no supports.', 13, ''), ('', 8, ''),
             ('Holes: 4 for the M2.5 through-screws,', 13, ''), ('2 recessed for the M2 self-tappers', 13, ''),
             ('(grey dots) that fix it to the board', 13, ''), ('and the surround. No pins.', 13, ''), ('', 8, ''),
             ('Green: the board. Blue: the display.', 13, ''), ('Outside the keycaps and display, the', 13, ''),
             ('print covers about 12% of the board.', 13, '')]
    for t, sz, wgt in notes:
        it.append(f'<text x="{rx:.1f}" y="{yy:.1f}" font-size="{sz}" font-weight="{wgt or "normal"}">{t}</text>'); yy += sz + 7
    it.append(f'<text x="{X(0):.1f}" y="{Y(Y_TOP) - 12:.1f}" font-size="13" text-anchor="middle" fill="#555">display end</text>')
    it.append(f'<text x="{X(0):.1f}" y="{Y(Y_BOT) + 22:.1f}" font-size="13" text-anchor="middle" fill="#555">key end</text>')
    w, h = rx + 330, Y(Y_BOT + 1) + 50
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w:.0f}" height="{h:.0f}" viewBox="0 0 {w:.0f} {h:.0f}" font-family="DejaVu Sans, sans-serif">'
            f'<rect width="100%" height="100%" fill="#fff"/><text x="20" y="32" font-size="18" font-weight="bold">Print 1 (orange): switch box + spacers</text>'
            + ''.join(it) + '</svg>')


(OUT / 'C-4-orange-piece-plan.svg').write_text(top_piece())
(OUT / 'C-0-plan.svg').write_text(plan())
for name, fn in (('C-1-section-A-screws', section_a), ('C-2-section-B-key-lengthwise', section_b), ('C-3-section-C-across-keys', section_c)):
    (OUT / f'{name}.svg').write_text(fn().svg())
print('ok')
