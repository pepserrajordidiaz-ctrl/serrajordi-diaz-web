# Generates the schematic plans (SVG, mm units, 1:75 on A3) for C/ Anselm Clavé 30.
import math, json, sys
sys.path.insert(0, '/home/claude/plans')
from geo import G, A, f, d, sub, dot

SC = 1000/75            # mm per metre at 1:75
W, H = 420, 297         # A3 landscape, mm
OX, OY = 112, 236       # drawing origin: façade, at u = 9.6
U0 = 9.75
def X(u): return OX + (U0 - u)*SC        # east is left: seen from the street
def Y(v): return OY - v*SC                # street at the bottom
def pt(u, v): return f"{X(u):.2f},{Y(v):.2f}"
def loc(p): q = sub(p, A); return (dot(q, f), dot(q, d))
L = G['local']
SITE = [L[k] for k in ('A','W1','Wj1','W2','W3','E3','E2','E1','B')]
EAT = [L[k] for k in ('E1','E2','E3','E4')]
CAD = [loc(p) for p in [(-4.85,1.78),(-4.17,1.91),(-5.01,6.30),(4.11,7.65),(5.21,1.58),(5.87,-2.05),(5.94,-2.41),(6.52,-5.61),(2.67,-6.27),(2.16,-6.36),(2.13,-5.58),(1.00,-5.82),(-2.61,-6.60),(-3.62,-3.39),(-4.23,-1.46),(-5.22,1.70)]]

def clip(poly, keep):   # Sutherland–Hodgman against keep(p) -> signed value (>=0 inside)
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i+1) % len(poly)]; fa, fb = keep(a), keep(b)
        if fa >= 0: out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa/(fa-fb); out.append((a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t))
    return out
def area(P): return abs(sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P))))/2
H2 = clip(clip(SITE, lambda p: 4.6-p[0]), lambda p: 10-p[1])            # casa 2 (west)
H1 = clip(clip(SITE, lambda p: p[0]-4.6), lambda p: 9.7-p[1])           # casa 1 (east)
Y2 = clip(clip(SITE, lambda p: 4.6-p[0]), lambda p: p[1]-10)
Y1 = clip(clip(SITE, lambda p: p[0]-4.6), lambda p: p[1]-9.7)

INK, MUTE, RED, ACC = '#1C2321', '#7B837F', '#A63A2E', '#EDB91F'
def poly(P, **a): return f'<polygon points="{" ".join(pt(*p) for p in P)}" {attrs(a)}/>'
def attrs(a): return ' '.join(f'{k.replace("_","-")}="{v}"' for k, v in a.items())
def rect(u0, v0, u1, v1, **a):
    x0, x1 = sorted((X(u0), X(u1))); y0, y1 = sorted((Y(v0), Y(v1)))
    return f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{x1-x0:.2f}" height="{y1-y0:.2f}" {attrs(a)}/>'
def line(u0, v0, u1, v1, **a): return f'<line x1="{X(u0):.2f}" y1="{Y(v0):.2f}" x2="{X(u1):.2f}" y2="{Y(v1):.2f}" {attrs(a)}/>'
def text(u, v, s, size=3.0, weight=400, fill=INK, anchor='middle', **a):
    return f'<text x="{X(u):.2f}" y="{Y(v):.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {attrs(a)}>{s}</text>'
def circle(u, v, r, **a): return f'<circle cx="{X(u):.2f}" cy="{Y(v):.2f}" r="{r*SC:.2f}" {attrs(a)}/>'
FUR = dict(fill='none', stroke=MUTE, stroke_width=0.25)

# --- house frame: s = distance from the shared wall, v = depth -------------------------------------------
class House:
    def __init__(s, n): s.n = n; s.sg = 1 if n == 1 else -1; s.u0 = 4.6 + 0.12*s.sg
    def u(s, x): return s.u0 + s.sg*x
    def rect(s, x0, v0, x1, v1, **a): return rect(s.u(x0), v0, s.u(x1), v1, **a)
    def line(s, x0, v0, x1, v1, **a): return line(s.u(x0), v0, s.u(x1), v1, **a)
    def text(s, x, v, t, **a): return text(s.u(x), v, t, **a)
    def circle(s, x, v, r, **a): return circle(s.u(x), v, r, **a)
