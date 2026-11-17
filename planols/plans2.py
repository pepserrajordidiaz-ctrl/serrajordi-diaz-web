# Plans v2: follows Pep's clean plans (casa A / casa B, 17-11-2026) on the measured site.
import math, sys
sys.path.insert(0, '/home/claude/plans')
from geo import G, A, f, d, sub, dot
SC = 1000/75
L = G['local']
SITE = [L[k] for k in ('A','W1','Wj1','W2','W3','E3','E2','E1','B')]
EAT = [L[k] for k in ('E1','E2','E3','E4')]
INK, MUTE, RED, ACC = '#1C2321', '#7B837F', '#A63A2E', '#EDB91F'
COL = {'gar': '#F1F1EF', 'day': '#F6F0E4', 'night': '#EEF1EC', 'suite': '#EFEDF5', 'wet': '#FFFFFF', 'ter': '#EFE6D3', 'green': '#DDE8D2', 'new': '#FFF1B8'}

def clip(poly, keep):
    out = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i+1) % len(poly)]; fa, fb = keep(a), keep(b)
        if fa >= 0: out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa/(fa-fb); out.append((a[0]+(b[0]-a[0])*t, a[1]+(b[1]-a[1])*t))
    return out
def area(P): return abs(sum(P[i][0]*P[(i+1)%len(P)][1]-P[(i+1)%len(P)][0]*P[i][1] for i in range(len(P))))/2 if len(P) > 2 else 0
DA, DB = 9.70, 9.80                                   # body depth: casa A stops where the occupied corner starts
HA = clip(clip(SITE, lambda p: p[0]-4.6), lambda p: DA-p[1]); YA = clip(clip(SITE, lambda p: p[0]-4.6), lambda p: p[1]-DA)
HB = clip(clip(SITE, lambda p: 4.6-p[0]), lambda p: DB-p[1]); YB = clip(clip(SITE, lambda p: 4.6-p[0]), lambda p: p[1]-DB)

CUR = {}
def X(u): return CUR['cx'] + (CUR['um'] - u)*SC
def Y(v): return CUR['fy'] - v*SC
def pt(u, v): return f"{X(u):.2f},{Y(v):.2f}"
def attrs(a): return ' '.join(f'{k.replace("_","-")}="{v}"' for k, v in a.items())
def poly(P, **a): return f'<polygon points="{" ".join(pt(*p) for p in P)}" {attrs(a)}/>'
def text_xy(x, y, s, size=3.0, weight=400, fill=INK, anchor='middle', **a):
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" {attrs(a)}>{s}</text>'

class H:
    def __init__(s, name):
        s.name = name; s.A = name == 'A'
        s.sg = 1 if s.A else -1; s.u0 = 4.8 if s.A else 4.4
        s.D = DA if s.A else DB; s.Di = s.D - 0.2
        s.P = HA if s.A else HB; s.Yd = YA if s.A else YB
    def u(s, x): return s.u0 + s.sg*x
    def R(s, x0, v0, x1, v1):     # rect polygon in local coords
        return [(s.u(x0), v0), (s.u(x1), v0), (s.u(x1), v1), (s.u(x0), v1)]
    def rect(s, x0, v0, x1, v1, **a): return poly(s.R(x0, v0, x1, v1), **a)
    def line(s, x0, v0, x1, v1, **a): return f'<line x1="{X(s.u(x0)):.2f}" y1="{Y(v0):.2f}" x2="{X(s.u(x1)):.2f}" y2="{Y(v1):.2f}" {attrs(a)}/>'
    def text(s, x, v, t, **a): return text_xy(X(s.u(x)), Y(v), t, **a)
    def circle(s, x, v, r, **a): return f'<circle cx="{X(s.u(x)):.2f}" cy="{Y(v):.2f}" r="{r*SC:.2f}" {attrs(a)}/>'
    def width_at(s, v):           # free width from the shared wall at depth v
        P = s.P if v <= s.D else s.Yd
        xs = [p[0] for p in clip(clip(P, lambda p: p[1]-(v-0.01)), lambda p: (v+0.01)-p[1])]
        return (max(xs) - s.u0 - 0.2) if s.A else (s.u0 - min(xs) - 0.2)
    def zone_area(s, x0, v0, x1, v1, P=None):
        R = s.R(x0, v0, x1, v1); us = sorted(p[0] for p in R)
        Q = clip(clip(clip(clip(P or s.P, lambda p: p[0]-us[0]), lambda p: us[-1]-p[0]), lambda p: p[1]-v0), lambda p: v1-p[1])
        return area(Q)

