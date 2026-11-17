// ---------- story: the model follows the scroll, chapter by chapter ----------
(function story() {
  const V = VIEW, S = V.S, sec = $("inici"), stick = sec.querySelector(".sticky");
  const rail = [...document.querySelectorAll("#rail a")], floors = [...document.querySelectorAll("#floors li")], clock = $("clock");
  const U = [0, 1, 0];
  const K = [
    { eye: [-4.6, 1.65, -11.9], target: [1.4, 2.6, -1.5], up: U, fov: 60, vis: ["plot"] },        // in front of the plot, at eye height
    { eye: [30, 21, -25], target: [-3, 2, -5], up: U, fov: 40, vis: ["plot", "st", "nb"] },        // the street from above
    { eye: [2.0, 34, 10.5], target: [0.6, 0, -0.8], up: U, fov: 34, vis: ["dim", "eat"] },                // the plot, north up
    { eye: [-4.5, 8, -31], target: [-0.3, 5.6, -6.8], up: U, fov: 37, vis: ["fl"] },              // the houses rise, seen from the front
    { eye: [-3.5, 31, 21], target: [0.8, 3.2, -2.8], up: U, fov: 38, vis: [] }                           // the back faces south
  ];
  const ORBIT = [false, false, false, false]; V.K = K;
  let vh = 1, top0 = 0, wide = true, aspect = 1.6, lastP = -1, intro = null;
  function measure() {
    vh = stick.clientHeight || innerHeight; top0 = sec.getBoundingClientRect().top + scrollY;
    wide = innerWidth > 860; aspect = (stick.clientWidth || innerWidth) / vh; lastP = -1;
  }
  measure(); addEventListener("resize", measure); new ResizeObserver(measure).observe(stick);
  // narrow screens: open the vertical field of view so the scene still fits across
  const adj = k => { if (aspect >= 1.15) return k; const f = Math.min(88, 2 * Math.atan(Math.tan(k.fov * DEG / 2) * clamp(1.2 / aspect, 1, 1.9)) / DEG); return Object.assign({}, k, { fov: f }); };
  function camAt(p) {
    const i = Math.min(K.length - 2, Math.floor(p)), t = clamp((p - i - 0.1) / 0.8, 0, 1);
    return (ORBIT[i] ? camOrbit : camPath)(adj(K[i]), adj(K[i + 1]), t);
  }
  if (!REDUCE && scrollY < 40) intro = { t0: performance.now() + 250, from: { eye: [-22, 74, 44], target: K[0].target, up: U, fov: 46 } };
  let sunMode = "set";
  V.onStory = (dt, now) => {
    const p = clamp((scrollY - top0) / vh, 0, K.length - 1), st = S.story;
    const k = Math.round(p), near = Math.abs(p - k) < 0.3;
    let moved = p !== lastP;
    if (moved) {
      lastP = p;
      st.ghostA = smooth(2.3, 2.55, p); st.ghostH = 0.05 + (HOUSE_H - 0.05) * smooth(2.45, 3.0, p);
      st.focus = 0.5 + 0.5 * smooth(0.1, 0.7, p); st.shift = wide ? 0.24 : 0; st.shiftY = wide ? 0 : 0.2;
      rail.forEach((a, i) => a.classList.toggle("on", i === k));
      floors.forEach(li => li.classList.toggle("on", st.ghostH >= [3.0, 6.0, 9.0, 11.8][+li.dataset.f]));
    }
    let cam = camAt(p);
    if (intro) { const t = (now - intro.t0) / 3200; if (t >= 1 || p > 0.05) intro = null; else { cam = camPath(adj(intro.from), cam, Math.max(0, t)); moved = true; } }
    st.cam = cam; st.vis = intro ? [] : near ? K[k].vis : [];
    // light: warm late afternoon of 21 June; in the last chapter the day runs on its own
    if (S.day !== "06-21") { S.day = "06-21"; V.setDay("06-21"); moved = true; }
    if (p > 3.45 && !REDUCE) {
      if (sunMode !== "run") { sunMode = "run"; if (S.min > 1250) S.min = 450; }
      S.min += dt * 0.07; if (S.min > 1290) S.min = 450; V.applySun(); moved = true;
    } else if (Math.abs(S.min - V.gold) > 0.5) { sunMode = "set"; S.min += (V.gold - S.min) * Math.min(1, dt * 0.006); V.applySun(); moved = true; }
    const ct = "21 de juny · " + hhmm(S.min); if (clock.textContent !== ct) clock.textContent = ct;
    if (moved) S.dirty = true;
  };
})();