WALL = 0.2
def room(h, x0, v0, x1, v1, name, hi=False, note=None, area_txt=None, tag=None):
    out = []
    if hi: out.append(h.rect(x0, v0, x1, v1, fill='#FFF3C4'))
    a = abs((x1-x0)*(v1-v0)) if area_txt is None else area_txt
    cx, cv = (x0+x1)/2, (v0+v1)/2
    out.append(h.text(cx, cv+0.12, name, size=3.1, weight=600))
    out.append(h.text(cx, cv-0.42, (f'{a:.1f}'.replace('.', ',') + ' m²') if isinstance(a, float) else a, size=2.5, fill=MUTE))
    if tag: out.append(h.text(cx, cv-0.95, tag, size=2.2, weight=700, fill='#9A6B00'))
    return out
def part(h, x0, v0, x1, v1): return h.rect(x0, v0, x1, v1, fill=INK)          # interior partition
def door(h, x, v, w, into=1, hinge=0):   # opening on a wall parallel to the façade at depth v, leaf swinging into +v/-v
    s0, s1 = (x, x+w) if hinge == 0 else (x+w, x)
    out = [h.rect(x, v-0.07, x+w, v+0.07, fill='#fff')]
    out.append(h.line(s0, v, s0, v+into*w, stroke=INK, stroke_width=0.3))
    a0, a1 = (h.u(s0), v+into*w), (h.u(s1), v)
    sweep = 1 if (into*h.sg*(1 if hinge == 0 else -1)) < 0 else 0
    out.append(f'<path d="M{X(a0[0]):.2f},{Y(a0[1]):.2f} A{w*SC:.2f},{w*SC:.2f} 0 0 {sweep} {X(a1[0]):.2f},{Y(a1[1]):.2f}" fill="none" stroke="{MUTE}" stroke-width="0.2"/>')
    return out
def stair(h, up=True):
    out = [h.rect(0, 3.4, 1.1, 7.4, fill='#fff', stroke=INK, stroke_width=0.3)]
    for i in range(1, 16): v = 3.4 + i*4.0/16; out.append(h.line(0, v, 1.1, v, stroke=MUTE, stroke_width=0.2))
    out.append(h.line(0.55, 3.6, 0.55, 7.1, stroke=INK, stroke_width=0.3, marker_end='url(#arr)'))
    return out
def car(h, x, v):
    return [h.rect(x, v, x+1.85, v+4.3, rx=1.6, **FUR), h.line(x+0.15, v+1.35, x+1.7, v+1.35, **FUR), h.line(x+0.15, v+3.0, x+1.7, v+3.0, **FUR)]
def bed(h, x, v, w=1.6, l=2.0):
    return [h.rect(x, v, x+w, v+l, **FUR), h.rect(x+0.12, v+l-0.5, x+w/2-0.06, v+l-0.12, **FUR), h.rect(x+w/2+0.06, v+l-0.5, x+w-0.12, v+l-0.12, **FUR), h.line(x, v+l-0.65, x+w, v+l-0.65, **FUR)]
def table(h, x, v, w=0.9, l=1.6):
    o = [h.rect(x, v, x+w, v+l, **FUR)]
    for k in range(3):
        vv = v+0.15+k*(l-0.3)/2-0.2
        o += [h.rect(x-0.45, vv, x-0.05, vv+0.4, **FUR), h.rect(x+w+0.05, vv, x+w+0.45, vv+0.4, **FUR)]
    return o
def sofa(h, x, v, w=2.2, depth=0.9, back='v0'):
    o = [h.rect(x, v, x+w, v+depth, **FUR)]
    o.append(h.rect(x, v, x+w, v+0.22, **FUR) if back == 'v0' else h.rect(x, v+depth-0.22, x+w, v+depth, **FUR))
    return o
def counter(h, x0, v0, x1, v1): return [h.rect(x0, v0, x1, v1, fill='#F2F1EC', stroke=MUTE, stroke_width=0.25)]
def hob(h, x, v): return [h.circle(x+dx, v+dv, 0.09, **FUR) for dx in (-0.15, 0.15) for dv in (-0.15, 0.15)]
def sink(h, x, v): return [h.rect(x-0.3, v-0.2, x+0.3, v+0.2, rx=0.6, **FUR)]
def wc(h, x, v, face=1):
    return [h.rect(x-0.2, v, x+0.2, v+0.18*face, **FUR) if face > 0 else h.rect(x-0.2, v+0.18*face, x+0.2, v, **FUR),
            f'<ellipse cx="{X(h.u(x)):.2f}" cy="{Y(v+0.45*face):.2f}" rx="{0.19*SC:.2f}" ry="{0.27*SC:.2f}" fill="none" stroke="{MUTE}" stroke-width="0.25"/>']