FUR = dict(fill='none', stroke=MUTE, stroke_width=0.25)
def fill_zone(h, x0, v0, x1, v1, c): return h.rect(x0, v0, x1, v1, fill=c)
def label(h, x, v, name, sub_=None, tag=None, size=3.1):
    o = [h.text(x, v, name, size=size, weight=700)]
    if sub_: o.append(h.text(x, v-0.42, sub_, size=2.3, fill=MUTE))
    if tag: o.append(h.text(x, v-0.85, tag, size=2.1, weight=700, fill='#9A6B00'))
    return o
def m2(a): return f'≈{a:.1f}'.replace('.', ',') + ' m²'
def part(h, x0, v0, x1, v1): return h.rect(x0, v0, x1, v1, fill='#5A615D')
def door(h, x, v, w, into=1):
    o = [h.rect(x, v-0.1, x+w, v+0.1, fill='#fff')]
    o.append(h.line(x, v, x, v+into*w, stroke=INK, stroke_width=0.3))
    sweep = 1 if into*h.sg < 0 else 0
    o.append(f'<path d="M{X(h.u(x)):.2f},{Y(v+into*w):.2f} A{w*SC:.2f},{w*SC:.2f} 0 0 {sweep} {X(h.u(x+w)):.2f},{Y(v):.2f}" fill="none" stroke="{MUTE}" stroke-width="0.2" stroke-dasharray="0.6 0.4"/>')
    return o
def slider(h, x0, x1, v): return [h.rect(x0, v-0.1, x1, v+0.1, fill='#fff'), h.line(x0, v-0.03, (x0+x1)/2+0.2, v-0.03, stroke=INK, stroke_width=0.35), h.line((x0+x1)/2-0.2, v+0.04, x1, v+0.04, stroke=INK, stroke_width=0.35)]
def window(h, x0, x1, v): return [h.rect(x0, v-0.1, x1, v+0.1, fill='#fff'), h.line(x0, v, x1, v, stroke=INK, stroke_width=0.2)]
def stair_straight(h, v0, v1):
    o = [h.rect(0, v0, 1.0, v1, fill='#fff', stroke=INK, stroke_width=0.3)]
    n = 16; o += [h.line(0, v0+i*(v1-v0)/n, 1.0, v0+i*(v1-v0)/n, stroke=MUTE, stroke_width=0.2) for i in range(1, n)]
    o.append(h.line(0.5, v0+0.15, 0.5, v1-0.25, stroke=INK, stroke_width=0.3, marker_end='url(#arr)'))
    o.append(h.circle(0.5, v0+0.15, 0.06, fill=INK)); o.append(h.text(1.45, v0+0.1, 'PUJA', size=2.3, weight=700))
    return o
def stair_L(h):   # P1 / P2: winders at 2,85–3,85, straight run to 5,90, landing to 6,75
    o = [h.rect(0, 2.85, 1.95, 3.85, fill='#fff', stroke=INK, stroke_width=0.3), h.rect(0, 3.85, 1.0, 5.9, fill='#fff', stroke=INK, stroke_width=0.3)]
    for i in range(1, 9): o.append(h.line(0, 3.85+i*(5.9-3.85)/9, 1.0, 3.85+i*(5.9-3.85)/9, stroke=MUTE, stroke_width=0.2))
    for x in (1.2, 1.45, 1.7): o.append(h.line(x, 2.85, x, 3.85, stroke=MUTE, stroke_width=0.2))
    o += [h.line(1.0, 2.85, 0.0, 3.85, stroke=MUTE, stroke_width=0.2), h.line(1.0, 3.35, 0.0, 3.85, stroke=MUTE, stroke_width=0.2), h.line(1.0, 3.85, 1.0, 2.85, stroke=MUTE, stroke_width=0.2)]
    o.append(h.circle(1.8, 3.35, 0.06, fill=INK)); o.append(h.line(1.8, 3.35, 0.5, 3.35, stroke=INK, stroke_width=0.3)); o.append(h.line(0.5, 3.35, 0.5, 5.6, stroke=INK, stroke_width=0.3, marker_end='url(#arr)'))
    o.append(h.text(2.6, 3.25, 'PUJA', size=2.3, weight=700))
    o.append(h.rect(0, 5.9, 1.0, 6.75, fill='#fff', stroke=MUTE, stroke_width=0.2)); o.append(h.text(0.5, 6.25, 'arriba', size=2.0, fill=MUTE))
    return o