// ---------- sun study: direct sun on the back terrace and on the roof ----------
const SUNSTUDY = (function () {
  const x0 = -50, y0 = -50, cs = 0.25, n = 400, H = new Float32Array(n * n);
  { // height map of every building (Cadastre) plus the two planned houses
    const cv = document.createElement("canvas"); cv.width = cv.height = n; const g = cv.getContext("2d");
    g.fillStyle = "#000"; g.fillRect(0, 0, n, n);
    const items = PARTS.map(p => ({ pts: p.pts, h: (p.H ?? ((SHOPS.has(p.rc) ? 3.6 : 3.2) + (p.fl - 1) * 2.95)) + 0.5 }))
      .concat(HOUSES.houses.map(q => ({ pts: q, h: HOUSE_H }))).sort((a, b) => a.h - b.h);
    for (const it of items) {
      const v = Math.min(255, Math.round(it.h * 8)); g.fillStyle = `rgb(${v},${v},${v})`; g.beginPath();
      it.pts.forEach(([E, N], i) => { const X = (E - x0) / cs, Y = (N - y0) / cs; if (i) g.lineTo(X, Y); else g.moveTo(X, Y); });
      g.closePath(); g.fill();
    }
    const d = g.getImageData(0, 0, n, n).data; for (let i = 0; i < n * n; i++) H[i] = d[i * 4] / 8;
  }
  const hAt = (E, N) => { const X = Math.floor((E - x0) / cs), Y = Math.floor((N - y0) / cs); return X < 0 || Y < 0 || X >= n || Y >= n ? 0 : H[Y * n + X]; };
  const RIDGE = [[7, 4.5, 15], [12, 1.0, 4], [353, 0.8, 5], [40, 1.7, 14], [86, 1.7, 11], [111, 2.2, 13], [160, 1.9, 22], [203, 1.3, 17], [316, 1.0, 20]];
  const gs = (a, c, w) => { const d = ((a - c + 540) % 360) - 180; return Math.exp(-d * d / (2 * w * w)); };
  const horizon = az => 0.65 + RIDGE.reduce((s, [c, k, w]) => s + k * gs(az, c, w), 0); // the same mountain line as the sky of the model
  function grid(polys, step, inset) {
    const out = [];
    for (const P of polys) {
      let a = 1e9, b = -1e9, c = 1e9, d = -1e9; for (const [E, N] of P) { a = Math.min(a, E); b = Math.max(b, E); c = Math.min(c, N); d = Math.max(d, N); }
      for (let E = a + inset; E <= b - inset + 1e-6; E += step) for (let N = c + inset; N <= d - inset + 1e-6; N += step)
        if (inPoly([E, N], P) && [[inset, 0], [-inset, 0], [0, inset], [0, -inset]].every(([u, v]) => inPoly([E + u, N + v], P))) out.push([E, N]);
    }
    return out;
  }
  const T = { t: { pts: grid(HOUSES.backs, 0.5, 0.25), y: 4.4 }, r: { pts: grid(HOUSES.houses, 0.8, 0.35), y: HOUSE_H + 0.25 } };
  function litFrac(set, az, el) {
    if (el <= horizon(az)) return 0;
    const dx = Math.sin(az * DEG), dn = Math.cos(az * DEG), tn = Math.tan(el * DEG), y = set.y, maxT = Math.min(80, (17.5 - y) / tn);
    let lit = 0;
    for (const [E, N] of set.pts) {
      let ok = 1; for (let t = 0.35; t < maxT; t += 0.25) if (hAt(E + dx * t, N + dn * t) > y + t * tn) { ok = 0; break; }
      lit += ok;
    }
    return lit / set.pts.length;
  }
  // 12 months (day 21) × 96 quarter hours
  const year = new Date().getFullYear(), data = { t: [], r: [] }, sunAt = [];
  function month(m) {
    const row = [];
    for (let q = 0; q < 96; q++) { const mins = q * 15 + 7.5, sp = sunPos(localToUTC(year, m, 21, mins), SITE.lat, SITE.lon); row.push(sp); }
    sunAt[m] = row;
    for (const k of ["t", "r"]) data[k][m] = row.map(sp => sp.el > 0 ? litFrac(T[k], sp.az, sp.el) : -1);
  }
  const hours = (k, m) => data[k][m].reduce((s, f) => s + Math.max(0, f) * 0.25, 0);
  const done = [];
  function run(cb) { // a month at a time, so the page stays responsive
    let m = 0;
    const step = () => { month(m); done.push(m); cb(m); if (++m < 12) setTimeout(step, 0); };
    setTimeout(step, 30);
  }
  return { run, data, sunAt, hours, T, horizon, hAt };
})();

