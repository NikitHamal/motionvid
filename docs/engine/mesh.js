// motionvid mesh engine: real 3D solids (rounded boxes, lathe solids, torus, extrusions), per-face lighting, textured screens.
// Faces are solid colors (flat shading, bevels catch the light): no shadows, no gradients. Kind: 'mesh' with `parts`.
import { val } from './ease.js';
import { makeProj, drawFlat } from './scene3d.js';
import { scratch, texQuad } from './assets.js';
import { DYN, STATIC_DYN, ramp } from './mesh3.js';

const TAU = Math.PI * 2;
const GEO = new Map();
const COL = new Map();
const rgb = (hex) => { let c = COL.get(hex); if (!c) { const n = parseInt((hex || '#17130F').slice(1), 16); c = [n >> 16 & 255, n >> 8 & 255, n & 255]; COL.set(hex, c); } return c; };
const lit = (hex, f) => { const c = rgb(hex); return `rgb(${c.map((v) => Math.max(0, Math.min(255, Math.round(f <= 1 ? v * f : v + (255 - v) * (f - 1))))).join(',')})`; };
const norm = (v) => { const l = Math.hypot(...v) || 1; return v.map((x) => x / l); };
const cen = (p) => [0, 1, 2].map((i) => p.reduce((s, q) => s + q[i], 0) / p.length);
const face = (p, n, tag) => ({ p, n: norm(n), c: cen(p), tag });