def car(h, x, v): return [h.rect(x, v, x+1.85, v+4.3, rx=1.6, fill='none', stroke=MUTE, stroke_width=0.3, stroke_dasharray='1 0.6'), h.rect(x+0.3, v+1.2, x+1.55, v+3.0, **FUR), h.text(x+0.92, v+3.5, 'cotxe', size=2.2, fill=MUTE)]
def bed(h, x, v, w=1.35, l=1.9, head='back'):
    if head == 'back': return [h.rect(x, v, x+w, v+l, fill='#fff', stroke=MUTE, stroke_width=0.25), h.rect(x+0.1, v+l-0.45, x+w/2-0.05, v+l-0.1, **FUR), h.rect(x+w/2+0.05, v+l-0.45, x+w-0.1, v+l-0.1, **FUR)]
    return [h.rect(x, v, x+l, v+w, fill='#fff', stroke=MUTE, stroke_width=0.25), h.rect(x+l-0.45, v+0.1, x+l-0.1, v+w/2-0.05, **FUR), h.rect(x+l-0.45, v+w/2+0.05, x+l-0.1, v+w-0.1, **FUR)]
def table(h, x, v, w=0.9, l=1.4):
    o = [h.rect(x, v, x+w, v+l, fill='#fff', stroke=MUTE, stroke_width=0.25)]
    for k in (0.25, l-0.65): o += [h.rect(x-0.5, v+k, x-0.1, v+k+0.4, **FUR), h.rect(x+w+0.1, v+k, x+w+0.5, v+k+0.4, **FUR)]
    return o
def counter(h, x0, v0, x1, v1): return [h.rect(x0, v0, x1, v1, fill='#fff', stroke=MUTE, stroke_width=0.25)]
def hob(h, x, v): return [h.circle(x+dx, v+dv, 0.09, **FUR) for dx in (-0.14, 0.14) for dv in (-0.14, 0.14)]
def sink(h, x, v): return [h.rect(x-0.28, v-0.18, x+0.28, v+0.18, rx=0.5, **FUR)]
def wc(h, x, v, face=1):
    return [h.rect(x-0.2, v, x+0.2, v+0.15*face, **FUR), f'<ellipse cx="{X(h.u(x)):.2f}" cy="{Y(v+0.42*face):.2f}" rx="{0.18*SC:.2f}" ry="{0.25*SC:.2f}" fill="none" stroke="{MUTE}" stroke-width="0.25"/>']
def basin(h, x, v): return [h.rect(x-0.25, v-0.2, x+0.25, v+0.2, **FUR), f'<ellipse cx="{X(h.u(x)):.2f}" cy="{Y(v):.2f}" rx="{0.15*SC:.2f}" ry="{0.11*SC:.2f}" fill="none" stroke="{MUTE}" stroke-width="0.25"/>']
def shower(h, x0, v0, x1, v1): return [h.rect(x0, v0, x1, v1, fill='#fff', stroke=MUTE, stroke_width=0.25), h.line(x0, v0, x1, v1, **FUR), h.line(x0, v1, x1, v0, **FUR)]
def sofa(h, x0, v0, x1, v1): return [h.rect(x0, v0, x1, v1, fill='#fff', stroke=MUTE, stroke_width=0.25)]
def wardrobe(h, x0, v0, x1, v1, t='armari'): return [h.rect(x0, v0, x1, v1, fill='#fff', stroke=MUTE, stroke_width=0.25), h.line(x0, (v0+v1)/2, x1, (v0+v1)/2, **FUR) if abs(v1-v0) < abs(x1-x0) else h.line((x0+x1)/2, v0, (x0+x1)/2, v1, **FUR), h.text((x0+x1)/2, (v0+v1)/2-0.08, t, size=1.8, fill=MUTE)]
def washer(h, x, v): return [h.rect(x, v, x+0.6, v+0.6, fill='#fff', stroke=MUTE, stroke_width=0.25), h.circle(x+0.3, v+0.3, 0.2, **FUR)]

def shell(h, key, P, wall=0.2, fillc='#fff'):
    cid = f'cp{h.name}{key}{len(P)}{int(P[0][1]*100)}'
    return [f'<clipPath id="{cid}"><polygon points="{" ".join(pt(*p) for p in P)}"/></clipPath>', poly(P, fill=fillc)], \
           [poly(P, fill='none', stroke=INK, stroke_width=f'{2*wall*SC:.2f}', clip_path=f'url(#{cid})')], cid

