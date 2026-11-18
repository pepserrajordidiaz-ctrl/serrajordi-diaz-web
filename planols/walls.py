# Sheet without furniture: every wall line of both houses with its length (exterior lines, partitions, curved wall, openings).
import math, re, sys
sys.path.insert(0, '/home/claude/plans')
import plans2 as P
BLUE, GREY = '#2F5F9E', '#6E7672'
REC = []
_orig = {k: getattr(P, k) for k in ('part', 'door', 'door_v', 'window', 'slider', 'slider_v')}
def _part(h, x0, v0, x1, v1): REC.append(('wall', h, (x0, v0, x1, v1))); return _orig['part'](h, x0, v0, x1, v1)
def _door(h, x, v, w, into=1, hinge='start'): REC.append(('oh', h, (x, x + w, v, 'porta'))); return _orig['door'](h, x, v, w, into, hinge)
def _door_v(h, xs, v, w, into=1, hinge='start'): REC.append(('ov', h, (v, v + w, xs, 'porta'))); return _orig['door_v'](h, xs, v, w, into, hinge)
def _window(h, x0, x1, v): REC.append(('oh', h, (x0, x1, v, 'finestra'))); return _orig['window'](h, x0, x1, v)
def _slider(h, x0, x1, v): REC.append(('oh', h, (x0, x1, v, 'corredera'))); return _orig['slider'](h, x0, x1, v)
def _slider_v(h, xs, v0, v1): REC.append(('ov', h, (v0, v1, xs, 'corredera'))); return _orig['slider_v'](h, xs, v0, v1)
P.part, P.door, P.door_v, P.window, P.slider, P.slider_v = _part, _door, _door_v, _window, _slider, _slider_v
fmt = P.fmt

def keep(el):
    if el.startswith('<text'):
        return 'font-weight="700"' in el and '#9A6B00' not in el
    if '<ellipse' in el: return False
    if el.startswith('<circle') and 'stroke="#7B837F"' in el: return False
    if 'stroke-dasharray="1 0.7"' in el: return True
    if el.startswith('<line') and 'stroke="#1C2321" stroke-width="0.25"' in el and 'dasharray' not in el: return False   # wardrobe fronts
    if 'fill="#fff" stroke="#7B837F"' in el: return False
    if 'stroke="#7B837F"' in el and ('stroke-width="0.25"' in el or 'stroke-width="0.15"' in el or 'stroke-width="0.3"' in el): return False
    return True
def shrink(el): return re.sub(r'font-size="([\d.]+)"', lambda m: f'font-size="{float(m.group(1))*0.62:.2f}"', el)

def label_at(u, v, txt, ang=0, col=BLUE, size=1.55):
    x, y = P.X(u), P.Y(v)
    if ang > 90: ang -= 180
    if ang < -90: ang += 180
    return f'<text x="{x:.2f}" y="{y + size*0.35:.2f}" font-size="{size}" fill="{col}" text-anchor="middle" transform="rotate({ang:.1f} {x:.2f} {y:.2f})" paint-order="stroke" stroke="#fff" stroke-width="0.5">{txt}</text>'

def edge_dims(poly, seen):
    o = []; cu = sum(p[0] for p in poly)/len(poly); cv = sum(p[1] for p in poly)/len(poly)
    for i in range(len(poly)):
        a, b = poly[i], poly[(i + 1) % len(poly)]
        L = math.dist(a, b)
        key = tuple(sorted([(round(a[0], 2), round(a[1], 2)), (round(b[0], 2), round(b[1], 2))]))
        if L < 0.2 or key in seen: continue
        seen.add(key)
        mu, mv = (a[0] + b[0])/2, (a[1] + b[1])/2
        nu, nv = -(b[1] - a[1])/L, (b[0] - a[0])/L
        if (mu + nu - cu)**2 + (mv + nv - cv)**2 < (mu - nu - cu)**2 + (mv - nv - cv)**2: nu, nv = -nu, -nv
        ang = math.degrees(math.atan2(P.Y(b[1]) - P.Y(a[1]), P.X(b[0]) - P.X(a[0])))
        o.append(label_at(mu + nu*0.36, mv + nv*0.36, fmt(L), ang, col='#1C2321', size=1.7))
    return o