// ---------- sun study: heat map ----------
(function heat() {
  const V = VIEW, hm = $("hm"), sideLab = $("sideLab"), sideBig = $("sideBig"), sideTxt = $("sideTxt"), tip = $("sideTip");
  const MON3 = ["gen", "febr", "març", "abr", "maig", "juny", "jul", "ag", "set", "oct", "nov", "des"];
  const H0 = 6, H1 = 21, cells = [], monthLbl = [];
  let kind = "t", curM = new Date().getMonth();
  hm.appendChild(Object.assign(document.createElement("span"), { className: "hd" }));
  for (let h = H0; h <= H1; h++) hm.appendChild(Object.assign(document.createElement("span"), { className: "hd", textContent: String(h) }));
  for (let m = 0; m < 12; m++) {
    const lab = Object.assign(document.createElement("span"), { className: "mo", textContent: MON3[m] }); hm.appendChild(lab); monthLbl.push(lab);
    for (let h = H0; h <= H1; h++) {
      const b = document.createElement("button"); b.type = "button"; b.dataset.m = m; b.dataset.h = h; b.disabled = true;
      b.setAttribute("aria-label", `21 ${MONTHS[m]}, de ${h}:00 a ${h + 1}:00`); hm.appendChild(b); cells.push(b);
    }
  }
  const STOPS = [[0, [229, 231, 225]], [0.33, [243, 210, 122]], [0.66, [232, 154, 26]], [1, [184, 92, 12]]];
  const col = v => { let i = 1; while (i < STOPS.length - 1 && v > STOPS[i][0]) i++; const [a, ca] = STOPS[i - 1], [b, cb] = STOPS[i], t = clamp((v - a) / (b - a), 0, 1); return `rgb(${ca.map((c, j) => Math.round(lerp(c, cb[j], t))).join(",")})`; };
  const cellVal = (m, h) => { const r = SUNSTUDY.data[kind][m]; if (!r) return null; const q = r.slice(h * 4, h * 4 + 4); if (q.every(f => f < 0)) return -1; return q.reduce((s, f) => s + Math.max(0, f), 0) / 4; };
  const fmtH = x => x.toFixed(1).replace(".", ",") + " h";
  const PLACE = { t: "a la terrassa del darrere", r: "a la coberta" };
  function paint(m) {
    for (const b of cells) {
      if (m !== undefined && +b.dataset.m !== m) continue;
      const v = cellVal(+b.dataset.m, +b.dataset.h); if (v === null) continue;
      b.disabled = v < 0; b.classList.toggle("night", v < 0); b.style.background = v < 0 ? "" : col(v);
    }
  }
  function side(m) {
    curM = m; monthLbl.forEach((l, i) => l.classList.toggle("on", i === m));
    sideLab.textContent = "21 " + MONTHS[m];
    if (!SUNSTUDY.data[kind][m]) return;
    sideBig.textContent = fmtH(SUNSTUDY.hours(kind, m)); sideTxt.textContent = "de sol directe al dia " + PLACE[kind];
  }
  function cellTip(b) {
    const m = +b.dataset.m, h = +b.dataset.h, v = cellVal(m, h);
    if (v === null || v < 0) { tip.textContent = `21 ${MONTHS[m]}, de ${h}:00 a ${h + 1}:00 · el sol encara no ha sortit o ja s'ha post.`; return; }
    const sp = SUNSTUDY.sunAt[m][h * 4 + 2];
    tip.textContent = `21 ${MONTHS[m]}, de ${h}:00 a ${h + 1}:00 · sol directe a un ${Math.round(v * 100)} % de l'espai` + (sp.el > 0 ? ` · sol a ${Math.round(sp.el)}°, cap al ${compass(sp.az)}` : "") + ". Fes-hi clic per veure-ho en 3D.";
  }
  hm.addEventListener("pointerover", e => { const b = e.target.closest("button"); if (!b) return; side(+b.dataset.m); cellTip(b); });
  hm.addEventListener("focusin", e => { const b = e.target.closest("button"); if (!b) return; side(+b.dataset.m); cellTip(b); });
  hm.addEventListener("click", e => {
    const b = e.target.closest("button"); if (!b || b.disabled || !V.ok) return;
    cells.forEach(c => c.classList.toggle("sel", c === b));
    const m = +b.dataset.m, h = +b.dataset.h, S = V.S;
    S.preset = true; S.min = h * 60 + 30; V.setDay(String(m + 1).padStart(2, "0") + "-21"); V.setGhost(true); V.setPlaying(false);
    if (kind === "t") Object.assign(S.aer, { yaw: 0.32, pitch: 0.62, dist: 44, target: [0.8, 3, -1] });
    else Object.assign(S.aer, { yaw: 0.6, pitch: 0.95, dist: 46, target: [0.6, 6, -1.5] });
    S.auto = false; S.mode = "aer";
    $("explora").scrollIntoView({ behavior: REDUCE ? "auto" : "smooth", block: "start" });
    setTimeout(() => { V.go("aer", 1600); V.showHint(`21 ${MONTHS[m]} a les ${h}:30, amb el volum previst de les cases`, 5000); }, 60);
  });
  document.querySelectorAll(".tabs .chip").forEach(t => t.addEventListener("click", () => {
    kind = t.dataset.k;
    document.querySelectorAll(".tabs .chip").forEach(o => { o.setAttribute("aria-pressed", String(o === t)); o.setAttribute("aria-selected", String(o === t)); });
    paint(); side(curM); tip.textContent = "Passa per sobre d'una casella per veure-la.";
  }));
  side(curM);
  SUNSTUDY.run(m => {
    paint(m); if (m === curM) side(m);
    if (m === 11) {
      const d = SUNSTUDY, roof = d.data.r.reduce((s, r, i) => s + d.hours("r", i), 0) / 12;
      $("sJun").textContent = fmtH(d.hours("t", 5)).replace(" h", " hores"); $("sDec").textContent = fmtH(d.hours("t", 11)).replace(" h", " hores");
      $("sRoof").textContent = fmtH(roof).replace(" h", " hores") + " al dia";
    }
  });
})();