def plan(h, lvl):
    """Return svg parts for one floor of one house (origin set in CUR)."""
    o, top = [], []
    body_in, body_w, cid = shell(h, lvl, h.P)
    yard = h.Yd; Wb = h.width_at(h.Di - 0.3)
    if lvl in ('pb', 'p1'):
        yi, yw, ycid = shell(h, lvl + 'y', yard, wall=0.15 if lvl == 'pb' else 0.0, fillc='#fff')
        o += yi
    elif lvl == 'p2':
        o.append(poly(yard, fill='none', stroke=MUTE, stroke_width=0.25, stroke_dasharray='1 0.7'))
        o.append(text_xy(*map(lambda t: t, (sum(X(p[0]) for p in yard)/len(yard), sum(Y(p[1]) for p in yard)/len(yard))), 'terrassa P1 (a sota)', size=2.2, fill=MUTE, font_style='italic'))
    else:
        o.append(poly(yard, fill='none', stroke=MUTE, stroke_width=0.25, stroke_dasharray='1 0.7'))
    o += body_in
    z = []                               # coloured zones, clipped to the body
    if lvl == 'pb':
        z += [fill_zone(h, -1, 0, 9, h.D, COL['gar']), fill_zone(h, -0.5, 0, 1.3, 1.3, '#E2E4E0')]
        o += [f'<g clip-path="url(#{cid})">'] + z + ['</g>']
        o += [part(h, 1.25, 0.0, 1.38, 1.3), part(h, 0, 1.25, 1.38, 1.38)] + door(h, 0.15, 1.32, 0.85, into=1)
        o += stair_straight(h, 2.25, 5.85) + [part(h, 1.0, 2.25, 1.1, 5.85)]
        o += car(h, 1.95, 0.55) + car(h, 1.95, 5.1)
        ga = h.zone_area(0, 0.2, 9, h.Di) - 1.25*1.1 - 1.1*3.6
        x0, y0 = X(h.u(1.55)), Y(5.0)
        o += [text_xy(x0, y0, 'GARATGE', size=3.1, weight=700, transform=f'rotate(-90 {x0:.2f} {y0:.2f})'), text_xy(x0 + 3.4, y0, f'2 cotxes en filera · {m2(ga)}', size=2.2, fill=MUTE, transform=f'rotate(-90 {x0+3.4:.2f} {y0:.2f})')]
        o.append(h.text(0.62, 0.62, 'PORXO', size=2.4, weight=700))
        o.append(h.rect(1.48, -0.12, 4.33, 0.12, fill='#fff', stroke=INK, stroke_width=0.25, stroke_dasharray='1 0.6'))
        o.append(h.text(2.9, 0.4, "porta de garatge 2,85", size=2.0, fill=MUTE))
        o += door(h, 0.6, h.D - 0.1, 0.8, into=1)
        ya = area(yard)
        if h.A:
            o += washer(h, 0.25, h.D + 1.5) + [h.rect(0.95, h.D + 1.45, 1.55, h.D + 2.05, **FUR)]
            o += label(h, 0.9, h.D + 1.0, 'SAFAREIG', m2(ya - 1.6), tag='NOU · més petit', size=2.6)
        else:
            o += label(h, 2.1, h.D + 1.75, 'SALA / SAFAREIG', m2(ya - 2.3))
    elif lvl == 'p1':
        if h.A:   # new: living at the front, dining in the middle, kitchen in the back corner, door to the small terrace on its right
            z += [fill_zone(h, -1, 0, 9, h.D, COL['new'])]
            o += [f'<g clip-path="url(#{cid})">'] + z + ['</g>']
            o += window(h, 0.5, 3.8, 0.1)
            o += [h.rect(0.0, 0.6, 0.35, 2.4, fill='#fff', stroke=MUTE, stroke_width=0.25), h.text(0.17, 1.4, 'TV', size=1.8, fill=MUTE)]
            o += sofa(h, 3.3, 0.5, 4.25, 2.75) + [h.rect(1.5, 0.7, 2.3, 1.5, **FUR)]
            o += label(h, 2.3, 2.6, 'ESTAR', m2(h.zone_area(0, 0.2, 9, 2.85) + h.zone_area(1.95, 2.85, 9, 3.6)), tag='NOU')
            o += table(h, 2.6, 3.95, l=1.4) + label(h, 3.05, 5.95, 'MENJADOR', None, size=2.6)
            Wk = h.width_at(8.0)
            o += counter(h, Wk - 0.62, 6.85, Wk + 0.3, h.Di) + counter(h, 1.75, h.Di - 0.62, Wk + 0.3, h.Di)
            o += hob(h, Wk - 0.31, 7.9) + sink(h, 2.6, h.Di - 0.31) + [h.rect(Wk - 0.62, 6.85, Wk + 0.3, 7.5, fill='#fff', stroke=MUTE, stroke_width=0.25), h.text(Wk - 0.2, 7.1, 'nevera', size=1.7, fill=MUTE)]
            o += label(h, 2.55, 8.05, 'CUINA', m2(h.zone_area(1.95, 6.75, 9, h.Di)), tag='NOU')
            o += slider(h, 0.2, 1.4, h.D - 0.1)
            ya = area(yard)
            o += [poly(yard, fill=COL['ter'])] + label(h, 0.85, h.D + 1.2, 'TERRASSA', m2(ya), tag='NOU · petita', size=2.6)
        else:
            z += [fill_zone(h, -1, 0, 9, h.D, COL['day'])]
            o += [f'<g clip-path="url(#{cid})">'] + z + ['</g>']
            Wf = h.width_at(0.6)
            o += counter(h, 1.0, 0.2, Wf, 0.8) + counter(h, 0, 0.2, 0.6, 2.3) + hob(h, 0.3, 1.6) + sink(h, 2.3, 0.5)
            o += [h.rect(Wf - 0.6, 0.2, Wf, 0.85, fill='#fff', stroke=MUTE, stroke_width=0.25), h.text(Wf - 0.3, 0.45, 'nevera', size=1.7, fill=MUTE), h.text(0.3, 0.9, 'forn', size=1.7, fill=MUTE)]
            o += table(h, 2.5, 3.8, l=1.4) + label(h, 2.7, 2.15, 'CUINA · MENJADOR', m2(h.zone_area(0, 0.2, 9, 6.75) - 1.95*1.0 - 3.9 - 0.85))
            Wm = h.width_at(8.0)
            o += sofa(h, 0.05, 7.4, 0.95, h.Di - 0.1) + [h.rect(Wm - 0.35, 6.9, Wm, 9.0, fill='#fff', stroke=MUTE, stroke_width=0.25), h.text(Wm - 0.17, 7.9, 'TV', size=1.8, fill=MUTE), h.rect(1.6, 7.6, 2.4, 8.4, **FUR)]
            o += label(h, 2.3, 7.05, 'ESTAR', m2(h.zone_area(0, 6.75, 9, h.Di) + h.zone_area(1.95, 5.9, 9, 6.75)))
            o += slider(h, 0.3, min(Wb, 4.2) - 0.2, h.D - 0.1)
            ya = area(yard)
            o += [poly(yard, fill=COL['ter'])] + bed(h, 1.4, h.D + 0.9, w=1.4, l=1.6) + label(h, 2.1, h.D + 0.55, 'TERRASSA', m2(ya), size=2.6)
        # common: L stair and toilet
        o += stair_L(h) + [part(h, 1.0, 3.85, 1.1, 5.9), part(h, 1.1, 3.85, 2.05, 3.95), part(h, 1.95, 3.95, 2.05, 5.9)]
        o += wc(h, 1.55, 4.0, face=1) + basin(h, 1.55, 5.45) + door(h, 1.12, 5.9, 0.75, into=1) + [h.text(1.55, 4.95, 'LAVABO', size=2.0, weight=700)]
    elif lvl == 'p2':
        z += [fill_zone(h, -1, 0, 9, h.D, COL['night'])]
        o += [f'<g clip-path="url(#{cid})">'] + z + ['</g>']
        Wf = h.width_at(0.6)
        o += window(h, 0.6, Wf - 0.4, 0.1) + [h.rect(0.6, 0.25, Wf - 0.4, 0.85, fill='#fff', stroke=MUTE, stroke_width=0.25)]
        o += [h.rect(x, 1.0, x + 0.4, 1.4, **FUR) for x in (1.0, 2.0, 2.8)]
        o += label(h, Wf/2, 2.1, 'ESTUDI', f'obert · {m2(h.zone_area(0, 0.2, 9, 2.85))}')
        o += stair_L(h) + [part(h, 1.0, 3.85, 1.1, 5.9)]
        o += [part(h, 1.1, 3.85, 3.05, 3.95), part(h, 2.95, 3.95, 3.05, 5.9), part(h, 1.1, 5.8, 2.3, 5.9)]
        o += shower(h, 1.2, 4.0, 2.05, 4.85) + wc(h, 2.75, 5.75, face=-1) + basin(h, 1.55, 5.45) + door(h, 2.35, 5.85, 0.6, into=-1) + label(h, 2.1, 5.1, 'BANY', m2(1.85*1.85), size=2.4)
        o.append(h.text(3.5, 4.7, 'pas', size=2.1, fill=MUTE))
        sm = Wb/2
        o += [part(h, 1.0, 6.7, Wb + 0.3, 6.8), part(h, sm - 0.05, 6.8, sm + 0.05, h.Di)]
        o += wardrobe(h, 0.05, 6.85, sm - 0.85, 7.35) + wardrobe(h, sm + 0.85, 6.85, Wb, 7.35)
        o += door(h, sm - 0.82, 6.75, 0.75, into=1) + door(h, sm + 0.07, 6.75, 0.75, into=1)
        o += bed(h, (sm - 1.35)/2, h.Di - 1.95) + bed(h, sm + (Wb - sm - 1.35)/2, h.Di - 1.95)
        o += window(h, 0.3, sm - 0.3, h.D - 0.1) + window(h, sm + 0.3, Wb - 0.3, h.D - 0.1)
        dA = h.zone_area(0, 6.8, sm, h.Di)
        o += label(h, sm/2, h.Di - 1.05, 'DORM. ' + ('1' if h.A else '2'), m2(dA), size=2.4) + label(h, sm + (Wb - sm)/2, h.Di - 1.05, 'DORM. ' + ('2' if h.A else '1'), m2(h.zone_area(sm, 6.8, 9, h.Di)), size=2.4)
    else:   # àtic
        vt = h.D - 2.05
        z += [fill_zone(h, -1, 0, 9, 2.8, COL['ter']), fill_zone(h, -1, vt, 9, h.D, COL['ter']), fill_zone(h, -1, 2.8, 9, vt, COL['suite'])]
        z += [fill_zone(h, -1, 0.2, 9, 0.6, COL['green']), fill_zone(h, -1, h.Di - 0.4, 9, h.Di, COL['green'])]
        o += [f'<g clip-path="url(#{cid})">'] + z + ['</g>']
        o += [part(h, 0, 2.75, 9, 2.9), part(h, 0, vt - 0.05, 9, vt + 0.1)] + slider(h, 1.3, 3.2, 2.82) + slider(h, 1.2, 2.6, vt)
        Wf = h.width_at(1.5)
        o += label(h, Wf/2, 1.55, 'TERRASSA', m2(h.zone_area(0, 0.2, 9, 2.75))) + [h.text(Wf/2, 0.32, 'jardinera', size=1.9, fill=MUTE)]
        o += label(h, Wb/2, (vt + h.D)/2 + 0.1, 'TERRASSA', m2(h.zone_area(0, vt + 0.1, 9, h.Di))) + [h.text(Wb/2, h.Di - 0.3, 'jardinera', size=1.9, fill=MUTE)]
        o += [h.rect(0, 2.9, 1.0, 5.9, fill='#fff', stroke=MUTE, stroke_width=0.25), h.line(0, 2.9, 1.0, 5.9, **FUR), h.text(0.5, 4.3, 'buit escala', size=1.8, fill=MUTE, transform='')]
        o += [h.rect(0, 5.9, 1.0, 6.75, fill='#fff', stroke=MUTE, stroke_width=0.2), h.text(0.5, 6.25, 'arriba', size=2.0, fill=MUTE)]
        o += [part(h, 1.0, 2.9, 1.1, 5.9)]
        Wm = h.width_at(6.6)
        if h.A:
            o += [part(h, 2.1, 5.75, 2.2, vt), part(h, 2.1, 5.7, Wm + 0.3, 5.8)] + shower(h, Wm - 0.85, 5.85, Wm, vt - 0.1) + wc(h, 2.75, vt - 0.05, face=-1) + basin(h, 2.7, 6.1) + door(h, 2.25, 5.75, 0.6, into=-1)
            o += label(h, 3.3, 6.85, 'BANY', m2((Wm - 2.2)*(vt - 5.8)), size=2.4) + wardrobe(h, 1.1, 6.75, 2.05, vt - 0.05)
        else:
            o += [part(h, 2.55, 5.75, 2.65, vt), part(h, 1.1, 5.7, Wm + 0.3, 5.8)] + shower(h, Wm - 0.9, 6.7, Wm, vt - 0.1) + wc(h, 3.0, 5.85, face=1) + basin(h, 3.0, vt - 0.3)
            o += label(h, 3.6, 6.1, 'BANY', m2((Wm - 2.65)*(vt - 5.8)), size=2.3) + wardrobe(h, 1.15, 6.95, 2.5, vt - 0.05, 'vestidor') + door(h, 1.6, 5.75, 0.7, into=-1)
        o += bed(h, 2.0, 3.25, w=1.5, l=2.0) + wardrobe(h, 1.15, 3.0, 1.6, 5.0, 'TV')
        o += label(h, 3.0 if h.A else 3.2, 5.35, 'SUITE', f'dormitori {m2(h.zone_area(1.1, 2.9, 9, 5.7))}')
    uid = f'u{h.name}{lvl}'
    out = [f'<clipPath id="{uid}"><polygon points="{" ".join(pt(*p) for p in h.P)}"/><polygon points="{" ".join(pt(*p) for p in yard)}"/></clipPath>']
    keep = [x for x in o if 'stroke-dasharray="1 0.7"' in x or 'font-style' in x]     # P1-terrace outline on upper floors stays unclipped
    out += keep + [f'<g clip-path="url(#{uid})">'] + [x for x in o if x not in keep] + ['</g>'] + body_w
    if lvl == 'pb': out += shell(h, lvl + 'yw', yard, wall=0.15, fillc='none')[1]
    return out