def shower(h, x0, v0, x1, v1): return [h.rect(x0, v0, x1, v1, **FUR), h.line(x0, v0, x1, v1, **FUR), h.line(x0, v1, x1, v0, **FUR)]
def washer(h, x, v): return [h.rect(x, v, x+0.6, v+0.6, **FUR), h.circle(x+0.3, v+0.3, 0.2, **FUR)]

def shell(level):
    o = []
    for P, cid in ((H1, 'c1'), (H2, 'c2')):
        o.append(f'<clipPath id="{cid}{level}"><polygon points="{" ".join(pt(*p) for p in P)}"/></clipPath>')
        o.append(poly(P, fill='#fff'))
    return o
def walls(level):
    return [poly(P, fill='none', stroke=INK, stroke_width=f'{2*WALL*SC:.2f}', clip_path=f'url(#{cid}{level})') for P, cid in ((H1, 'c1'), (H2, 'c2'))]
def yard_room(P, cid, built):
    o = [f'<clipPath id="{cid}"><polygon points="{" ".join(pt(*p) for p in P)}"/></clipPath>']
    if built:
        o += [poly(P, fill='#fff'), poly(P, fill='none', stroke=INK, stroke_width=f'{2*0.15*SC:.2f}', clip_path=f'url(#{cid})')]
    else:
        o += [poly(P, fill='url(#deck)', stroke=INK, stroke_width=0.35, stroke_dasharray='1.6 0.8')]
    return o
def context(level, notes=True):
    o = [poly(CAD, fill='none', stroke=MUTE, stroke_width=0.25, stroke_dasharray='1.2 1')]
    o.append(poly(EAT, fill='url(#eat)', stroke=RED, stroke_width=0.45))
    o.append(poly(SITE, fill='none', stroke=ACC, stroke_width=0.7))
    cu = sum(p[0] for p in EAT)/4; cv = sum(p[1] for p in EAT)/4
    o.append(text(cu, cv+0.2, 'Ocupat pel veí', size=2.6, weight=700, fill=RED))
    o.append(text(cu, cv-0.4, '3,00 × 2,70 m', size=2.3, fill=RED))
    # street and neighbours
    o.append(f'<rect x="{X(U0+2.2):.2f}" y="{Y(-0.15):.2f}" width="{(U0+2.2-(-3.0))*SC:.2f}" height="{4.2*SC:.2f}" fill="#EFEFEA"/>')
    o.append(text(4.6, -1.7, "CARRER D'ANSELM CLAVÉ", size=3.2, weight=600, fill=MUTE, letter_spacing='0.6'))
    o.append(text(10.9, 5.0, 'núm. 28', size=2.8, fill=MUTE)); o.append(text(-1.9, 3.0, 'núm. 32', size=2.8, fill=MUTE))
    o.append(text(4.0, 14.0, 'veí del darrere', size=2.8, fill=MUTE))
    return o

DEFS = f'''<defs>
<pattern id="eat" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.4" height="2.4" fill="#F6E1DD"/><rect width="1.0" height="2.4" fill="#E4A79E"/></pattern>
<pattern id="deck" width="2.2" height="2.2" patternUnits="userSpaceOnUse"><rect width="2.2" height="2.2" fill="#F7F5EF"/><path d="M0 0H2.2" stroke="#D8D3C6" stroke-width="0.25"/></pattern>
<marker id="arr" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0L6 3L0 6z" fill="{INK}"/></marker>
</defs>'''
C1, C2 = House(1), House(2)

def dim_h(u0, u1, v, label, off=-0.9):   # dimension along the façade
    y = Y(v+off); o = [f'<line x1="{X(u0):.2f}" y1="{y:.2f}" x2="{X(u1):.2f}" y2="{y:.2f}" stroke="{INK}" stroke-width="0.25"/>']
    for u in (u0, u1): o.append(f'<line x1="{X(u):.2f}" y1="{y-1.2:.2f}" x2="{X(u):.2f}" y2="{y+1.2:.2f}" stroke="{INK}" stroke-width="0.25"/>')
    o.append(f'<text x="{(X(u0)+X(u1))/2:.2f}" y="{y-1.0:.2f}" font-size="2.6" text-anchor="middle" fill="{INK}">{label}</text>'); return o
