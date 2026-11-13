// ---------- mesh builder (real cadastral footprints) ----------
const FPV = 20;
const Z4 = [0, 0, 0, 0];
const hex2lin = h => [1, 3, 5].map(i => Math.pow(parseInt(h.slice(i, i + 2), 16) / 255, 2.2));
class Mesh {
  constructor() { this.v = []; this.i = []; this.n = 0; }
  vert(p, n, uv, c, mat, P, Q) { this.v.push(p[0], p[1], p[2], n[0], n[1], n[2], uv[0], uv[1], c[0], c[1], c[2], mat, P[0], P[1], P[2], P[3], Q[0], Q[1], Q[2], Q[3]); return this.n++; }
  poly(ps, n, uvs, c, mat, P = Z4, Q = Z4) {
    let ord = ps.map((_, k) => k);
    if (V3.dot(V3.cross(V3.sub(ps[1], ps[0]), V3.sub(ps[2], ps[0])), n) < 0) ord = ord.reverse();
    const id = ord.map(k => this.vert(ps[k], n, uvs[k], c, mat, P, Q));
    for (let k = 1; k < id.length - 1; k++) this.i.push(id[0], id[k], id[k + 1]);
  }
  tris(pts3, idx, n, c, mat, P = Z4, Q = Z4, uvf = p => [p[0], p[2]]) {
    for (const [a, b, d] of idx) {
      const t = [pts3[a], pts3[b], pts3[d]];
      this.poly(t, n, t.map(uvf), c, mat, P, Q);
    }
  }
  // box oriented along edge direction (ex,ez unit, horizontal), outward normal (nx,nz)
  obox(o, e, nrm, w, h, d, c, mat, y0 = 0) {
    const P = (s, t, y) => [o[0] + e[0] * s + nrm[0] * t, y0 + y, o[1] + e[1] * s + nrm[1] * t];
    const N3 = [nrm[0], 0, nrm[1]], E3 = [e[0], 0, e[1]];
    const f = (ps, n, a, b) => this.poly(ps, n, [[0, 0], [a, 0], [a, b], [0, b]], c, mat);
    f([P(0, d, 0), P(w, d, 0), P(w, d, h), P(0, d, h)], N3, w, h);
    f([P(0, 0, 0), P(w, 0, 0), P(w, 0, h), P(0, 0, h)], V3.scale(N3, -1), w, h);
    f([P(0, 0, 0), P(0, d, 0), P(0, d, h), P(0, 0, h)], V3.scale(E3, -1), d, h);
    f([P(w, 0, 0), P(w, d, 0), P(w, d, h), P(w, 0, h)], E3, d, h);
    f([P(0, 0, h), P(w, 0, h), P(w, d, h), P(0, d, h)], [0, 1, 0], w, d);
    f([P(0, 0, 0), P(w, 0, 0), P(w, d, 0), P(0, d, 0)], [0, -1, 0], w, d);
  }
}
const COL = {
  party: hex2lin("#BDB6AA"), slab: hex2lin("#D2CCC0"), metal: hex2lin("#2E3230"), flat: hex2lin("#B7B3AA"),
  curb: hex2lin("#A9A49A"), trunk: hex2lin("#5B4733"),
  leaf: [hex2lin("#5E7D43"), hex2lin("#6E8A4A"), hex2lin("#53703D"), hex2lin("#7A9152")],
  mat: { 6: hex2lin("#76726D"), 7: hex2lin("#A19D96"), 8: hex2lin("#B79C76"), 9: hex2lin("#6F8A4D"), 10: hex2lin("#CDC5B6") },
  pot: [hex2lin("#A65B3B"), hex2lin("#B86A45"), hex2lin("#8E4B33"), hex2lin("#C9C2B4")],
  bloom: [hex2lin("#C93A43"), hex2lin("#E58CA6"), hex2lin("#F4F1EA"), hex2lin("#B4467F"), hex2lin("#E2553E"), hex2lin("#F0B23A")]
};
const FACADE = ["#E9E4D8", "#E6D6B8", "#DCC6A0", "#D9B9A4", "#D4D2CB", "#CBC4B6", "#E2DCCF", "#EDEBE4"];
// ---- 2D helpers (E,N) ----
const area2 = p => { let s = 0; for (let i = 0; i < p.length; i++) { const a = p[i], b = p[(i + 1) % p.length]; s += a[0] * b[1] - b[0] * a[1]; } return s / 2; };
const ccw = p => area2(p) < 0 ? p.slice().reverse() : p;
function inPoly(q, p) { let c = false; for (let i = 0, j = p.length - 1; i < p.length; j = i++) { const a = p[i], b = p[j]; if ((a[1] > q[1]) !== (b[1] > q[1]) && q[0] < (b[0] - a[0]) * (q[1] - a[1]) / (b[1] - a[1]) + a[0]) c = !c; } return c; }
function earclip(p) {
  const idx = p.map((_, i) => i), out = []; let guard = 0;
  const cr = (a, b, c) => (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0]);
  while (idx.length > 3 && guard++ < 5000) {
    let cut = false;
    for (let k = 0; k < idx.length; k++) {
      const i0 = idx[(k + idx.length - 1) % idx.length], i1 = idx[k], i2 = idx[(k + 1) % idx.length];
      const a = p[i0], b = p[i1], c = p[i2];
      if (cr(a, b, c) <= 1e-9) continue;
      let ok = true;
      for (const j of idx) { if (j === i0 || j === i1 || j === i2) continue; const q = p[j]; if (cr(a, b, q) >= 0 && cr(b, c, q) >= 0 && cr(c, a, q) >= 0) { ok = false; break; } }
      if (!ok) continue;
      out.push([i0, i1, i2]); idx.splice(k, 1); cut = true; break;
    }
    if (!cut) break;
  }
  if (idx.length === 3) out.push([idx[0], idx[1], idx[2]]);
  return out;
}
function clipHalf(p, n, c) { // keep dot(q,n) <= c
  const out = [];
  for (let i = 0; i < p.length; i++) {
    const a = p[i], b = p[(i + 1) % p.length], da = a[0] * n[0] + a[1] * n[1] - c, db = b[0] * n[0] + b[1] * n[1] - c;
    if (da <= 0) out.push(a);
    if ((da < 0) !== (db < 0) && da !== db) { const t = da / (da - db); out.push([a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t]); }
  }
  return out;
}
const parseTxt = (txt, withFl) => txt.trim().split("\n").map(l => {
  const s = l.split("|"); const pts = s[s.length - 1].split(";").map(q => q.split(",").map(Number));
  return withFl ? { rc: s[0], fl: +s[1], pts: ccw(pts) } : { rc: s[0], pts: ccw(pts) };
});
const W3 = (p, y) => [p[0], y, -p[1]];
const PARTS = parseTxt(BP_TXT, true);
const PARCELS = parseTxt(CP_TXT, false).concat([{ rc: "0400003", pts: ccw(PLOT_EN), plot: true }]);
const PLOT = ccw(PLOT_EN);
const FOOT = [];
const GARDEN = new Set(["0301617", "0301619", "0301620", "0401610", "0401611", "0301615", "0301614", "0401609"]);
const hashRC = rc => { let h = 7; for (const ch of rc) h = (h * 31 + ch.charCodeAt(0)) % 9973; return h; };
const inParcel = q => PARCELS.some(c => inPoly(q, c.pts));