def neighbour_and_street(h, lvl):
    o = []
    if h.A:
        o.append(poly(EAT, fill='url(#eat)', stroke=RED, stroke_width=0.45))
        cu = sum(p[0] for p in EAT)/4; cv = sum(p[1] for p in EAT)/4
        o.append(text_xy(X(cu), Y(cv)-1, 'ocupat pel', size=2.2, weight=700, fill=RED)); o.append(text_xy(X(cu), Y(cv)+2.2, 'veí del darrere', size=2.2, weight=700, fill=RED))
        o.append(text_xy(X(9.95), Y(6.5), 'núm. 28 (veí)', size=2.2, fill=MUTE, transform=f'rotate(-90 {X(9.95):.1f} {Y(6.5):.1f})'))
        o.append(text_xy(X(4.25), Y(6.5), 'CASA B', size=2.2, fill=MUTE, transform=f'rotate(-90 {X(4.25):.1f} {Y(6.5):.1f})'))
    else:
        o.append(text_xy(X(-1.35), Y(6.5), 'veí (parcel·la 02)', size=2.2, fill=MUTE, transform=f'rotate(-90 {X(-1.35):.1f} {Y(6.5):.1f})'))
        o.append(text_xy(X(4.95), Y(6.5), 'CASA A', size=2.2, fill=MUTE, transform=f'rotate(-90 {X(4.95):.1f} {Y(6.5):.1f})'))
    us = [p[0] for p in h.P]
    o.append(f'<line x1="{X(max(us))-3:.1f}" y1="{Y(0)+0.6:.1f}" x2="{X(min(us))+3:.1f}" y2="{Y(0)+0.6:.1f}" stroke="#8B5FA8" stroke-width="0.35" stroke-dasharray="1.4 0.9"/>')
    o.append(text_xy((X(min(us))+X(max(us)))/2, Y(0)+6, "C/ ANSELM CLAVÉ", size=2.4, weight=700, fill='#6E4A8C'))
    return o