def wall_dims(h, recs):
    o = []; ops_h = [r for k, hh, r in recs if k == 'oh']; ops_v = [r for k, hh, r in recs if k == 'ov']
    for k, hh, (x0, v0, x1, v1) in [r for r in recs if r[0] == 'wall']:
        x0, x1 = sorted((x0, x1)); v0, v1 = sorted((v0, v1))
        horiz = (x1 - x0) >= (v1 - v0)
        if horiz:
            vm = (v0 + v1)/2; lo, hi = max(x0, 0.0), min(x1, h.width_at(vm))
            cuts = sorted((a, b) for a, b, vv, _ in ops_h if v0 - 0.08 <= vv <= v1 + 0.08)
        else:
            sm_ = (x0 + x1)/2; lo, hi = max(v0, 0.1), min(v1, h.D - 0.1)
            cuts = sorted((a, b) for a, b, ss, _ in ops_v if x0 - 0.08 <= ss <= x1 + 0.08)
        segs, cur = [], lo
        for a, b in cuts:
            if b <= cur or a >= hi: continue
            if a > cur: segs.append((cur, a))
            cur = max(cur, b)
        if cur < hi: segs.append((cur, hi))
        for a, b in segs:
            if b - a < 0.25: continue
            if horiz: o.append(label_at(h.u((a + b)/2), v1 + 0.17, fmt(b - a)))
            else: o.append(label_at(h.u(x1 + 0.17*1) if True else 0, (a + b)/2, fmt(b - a), ang=-90 if h.A else 90))
    for a, b, vv, t in ops_h:
        if b - a > 0.3: o.append(label_at(h.u((a + b)/2), vv - 0.28 if vv > 0.5 else vv + 0.32, f'{t[0]} {fmt(b - a)}', col=GREY, size=1.3))
    for a, b, ss, t in ops_v:
        o.append(label_at(h.u(ss - 0.28), (a + b)/2, f'{t[0]} {fmt(b - a)}', ang=-90, col=GREY, size=1.3))
    return o

def sheet():
    SC0 = P.SC; P.SC = 1000/110
    o = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 420 297" font-family="Archivo, Helvetica, Arial, sans-serif" role="img" aria-label="Parets i mides">', P.DEFS, '<rect width="420" height="297" fill="#fff"/>']
    o.append(P.text_xy(12, 14, 'PARETS I MIDES · sense mobles', size=4.6, weight=700, anchor='start'))
    o.append(P.text_xy(12, 19.5, "Llargada de cada línia en metres. Negre: línies exteriors (façanes, mitgeres i límits). Blau: envans, per trams entre obertures. Gris: obertures (p porta · f finestra · c corredera). E 1:110 en DIN A3.", size=2.3, fill=P.MUTE, anchor='start'))
    for row, name in enumerate('AB'):
        h = P.H(name)
        us = [p[0] for p in P.SITE if (p[0] >= 4.6 if h.A else p[0] <= 4.6)] + [4.6]
        um = (max(us) + min(us))/2
        top = 27 + row*130
        ymax = max(p[1] for p in h.Yd)
        fy = top + 5 + ymax*P.SC
        o.append(P.text_xy(12, top + 2, f'CASA {name}', size=3.4, weight=700, anchor='start'))
        for i, (k, t, c) in enumerate(P.LV):
            P.CUR.update(cx=70 + i*96, um=um, fy=fy)
            o.append(P.text_xy(P.CUR['cx'], top + 2, t + ' · ' + c, size=2.1, weight=700))
            REC.clear(); P.CURVES.clear()
            els = P.neighbour_and_street(h, k) + P.plan(h, k)
            o += [shrink(e) for e in els if keep(e)]
            seen = set()
            o += edge_dims(h.P, seen)
            if k in ('pb', 'p1'): o += edge_dims(h.Yd, seen)
            o += wall_dims(h, list(REC))
            for bz in P.CURVES:
                L = sum(math.dist(bz[j], bz[j + 1]) for j in range(len(bz) - 1)); m = bz[len(bz)//2]
                o.append(label_at(h.u(m[0] - 0.25), m[1] - 0.25, fmt(L) + ' (corba)', ang=0))
    o.append(P.text_xy(12, 292, "Mides de les línies exteriors segons el solar mesurat el 17/11/2026; envans i obertures segons la proposta. Avantprojecte orientatiu, pendent de l'arquitecte · Serrajordi-Diaz Investments", size=2.1, fill=P.MUTE, anchor='start'))
    o.append('</svg>'); P.SC = SC0
    return '\n'.join(o).replace('url(#eat)', 'url(#eatW)').replace('id="eat"', 'id="eatW"').replace('url(#arr)', 'url(#arrW)').replace('id="arr"', 'id="arrW"')
if __name__ == '__main__':
    open('/home/claude/plans/out2/parets.svg', 'w').write(sheet())
