# Technical sheets "Parets i mides · sense mobles": one A3 per house, 1:75, same composition as the furnished sheets,
# so every floor overlays its furnished version exactly. Geometry comes from the same plan() calls; only furniture,
# colour fills and furniture texts are removed, and dimensions are added.
import math, re, sys
sys.path.insert(0, '/home/claude/plans')
import plans2 as P
INK, MUTE = P.INK, P.MUTE
EXT, INT, OPN = '#1C2321', '#2F5F9E', '#6E7672'
REC = []
_orig = {k: getattr(P, k) for k in ('part', 'door', 'door_v', 'window', 'slider', 'slider_v')}
def _part(h, x0, v0, x1, v1): REC.append(('wall', (x0, v0, x1, v1))); return _orig['part'](h, x0, v0, x1, v1)
def _door(h, x, v, w, into=1, hinge='start'): REC.append(('oh', (x, x + w, v, 'p'))); return _orig['door'](h, x, v, w, into, hinge)
def _door_v(h, xs, v, w, into=1, hinge='start'): REC.append(('ov', (v, v + w, xs, 'p'))); return _orig['door_v'](h, xs, v, w, into, hinge)
def _window(h, x0, x1, v): REC.append(('oh', (x0, x1, v, 'f'))); return _orig['window'](h, x0, x1, v)
def _slider(h, x0, x1, v): REC.append(('oh', (x0, x1, v, 'c'))); return _orig['slider'](h, x0, x1, v)
def _slider_v(h, xs, v0, v1): REC.append(('ov', (v0, v1, xs, 'c'))); return _orig['slider_v'](h, xs, v0, v1)
P.part, P.door, P.door_v, P.window, P.slider, P.slider_v = _part, _door, _door_v, _window, _slider, _slider_v
fmt = P.fmt
FILLS = set(P.COL.values()) | {'#E2E4E0'}

def keep(el):
    if el.startswith('<text'): return False                     # all texts are re-set below
    if el.startswith('<g') or el.startswith('</g'): return True
    m = re.search(r'fill="(#[0-9A-Fa-f]{6})"', el)
    if m and m.group(1) in FILLS and 'stroke=' not in el: return False   # colour fills of rooms and terraces
    if '<ellipse' in el: return False
    if el.startswith('<circle') and 'stroke="#7B837F"' in el: return False
    if 'stroke-dasharray="1 0.7"' in el: return True             # outline of the P1 terrace seen from above
    if 'fill="#fff" stroke="#7B837F"' in el: return False         # furniture
    if 'stroke="#7B837F"' in el and any(f'stroke-width="{w}"' in el for w in ('0.25', '0.15', '0.3')): return False
    if el.startswith('<line') and 'stroke="#1C2321" stroke-width="0.25"' in el and 'dasharray' not in el: return False   # wardrobe fronts
    return True
def tidy(el): return el.replace('fill="#6B726E"', 'fill="#3A403D"')

def T(x, y, s, size=1.8, fill=INK, ang=0, weight=400, anchor='middle'):
    if ang >= 89.9: ang -= 180
    if ang < -90.1: ang += 180
    return f'<text x="{x:.2f}" y="{y:.2f}" font-size="{size}" font-weight="{weight}" fill="{fill}" text-anchor="{anchor}" transform="rotate({ang:.1f} {x:.2f} {y:.2f})">{s}</text>'