def dim_bottom(h, txt):
    us = [p[0] for p in h.P if p[1] < 0.5]; x0, x1 = X(h.u(0)), X(h.u(h.width_at(0.6)))
    y = Y(0) + 12
    return [f'<line x1="{x0:.2f}" y1="{y:.2f}" x2="{x1:.2f}" y2="{y:.2f}" stroke="{INK}" stroke-width="0.25"/>'] + [f'<line x1="{x-1:.2f}" y1="{y+1:.2f}" x2="{x+1:.2f}" y2="{y-1:.2f}" stroke="{INK}" stroke-width="0.25"/>' for x in (x0, x1)] + [text_xy((x0+x1)/2, y-1.2, txt, size=2.3)]
def dim_side(h, v0, v1, txt):
    us = [p[0] for p in h.P]; x = X(min(us)) + 4 if h.A else X(max(us)) - 4
    if h.A: x = X(max(us)) - 4
    else: x = X(min(us)) + 4
    x = x - 4 if h.A else x + 4
    o = [f'<line x1="{x:.2f}" y1="{Y(v0):.2f}" x2="{x:.2f}" y2="{Y(v1):.2f}" stroke="{INK}" stroke-width="0.25"/>'] + [f'<line x1="{x-1:.2f}" y1="{Y(v)+1:.2f}" x2="{x+1:.2f}" y2="{Y(v)-1:.2f}" stroke="{INK}" stroke-width="0.25"/>' for v in (v0, v1)]
    ym = (Y(v0)+Y(v1))/2; o.append(text_xy(x-1.3, ym, txt, size=2.2, transform=f'rotate(-90 {x-1.3:.2f} {ym:.2f})')); return o