def dim_v(u, v0, v1, label, off=0.9):
    x = X(u+off); o = [f'<line x1="{x:.2f}" y1="{Y(v0):.2f}" x2="{x:.2f}" y2="{Y(v1):.2f}" stroke="{INK}" stroke-width="0.25"/>']
    for v in (v0, v1): o.append(f'<line x1="{x-1.2:.2f}" y1="{Y(v):.2f}" x2="{x+1.2:.2f}" y2="{Y(v):.2f}" stroke="{INK}" stroke-width="0.25"/>')
    o.append(f'<text x="{x-1.2:.2f}" y="{(Y(v0)+Y(v1))/2:.2f}" font-size="2.6" text-anchor="middle" fill="{INK}" transform="rotate(-90 {x-1.2:.2f} {(Y(v0)+Y(v1))/2:.2f})">{label}</text>'); return o

def level_pb():
    o = shell('pb') + walls('pb')
    o += yard_room(Y1, 'y1pb', True) + yard_room(Y2, 'y2pb', True)
    for h in (C1, C2):
        o += stair(h) + car(h, 2.0, 0.55) + car(h, 2.0, 5.05)
        o += room(h, 2.9, 4.75, 2.9, 4.75, '', area_txt='')  # spacer
        o.append(h.text(2.95, 4.95, 'Garatge', size=3.1, weight=600)); o.append(h.text(2.95, 4.45, '2 cotxes', size=2.5, fill=MUTE))
        o += door(h, 0.12, 0.0, 0.85, into=1)                                    # pedestrian door
        o.append(h.rect(1.35, -0.08, 4.25, 0.25, fill='#fff', stroke=INK, stroke_width=0.25, stroke_dasharray='1 0.6'))  # garage door
        o.append(h.text(0.55, 1.5, 'Entrada', size=2.4, fill=MUTE))
    vb1, vb2 = 9.7 - WALL/2, 10 - WALL/2
    o += door(C1, 0.3, vb1, 0.8, into=1); o += door(C2, 0.6, vb2, 0.8, into=1)
    o.append(text(5.75, 11.2, 'Safareig', size=3.0, weight=600)); o.append(text(5.75, 10.7, f'≈{area(Y1)-1.3:.0f} m² · nou', size=2.4, fill='#9A6B00', weight=700))
    o += washer(C1, 0.15, 11.8); o.append(text(2.4, 11.6, 'Sala polivalent / safareig', size=3.0, weight=600)); o.append(text(2.4, 11.05, f'≈{area(Y2)-2.2:.0f} m²', size=2.5, fill=MUTE))
    return o