const axisCoords = (H, r, seg) => { const a = [], b = []; for (let i = 0; i <= seg; i++) { a.push(-H + (r * i) / seg); b.push(H - r + (r * i) / seg); } return a.concat(b); };
const BOXF = [['front', 2, 1, 0, 1], ['back', 2, -1, 0, 1], ['right', 0, 1, 1, 2], ['left', 0, -1, 1, 2], ['top', 1, -1, 0, 2], ['bottom', 1, 1, 0, 2]];
function rbox(w, h, d, r, seg = 3) {
  const H = [w / 2, h / 2, d / 2];
  r = Math.max(0.5, Math.min(r, ...H));
  const C = H.map((x) => axisCoords(x, r, seg)), out = [];
  const vert = (q) => {
    const inn = q.map((v, i) => Math.max(-(H[i] - r), Math.min(H[i] - r, v))), n = norm(q.map((v, i) => v - inn[i]));
    return { p: inn.map((v, i) => v + n[i] * r), n };
  };
  for (const [tag, k, s, a, b] of BOXF) {
    const V = C[a].map((ua) => C[b].map((ub) => { const q = [0, 0, 0]; q[k] = s * H[k]; q[a] = ua; q[b] = ub; return vert(q); }));
    for (let i = 0; i < C[a].length - 1; i++) for (let j = 0; j < C[b].length - 1; j++) {
      const q = [V[i][j], V[i + 1][j], V[i + 1][j + 1], V[i][j + 1]];
      out.push(face(q.map((v) => v.p), [0, 1, 2].map((m) => q.reduce((acc, v) => acc + v.n[m], 0)), tag));
    }
  }
  return out;
}
function lathe(prof, seg = 40) {
  const ring = prof.map(([r, y]) => Array.from({ length: seg }, (_, i) => [Math.cos((i / seg) * TAU) * r, y, Math.sin((i / seg) * TAU) * r]));
  const ys = prof.map((q) => q[1]), mid = (Math.min(...ys) + Math.max(...ys)) / 2, out = [];
  for (let s = 0; s < prof.length - 1; s++) {
    const [r0, y0] = prof[s], [r1, y1] = prof[s + 1];
    let nr = y1 - y0, ny = -(r1 - r0);
    if (nr * ((r0 + r1) / 2) + ny * ((y0 + y1) / 2 - mid) < 0) { nr = -nr; ny = -ny; }
    for (let i = 0; i < seg; i++) {
      const a = ((i + 0.5) / seg) * TAU, j = (i + 1) % seg;
      out.push(face([ring[s][i], ring[s][j], ring[s + 1][j], ring[s + 1][i]], [nr * Math.cos(a), ny, nr * Math.sin(a)], s === 0 ? 'top' : s === prof.length - 2 ? 'bottom' : 'side'));
    }
  }
  return out;
}
const arc = (cx, cy, r, a0, a1, n) => Array.from({ length: n + 1 }, (_, i) => { const a = ((a0 + ((a1 - a0) * i) / n) * Math.PI) / 180; return [cx + r * Math.cos(a), cy + r * Math.sin(a)]; });
const cylProf = (r, h, b) => { b = Math.min(b, r, h / 2); return [[0, -h / 2], [Math.max(0, r - b), -h / 2], ...arc(r - b, -h / 2 + b, b, -90, 0, 5), ...arc(r - b, h / 2 - b, b, 0, 90, 5), [0, h / 2]]; };
const sphProf = (r, n) => arc(0, 0, r, -90, 90, n).map(([a, b]) => [Math.max(0, a), b]);
const capProf = (r, len) => [...arc(0, -len / 2, r, -90, 0, 8).map(([a, b]) => [Math.max(0, a), b]), ...arc(0, len / 2, r, 0, 90, 8).map(([a, b]) => [Math.max(0, a), b])];
function torus(R, r, nu = 48, nv = 18) {
  const P = (th, ph) => [(R + r * Math.cos(ph)) * Math.cos(th), r * Math.sin(ph), (R + r * Math.cos(ph)) * Math.sin(th)];
  const out = [];
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
    const [t0, t1, p0, p1] = [(i / nu) * TAU, ((i + 1) / nu) * TAU, (j / nv) * TAU, ((j + 1) / nv) * TAU], tm = (t0 + t1) / 2, pm = (p0 + p1) / 2;
    out.push(face([P(t0, p0), P(t1, p0), P(t1, p1), P(t0, p1)], [Math.cos(pm) * Math.cos(tm), Math.sin(pm), Math.cos(pm) * Math.sin(tm)], 'side'));
  }
  return out;
}
function extrude(pts, d) {
  const m = cen(pts.map(([x, y]) => [x, y, 0])), out = [], n = pts.length;
  out.push(face(pts.map(([x, y]) => [x, y, d / 2]), [0, 0, 1], 'front'), face(pts.map(([x, y]) => [x, y, -d / 2]).reverse(), [0, 0, -1], 'back'));
  for (let i = 0; i < n; i++) {
    const [a, b] = [pts[i], pts[(i + 1) % n]];
    let nx = b[1] - a[1], ny = -(b[0] - a[0]);
    if (nx * ((a[0] + b[0]) / 2 - m[0]) + ny * ((a[1] + b[1]) / 2 - m[1]) < 0) { nx = -nx; ny = -ny; }
    out.push(face([[a[0], a[1], d / 2], [b[0], b[1], d / 2], [b[0], b[1], -d / 2], [a[0], a[1], -d / 2]], [nx, ny, 0], 'side'));
  }
  return out;
}
const ARGN = ['w', 'h', 'd', 'r', 'b', 'len', 'R'];
function build(part, pg) {
  const A = (n, d) => pg(n, part[n] ?? d), seg = part.seg;
  const v = Object.fromEntries(ARGN.map((n) => [n, A(n, n === 'b' ? 8 : n === 'r' ? 12 : 100)]));
  const key = JSON.stringify([part.prim, ARGN.map((n) => +v[n].toFixed(1)), seg, part.pts ? part.pts.length + ':' + part.pts[1] : 0]);
  let g = GEO.get(key);
  if (g) return g;
  switch (part.prim) {
    case 'cyl': g = lathe(cylProf(v.r, v.h, v.b), seg || 64); break;
    case 'sphere': g = lathe(sphProf(v.r, 30), seg || 72); break;
    case 'cone': g = lathe([[0, -v.h / 2], [v.r, v.h / 2], [0, v.h / 2]], seg || 40); break;
    case 'capsule': g = lathe(capProf(v.r, v.len), seg || 48); break;
    case 'gem': g = lathe([[0, -v.h / 2], [v.r * 0.55, -v.h / 2], [v.r, -v.h * 0.14], [v.r, -v.h * 0.08], [0, v.h / 2]], seg || 8); break;
    case 'torus': g = torus(v.R, v.r, seg || 72, 28); break;
    case 'extrude': g = extrude(part.pts, v.d); break;
    default: g = rbox(v.w, v.h, v.d, v.r, seg || 3);
  }
  if (GEO.size > 300) GEO.clear();
  GEO.set(key, g);
  return g;
}
const DYN_DEF = { w: 900, h: 100, d: 700, r: 200, R: 220, amp: 90, len: 700 };
const dynCache = new Map();
function dynFaces(part, pg, t) {
  const v = { ...part };
  for (const n of Object.keys(DYN_DEF)) v[n] = pg(n, part[n] ?? DYN_DEF[n]);
  if (part.prim === 'blob') v.amp = pg('amp', part.amp ?? 0.22);
  const ph = pg('ph', t * (part.speed ?? 1));
  if (!STATIC_DYN.has(part.prim)) return DYN[part.prim](v, ph);
  const key = JSON.stringify([part.prim, v.R, v.r, v.h, v.p, v.q, v.turns, v.seg]);
  let g = dynCache.get(key);
  if (!g) { if (dynCache.size > 40) dynCache.clear(); g = DYN[part.prim](v, ph); dynCache.set(key, g); }
  return g;
}
const SCREEN = { front: [[0, 0, 1], [1, 0, 0], [0, 1, 0]], back: [[0, 0, -1], [-1, 0, 0], [0, 1, 0]], right: [[1, 0, 0], [0, 0, -1], [0, 1, 0]], left: [[-1, 0, 0], [0, 0, 1], [0, 1, 0]], top: [[0, -1, 0], [1, 0, 0], [0, 0, 1]] };
const getter = (tracks, t) => (n, d) => { const v = val(tracks[n], t); return v === null ? d : v; };