function addPart(m, part, k) {
  const yr = YEAR[part.rc] || 1960, shop = SHOPS.has(part.rc) ? 1 : 0, seed = hashRC(part.rc);
  const style = yr < 1958 ? 0 : yr < 1995 ? 1 : 2;
  const col = hex2lin(REAL_COL[part.rc] || FACADE[style === 2 ? 7 : seed % 7]);
  const gh = shop ? 3.6 : 3.2, fh = 2.95, H = gh + (part.fl - 1) * fh; part.H = H;
  const p = part.pts, sh = BROWN.has(part.rc) ? 1 : seed % 3;
  FOOT.push(p.map(q => [q[0], -q[1]]));
  for (let i = 0; i < p.length; i++) {
    const a = p[i], b = p[(i + 1) % p.length], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
    if (L < 0.05) continue;
    const n = [dy / L, -dx / L], mid = [(a[0] + b[0]) / 2 + n[0] * 0.3, (a[1] + b[1]) / 2 + n[1] * 0.3];
    let y0 = 0, mat;
    const other = PARTS.filter((o, j) => j !== k && inPoly(mid, o.pts));
    if (other.length) { const h2 = Math.max(...other.map(o => o.Hpre)); if (h2 >= H - 0.1) continue; y0 = h2; mat = 3; }
    else if (inPoly(mid, PLOT)) mat = 3;
    else if (inParcel(mid)) mat = 2;
    else mat = 1;
    if (L < 1.3 && mat !== 3) mat = 3;
    const nb = Math.max(1, Math.round(L / (style === 2 ? 3.3 : 2.6))), bw = L / nb;
    const nW = [n[0], 0, -n[1]];
    m.poly([W3(a, y0), W3(b, y0), W3(b, H), W3(a, H)], nW, [[0, y0], [L, y0], [L, H], [0, H]],
      mat === 3 ? (part.rc === "0400002" && inPoly(mid, PLOT) ? hex2lin("#9C4036") : part.rc === "0400003" ? hex2lin("#D8B45E") : V3.lerp(COL.party, col, 0.35)) : col, mat, [gh, fh, part.fl, bw], [mat === 1 ? shop : 0, sh, seed + i, style + 10 * (FLAGS[part.rc] || 0)]);
    const e = [dx / L, -dy / L], nn = [n[0], -n[1]];
    const pitched = mat === 1 && style < 2 && part.fl <= 4 && !FLAT.has(part.rc) && L > 1.2;
    if (pitched) addEave(m, a, b, n, L, H, p, col, seed);
    if (mat === 1 && L > 3) m.obox([a[0] + (dx / L) * 0.18 + n[0] * 0.02, -(a[1] + (dy / L) * 0.18 + n[1] * 0.02)], [dx / L, -dy / L], [n[0], -n[1]], 0.09, H - 0.1, 0.09, hex2lin("#C8C4BA"), 0, 0);
    if (mat !== 3 && H > 4 && !pitched) m.obox([a[0] - n[0] * 0.22, -(a[1] - n[1] * 0.22)], e, nn, L, 0.9, 0.22, col, 0, H);
    if (mat === 1 && style < 2 && part.fl > 1 && L > 2.4) {
      for (let f = 1; f < part.fl; f++) for (let q = 0; q < nb; q++) {
        const y = gh + (f - 1) * fh, rr = rng(seed * 7 + q * 131 + f * 977), roll = (seed + f * 7 + q * 13) % 10;
        if (style === 1 && q % 2 === 1) { // plain window: some have a flower box under the sill
          if (roll < 3) {
            const s0 = (q + 0.5) * bw - 0.55, o = [a[0] + (dx / L) * s0, -(a[1] + (dy / L) * s0)];
            m.obox(o, e, nn, 1.1, 0.22, 0.22, COL.pot[Math.floor(rr() * 3)], 0, y + 0.6);
            for (let k = 0; k < 4; k++) {
              const t = 0.16 + k * 0.26, c = [o[0] + e[0] * t + nn[0] * 0.11, o[1] + e[1] * t + nn[1] * 0.11];
              addSphere(m, c[0], y + 0.9, c[1], 0.16, COL.leaf, rr, 7, 5);
              addBlooms(m, [c[0], y + 0.9, c[1]], 0.16, 3, rr);
            }
          }
          continue;
        }
        const hw = (style === 0 ? 0.55 : 0.8) + 0.3, s0 = (q + 0.5) * bw - hw;
        const o = [a[0] + (dx / L) * s0, -(a[1] + (dy / L) * s0)];
        m.obox(o, e, nn, hw * 2, 0.14, 0.72, COL.slab, 0, y - 0.14);
        m.obox([o[0] + nn[0] * 0.68, o[1] + nn[1] * 0.68], e, nn, hw * 2, 0.95, 0.04, COL.metal, 16, y);
        if (roll < 5) { // pots on the balcony, most of them in flower
          const n2 = roll < 2 ? 2 : 1;
          for (let k = 0; k < n2; k++) {
            const t = k ? hw * 1.45 : hw * 0.35, pp = [o[0] + e[0] * t + nn[0] * 0.3, o[1] + e[1] * t + nn[1] * 0.3], c = [pp[0] + e[0] * 0.17 + nn[0] * 0.15, pp[1] + e[1] * 0.17 + nn[1] * 0.15];
            m.obox(pp, e, nn, 0.34, 0.3, 0.3, COL.pot[Math.floor(rr() * 4)], 0, y);
            const r = 0.24 + rr() * 0.1; addSphere(m, c[0], y + 0.3 + r * 0.8, c[1], r, COL.leaf, rr, 9, 6);
            if (rr() < 0.75) addBlooms(m, [c[0], y + 0.3 + r * 0.8, c[1]], r, 4 + Math.floor(rr() * 4), rr);
          }
        }
      }
    }
    if (mat === 1 && !shop && L > 3 && seed % 3 === 0) { // a plant by the front door
      const rr = rng(seed + i * 17), t = bw * 0.5 + 0.98, o = [a[0] + (dx / L) * t + n[0] * 0.06, -(a[1] + (dy / L) * t + n[1] * 0.06)];
      if (t + 0.4 < L) {
        m.obox(o, e, nn, 0.38, 0.46, 0.38, COL.pot[Math.floor(rr() * 4)], 0, 0.03);
        const c = [o[0] + e[0] * 0.19 + nn[0] * 0.19, o[1] + e[1] * 0.19 + nn[1] * 0.19], r = 0.34;
        addSphere(m, c[0], 0.49 + r * 0.85, c[1], r, COL.leaf, rr, 9, 6);
        if (rr() < 0.6) addBlooms(m, [c[0], 0.49 + r * 0.85, c[1]], r, 6, rr);
      }
    }
  }
  const top = p.map(q => W3(q, H));
  m.tris(top, earclip(p), [0, 1, 0], style === 0 ? hex2lin("#B08D72") : COL.flat, 5, Z4, [seed, 0, 0, 0]);
}

