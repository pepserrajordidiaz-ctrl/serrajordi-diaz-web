// ---------- renderer ----------
function compile(gl, vs, fs) {
  const mk = (t, s) => {
    const sh = gl.createShader(t); gl.shaderSource(sh, s); gl.compileShader(sh);
    if (!gl.getShaderParameter(sh, gl.COMPILE_STATUS)) throw new Error("shader: " + gl.getShaderInfoLog(sh));
    return sh;
  };
  const p = gl.createProgram();
  gl.attachShader(p, mk(gl.VERTEX_SHADER, vs)); gl.attachShader(p, mk(gl.FRAGMENT_SHADER, fs)); gl.linkProgram(p);
  if (!gl.getProgramParameter(p, gl.LINK_STATUS)) throw new Error("link: " + gl.getProgramInfoLog(p));
  const u = {}, n = gl.getProgramParameter(p, gl.ACTIVE_UNIFORMS);
  for (let i = 0; i < n; i++) { const a = gl.getActiveUniform(p, i); u[a.name] = gl.getUniformLocation(p, a.name); }
  return { p, u };
}
function upload(gl, mesh) {
  const vao = gl.createVertexArray(); gl.bindVertexArray(vao);
  const vb = gl.createBuffer(); gl.bindBuffer(gl.ARRAY_BUFFER, vb); gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(mesh.v), gl.STATIC_DRAW);
  const ib = gl.createBuffer(); gl.bindBuffer(gl.ELEMENT_ARRAY_BUFFER, ib); gl.bufferData(gl.ELEMENT_ARRAY_BUFFER, new Uint32Array(mesh.i), gl.STATIC_DRAW);
  for (const [loc, size, off] of [[0, 3, 0], [1, 3, 3], [2, 2, 6], [3, 3, 8], [4, 1, 11], [5, 4, 12], [6, 4, 16]]) {
    gl.enableVertexAttribArray(loc); gl.vertexAttribPointer(loc, size, gl.FLOAT, false, FPV * 4, off * 4);
  }
  gl.bindVertexArray(null);
  return { vao, count: mesh.i.length };
}
function bakeAO(gl) {
  const size = 1024, half = DISC.r + 4, x0 = DISC.cx - half, z0 = DISC.cz - half, span = half * 2, s = size / span;
  const src = document.createElement("canvas"); src.width = src.height = size;
  const t = src.getContext("2d"); t.fillStyle = "#fff"; t.fillRect(0, 0, size, size); t.fillStyle = "#000";
  for (const poly of FOOT) { t.beginPath(); poly.forEach(([x, z], i) => i ? t.lineTo((x - x0) * s, (z - z0) * s) : t.moveTo((x - x0) * s, (z - z0) * s)); t.closePath(); t.fill(); }
  const out = document.createElement("canvas"); out.width = out.height = size;
  const g = out.getContext("2d"); g.fillStyle = "#fff"; g.fillRect(0, 0, size, size);
  g.filter = "blur(9px)"; g.drawImage(src, 0, 0); g.filter = "none";
  g.globalCompositeOperation = "multiply"; g.filter = "blur(3px)"; g.drawImage(src, 0, 0); g.filter = "none";
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, out);
  gl.generateMipmap(gl.TEXTURE_2D);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR);
  gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE); gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE);
  return { tex, rect: [x0, z0, span, 0] };
}
function makeShadow(gl, size) {
  const tex = gl.createTexture(); gl.bindTexture(gl.TEXTURE_2D, tex);
  gl.texStorage2D(gl.TEXTURE_2D, 1, gl.DEPTH_COMPONENT24, size, size);
  for (const [k, v] of [[gl.TEXTURE_MIN_FILTER, gl.LINEAR], [gl.TEXTURE_MAG_FILTER, gl.LINEAR], [gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE], [gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE],
    [gl.TEXTURE_COMPARE_MODE, gl.COMPARE_REF_TO_TEXTURE], [gl.TEXTURE_COMPARE_FUNC, gl.LEQUAL]]) gl.texParameteri(gl.TEXTURE_2D, k, v);
  const fb = gl.createFramebuffer(); gl.bindFramebuffer(gl.FRAMEBUFFER, fb);
  gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.TEXTURE_2D, tex, 0);
  gl.drawBuffers([gl.NONE]); gl.readBuffer(gl.NONE);
  gl.bindFramebuffer(gl.FRAMEBUFFER, null);
  return { tex, fb, size };
}
const smooth = (a, b, x) => { const t = clamp((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t); };
function lightFor(el) { // warm, soft light: golden low sun, generous sky and bounce so shadows stay open
  const se = Math.sin(el * DEG), k = clamp((el - 1) / 40, 0, 1);
  const col = V3.lerp([1.0, 0.50, 0.25], [1.0, 0.92, 0.80], Math.sqrt(k));
  const I = 3.5 * clamp((el + 1.5) / 9, 0, 1) * (0.8 + 0.2 * clamp(el / 45, 0, 1));
  const dim = clamp((el + 5) / 12, 0.2, 1);
  return {
    sun: V3.scale(col, I),
    sky: V3.scale(V3.lerp([0.40, 0.33, 0.34], [0.40, 0.45, 0.56], k), dim),
    gnd: V3.scale(V3.lerp([0.34, 0.24, 0.17], [0.40, 0.32, 0.24], k), dim),
    fog: V3.lerp([0.62, 0.47, 0.42], [0.76, 0.80, 0.86], smooth(0, 0.45, se)),
    exposure: el < 6 ? 1.12 : 0.98,
    lamp: clamp((5 - el) / 8, 0, 1), day: clamp((el + 4) / 14, 0, 1)
  };
}
function Renderer(canvas) {
  const gl = canvas.getContext("webgl2", { antialias: true, alpha: false, powerPreference: "high-performance" });
  if (!gl) throw new Error("webgl2");
  const P = { scene: compile(gl, VS_SCENE, FS_SCENE), sky: compile(gl, VS_SKY, FS_SKY), depth: compile(gl, VS_DEPTH, FS_DEPTH), ghost: compile(gl, VS_SCENE, FS_GHOST) };
  const built = buildScene();
  const scene = upload(gl, built.m), ghost = upload(gl, buildGhost());
  const ao = bakeAO(gl);
  const small = Math.min(window.innerWidth, window.innerHeight) < 700;
  const sh = makeShadow(gl, small ? 2048 : 4096);
  const skyVao = gl.createVertexArray();
  let lvp = null, sunDir = [0, 1, 0], L = lightFor(45);
  const R = {
    gl,
    setSun(dir, el) { sunDir = dir; L = lightFor(el); this.shadowDirty = true; },
    shadowDirty: true,
    draw(cam, ghostA, opt = {}) {
      const w = canvas.width, h = canvas.height;
      const proj = M4.persp(cam.fov * DEG, w / h, 0.3, 12000), view = M4.lookAt(cam.eye, cam.target, cam.up);
      proj[8] = -(opt.shift || 0); proj[9] = -(opt.shiftY || 0);
      const vp = M4.mul(proj, view);
      const gS = ghostA > 0.5, gH = opt.ghostH ?? 99;
      if (gS !== this._gS || (gS && Math.abs(gH - this._gH) > 0.005)) { this.shadowDirty = true; this._gS = gS; this._gH = gH; }
      if (this.shadowDirty) {
        const c = [0, 0, 0], s = sunDir[1] > 0.04 ? sunDir : V3.norm([sunDir[0], 0.04, sunDir[2]]);
        const e = V3.add(c, V3.scale(s, 220));
        lvp = M4.mul(M4.ortho(-62, 62, -62, 62, 60, 420), M4.lookAt(e, c, Math.abs(s[1]) > 0.98 ? [0, 0, 1] : [0, 1, 0]));
        gl.bindFramebuffer(gl.FRAMEBUFFER, sh.fb); gl.viewport(0, 0, sh.size, sh.size);
        gl.enable(gl.DEPTH_TEST); gl.depthMask(true); gl.disable(gl.CULL_FACE); gl.clear(gl.DEPTH_BUFFER_BIT);
        gl.useProgram(P.depth.p); gl.uniformMatrix4fv(P.depth.u.uLVP, false, lvp);
        gl.uniform4f(P.depth.u.uDisc, DISC.cx, DISC.cz, DISC.r, 0); gl.uniform1f(P.depth.u.uClipH, 1e4);
        gl.bindVertexArray(scene.vao); gl.drawElements(gl.TRIANGLES, scene.count, gl.UNSIGNED_INT, 0);
        if (gS) { gl.uniform1f(P.depth.u.uClipH, gH); gl.bindVertexArray(ghost.vao); gl.drawElements(gl.TRIANGLES, ghost.count, gl.UNSIGNED_INT, 0); }
        gl.bindFramebuffer(gl.FRAMEBUFFER, null); this.shadowDirty = false;
      }
      gl.viewport(0, 0, w, h); gl.clearColor(0.7, 0.75, 0.8, 1); gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT);
      const sky = P.sky;
      gl.disable(gl.DEPTH_TEST); gl.depthMask(false); gl.useProgram(sky.p);
      gl.uniformMatrix4fv(sky.u.uInvVP, false, M4.inv(vp)); gl.uniform3fv(sky.u.uEye, cam.eye);
      gl.uniform3fv(sky.u.uSunDir, sunDir); gl.uniform3fv(sky.u.uSunCol, L.sun); gl.uniform3fv(sky.u.uFogCol, L.fog); gl.uniform3fv(sky.u.uSkyCol, L.sky);
      gl.uniform1f(sky.u.uExposure, L.exposure); gl.uniform4f(sky.u.uAxes, UX[0], UX[1], VZ[0], VZ[1]);
      gl.bindVertexArray(skyVao); gl.drawArrays(gl.TRIANGLES, 0, 3);
      gl.enable(gl.DEPTH_TEST); gl.depthMask(true); gl.depthFunc(gl.LEQUAL);
      const S = P.scene; gl.useProgram(S.p);
      gl.uniformMatrix4fv(S.u.uVP, false, vp); gl.uniformMatrix4fv(S.u.uLVP, false, lvp);
      gl.uniform3fv(S.u.uEye, cam.eye); gl.uniform3fv(S.u.uSunDir, sunDir); gl.uniform3fv(S.u.uSunCol, L.sun);
      gl.uniform3fv(S.u.uSkyCol, L.sky); gl.uniform3fv(S.u.uGndCol, L.gnd); gl.uniform3fv(S.u.uFogCol, L.fog);
      gl.uniform1f(S.u.uFogDen, 0.001); gl.uniform1f(S.u.uExposure, L.exposure); gl.uniform1f(S.u.uGlow, 0.4); gl.uniform1f(S.u.uLamp, L.lamp); gl.uniform1f(S.u.uFocus, opt.focus || 0);
      gl.uniform4f(S.u.uDisc, DISC.cx, DISC.cz, DISC.r, 0); gl.uniform4fv(S.u.uAOr, ao.rect);
      gl.uniform2fv(S.u["uPoly[0]"], new Float32Array(PLOT.flatMap(q => [q[0], -q[1]]))); gl.uniform1i(S.u.uPolyN, PLOT.length);
      gl.activeTexture(gl.TEXTURE0); gl.bindTexture(gl.TEXTURE_2D, sh.tex); gl.uniform1i(S.u.uShadow, 0);
      gl.activeTexture(gl.TEXTURE1); gl.bindTexture(gl.TEXTURE_2D, ao.tex); gl.uniform1i(S.u.uAO, 1);
      gl.bindVertexArray(scene.vao); gl.drawElements(gl.TRIANGLES, scene.count, gl.UNSIGNED_INT, 0);
      if (ghostA > 0.01) {
        const G = P.ghost; gl.useProgram(G.p); gl.enable(gl.BLEND); gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA); gl.depthMask(false);
        gl.uniformMatrix4fv(G.u.uVP, false, vp); if (G.u.uLVP) gl.uniformMatrix4fv(G.u.uLVP, false, lvp);
        gl.uniform3fv(G.u.uSunDir, sunDir); gl.uniform1f(G.u.uAlpha, ghostA); gl.uniform1f(G.u.uDay, L.day); gl.uniform1f(G.u.uGhostH, opt.ghostH ?? 99);
        gl.bindVertexArray(ghost.vao); gl.drawElements(gl.TRIANGLES, ghost.count, gl.UNSIGNED_INT, 0);
        gl.depthMask(true); gl.disable(gl.BLEND);
      }
      gl.bindVertexArray(null);
      return vp;
    }
  };
  return R;
}