def dimline(a, b, n, d, col, txt, ext=True, size=1.75):
    """Dimension line parallel to a–b (local metres), offset d along unit normal n, with extension lines and ticks."""
    A = (a[0] + n[0]*d, a[1] + n[1]*d); B = (b[0] + n[0]*d, b[1] + n[1]*d)
    ax, ay, bx, by = P.X(A[0]), P.Y(A[1]), P.X(B[0]), P.Y(B[1])
    o = [f'<line x1="{ax:.2f}" y1="{ay:.2f}" x2="{bx:.2f}" y2="{by:.2f}" stroke="{col}" stroke-width="0.18"/>']
    if ext:
        for p in (a, b):
            s0 = (p[0] + n[0]*0.12, p[1] + n[1]*0.12); s1 = (p[0] + n[0]*(d + 0.12), p[1] + n[1]*(d + 0.12))
            o.append(f'<line x1="{P.X(s0[0]):.2f}" y1="{P.Y(s0[1]):.2f}" x2="{P.X(s1[0]):.2f}" y2="{P.Y(s1[1]):.2f}" stroke="{col}" stroke-width="0.12"/>')
    L = math.hypot(bx - ax, by - ay) or 1; ux, uy = (bx - ax)/L, (by - ay)/L
    for x, y in ((ax, ay), (bx, by)):            # 45° ticks
        tx, ty = (ux - uy)*0.75, (uy + ux)*0.75
        o.append(f'<line x1="{x - tx:.2f}" y1="{y - ty:.2f}" x2="{x + tx:.2f}" y2="{y + ty:.2f}" stroke="{col}" stroke-width="0.25"/>')
    ang = math.degrees(math.atan2(by - ay, bx - ax))
    a2 = ang - 180 if ang >= 89.9 else (ang + 180 if ang < -90.1 else ang)
    nx, ny = P.X(A[0] + n[0]) - P.X(A[0]), P.Y(A[1] + n[1]) - P.Y(A[1])
    upx, upy = math.sin(math.radians(a2)), -math.cos(math.radians(a2))     # screen 'up' of the rotated text
    k = 0.45 if upx*nx + upy*ny > 0 else -(size*0.72 + 0.45)                 # text always on the side away from the wall
    mx, my = (ax + bx)/2 + upx*k, (ay + by)/2 + upy*k
    o.append(T(mx, my, txt, size=size, fill=col, ang=a2))
    return o

def outward(poly, a, b):
    L = math.dist(a, b); nu, nv = -(b[1] - a[1])/L, (b[0] - a[0])/L
    cu = sum(p[0] for p in poly)/len(poly); cv = sum(p[1] for p in poly)/len(poly)
    mu, mv = (a[0] + b[0])/2, (a[1] + b[1])/2
    return (nu, nv) if (mu + nu - cu)**2 + (mv + nv - cv)**2 > (mu - nu - cu)**2 + (mv - nv - cv)**2 else (-nu, -nv)

def exterior_dims(poly, seen, d=0.62, skip=None):
    o = []
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        L = math.dist(a, b)
        if skip and skip(a, b): continue
        key = tuple(sorted([(round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2))]))
        if L < 0.2 or key in seen: continue
        seen.add(key)
        o += dimline(a, b, outward(poly, a, b), d if L > 0.8 else d + 0.8, EXT, fmt(L))
    return o

def interior_dims(h):
    o = []; oh = [r for k, r in REC if k == 'oh']; ov = [r for k, r in REC if k == 'ov']; done = set()
    for k, (x0, v0, x1, v1) in [r for r in REC if r[0] == 'wall']:
        x0, x1 = sorted((x0, x1)); v0, v1 = sorted((v0, v1))
        horiz = (x1 - x0) >= (v1 - v0)
        if horiz:
            vm = (v0 + v1)/2; lo, hi = max(x0, 0.0), min(x1, h.width_at(vm))
            cuts = sorted((a, b) for a, b, vv, _ in oh if v0 - 0.08 <= vv <= v1 + 0.08)
        else:
            sm_ = (x0 + x1)/2; lo, hi = max(v0, 0.1), min(v1, h.D - 0.1)
            cuts = sorted((a, b) for a, b, ss, _ in ov if x0 - 0.08 <= ss <= x1 + 0.08)
        segs, cur = [], lo
        for a, b in cuts:
            if b <= cur or a >= hi: continue
            if a > cur: segs.append((cur, a))
            cur = max(cur, b)
        if cur < hi: segs.append((cur, hi))
        for a, b in segs:
            if b - a < 0.2: continue
            key = (horiz, round(a, 2), round(b, 2), round(v1 if horiz else x1, 1))
            if key in done: continue
            done.add(key)
            if horiz: o += dimline((h.u(a), v1), (h.u(b), v1), (0, 1), 0.2, INT, fmt(b - a), ext=False, size=1.55)
            else: o += dimline((h.u(x1), a), (h.u(x1), b), (h.sg, 0), 0.2, INT, fmt(b - a), ext=False, size=1.55)
    for a, b, vv, t in oh:
        if b - a < 0.3: continue
        inside = -0.32 if vv > h.D - 0.3 else (0.34 if vv < 0.3 else -0.3)
        o.append(T(P.X(h.u((a + b)/2)), P.Y(vv + inside) + 0.6, f'{t} {fmt(b - a)}', size=1.4, fill=OPN))
    for a, b, ss, t in ov:
        x = P.X(h.u(ss - 0.3)); y = P.Y((a + b)/2)
        o.append(T(x, y, f'{t} {fmt(b - a)}', size=1.4, fill=OPN, ang=-90))
    return o