export function drawMesh(ctx, el, g, t, drawText) {
  const proj = makeProj(g('rx', el.rx || 0), g('ry', el.ry || 0), g('rz', el.rz || 0), el.persp || 1800), R = proj.rot, persp = proj.persp;
  const L1 = norm(el.light || [-0.45, -0.7, 0.55]), L2 = norm([0.7, 0.25, 0.45]), HV = norm([L1[0], L1[1], L1[2] + 1]), toon = el.toon || 0;
  const list = [];
  for (const part of el.parts || []) {
    const pg = getter(part.tracks || {}, t), po = pg('opacity', 1);
    if (po <= 0) continue;
    const pos = [pg('x', part.pos ? part.pos[0] : 0), pg('y', part.pos ? part.pos[1] : 0), pg('z', part.pos ? part.pos[2] : 0)], s = pg('s', part.s ?? 1);
    const PR = makeProj(pg('rx', part.rot ? part.rot[0] : 0), pg('ry', part.rot ? part.rot[1] : 0), pg('rz', part.rot ? part.rot[2] : 0), 1e9).rot;
    const xf = (v) => { const a = PR(v[0] * s, v[1] * s, v[2] * s); return R(a[0] + pos[0], a[1] + pos[1], a[2] + pos[2]); };
    const nf = (n) => R(...PR(...n));
    const facing = (nr, cr) => nr[0] * -cr[0] + nr[1] * -cr[1] + nr[2] * (persp - cr[2]) > 0;
    const prj = (r) => { const k = persp / Math.max(60, persp - r[2]); return [r[0] * k, r[1] * k]; };
    const faces = DYN[part.prim] ? dynFaces(part, pg, t) : build(part, pg);
    for (const f of faces) {
      const nr = nf(f.n), cr = xf(f.c);
      if (!part.both && !facing(nr, cr)) continue;
      const nz = part.both && nr[2] < 0 ? -1 : 1, d1 = Math.max(0, nz * (nr[0] * L1[0] + nr[1] * L1[1] + nr[2] * L1[2])), d2 = Math.max(0, nz * (nr[0] * L2[0] + nr[1] * L2[1] + nr[2] * L2[2]));
      let lum = 0.5 + 0.56 * d1 + 0.16 * d2;
      if (el.hemi) lum += el.hemi * (-nr[1]) * 0.3;
      if (part.ao && f.u !== undefined) lum *= 1 - part.ao + part.ao * (0.35 + 0.65 * f.u);
      if (el.rim) lum += Math.pow(1 - Math.min(1, Math.abs(nr[2])), 3) * el.rim;
      if (part.gloss) lum += Math.pow(Math.max(0, nr[0] * HV[0] + nr[1] * HV[1] + nr[2] * HV[2]), part.gloss) * 0.42;
      if (toon) lum = Math.round(lum * toon) / toon;
      list.push({ z: cr[2], pts: f.p.map((v) => prj(xf(v))), col: lit((part.ramp && f.u !== undefined && ramp(part.ramp, part.cycle ? (f.u * part.cycle) % 1 : f.u)) || (part.faces && part.faces[f.tag]) || part.color || el.color || '#FF6A45', lum), a: po });
    }
    for (const sc of part.screen ? [].concat(part.screen) : []) {
      const [n, u, v] = SCREEN[sc.face || 'front'], half = [(part.w || 100) / 2, (part.h || 100) / 2, (part.d || 100) / 2];
      const dims = n[2] ? [part.w, part.h] : n[0] ? [part.d, part.h] : [part.w, part.d];
      const sw = sc.w || dims[0] * 0.92, sh = sc.h || dims[1] * 0.94, c0 = n.map((q, i) => q * (half[i] + 0.4));
      const cc = c0.map((q, i) => q + (sc.ox || 0) * u[i] + (sc.oy || 0) * v[i]);
      const cr = xf(cc);
      if (facing(nf(n), cr)) {
        const pt = (a, b) => prj(xf(cc.map((q, i) => q + u[i] * (a - 0.5) * sw + v[i] * (b - 0.5) * sh)));
        list.push({ z: cr[2] + 0.5, a: po, tex: { sc, sw, sh }, pt });
      }
    }
  }
  list.sort((a, b) => a.z - b.z);
  const base = ctx.globalAlpha;
  for (const f of list) {
    ctx.globalAlpha = base * f.a;
    if (f.tex) {
      const { sc, sw, sh } = f.tex, ts = Math.min(1, 1100 / Math.max(sw, sh)), tex = scratch(Math.round(sw * ts), Math.round(sh * ts)), c2 = tex.getContext('2d');
      c2.save(); c2.scale(ts, ts); c2.translate(sw / 2, sh / 2);
      c2.beginPath(); c2.roundRect(-sw / 2, -sh / 2, sw, sh, sc.r || 0); c2.clip();
      c2.fillStyle = sc.bg || '#F6EFE3'; c2.fillRect(-sw / 2, -sh / 2, sw, sh);
      drawFlat(c2, sc.items || [], t, drawText);
      c2.restore();
      texQuad(ctx, tex, f.pt, sc.n || 5);
    } else {
      ctx.fillStyle = f.col; ctx.strokeStyle = f.col; ctx.lineWidth = 1.5; ctx.lineJoin = 'round';
      ctx.beginPath(); f.pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.closePath(); ctx.fill(); ctx.stroke();
    }
  }
  ctx.globalAlpha = base;
}
