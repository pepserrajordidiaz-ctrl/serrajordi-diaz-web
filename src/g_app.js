// ---------- app · viewer core (one WebGL canvas that moves between the story and the explorer) ----------
const $ = id => document.getElementById(id);
const REDUCE = matchMedia("(prefers-reduced-motion: reduce)").matches;
const MONTHS = ["de gener", "de febrer", "de març", "d'abril", "de maig", "de juny", "de juliol", "d'agost", "de setembre", "d'octubre", "de novembre", "de desembre"];
const easeOut3 = t => 1 - Math.pow(1 - t, 3), easeIn3 = t => t * t * t;
// camera moves that stay out of the buildings: rise first then travel, or travel first then come down
function camPath(a, b, t) {
  const s = ease(clamp(t, 0, 1)), up = b.eye[1] >= a.eye[1];
  const h = up ? easeIn3(s) : easeOut3(s), v = up ? easeOut3(s) : easeIn3(s);
  return {
    eye: [lerp(a.eye[0], b.eye[0], h), lerp(a.eye[1], b.eye[1], v), lerp(a.eye[2], b.eye[2], h)],
    target: V3.lerp(a.target, b.target, s), up: V3.norm(V3.lerp(a.up, b.up, s)), fov: lerp(a.fov, b.fov, s)
  };
}
const sph = c => { const d = V3.sub(c.eye, c.target), r = Math.hypot(d[0], d[1], d[2]); return { r, yaw: Math.atan2(d[0], d[2]), pitch: Math.asin(clamp(d[1] / r, -1, 1)) }; };
function camOrbit(a, b, t) { // sweep around the site
  const s = ease(clamp(t, 0, 1)), A = sph(a), B = sph(b);
  const dy = ((B.yaw - A.yaw + 3 * Math.PI) % (2 * Math.PI)) - Math.PI;
  const yaw = A.yaw + dy * s, pitch = lerp(A.pitch, B.pitch, s), r = Math.exp(lerp(Math.log(A.r), Math.log(B.r), s));
  const tg = V3.lerp(a.target, b.target, s), cp = Math.cos(pitch);
  return { eye: V3.add(tg, [Math.sin(yaw) * cp * r, Math.sin(pitch) * r, Math.cos(yaw) * cp * r]), target: tg, up: [0, 1, 0], fov: lerp(a.fov, b.fov, s) };
}