ROOMS = {   # room names, same positions as on the furnished sheets (local s, v)
 'pb':  lambda h: [('GARATGE', 2.9, 8.2), ('PORXO', 0.62, 0.75)] + ([('SAFAREIG', 1.15, h.D + 2.4)] if h.A else [('SALA / SAFAREIG', 2.1, h.D + 2.2)]),
 'p1':  lambda h: ([('ESTAR', 2.3, 2.0), ('CUINA · MENJADOR', 3.05, 6.6), ('LAVABO', 1.5, 5.3), ('TERRASSA', 0.85, h.D + 1.6)] if h.A else
                   [('CUINA · MENJADOR', 2.7, 1.85), ('ESTAR', 2.3, 7.4), ('LAVABO', 1.5, 5.3), ('TERRASSA', 2.1, h.D + 1.6)]),
 'p2':  lambda h: [('ESTUDI', 2.2, 1.6), ('BANY', 2.3, 4.55), ('PAS', 3.5, 4.2), ('DORM. 1', 1.15, 8.6), ('DORM. 2', h.width_at(9.0)*0.75 + 0.1, 8.6)],
 'at':  lambda h: [('TERRASSA', 2.25, 1.5), ('SUITE', 1.8, 4.3), ('BANY', 3.3, 6.95 if h.A else 7.05), ('TERRASSA', 2.25, h.D - 1.0)],
}

def legend(x, y):
    o = [T(x, y, 'LLEGENDA', size=2.4, weight=700, anchor='start')]
    y += 4
    o += [f'<rect x="{x}" y="{y-1.6}" width="8" height="2.2" fill="{INK}"/>', T(x + 10, y, 'Façana o mitgera', size=2, anchor='start')]
    o += [f'<rect x="{x+44}" y="{y-1.1}" width="8" height="1.3" fill="#3A403D"/>', T(x + 54, y, 'Envà interior', size=2, anchor='start')]
    o += [f'<rect x="{x+84}" y="{y-1.6}" width="8" height="2.2" fill="#fff" stroke="{INK}" stroke-width="0.2"/>', f'<line x1="{x+84}" y1="{y-0.5}" x2="{x+92}" y2="{y-0.5}" stroke="{INK}" stroke-width="0.28"/>', T(x + 94, y, 'f  Finestra', size=2, anchor='start')]
    o += [f'<line x1="{x+120}" y1="{y-1}" x2="{x+125}" y2="{y-1}" stroke="{INK}" stroke-width="0.35"/>', f'<line x1="{x+123}" y1="{y}" x2="{x+128}" y2="{y}" stroke="{INK}" stroke-width="0.35"/>', T(x + 130, y, 'c  Corredera', size=2, anchor='start')]
    o += [f'<path d="M{x+158},{y+0.6} L{x+158},{y-3} A3.6,3.6 0 0 1 {x+161.6},{y+0.6}" fill="none" stroke="{MUTE}" stroke-width="0.2" stroke-dasharray="0.6 0.4"/>', T(x + 164, y, 'p  Porta i obertura', size=2, anchor='start')]
    y += 5
    o += [f'<line x1="{x}" y1="{y-0.7}" x2="{x+8}" y2="{y-0.7}" stroke="{EXT}" stroke-width="0.18"/>', T(x + 10, y, 'Cota exterior, mesurada al solar el 17/11/2026 (línia del límit)', size=2, anchor='start')]
    o += [f'<line x1="{x+100}" y1="{y-0.7}" x2="{x+108}" y2="{y-0.7}" stroke="{INT}" stroke-width="0.18"/>', T(x + 110, y, "Cota interior de la proposta, per trams entre obertures (orientativa, pendent de verificar)", size=2, fill=INT, anchor='start')]
    return o