function addEave(m, a, b, n, L, H, poly, col, seed) {
  let maxd = 0; for (const q of poly) maxd = Math.max(maxd, (a[0] - q[0]) * n[0] + (a[1] - q[1]) * n[1]);
  const D = Math.min(3.4, Math.max(1.2, maxd * 0.45)), s = 0.32, rise = D * s, ov = 0.42, ye = H - ov * s;
  const P = (q, k, y) => [q[0] + n[0] * k, y, -(q[1] + n[1] * k)];
  const N = V3.norm([n[0] * s, 1, -n[1] * s]), sl = Math.hypot(D + ov, rise + ov * s);
  const tile = V3.lerp(hex2lin("#A55E40"), [0.16, 0.11, 0.08], (seed % 7) / 30);
  m.poly([P(a, ov, ye), P(b, ov, ye), P(b, -D, H + rise), P(a, -D, H + rise)], N, [[0, 0], [L, 0], [L, sl], [0, sl]], tile, 4, Z4, [seed, 0, 0, 0]);
  m.poly([P(a, 0, ye - 0.04), P(b, 0, ye - 0.04), P(b, ov, ye - 0.04), P(a, ov, ye - 0.04)], [0, -1, 0], [[0, 0], [L, 0], [L, ov], [0, ov]], V3.scale(col, 0.82), 0);
  m.poly([P(a, ov, ye - 0.04), P(b, ov, ye - 0.04), P(b, ov, ye + 0.06), P(a, ov, ye + 0.06)], [n[0], 0, -n[1]], [[0, 0], [L, 0], [L, .1], [0, .1]], tile, 0);
  const e = [b[0] - a[0], 0, -(b[1] - a[1])], ex = V3.norm(e), pc = V3.lerp(COL.party, col, 0.35);
  m.poly([P(a, 0, H), P(a, -D, H), P(a, -D, H + rise)], V3.scale(ex, -1), [[0, H], [D, H], [D, H + rise]], pc, 3);
  m.poly([P(b, 0, H), P(b, -D, H), P(b, -D, H + rise)], ex, [[0, H], [D, H], [D, H + rise]], pc, 3);
}
function addBlooms(m, c, r, n, rnd) { // small flowers on the top half of a plant
  const col = COL.bloom[Math.floor(rnd() * COL.bloom.length)];
  for (let k = 0; k < n; k++) {
    const th = rnd() * 1.2, ph = rnd() * Math.PI * 2, d = [Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph)];
    addSphere(m, c[0] + d[0] * r * 0.92, c[1] + d[1] * r * 0.86, c[2] + d[2] * r * 0.92, 0.045 + rnd() * 0.035, [rnd() < 0.8 ? col : COL.bloom[Math.floor(rnd() * COL.bloom.length)]], rnd, 5, 3);
  }
}
function addSphere(m, cx, cy, cz, r, cols, rnd, seg = 10, ring = 7) {
  const pts = [];
  for (let j = 0; j <= ring; j++) {
    const th = j / ring * Math.PI, row = [];
    for (let i = 0; i <= seg; i++) {
      const ph = i / seg * Math.PI * 2, jit = 1 + (j > 0 && j < ring && i < seg ? (rnd() - 0.5) * 0.22 : 0);
      const n = [Math.sin(th) * Math.cos(ph), Math.cos(th), Math.sin(th) * Math.sin(ph)];
      row.push({ p: [cx + n[0] * r * jit, cy + n[1] * r * 0.92 * jit, cz + n[2] * r * jit], n });
    }
    row[seg] = row[0]; pts.push(row);
  }
  const c = cols[Math.floor(rnd() * cols.length)];
  for (let j = 0; j < ring; j++) for (let i = 0; i < seg; i++) {
    const a = pts[j][i], b = pts[j][i + 1], d = pts[j + 1][i], e = pts[j + 1][i + 1];
    m.poly([a.p, b.p, e.p, d.p], V3.norm(V3.add(V3.add(a.n, b.n), V3.add(d.n, e.n))), [[0, 0], [1, 0], [1, 1], [0, 1]], V3.scale(c, 0.85 + rnd() * 0.3), 11);
  }
}