// ---------- plans: one floor at a time ----------
(function plans() {
  const tabs = document.querySelectorAll(".ptabs .chip");
  tabs.forEach(t => t.addEventListener("click", () => {
    const k = t.dataset.k;
    tabs.forEach(o => o.setAttribute("aria-pressed", String(o === t)));
    document.querySelectorAll(".planfig svg.pl, .planside .pside").forEach(el => el.classList.toggle("on", el.dataset.k === k));
  }));
})();

// ---------- mortgage simulator ----------
(function quota() {
  const PRICE = 396000, ent = $("qEnt"), any = $("qAny"), tin = $("qTin");
  const eur = x => Math.round(x).toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".") + " €";
  function upd() {
    const e = +ent.value / 100, n = +any.value * 12, r = +tin.value / 100 / 12, L = PRICE * (1 - e);
    const P = r > 0 ? L * r / (1 - Math.pow(1 + r, -n)) : L / n;
    $("oEnt").textContent = ent.value + " % · " + eur(PRICE * e); $("oAny").textContent = any.value + " anys";
    $("oTin").textContent = (+tin.value).toFixed(2).replace(".", ",") + " %";
    $("qQuota").textContent = eur(P) + "/mes"; $("qLoan").textContent = eur(L); $("qDown").textContent = eur(PRICE * e); $("qInc").textContent = eur(P / 0.35) + "/mes";
    $("qPreu").textContent = eur(PRICE);
  }
  [ent, any, tin].forEach(i => i.addEventListener("input", upd)); upd();
})();

// ---------- reveal on scroll and counters ----------
(function reveal() {
  const els = document.querySelectorAll(".block h2, .block .lede, .block .frame, .heat, .sunside, .calc, .result, .facts, .princ, .tabs, .planfig, .planside");
  const count = el => {
    const end = +el.dataset.count, sep = el.dataset.sep, t0 = performance.now(), dur = 1300;
    const f = now => { const t = clamp((now - t0) / dur, 0, 1), v = Math.round(end * easeOut3(t)); el.textContent = sep ? v.toString().replace(/\B(?=(\d{3})+(?!\d))/g, ".") : String(v); if (t < 1) requestAnimationFrame(f); };
    requestAnimationFrame(f);
  };
  if (REDUCE || !("IntersectionObserver" in window)) return;
  const io = new IntersectionObserver(es => {
    for (const e of es) if (e.isIntersecting) { e.target.classList.add("in"); e.target.querySelectorAll("[data-count]").forEach(count); io.unobserve(e.target); }
  }, { rootMargin: "0px 0px -8% 0px", threshold: 0.12 });
  els.forEach(el => { el.classList.add("rv"); io.observe(el); });
})();