def level_p1():
    o = shell('p1') + walls('p1')
    o += yard_room(Y1, 'y1p1', False) + yard_room(Y2, 'y2p1', False)
    # casa 1 (new): living at the front, dining in the middle, kitchen in the back corner, door to the small terrace beside it
    h = C1
    o.append(h.rect(1.2, 0.1, 4.6, 4.1, fill='#FFF3C4')); o.append(h.rect(1.2, 4.1, 4.6, 6.5, fill='#FFF3C4')); o.append(h.rect(1.2, 6.5, 4.6, 9.6, fill='#FFF3C4')); o.append(h.rect(0, 7.4, 1.2, 9.6, fill='#FFF3C4'))
    o += sofa(h, 1.6, 2.9, w=2.3, back='v1') + [h.rect(1.7, 0.35, 3.8, 0.75, **FUR)]
    o += room(h, 2.75, 2.05, 2.75, 2.05, "Sala d'estar", area_txt='≈15 m²', tag='NOU')
    o += table(h, 1.65, 4.4) + room(h, 3.65, 5.3, 3.65, 5.3, 'Menjador', area_txt='≈8 m²')
    o += counter(h, 3.7, 6.7, 4.33, 9.5) + counter(h, 1.95, 8.88, 4.33, 9.5) + hob(h, 4.02, 7.4) + sink(h, 2.85, 9.19)
    o += room(h, 2.6, 7.75, 2.6, 7.75, 'Cuina', area_txt='≈10 m²', tag='NOU')
    o += door(h, 0.25, 9.7 - WALL/2, 0.85, into=1)
    o.append(text(5.55, 11.5, 'Terrassa', size=3.0, weight=600)); o.append(text(5.55, 10.95, f'≈{area(Y1):.0f} m² · nou', size=2.4, fill='#9A6B00', weight=700))
    # casa 2 (unchanged): kitchen and dining at the front, living at the back with the large terrace
    h = C2
    o += counter(h, 3.72, 0.3, 4.33, 3.9) + counter(h, 1.3, 0.3, 4.33, 0.9) + hob(h, 4.03, 2.2) + sink(h, 2.4, 0.6)
    o += room(h, 2.4, 2.0, 2.4, 2.0, 'Cuina', area_txt='≈11 m²') + table(h, 1.65, 4.2, w=0.9, l=1.5) + room(h, 3.65, 5.2, 3.65, 5.2, 'Menjador', area_txt='≈8 m²')
    o += sofa(h, 1.5, 7.0, w=2.4, back='v0') + [h.rect(1.6, 9.3, 3.8, 9.7, **FUR)]
    o += room(h, 2.7, 8.55, 2.7, 8.55, "Sala d'estar", area_txt='≈14 m²') + door(h, 0.4, 10 - WALL/2, 0.85, into=1)
    o.append(text(2.4, 11.6, 'Terrassa', size=3.0, weight=600)); o.append(text(2.4, 11.05, f'≈{area(Y2):.0f} m²', size=2.5, fill=MUTE))
    for h in (C1, C2):
        o += stair(h) + [part(h, 0, 2.0, 1.2, 2.1), part(h, 1.1, 2.0, 1.2, 3.4)] + wc(h, 0.55, 3.3, face=-1) + [h.text(0.55, 2.45, 'Lavabo', size=2.2, fill=MUTE)]
    return o

def level_p2():
    o = shell('p2') + walls('p2')
    for h, vb in ((C1, 9.6), (C2, 9.9)):
        o += stair(h) + bed(h, 2.6, 0.45) + room(h, 1.85, 1.6, 1.85, 1.6, 'Habitació 1', area_txt='≈14 m²')
        o += [part(h, 0, 3.55, 4.4, 3.65), part(h, 1.15, 3.65, 1.25, 5.7), part(h, 1.25, 5.65, 4.4, 5.75)]
        o += shower(h, 3.3, 3.75, 4.3, 4.75) + wc(h, 1.75, 5.6, face=-1) + sink(h, 2.6, 5.4) + room(h, 2.7, 4.75, 2.7, 4.75, 'Bany', area_txt='≈6 m²')
        o += [h.rect(3.7, 5.9, 4.3, 7.3, **FUR), h.rect(3.25, 6.4, 3.6, 6.8, **FUR)] + room(h, 2.3, 6.6, 2.3, 6.6, 'Estudi obert', area_txt='≈5 m²')
        o += [part(h, 1.2, 7.22, 4.4, 7.32)] + bed(h, 2.6, vb-2.2) + room(h, 1.85, 8.6, 1.85, 8.6, 'Habitació 2', area_txt='≈12 m²')
    return o

def level_at():
    o = shell('at') + walls('at')
    for h, vb in ((C1, 9.7), (C2, 10)):
        o.append(h.rect(0, 0.1, 4.6, 2.6, fill='url(#deck)')); o.append(h.rect(0, 8.1, 4.6, vb-0.1, fill='url(#deck)'))
        o += [part(h, 0, 2.55, 4.4, 2.75), part(h, 0, 8.0, 4.4, 8.2)]
        o += room(h, 2.2, 1.5, 2.2, 1.5, 'Terrassa', area_txt='≈10 m²') + room(h, 2.2, (8.2+vb)/2, 2.2, (8.2+vb)/2, 'Terrassa', area_txt=f'≈{4.4*(vb-8.3):.0f} m²')
        o += stair(h) + bed(h, 2.0, 3.2) + room(h, 2.8, 5.8, 2.8, 5.8, 'Suite', area_txt='≈14 m²')
        o += [part(h, 1.2, 6.45, 4.4, 6.55)] + shower(h, 3.3, 6.65, 4.3, 7.9) + wc(h, 1.8, 7.9, face=-1) + sink(h, 2.6, 7.65) + room(h, 2.5, 7.0, 2.5, 7.0, 'Bany', area_txt='≈6 m²')
    return o

