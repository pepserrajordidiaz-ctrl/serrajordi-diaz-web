# Casas A + B together, sharing the party wall at their real position on the plot: one furnished sheet and one
# walls-and-dimensions sheet, DIN A2 at 1:100. Both come from the same plan() geometry as the individual sheets.
import math, re, sys
sys.path.insert(0, '/home/claude/plans')
import plans2 as P, walls as Wm
T = Wm.T
def build(tech):
    SC0 = P.SC; P.SC = 10.0
    W, H = 594, 420
    o = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" font-family="Archivo, Helvetica, Arial, sans-serif" role="img" aria-label="Cases A i B juntes">', P.DEFS, f'<rect width="{W}" height="{H}" fill="#fff"/>']
    title = 'CASES A + B · PARETS I MIDES · sense mobles' if tech else 'CASES A + B · CONJUNT AMB MOBLES'
    o.append(T(14, 22, title, size=6.5, weight=700, anchor='start'))
    o.append(T(14, 30, "Les dues cases juntes, a la seva posició real al solar i compartint la mitgera (casa A a l'esquerra i casa B a la dreta, vistes des del carrer d'Anselm Clavé). "
               "Façana conjunta 9,20 m · casa A 4,60 × 9,70 m · casa B 4,60 × 9,80 m amb el graó a 5,90 m. Cases independents, sense comunicació interior. Revisió 18/11/2026 · Serrajordi-Diaz Investments", size=2.9, fill=P.MUTE, anchor='start'))
    o.append(T(W - 14, 22, 'E 1:100 (en DIN A2)', size=5, weight=700, anchor='end'))
    for i in range(5): o.append(f'<rect x="{W-14-50+i*10:.2f}" y="26" width="10" height="2.4" fill="{P.INK if i % 2 == 0 else "#fff"}" stroke="{P.INK}" stroke-width="0.25"/>')
    o.append(T(W - 64, 33.5, '0', size=2.6)); o.append(T(W - 14, 33.5, '5 m', size=2.6))
    us = [p[0] for p in P.SITE]; um = (min(us) + max(us))/2
    hA, hB = P.H('A'), P.H('B')
    shared = lambda a, b: abs(a[0] - 4.6) < 0.02 and abs(b[0] - 4.6) < 0.02
    for i, (k, t, c) in enumerate(P.LV):
        P.CUR.update(cx=86 + i*141, um=um, fy=318)
        o.append(T(P.CUR['cx'], 150, t, size=4.2, weight=700)); o.append(T(P.CUR['cx'], 156, c, size=2.9, fill=P.MUTE))
        for h in (hA, hB):
            Wm.REC.clear(); P.CURVES.clear()
            els = P.plan(h, k)
            if tech:
                o += [Wm.tidy(e) for e in els if Wm.keep(e)]
                if k == 'p1': o.append(P.poly(h.Yd, fill='none', stroke=P.INK, stroke_width=0.35))
                o += [T(P.X(h.u(s)), P.Y(v), n, size=1.9, fill='#505654', weight=700) for n, s, v in Wm.ROOMS[k](h)]
                seen = set()
                o += Wm.exterior_dims(h.P, seen, skip=shared)
                if k in ('pb', 'p1'): o += Wm.exterior_dims(h.Yd, seen, skip=shared)
                o += Wm.interior_dims(h)
                for bz in P.CURVES:
                    L = sum(math.dist(bz[j], bz[j + 1]) for j in range(len(bz) - 1)); m = bz[len(bz)//2]
                    o.append(T(P.X(h.u(m[0] - 0.35)), P.Y(m[1] - 0.3), P.fmt(L) + ' (corba)', size=1.5, fill=Wm.INT))
            else:
                o += [re.sub(r'font-size="([\d.]+)"', lambda m: f'font-size="{float(m.group(1))*0.8:.2f}"', e) for e in els]
            # house tag above the back of each house
            o.append(T(P.X(h.u(2.3)), P.Y(13.0) - 11, f'CASA {h.name}', size=3.0, weight=700, fill='#6E4A8C'))
        # neighbour corner, street, neighbours
        o.append(P.poly(P.EAT, fill='url(#eat)', stroke=P.RED, stroke_width=0.45))
        o.append(T(P.X(sum(p[0] for p in P.EAT)/4), P.Y(sum(p[1] for p in P.EAT)/4), 'ocupat pel veí', size=2.0, weight=700, fill=P.RED))
        x0, x1 = P.X(max(us)), P.X(min(us))
        o.append(f'<line x1="{x0-4:.1f}" y1="{P.Y(0)+0.6:.1f}" x2="{x1+4:.1f}" y2="{P.Y(0)+0.6:.1f}" stroke="#8B5FA8" stroke-width="0.35" stroke-dasharray="1.4 0.9"/>')
        o.append(T((x0 + x1)/2, P.Y(0) + 4.6, "C/ ANSELM CLAVÉ", size=2.6, weight=700, fill='#6E4A8C'))
        o.append(T(x0 - 13, P.Y(5.0), 'núm. 28', size=2.3, fill=P.MUTE, ang=-90)); o.append(T(x1 + 15, P.Y(5.0), 'veí (parcel·la 02)', size=2.3, fill=P.MUTE, ang=-90))
        # façade: each house and the whole front
        a, b, m = (9.2, 0.0), (0.0, 0.0), (4.6, 0.0)
        if tech:
            o += Wm.dimline(a, b, (0, -1), 1.45, Wm.EXT, '9,20 façana conjunta')
        else:
            o += Wm.dimline(m, b, (0, -1), 0.75, Wm.EXT, '4,60 casa B') + Wm.dimline(a, m, (0, -1), 0.75, Wm.EXT, '4,60 casa A') + Wm.dimline(a, b, (0, -1), 1.5, Wm.EXT, '9,20')
    if tech:
        o += Wm.legend(14, 392)
    o.append(T(14, 412, "Mides exteriors segons el solar mesurat el 17/11/2026; mides interiors de la proposta, orientatives. Mitgera compartida dibuixada una sola vegada. Avantprojecte orientatiu, pendent de validació per l'arquitecte.", size=2.6, fill=P.MUTE, anchor='start'))
    o.append('</svg>'); P.SC = SC0
    svg = '\n'.join(o); pre = 'jt' if tech else 'jf'
    svg = re.sub(r'id="([^"]+)"', lambda m: f'id="{pre}{m.group(1)}"', svg)
    return re.sub(r'url\(#([^)]+)\)', lambda m: f'url(#{pre}{m.group(1)})', svg)
if __name__ == '__main__':
    open('/home/claude/plans/out2/conjunt.svg', 'w').write(build(False))
    open('/home/claude/plans/out2/conjuntT.svg', 'w').write(build(True))