function buildScene() {
  const m = new Mesh(), rnd = rng(30);
  const R = DISC.r + 6, cx = DISC.cx, cz = DISC.cz;
  m.poly([[cx - R, 0, cz - R], [cx + R, 0, cz - R], [cx + R, 0, cz + R], [cx - R, 0, cz + R]], [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]], COL.mat[6], 6);
  for (const c of PARCELS) {
    const mat = c.plot ? 8 : GARDEN.has(c.rc) ? 9 : 10, y = c.plot ? 0.06 : 0.07;
    m.tris(c.pts.map(q => W3(q, y)), earclip(c.pts), [0, 1, 0], COL.mat[mat], mat);
    for (let i = 0; i < c.pts.length; i++) {
      const a = c.pts[i], b = c.pts[(i + 1) % c.pts.length], dx = b[0] - a[0], dy = b[1] - a[1], L = Math.hypot(dx, dy);
      if (L < 0.05) continue;
      const n = [dy / L, -dx / L], mid = [(a[0] + b[0]) / 2 + n[0] * 0.4, (a[1] + b[1]) / 2 + n[1] * 0.4];
      if (inParcel(mid)) continue;
      const a2 = [a[0] + n[0] * 1.05, a[1] + n[1] * 1.05], b2 = [b[0] + n[0] * 1.05, b[1] + n[1] * 1.05];
      m.poly([W3(a, 0.03), W3(b, 0.03), W3(b2, 0.03), W3(a2, 0.03)], [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]], COL.mat[7], 7);
      const inner = [(a[0] + b[0]) / 2 - n[0] * 0.3, (a[1] + b[1]) / 2 - n[1] * 0.3];
      if (!c.plot && L > 0.8 && !PARTS.some(o => inPoly(inner, o.pts))) {
        const e = [dx / L, -dy / L], nn = [n[0], -n[1]];
        m.obox([a[0] - n[0] * 0.25, -(a[1] - n[1] * 0.25)], e, nn, L, 2.3, 0.25, hex2lin("#9C9588"), 19, 0.03);
      }
    }
  }
  PARTS.forEach(p => { p.Hpre = (SHOPS.has(p.rc) ? 3.6 : 3.2) + (p.fl - 1) * 2.95; });
  PARTS.forEach((p, k) => addPart(m, p, k));
  for (const [bx, bn] of BOLLARDS) { m.obox([bx - 0.055, -bn - 0.055], [1, 0], [0, 1], 0.11, 0.85, 0.11, hex2lin("#1E2120"), 0, 0.03); m.obox([bx - 0.075, -bn - 0.075], [1, 0], [0, 1], 0.15, 0.06, 0.15, hex2lin("#2A2E2C"), 0, 0.88); }
  for (const [x, nN] of LAMPS) {
    const z = -nN, dk = hex2lin("#1E2120");
    m.obox([x - 0.07, z - 0.07], [1, 0], [0, 1], 0.14, 3.6, 0.14, dk, 0, 0);
    m.obox([x - 0.2, z - 0.2], [1, 0], [0, 1], 0.4, 0.5, 0.4, hex2lin("#E2DCC8"), 22, 3.6);
    m.obox([x - 0.26, z - 0.26], [1, 0], [0, 1], 0.52, 0.12, 0.52, dk, 0, 4.1);
  }
  for (const [x, n, r, h] of TREES) { // trunk and a loose crown of leaf clusters
    const tr = rng(Math.round(x * 13 + n * 7) >>> 0);
    m.obox([x - 0.15, -n - 0.15], [1, 0], [0, 1], 0.3, h - r * 0.55, 0.3, COL.trunk, 12);
    addSphere(m, x, h, -n, r * 0.74, COL.leaf, tr);
    for (let k = 0; k < 7; k++) { const a = tr() * Math.PI * 2, d = r * (0.32 + tr() * 0.4); addSphere(m, x + Math.cos(a) * d, h + (tr() - 0.35) * r * 0.75, -n + Math.sin(a) * d, r * (0.36 + tr() * 0.24), COL.leaf, tr, 9, 6); }
  }
  const S = 160, sk = hex2lin("#222A27");
  for (let k = 0; k < S; k++) {
    const a0 = k / S * Math.PI * 2, a1 = (k + 1) / S * Math.PI * 2, P = a => [DISC.cx + Math.cos(a) * DISC.r, DISC.cz + Math.sin(a) * DISC.r];
    const [x0, z0] = P(a0), [x1, z1] = P(a1), n = [Math.cos((a0 + a1) / 2), 0, Math.sin((a0 + a1) / 2)];
    m.poly([[x0, DISC.base, z0], [x1, DISC.base, z1], [x1, 0.2, z1], [x0, 0.2, z0]], n, [[0, 0], [1, 0], [1, 1], [0, 1]], sk, 13);
  }
  const T = 5000;
  m.poly([[-T, DISC.base, -T], [T, DISC.base, -T], [T, DISC.base, T], [-T, DISC.base, T]], [0, 1, 0], [[0, 0], [1, 0], [1, 1], [0, 1]], hex2lin("#D9DCD5"), 14);
  return { m };
}