def level_site():
    o = [poly(CAD, fill='none', stroke=MUTE, stroke_width=0.3, stroke_dasharray='1.2 1')]
    o.append(poly(SITE, fill='#FBF7EA', stroke=INK, stroke_width=0.6))
    o.append(poly(EAT, fill='url(#eat)', stroke=RED, stroke_width=0.5))
    for P in (H1, H2): o.append(poly(P, fill='none', stroke=INK, stroke_width=0.3, stroke_dasharray='2 1'))
    o.append(line(4.6, 0, 4.6, 10, stroke=INK, stroke_width=0.3, stroke_dasharray='2 1'))
    o.append(text(6.9, 5.0, 'CASA 1', size=3.4, weight=700)); o.append(text(2.3, 5.0, 'CASA 2', size=3.4, weight=700))
    o.append(text(6.9, 4.3, 'fondària 9,70 m', size=2.5, fill=MUTE)); o.append(text(2.3, 4.3, 'fondària 10,00 m', size=2.5, fill=MUTE))
    o.append(text(6.9, 7.2, f'Superfície útil ≈{G["area"]:.0f} m²'.replace('.', ','), size=2.8, weight=600))
    labels = [('A','W1','5,90'),('W2','W3','7,10'),('W3','E3','6,40'),('E3','E2','2,70'),('E2','E1','3,00'),('E1','B','9,70'),('B','A','9,20')]
    for a, b, t in labels:
        pa, pb = L[a], L[b]; mu, mv = (pa[0]+pb[0])/2, (pa[1]+pb[1])/2; Ln = math.hypot(pb[0]-pa[0], pb[1]-pa[1])
        nu, nv = -(pb[1]-pa[1])/Ln, (pb[0]-pa[0])/Ln    # left normal: inside for this order
        k = -0.75
        o.append(text(mu+nu*k, mv+nv*k-0.25, t + ' m', size=2.7, weight=600, fill=RED if t in ('2,70', '3,00') else INK))
    cu = sum(p[0] for p in EAT)/4; cv = sum(p[1] for p in EAT)/4
    o.append(text(cu, cv+0.25, 'Ocupat pel veí', size=2.6, weight=700, fill=RED)); o.append(text(cu, cv-0.35, '≈8 m²', size=2.4, fill=RED))
    o.append(f'<rect x="{X(U0+2.2):.2f}" y="{Y(-0.15):.2f}" width="{(U0+2.2+3.0)*SC:.2f}" height="{4.2*SC:.2f}" fill="#EFEFEA"/>')
    o.append(text(4.6, -1.7, "CARRER D'ANSELM CLAVÉ", size=3.2, weight=600, fill=MUTE, letter_spacing='0.6'))
    o.append(text(10.9, 5.0, 'núm. 28', size=2.8, fill=MUTE)); o.append(text(-1.9, 3.0, 'núm. 32', size=2.8, fill=MUTE)); o.append(text(4.0, 14.0, 'veí del darrere', size=2.8, fill=MUTE))
    return o

SHEETS = [('situacio', 'Solar i mides', 'Mides preses al solar (novembre 2026). Línia discontínua grisa: límit segons el Cadastre.', level_site),
          ('pb', 'Planta baixa', 'Garatge per a dos cotxes. Casa 1: safareig petit al pati que queda.', level_pb),
          ('p1', 'Planta primera', 'Casa 1 (nou): sala al davant, cuina a la cantonada del darrere i porta a la terrassa petita. Casa 2: sense canvis.', level_p1),
          ('p2', 'Planta segona', 'Dues habitacions dobles, bany compartit i estudi obert.', level_p2),
          ('at', 'Altell', 'Suite amb bany i terrasses al davant i al darrere.', level_at)]

def furniture_free(): pass
def north():
    # north points to the street (bottom), slightly rotated with the façade
    ang = math.degrees(math.atan2(-f[1], f[0]))  # rotation of the façade on paper
    cx, cy = 40, 40
    return f'<g transform="translate({cx:.1f},{cy:.1f}) rotate({180+ang:.1f})"><circle r="6" fill="none" stroke="{INK}" stroke-width="0.3"/><path d="M0,-5 L2.2,3 L0,1.6 L-2.2,3Z" fill="{INK}"/></g><text x="{cx:.1f}" y="{cy+11:.1f}" font-size="2.6" text-anchor="middle" fill="{INK}">Nord</text>'