def sheet(name):
    h = P.H(name)
    us = [p[0] for p in P.SITE if (p[0] >= 4.6 if h.A else p[0] <= 4.6)] + [4.6]
    um = (max(us) + min(us))/2
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" font-family="Archivo, Helvetica, Arial, sans-serif" role="img" aria-label="Casa {name} · parets i mides">', P.DEFS, '<rect width="420" height="297" fill="#fff"/>']
    o.append(T(12, 20, f'CASA ADOSSADA {name} · PARETS I MIDES · sense mobles', size=5.2, weight=700, anchor='start'))
    sub_ = ("Façana 4,60 m · fondària 9,70 m · cantonada del darrere ocupada pel veí 3,00 × 2,70 m." if h.A
            else "Façana 4,60 m · fondària 9,80 m · graó del límit lateral a 5,90 m de la façana.")
    o.append(T(12, 27, sub_ + " Mateixa geometria que la làmina de la casa " + name + " amb mobles. Revisió 18/11/2026 · Serrajordi-Diaz Investments", size=2.6, fill=MUTE, anchor='start'))
    o.append(T(408, 20, 'E 1:75 (en DIN A3)', size=4, weight=700, anchor='end'))
    for i in range(5): o.append(f'<rect x="{341.3+i*P.SC:.2f}" y="24" width="{P.SC:.2f}" height="2" fill="{INK if i % 2 == 0 else "#fff"}" stroke="{INK}" stroke-width="0.2"/>')
    o.append(T(341.3, 30.5, '0', size=2.2)); o.append(T(341.3 + 5*P.SC, 30.5, '5 m', size=2.2))
    for i, (k, t, c) in enumerate(P.LV):
        P.CUR.update(cx=58 + i*101, um=um, fy=238)
        o.append(T(P.CUR['cx'], 48, t, size=3.4, weight=700)); o.append(T(P.CUR['cx'], 53, c, size=2.3, fill=MUTE))
        REC.clear(); P.CURVES.clear()
        els = P.neighbour_and_street(h, k) + P.plan(h, k)
        o += [tidy(e) for e in els if keep(e)]
        # terraces: outline only
        if k == 'p1': o.append(P.poly(h.Yd, fill='none', stroke=INK, stroke_width=0.35))
        o += [T(P.X(h.u(s)), P.Y(v), n, size=2.0, fill='#505654', weight=700) for n, s, v in ROOMS[k](h)]
        o += [T(P.X(4.6 if True else 0) , P.Y(0) + 5.5, '', size=0.1)]
        o += [T((P.X(min(p[0] for p in h.P)) + P.X(max(p[0] for p in h.P)))/2, P.Y(0) + 4.4, 'C/ ANSELM CLAVÉ', size=2.2, weight=700, fill='#6E4A8C')]
        if h.A: o.append(T(P.X(sum(p[0] for p in P.EAT)/4), P.Y(sum(p[1] for p in P.EAT)/4), 'ocupat pel veí', size=1.9, weight=700, fill=P.RED))
        if k == 'pb':
            o.append(T(P.X(h.u(2.9)), P.Y(0) - 1.6, 'porta de garatge 2,85', size=1.4, fill=OPN))
            o.append(T(P.X(h.u(0.62)), P.Y(0) - 1.6, 'obert 1,25', size=1.4, fill=OPN))
        seen = set()
        o += exterior_dims(h.P, seen)
        if k in ('pb', 'p1'): o += exterior_dims(h.Yd, seen)
        o += interior_dims(h)
        for bz in P.CURVES:
            L = sum(math.dist(bz[j], bz[j + 1]) for j in range(len(bz) - 1)); m = bz[len(bz)//2]
            o.append(T(P.X(h.u(m[0] - 0.35)), P.Y(m[1] - 0.3), fmt(L) + ' (paret corba)', size=1.55, fill=INT))
    o += legend(12, 262)
    o.append(T(12, 285, "Les cotes exteriors són les del solar mesurat; les interiors es dedueixen de la proposta i s'han de verificar a obra. Avantprojecte orientatiu, pendent de validació tècnica, estructural i urbanística per l'arquitecte.", size=2.2, fill=MUTE, anchor='start'))
    o.append('</svg>')
    svg = '\n'.join(o)
    # unique ids for this sheet (the PDF holds several sheets in one page context)
    pre = f'w{name}'
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', svg)
    svg = re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pre}{m.group(1)})', svg)
    return svg
if __name__ == '__main__':
    for n in 'AB': open(f'/home/claude/plans/out2/parets{n}.svg', 'w').write(sheet(n))