// planned volume: two houses, 10 m deep from the façade, split at the middle of the frontage
const HOUSES = (() => {
  const [A, B] = PLOT_FRONT, fl = Math.hypot(B[0] - A[0], B[1] - A[1]), f = [(B[0] - A[0]) / fl, (B[1] - A[1]) / fl];
  const d = [f[1], -f[0]], M = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2], c0 = A[0] * d[0] + A[1] * d[1];
  const strip = clipHalf(PLOT, d, c0 + 10), back = clipHalf(PLOT, [-d[0], -d[1]], -(c0 + 10)), mf = M[0] * f[0] + M[1] * f[1];
  return { houses: [clipHalf(strip, f, mf), clipHalf(strip, [-f[0], -f[1]], -mf)].map(ccw), back: ccw(back), f, d, A };
})();
function buildGhost() {
  const m = new Mesh(), H = 9.2, c = [1, 1, 1];
  const [A, B] = PLOT_FRONT, fl = Math.hypot(B[0] - A[0], B[1] - A[1]), f = [(B[0] - A[0]) / fl, (B[1] - A[1]) / fl];
  const d = [f[1], -f[0]], M = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
  const strip = clipHalf(PLOT, d, A[0] * d[0] + A[1] * d[1] + 10);
  const houses = [clipHalf(strip, f, M[0] * f[0] + M[1] * f[1]), clipHalf(strip, [-f[0], -f[1]], -(M[0] * f[0] + M[1] * f[1]))];
  for (const h of houses.map(ccw)) {
    for (let i = 0; i < h.length; i++) {
      const a = h[i], b = h[(i + 1) % h.length], L = Math.hypot(b[0] - a[0], b[1] - a[1]); if (L < 0.05) continue;
      const n = [(b[1] - a[1]) / L, 0, (b[0] - a[0]) / L];
      m.poly([W3(a, 0.08), W3(b, 0.08), W3(b, H), W3(a, H)], n, [[0, 0], [L, 0], [L, H], [0, H]], c, 17, [L, H, 0, 0]);
    }
    m.tris(h.map(q => W3(q, H)), earclip(h), [0, 1, 0], c, 17, [100, 100, 0, 0], Z4, () => [50, 50]);
  }
  return m;
}