const VIEW = (function () {
  const hosts = { story: $("storyHost"), explore: $("exploreHost") }, posters = {};
  for (const k in hosts) { const p = document.createElement("canvas"); p.className = "poster"; p.setAttribute("aria-hidden", "true"); hosts[k].appendChild(p); posters[k] = p; hosts[k].dataset.k = k; }
  const canvas = document.createElement("canvas"); canvas.id = "gl"; canvas.setAttribute("role", "img");
  canvas.setAttribute("aria-label", "Maqueta 3D del carrer d'Anselm Clavé i del solar, amb el sol real de cada hora");
  const layer = document.createElement("div"); layer.className = "labels"; layer.id = "labels";
  hosts.story.append(canvas, layer);
  const stage = $("stage"), hint = $("hint"), hr = $("hr"), read = $("sunread"), tb = $("tb");
  const S = {
    ctx: "story", pending: null, mode: "str", started: false, ok: true,
    aer: { yaw: Math.PI + 0.35, pitch: 0.82, dist: 62, target: [0.6, 2, -0.5] },
    str: { x: -0.5, z: -11.4, yaw: 0.05, pitch: 0.1, fov: 74 }, pla: { dist: 62 },
    cam: null, anim: null, dirty: true, ghost: false, ghostA: 0, labels: true, auto: !REDUCE, playing: false,
    day: "06-21", min: 1125, armed: false, q: 1, last: null,
    story: { cam: null, ghostA: 0, ghostH: 0, vis: [], shift: 0, shiftY: 0, focus: 1 }, focus: true, focusA: 0.4
  };
  let R = null;
  try { R = Renderer(canvas); } catch (e) {
    console.error(e); S.ok = false;
    for (const k in hosts) { const d = document.createElement("p"); d.className = "fallback"; d.textContent = "Aquest navegador no pot mostrar la maqueta 3D: cal WebGL 2. Prova-ho amb Chrome, Edge, Firefox o Safari actualitzats."; hosts[k].appendChild(d); }
    canvas.remove(); hint.classList.add("gone");
  }

  // ----- sun -----
  function dayParts() {
    if (S.day === "today") { const now = Date.now(), l = new Date(now + madridOffsetH(new Date(now).getUTCFullYear(), now) * 3600000); return [l.getUTCFullYear(), l.getUTCMonth(), l.getUTCDate()]; }
    const [m, d] = S.day.split("-").map(Number); return [new Date().getFullYear(), m - 1, d];
  }
  function applySun() {
    const [y, mo, d] = dayParts(), sp = sunPos(localToUTC(y, mo, d, S.min), SITE.lat, SITE.lon), ch = Math.cos(sp.el * DEG);
    const [wx, wz] = enToWorld(Math.sin(sp.az * DEG) * ch, Math.cos(sp.az * DEG) * ch);
    if (R) R.setSun(V3.norm([wx, Math.sin(sp.el * DEG), wz]), sp.el); S.dirty = true;
    read.textContent = `${d} ${MONTHS[mo]} · ${hhmm(S.min)} · ` + (sp.el > 0 ? `sol a ${Math.round(sp.el)}° d'alçada, direcció ${compass(sp.az)}` : "el sol és sota l'horitzó");
    return sp;
  }
  function setDay(day) {
    S.day = day; const [y, mo, d] = dayParts(), info = dayInfo(y, mo, d);
    hr.min = info.rise - 10; hr.max = info.set + 10; S.min = clamp(S.min, +hr.min, +hr.max); hr.value = S.min;
    document.querySelectorAll("#days .chip").forEach(c => c.setAttribute("aria-pressed", String(c.dataset.d === day)));
    return applySun();
  }
  const setPlaying = on => { S.playing = on; $("play").setAttribute("aria-pressed", String(on)); $("play").textContent = on ? "Atura" : "Mou el sol"; };
  document.querySelectorAll("#days .chip").forEach(c => c.addEventListener("click", () => setDay(c.dataset.d)));
  hr.addEventListener("input", () => { S.min = +hr.value; applySun(); });
  $("play").addEventListener("click", () => setPlaying(!S.playing));
  if (!R) return { S, ok: false, setDay, applySun, showMoment() { location.hash = "#explora"; } };

  // ----- explorer cameras -----
  const HINTS = {
    aer: "Arrossega per girar · Maj. + arrossega per desplaçar · fes clic i usa la roda per apropar-te",
    str: "Arrossega per mirar al voltant · fletxes o botons per caminar pel carrer",
    pla: "Planta amb el nord a dalt · fes clic i usa la roda per apropar-te"
  };
  function camFor(m) {
    if (m === "aer") { const a = S.aer, cp = Math.cos(a.pitch); return { eye: V3.add(a.target, [Math.sin(a.yaw) * cp * a.dist, Math.sin(a.pitch) * a.dist, Math.cos(a.yaw) * cp * a.dist]), target: a.target.slice(), up: [0, 1, 0], fov: 40 }; }
    if (m === "str") { const s = S.str, cp = Math.cos(s.pitch), e = [s.x, 1.65, s.z]; return { eye: e, target: V3.add(e, [Math.sin(s.yaw) * cp, Math.sin(s.pitch), Math.cos(s.yaw) * cp]), up: [0, 1, 0], fov: s.fov }; }
    return { eye: [0.6, S.pla.dist, -0.5], target: [0.6, 0, -0.5], up: NORTH.slice(), fov: 30 };
  }
  function currentCam(now) {
    const to = camFor(S.mode); if (!S.anim) return to;
    const t = (now - S.anim.t0) / S.anim.dur; if (t >= 1) { S.anim = null; return to; }
    return camPath(S.anim.from, to, t);
  }
  function showHint(txt, ms = 6000) { hint.textContent = txt || HINTS[S.mode]; hint.classList.remove("gone"); clearTimeout(S.ht); S.ht = setTimeout(() => hint.classList.add("gone"), ms); }
  function go(m, dur = 1300) {
    const c = S.cam || camFor(m);
    S.anim = { from: { eye: c.eye.slice(), target: c.target.slice(), up: c.up.slice(), fov: c.fov }, t0: performance.now(), dur: REDUCE ? 1 : dur };
    S.mode = m; S.dirty = true;
    for (const [k, id] of [["aer", "mAer"], ["str", "mStr"], ["pla", "mPla"]]) $(id).setAttribute("aria-pressed", String(S.mode === k));
    $("walk").classList.toggle("on", m === "str"); tb.classList.toggle("plan", m === "pla");
    $("tbView").firstChild.textContent = { aer: "Maqueta aèria ", str: "A peu de carrer, a 1,65 m ", pla: "Planta " }[m];
    if (S.ctx === "explore") showHint();
  }
  const setGhost = on => { S.ghost = on; $("tVol").setAttribute("aria-pressed", String(on)); S.dirty = true; };

  // ----- labels -----
  const labels = [];
  const addLabel = (html, pos, cls, extra) => { const el = document.createElement("div"); el.className = "lbl hide " + cls; el.innerHTML = html; layer.appendChild(el); labels.push(Object.assign({ el, pos, cls, on: false }, extra)); };
  addLabel("C/ Anselm Clavé, 30<em>Solar de ≈" + SITE_AREA + " m² útils · aquí farem les cases</em>", [0.6, 0.3, -0.5], "plot");
  addLabel("Carrer d'Anselm Clavé", [-21, 0.3, -7.2], "st");
  for (const rc of Object.keys(NUMBERS)) {
    const ps = PARTS.filter(p => p.rc === rc); if (!ps.length) continue;
    const top = ps.reduce((a, b) => b.H > a.H ? b : a), c = top.pts.reduce((a, q) => [a[0] + q[0] / top.pts.length, a[1] + q[1] / top.pts.length], [0, 0]);
    addLabel(NUMBERS[rc] + " · " + (top.fl > 1 ? "PB+" + (top.fl - 1) : "PB"), [c[0], top.H + 1.4, -c[1]], "nb");
  }
  for (const [i, j, t] of SITE_DIMS) { // measured on site
    const a = SITE_EN[i], b = SITE_EN[j], L = Math.hypot(b[0] - a[0], b[1] - a[1]), n = [-(b[1] - a[1]) / L, (b[0] - a[0]) / L], k = L < 3.5 ? 0.75 : 1.1;
    addLabel(t, [(a[0] + b[0]) / 2 + n[0] * k, 0.3, -((a[1] + b[1]) / 2 + n[1] * k)], "dim");
  }
  { const c = EAT_EN.reduce((s, q) => [s[0] + q[0] / 4, s[1] + q[1] / 4], [0, 0]); addLabel("Ocupat pel veí<em>3,00 × 2,70 m · ≈8 m²</em>", [c[0] + HOUSES.f[0] * 1.2 + HOUSES.d[0] * 0.6, 0.3, -(c[1] + HOUSES.f[1] * 1.2 + HOUSES.d[1] * 0.6)], "eat"); }
  {
    const [A, B] = PLOT_FRONT, M = [(A[0] + B[0]) / 2, (A[1] + B[1]) / 2];
    [["PB · Garatge i porxo", 1.5, 2.9], ["P1 · Cuina-menjador i estar", 4.4, 5.85], ["P2 · 2 dormitoris + estudi", 7.4, 8.8], ["Altell · Suite sota coberta", 10.3, 11.7]]
      .forEach(([t, y, minH]) => addLabel(t, [M[0], y, -(M[1] + 0.25)], "fl", { minH }));
  }
  const VIS = { plot: ["aer", "str"], st: ["aer", "pla"], nb: ["aer"], dim: ["pla"], eat: ["aer", "pla"], fl: ["aer", "str"] };
  function placeLabels(vp, vis, ghostH, still) {
    const w = canvas.clientWidth, h = canvas.clientHeight;
    for (const L of labels) {
      let ok = still && vis.includes(L.cls) && (L.cls !== "fl" || ghostH >= L.minH), p;
      if (ok) {
        p = M4.xform(vp, L.cls === "plot" ? [L.pos[0], 0.3 + Math.min(ghostH, HOUSE_H) * 1.03, L.pos[2]] : L.pos);
        ok = p[3] > 0 && p[2] < 1 && Math.abs(p[0]) < 1.05 && Math.abs(p[1]) < 1.05;
      }
      if (ok !== L.on) { L.on = ok; L.el.classList.toggle("hide", !ok); }
      if (!ok) continue;
      L.el.style.transform = `translate(${((p[0] * 0.5 + 0.5) * w).toFixed(1)}px,${((0.5 - p[1] * 0.5) * h).toFixed(1)}px) ` + (L.cls === "dim" || L.cls === "fl" || L.cls === "eat" ? "translate(-50%,-50%)" : "translate(-50%,-100%)");
    }
  }
  function updateNorth(vp) {
    const o = [0, 0, 6], c = M4.xform(vp, o), n = M4.xform(vp, V3.add(o, V3.scale(NORTH, 10)));
    if (c[3] <= 0 || n[3] <= 0) return;
    const ang = Math.atan2((n[0] - c[0]) * canvas.clientWidth, (n[1] - c[1]) * canvas.clientHeight);
    $("north").style.transform = `rotate(${(ang / DEG).toFixed(1)}deg)`;
  }
  function updateScale(vp) {
    if (S.mode !== "pla") return;
    const a = M4.xform(vp, [0, 0, 6.3]), b = M4.xform(vp, [10, 0, 6.3]);
    const px = Math.hypot((b[0] - a[0]) * canvas.clientWidth / 2, (b[1] - a[1]) * canvas.clientHeight / 2);
    const m = px > 140 ? 5 : px < 45 ? 20 : 10, sc = $("tbView").querySelector(".scale");
    sc.querySelector("i").style.width = (px * m / 10).toFixed(0) + "px"; sc.lastChild.textContent = m + " m";
  }

  // ----- explorer tools -----
  $("tVol").addEventListener("click", () => setGhost(!S.ghost));
  $("tFoc").addEventListener("click", () => { S.focus = !S.focus; $("tFoc").setAttribute("aria-pressed", String(S.focus)); S.dirty = true; });
  $("tLbl").addEventListener("click", () => { S.labels = !S.labels; $("tLbl").setAttribute("aria-pressed", String(S.labels)); S.dirty = true; });
  $("tFull").addEventListener("click", () => { const v = $("viewer"); try { if (document.fullscreenElement) document.exitFullscreen(); else v.requestFullscreen().catch(() => {}); } catch (e) { } });
  $("mAer").addEventListener("click", () => go("aer")); $("mStr").addEventListener("click", () => go("str", 1600)); $("mPla").addEventListener("click", () => go("pla"));
  function walk(fw, st) {
    const s = S.str, f = [Math.sin(s.yaw), Math.cos(s.yaw)], r = [-Math.cos(s.yaw), Math.sin(s.yaw)];
    const nx = s.x + f[0] * fw + r[0] * st, nz = s.z + f[1] * fw + r[1] * st;
    if (Math.hypot(nx - DISC.cx, nz - DISC.cz) < DISC.r - 3 && !inParcel([nx, -nz])) { s.x = nx; s.z = nz; } S.dirty = true;
  }
  $("wF").addEventListener("click", () => walk(2, 0)); $("wB").addEventListener("click", () => walk(-2, 0));
  $("wL").addEventListener("click", () => walk(0, -2)); $("wR").addEventListener("click", () => walk(0, 2));
  addEventListener("keydown", e => {
    if (S.ctx !== "explore" || S.mode !== "str" || !S.armed) return;
    const k = { ArrowUp: [1, 0], w: [1, 0], ArrowDown: [-1, 0], s: [-1, 0], ArrowLeft: [0, -1], a: [0, -1], ArrowRight: [0, 1], d: [0, 1] }[e.key];
    if (k) { e.preventDefault(); walk(k[0] * 1.2, k[1] * 1.2); }
  });

  // ----- pointer, wheel and pinch (explorer only) -----
  const ptrs = new Map(); let pinch0 = 0;
  function rotate(dx, dy, pan) {
    if (S.anim) return;
    if (S.mode === "aer") {
      const a = S.aer;
      if (pan) {
        const r = [Math.cos(a.yaw), 0, -Math.sin(a.yaw)], f = [-Math.sin(a.yaw), 0, -Math.cos(a.yaw)], k = a.dist * 0.0016;
        a.target = V3.add(a.target, V3.add(V3.scale(r, -dx * k), V3.scale(f, dy * k)));
        const d = Math.hypot(a.target[0], a.target[2] - 4); if (d > 30) { a.target[0] *= 30 / d; a.target[2] = 4 + (a.target[2] - 4) * 30 / d; }
      } else { a.yaw -= dx * 0.0055; a.pitch = clamp(a.pitch + dy * 0.0045, 0.1, 1.45); }
    } else if (S.mode === "str") { S.str.yaw += dx * 0.0042; S.str.pitch = clamp(S.str.pitch + dy * 0.0035, -0.6, 0.9); }
    S.dirty = true;
  }
  function zoom(f) {
    if (S.mode === "aer") S.aer.dist = clamp(S.aer.dist * f, 20, 180);
    else if (S.mode === "str") S.str.fov = clamp(S.str.fov * f, 30, 95);
    else S.pla.dist = clamp(S.pla.dist * f, 55, 260);
    S.dirty = true;
  }
  const interact = () => { S.auto = false; hint.classList.add("gone"); };
  stage.addEventListener("pointerdown", e => {
    if (S.ctx !== "explore") return;
    stage.setPointerCapture(e.pointerId); ptrs.set(e.pointerId, { x: e.clientX, y: e.clientY, pan: e.button === 2 || e.shiftKey });
    S.armed = true; interact(); stage.classList.add("dragging");
    if (ptrs.size === 2) { const [a, b] = [...ptrs.values()]; pinch0 = Math.hypot(a.x - b.x, a.y - b.y); }
  });
  stage.addEventListener("pointermove", e => {
    const p = ptrs.get(e.pointerId); if (!p) return;
    const dx = e.clientX - p.x, dy = e.clientY - p.y; p.x = e.clientX; p.y = e.clientY;
    if (ptrs.size === 2) { const [a, b] = [...ptrs.values()], d = Math.hypot(a.x - b.x, a.y - b.y); if (pinch0 > 0 && d > 0) zoom(pinch0 / d); pinch0 = d; return; }
    rotate(dx, dy, p.pan || e.shiftKey);
  });
  const end = e => { ptrs.delete(e.pointerId); if (ptrs.size < 2) pinch0 = 0; if (!ptrs.size) stage.classList.remove("dragging"); };
  stage.addEventListener("pointerup", end); stage.addEventListener("pointercancel", end);
  stage.addEventListener("pointerleave", () => { if (!document.fullscreenElement) S.armed = false; });
  stage.addEventListener("contextmenu", e => e.preventDefault());
  stage.addEventListener("wheel", e => {
    if (S.ctx !== "explore") return;
    if (!S.armed && !e.ctrlKey && !document.fullscreenElement) { showHint("Fes clic a la maqueta (o mantén Ctrl) per apropar-te amb la roda", 2200); return; }
    e.preventDefault(); interact(); zoom(Math.exp(clamp(e.deltaY, -120, 120) * 0.0016));
  }, { passive: false });

  // ----- which host shows the model -----
  function resize() {
    const h = hosts[S.ctx], dpr = Math.min(window.devicePixelRatio || 1, S.ctx === "story" ? 1.5 : 2) * S.q;
    const w = Math.max(1, Math.round(h.clientWidth * dpr)), hh = Math.max(1, Math.round(h.clientHeight * dpr));
    if (canvas.width !== w || canvas.height !== hh) { canvas.width = w; canvas.height = hh; S.dirty = true; }
  }
  const ro = new ResizeObserver(es => { if (es.some(e => e.target === hosts[S.ctx])) resize(); });
  ro.observe(hosts.story); ro.observe(hosts.explore);
  document.addEventListener("fullscreenchange", () => { S.armed = !!document.fullscreenElement; resize(); });
  const ratio = { story: 0, explore: 0 };
  let visible = true;
  function decide() {
    const want = ratio.explore > 0.3 || (ratio.explore > 0 && ratio.story === 0) ? "explore" : ratio.story > 0 ? "story" : S.ctx;
    if (want !== S.ctx) S.pending = want;
    visible = ratio[S.ctx] > 0 || (S.pending && ratio[S.pending] > 0);
    if (visible) S.dirty = true;
  }
  new IntersectionObserver(es => { for (const e of es) ratio[e.target.dataset.k] = e.isIntersecting ? e.intersectionRatio : 0; decide(); },
    { threshold: [0, 0.02, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1] }).observe(hosts.story);
  new IntersectionObserver(es => { for (const e of es) ratio[e.target.dataset.k] = e.isIntersecting ? e.intersectionRatio : 0; decide(); },
    { threshold: [0, 0.02, 0.1, 0.2, 0.3, 0.4, 0.6, 0.8, 1] }).observe(hosts.explore);
  function mount(k) {
    if (S.last) { // freeze the last frame in the host we leave
      R.draw(S.last.cam, S.last.gA, S.last.opt);
      const p = posters[S.ctx]; p.width = Math.max(1, canvas.width >> 1); p.height = Math.max(1, canvas.height >> 1);
      p.getContext("2d").drawImage(canvas, 0, 0, p.width, p.height);
    }
    hosts[k].append(canvas, layer); S.ctx = k; resize(); S.dirty = true;
    if (k === "explore") { if (!S.started && !S.preset) S.min = api.gold; setDay(S.day); go(S.mode, S.started ? 1400 : 2400); S.started = true; showHint(); }
    else { S.anim = null; S.armed = false; }
  }

  // ----- loop -----
  let last = performance.now(), slow = 0;
  const api = { S, ok: true, go, setDay, applySun, walk, setGhost, setPlaying, showHint, onStory: null, R, labels, gold: 1125 };
  function frame(now) {
    const dt = Math.min(64, now - last); last = now;
    if (S.pending) { const k = S.pending; S.pending = null; if (k !== S.ctx) mount(k); }
    if (visible) {
      let cam, gA, opt, vis, still;
      if (S.ctx === "story") {
        if (api.onStory) api.onStory(dt, now);
        const st = S.story; cam = st.cam || camFor("str"); gA = st.ghostA; opt = { shift: st.shift, shiftY: st.shiftY, ghostH: st.ghostH, focus: st.focus };
        vis = st.vis; still = true;
      } else {
        if (S.auto && !S.anim && S.mode === "aer") { S.aer.yaw += dt * 0.00004; S.dirty = true; }
        if (S.playing) { S.min += dt * 0.03; if (S.min > +hr.max) S.min = +hr.min; hr.value = S.min; applySun(); }
        const tg = S.ghost ? 1 : 0;
        if (Math.abs(S.ghostA - tg) > 0.002) { S.ghostA += (tg - S.ghostA) * Math.min(1, dt * 0.008); S.dirty = true; } else S.ghostA = tg;
        const fT = S.focus ? (S.mode === "str" ? 0.45 : 1) : 0;
        if (Math.abs(S.focusA - fT) > 0.002) { S.focusA += (fT - S.focusA) * Math.min(1, dt * 0.006); S.dirty = true; } else S.focusA = fT;
        cam = null; gA = S.ghostA; opt = { ghostH: 99, focus: S.focusA };
        vis = S.labels ? Object.keys(VIS).filter(c => VIS[c].includes(S.mode) && (c !== "fl" || S.ghost)) : []; still = !S.anim;
      }
      if (S.dirty || S.anim) {
        const t0 = performance.now();
        if (!cam) cam = currentCam(now);
        const vp = R.draw(cam, gA, opt); S.cam = cam; S.last = { cam, gA, opt };
        placeLabels(vp, vis, S.ctx === "story" ? opt.ghostH : S.ghostA * HOUSE_H, still);
        if (S.ctx === "explore") { updateNorth(vp); updateScale(vp); }
        S.dirty = false;
        // very slow GPU: render fewer pixels
        if (dt > 45 && performance.now() - t0 > 4) { if (++slow > 20 && S.q > 0.55) { S.q *= 0.8; slow = 0; resize(); } } else slow = Math.max(0, slow - 1);
      }
    }
    requestAnimationFrame(frame);
  }
  setDay("06-21");
  resize();
  requestAnimationFrame(frame);
  window.__maqueta = api;
  return api;
})();