def scale_bar():
    x0, y0 = 28, 282
    o = [f'<text x="{x0:.1f}" y="{y0-3:.1f}" font-size="2.5" fill="{INK}">0</text>']
    for i in range(5): o.append(f'<rect x="{x0+i*SC:.2f}" y="{y0:.2f}" width="{SC:.2f}" height="1.6" fill="{INK if i%2==0 else "#fff"}" stroke="{INK}" stroke-width="0.2"/>')
    o.append(f'<text x="{x0+5*SC:.1f}" y="{y0-3:.1f}" font-size="2.5" fill="{INK}" text-anchor="middle">5 m</text>')
    return o
def sheet(key, title, sub_, fn, for_web=False):
    body = fn()
    if key not in ('situacio',):
        cps = ''.join(f'<polygon points="{" ".join(pt(*p) for p in P)}"/>' for P in (H1, H2, Y1, Y2))
        ctx = context(key)
        body = ctx[:1] + [f'<clipPath id="all{key}">{cps}</clipPath><g clip-path="url(#all{key})">'] + body + ['</g>'] + ctx[1:]
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Archivo, Helvetica, Arial, sans-serif" role="img" aria-label="{title}">', DEFS]
    o.append(f'<rect width="{W}" height="{H}" fill="#fff"/>')
    o += body
    o.append(text(6.9, -0.7 if key != 'situacio' else 15.2, '', size=1))
    if key != 'situacio':
        o.append(text(6.9, -2.9, 'CASA 1', size=3.0, weight=700)); o.append(text(2.3, -2.9, 'CASA 2', size=3.0, weight=700))
        o += dim_h(4.6, 9.2, 0, '4,60', off=-0.55) if False else []
    o.append(north()); o += scale_bar()
    # title block
    tx = 300
    o.append(f'<line x1="{tx-8}" y1="14" x2="{tx-8}" y2="283" stroke="#D9D9D2" stroke-width="0.3"/>')
    o.append(f'<text x="{tx}" y="26" font-size="4" font-weight="700" fill="{INK}">Serrajordi-Diaz Investments</text>')
    o.append(f'<text x="{tx}" y="33" font-size="3" fill="{MUTE}">C/ Anselm Clavé, 30 · Llinars del Vallès</text>')
    o.append(f'<text x="{tx}" y="58" font-size="9" font-weight="700" fill="{INK}">{title}</text>')
    y = 68
    for ln in wrap(sub_, 46): o.append(f'<text x="{tx}" y="{y}" font-size="3.2" fill="{INK}">{ln}</text>'); y += 5
    y += 6
    legend = [('#FFF3C4', INK, 'Canvis a la casa 1 (17/11/2026)'), ('url(#eat)', RED, 'Cantonada ocupada pel veí del darrere'), ('none', ACC, 'Solar útil, amb les mides preses al solar')]
    for fill, st, t in legend:
        o.append(f'<rect x="{tx}" y="{y-3.2}" width="7" height="4.2" fill="{fill}" stroke="{st}" stroke-width="0.5"/><text x="{tx+10}" y="{y}" font-size="3" fill="{INK}">{t}</text>'); y += 7
    o.append(f'<text x="{tx}" y="262" font-size="3" fill="{INK}">Escala 1:75 en DIN A3</text>')
    o.append(f'<text x="{tx}" y="268" font-size="3" fill="{INK}">17 de novembre de 2026</text>')
    o.append(f'<text x="{tx}" y="276" font-size="2.6" fill="{MUTE}">Esquema orientatiu, pendent del projecte de l\'arquitecte.</text>')
    o.append('</svg>')
    return '\n'.join(o)
def wrap(s, n):
    out, cur = [], ''
    for w in s.split():
        if len(cur) + len(w) + 1 > n: out.append(cur); cur = w
        else: cur = (cur + ' ' + w).strip()
    return out + [cur]

if __name__ == '__main__':
    import os; os.makedirs('/home/claude/plans/out', exist_ok=True)
    for k, t, s_, fn in SHEETS:
        open(f'/home/claude/plans/out/{k}.svg', 'w').write(sheet(k, t, s_, fn))
    print('ok', [round(area(P), 1) for P in (H1, H2, Y1, Y2)])