DEFS = f'''<defs><pattern id="eat" width="2.4" height="2.4" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><rect width="2.4" height="2.4" fill="#F6E1DD"/><rect width="1.0" height="2.4" fill="#E4A79E"/></pattern>
<marker id="arr" viewBox="0 0 6 6" refX="5" refY="3" markerWidth="4" markerHeight="4" orient="auto"><path d="M0 0L6 3L0 6z" fill="{INK}"/></marker></defs>'''
LV = [('pb', 'PLANTA BAIXA', 'cota +0,00 m'), ('p1', 'PLANTA PRIMERA', 'cota +2,95 m'), ('p2', 'PLANTA SEGONA', 'cota +5,90 m'), ('at', 'PLANTA TERCERA · ÀTIC', 'cota +8,85 m')]
def house_sheet(name):
    h = H(name)
    us = [p[0] for p in SITE if (p[0] >= 4.6 if h.A else p[0] <= 4.6)] + [4.6]
    um = (max(us) + min(us))/2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" font-family="Archivo, Helvetica, Arial, sans-serif" role="img" aria-label="Casa {name}">', DEFS.replace('id="eat"', f'id="eat{name}"').replace('id="arr"', f'id="arr{name}"'), '<rect width="420" height="297" fill="#fff"/>']
    o.append(text_xy(12, 20, f'CASA ADOSSADA {name} · C/ Anselm Clavé 30, Llinars del Vallès', size=5.2, weight=700, anchor='start'))
    sub_ = ("Distribució dels plànols de Pep sobre les mides reals del solar. El veí del darrere ocupa 3,00 × 2,70 m: cuina al darrere i estar al davant a la P1." if h.A
            else "Mateixa distribució que la casa A en espill, ajustada al límit real de la parcel·la (graó a 5,90 m de la façana).")
    o.append(text_xy(12, 27, sub_ + ' · Serrajordi-Diaz Investments', size=2.7, fill=MUTE, anchor='start'))
    o.append(text_xy(408, 20, 'E 1:75 (en DIN A3)', size=4, weight=700, anchor='end'))
    for i in range(5): o.append(f'<rect x="{341.3+i*SC:.2f}" y="24" width="{SC:.2f}" height="2" fill="{INK if i % 2 == 0 else "#fff"}" stroke="{INK}" stroke-width="0.2"/>')
    o.append(text_xy(341.3, 30.5, '0', size=2.2)); o.append(text_xy(341.3+5*SC, 30.5, '5 m', size=2.2))
    for i, (k, t, c) in enumerate(LV):
        CUR.update(cx=58 + i*101, um=um, fy=238)
        o.append(text_xy(CUR['cx'], 52, t, size=3.6, weight=700)); o.append(text_xy(CUR['cx'], 57, c, size=2.4, fill=MUTE))
        o += neighbour_and_street(h, k) + plan(h, k)
        if k in ('p1', 'at'): o += dim_bottom(h, f'{h.width_at(0.6):.2f}'.replace('.', ',') + ' lliures')
        if k == 'pb':
            o += dim_side(h, 0, h.D, f'{h.D:.2f}'.replace('.', ',')) + dim_side(h, h.D, max(p[1] for p in h.Yd), f'≈{max(p[1] for p in h.Yd)-h.D:.1f}'.replace('.', ','))
            o += dim_bottom(h, '1,25 porxo · 2,85 porta de garatge')
    notes = ['Superfícies útils orientatives, calculades amb les mides preses al solar el 17/11/2026 (façana 9,20 · fondària 9,70 al costat del núm. 28).',
             "Escala d'1,00 m de pas al costat de la mitgera, a la mateixa posició a totes les plantes; a P1 i P2 arrenca en L amb graons compensats · 16 graons ≈18,4 cm (2,95 m entre forjats).",
             "Pendent de verificar amb l'arquitecte: nombre de plantes i alçada permesa, fondària edificable, recular l'àtic, gàlib de l'escala sota l'àtic i la cantonada ocupada pel veí."]
    for j, n in enumerate(notes): o.append(text_xy(12, 270 + j*6, n, size=2.5, fill=INK, anchor='start'))
    o.append('</svg>'); return '\n'.join(o).replace('url(#eat)', f'url(#eat{name})').replace('url(#arr)', f'url(#arr{name})')

def site_sheet():
    import plans as P1mod
    return P1mod.sheet('situacio', 'Solar i mides', 'Mides preses al solar (novembre 2026). Línia discontínua grisa: límit segons el Cadastre.', P1mod.level_site).replace('CASA 1', 'CASA A').replace('CASA 2', 'CASA B').replace('fondària 10,00 m', 'fondària 9,80 m').replace('Canvis a la casa 1 (17/11/2026)', 'Canvis a la casa A (17/11/2026)')

if __name__ == '__main__':
    import os; os.makedirs('/home/claude/plans/out2', exist_ok=True)
    open('/home/claude/plans/out2/casaA.svg', 'w').write(house_sheet('A'))
    open('/home/claude/plans/out2/casaB.svg', 'w').write(house_sheet('B'))
    open('/home/claude/plans/out2/solar.svg', 'w').write(site_sheet())
    hA, hB = H('A'), H('B')
    print('A width front/back', round(hA.width_at(0.6), 2), round(hA.width_at(9.2), 2), 'B', round(hB.width_at(0.6), 2), round(hB.width_at(5.0), 2), round(hB.width_at(7.0), 2), round(hB.width_at(9.4), 2))
    print('yards', round(area(YA), 1), round(area(YB), 1))
