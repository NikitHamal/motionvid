// motionvid 3D layer: perspective groups (UI planes with depth), box3d solids, spheres, paths. Flat shading only: no shadows, no gradients.
import { val } from './ease.js';

const D2R = Math.PI / 180;
const clamp01 = (x) => Math.max(0, Math.min(1, x));

export function shade(hex, f) {
  const n = parseInt((hex || '#17130F').slice(1), 16), c = [n >> 16 & 255, n >> 8 & 255, n & 255];
  const o = c.map((v) => Math.round(f <= 1 ? v * f : v + (255 - v) * (f - 1)));
  return `rgb(${o[0]},${o[1]},${o[2]})`;
}

export function makeProj(rx, ry, rz, persp = 1800) {
  const [sa, ca, sb, cb, sc, cc] = [Math.sin(rx * D2R), Math.cos(rx * D2R), Math.sin(ry * D2R), Math.cos(ry * D2R), Math.sin(rz * D2R), Math.cos(rz * D2R)];
  const rot = (x, y, z) => {
    const x1 = x * cc - y * sc, y1 = x * sc + y * cc;
    const x2 = x1 * cb + z * sb, z2 = -x1 * sb + z * cb;
    return [x2, y1 * ca - z2 * sa, y1 * sa + z2 * ca];
  };
  const P = (x, y, z) => {
    const [a, b, c] = rot(x, y, z);
    const s = persp / Math.max(60, persp - c);
    return [a * s, b * s, s, c];
  };
  return { rot, P, persp };
}
const FLAT = { P: (x, y, z) => [x, y, 1, z], rot: (x, y, z) => [x, y, z], persp: 1e9 };

const poly = (ctx, pts) => {
  ctx.beginPath();
  pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1])));
  ctx.closePath();
};

function rrPts(w, h, r, seg = 8) {
  r = Math.max(0, Math.min(r, w / 2, h / 2));
  const out = [];
  for (const [cx, cy, a0] of [[w / 2 - r, -h / 2 + r, -90], [w / 2 - r, h / 2 - r, 0], [-w / 2 + r, h / 2 - r, 90], [-w / 2 + r, -h / 2 + r, 180]]) {
    for (let i = 0; i <= seg; i++) { const a = (a0 + (90 * i) / seg) * D2R; out.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
  }
  return out;
}
const ellPts = (rx, ry, a0 = 0, a1 = 360, n = 64) => Array.from({ length: n + 1 }, (_, i) => { const a = (a0 + ((a1 - a0) * i) / n) * D2R; return [Math.cos(a) * rx, Math.sin(a) * ry]; });
const blobPts = (R, n, amp) => Array.from({ length: 121 }, (_, i) => { const a = (i / 120) * Math.PI * 2, r = R * (1 + amp * Math.cos(n * a)); return [Math.cos(a) * r, Math.sin(a) * r]; });

function trim(pts, p) {
  if (p >= 1) return pts;
  const seg = pts.slice(1).map((q, i) => Math.hypot(q[0] - pts[i][0], q[1] - pts[i][1]));
  let left = seg.reduce((a, b) => a + b, 0) * Math.max(0, p);
  const out = [pts[0]];
  for (let i = 0; i < seg.length && left > 0; i++) {
    const f = Math.min(1, left / (seg[i] || 1));
    out.push([pts[i][0] + (pts[i + 1][0] - pts[i][0]) * f, pts[i][1] + (pts[i + 1][1] - pts[i][1]) * f]);
    left -= seg[i];
  }
  return out;
}

// One item (a group child, a box face item, or a top-level shape when `local`). cg reads this item's tracks at time t.
export function drawItem(ctx, c, cg, t, proj, local, drawText, lum = 1) {
  const op = clamp01(cg('opacity', 1));
  const sc = local ? 1 : cg('scale', 1);
  if (op <= 0 || sc <= 0) return;
  const x = local ? 0 : cg('x', 0), y = local ? 0 : cg('y', 0), z = cg('z', c.z || 0), rot = local ? 0 : cg('rotation', 0) * D2R;
  const w = cg('w', c.w || 100), h = cg('h', c.h ?? w), { P } = proj;
  const [cs, sn] = [Math.cos(rot), Math.sin(rot)];
  const map = (pts, dz = 0) => pts.map(([a, b]) => P((a * cs - b * sn) * sc + x, (a * sn + b * cs) * sc + y, z + dz));
  const avg = P(x, y, z)[2];
  const col = lum === 1 ? c.color : shade(c.color, lum);
  const prevA = ctx.globalAlpha;
  ctx.globalAlpha = prevA * op;
  ctx.fillStyle = col; ctx.strokeStyle = col;
  ctx.lineJoin = 'round'; ctx.lineCap = 'round';
  const k = c.kind;
  if (k === 'rrect') {
    const outline = rrPts(w, h, c.r === 'pill' ? Math.min(w, h) / 2 : cg('r', c.r || 0), c.r === 'pill' || (c.r || 0) > 40 ? 12 : 6);
    for (let i = c.ext || 0; i > 0; i -= 2) { ctx.fillStyle = shade(c.color, 0.66 * lum); poly(ctx, map(outline, -i)); ctx.fill(); }
    ctx.fillStyle = col; poly(ctx, map(outline)); ctx.fill();
    if (c.stroke) { ctx.lineWidth = c.stroke * sc * avg; ctx.strokeStyle = c.line || col; poly(ctx, map(outline)); ctx.stroke(); }
  } else if (k === 'circle' || k === 'ring') {
    const sw = k === 'ring' ? cg('sweep', 1) : 1;
    const pts = map(ellPts(w / 2, h / 2, -90, -90 + 360 * Math.max(0.0001, sw)));
    if (k === 'ring') { ctx.lineWidth = cg('stroke', c.stroke || 12) * sc * avg; ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke(); }
    else { poly(ctx, pts); ctx.fill(); }
  } else if (k === 'sphere') {
    const [px, py, s] = P(x, y, z), R = (w / 2) * sc * s;
    ctx.fillStyle = shade(c.color, 0.78); ctx.beginPath(); ctx.arc(px, py, R, 0, Math.PI * 2); ctx.fill();
    ctx.save(); ctx.clip();
    ctx.fillStyle = shade(c.color, 1.0); ctx.beginPath(); ctx.arc(px - R * 0.14, py - R * 0.18, R * 0.88, 0, Math.PI * 2); ctx.fill();
    ctx.fillStyle = shade(c.color, 1.22); ctx.beginPath(); ctx.arc(px - R * 0.28, py - R * 0.34, R * 0.52, 0, Math.PI * 2); ctx.fill();
    ctx.restore();
    ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.beginPath(); ctx.arc(px - R * 0.38, py - R * 0.44, R * 0.1, 0, Math.PI * 2); ctx.fill();
  } else if (k === 'blob') {
    poly(ctx, map(blobPts(w / 2, c.n || 8, cg('amp', c.amp ?? 0.08)))); ctx.fill();
  } else if (k === 'poly') {
    poly(ctx, map(c.pts)); ctx.fill();
  } else if (k === 'path') {
    const pts = map(trim(c.pts, cg('p', 1)));
    if (pts.length > 1) { ctx.lineWidth = cg('stroke', c.stroke || 10) * sc * avg; ctx.beginPath(); pts.forEach((p, i) => (i ? ctx.lineTo(p[0], p[1]) : ctx.moveTo(p[0], p[1]))); ctx.stroke(); }
  } else if (k === 'text') {
    const p0 = P(x, y, z), px = P(x + cs, y + sn, z), py = P(x - sn, y + cs, z);
    ctx.save();
    ctx.transform(px[0] - p0[0], px[1] - p0[1], py[0] - p0[0], py[1] - p0[1], p0[0], p0[1]);
    ctx.scale(sc, sc);
    drawText(ctx, c, cg, t);
    ctx.restore();
  }
  ctx.globalAlpha = prevA;
}

const getter = (tracks, t) => (n, d) => { const v = val(tracks[n], t); return v === null ? d : v; };

// A group is a UI plane: children live in local px around the group centre; rx/ry tilt it in perspective, child z gives depth.
export function drawGroup(ctx, el, g, t, drawText) {
  const proj = makeProj(g('rx', el.rx || 0), g('ry', el.ry || 0), 0, el.persp || 1800);
  const lum = el.shade === false ? 1 : 0.84 + 0.16 * Math.max(0, proj.rot(0, 0, 1)[2]);
  const items = (el.items || []).map((c) => { const cg = getter(c.tracks || {}, t); return { c, cg, z: proj.P(cg('x', 0), cg('y', 0), cg('z', c.z || 0))[3] }; });
  items.sort((a, b) => a.z - b.z);
  for (const it of items) drawItem(ctx, it.c, it.cg, t, proj, false, drawText, lum);
}

const FACES = [
  [[0, 0, 1], [[-1, -1, 1], [1, -1, 1], [1, 1, 1], [-1, 1, 1]]], [[0, 0, -1], [[1, -1, -1], [-1, -1, -1], [-1, 1, -1], [1, 1, -1]]],
  [[1, 0, 0], [[1, -1, 1], [1, -1, -1], [1, 1, -1], [1, 1, 1]]], [[-1, 0, 0], [[-1, -1, -1], [-1, -1, 1], [-1, 1, 1], [-1, 1, -1]]],
  [[0, -1, 0], [[-1, -1, -1], [1, -1, -1], [1, -1, 1], [-1, -1, 1]]], [[0, 1, 0], [[-1, 1, 1], [1, 1, 1], [1, 1, -1], [-1, 1, -1]]],
];
const LIGHT = (() => { const l = [-0.42, -0.74, 0.52], m = Math.hypot(...l); return l.map((v) => v / m); })();

export function drawBox(ctx, el, g, t, drawText) {
  const [w, h, d] = [g('w', el.w || 200), g('h', el.h || el.w || 200), g('d', el.d || el.w || 200)];
  const proj = makeProj(g('rx', el.rx || 0), g('ry', el.ry || 0), g('rz', el.rz || 0), el.persp || 1800);
  const names = ['front', 'back', 'right', 'left', 'top', 'bottom'];
  const vis = [];
  FACES.forEach(([n, quad], i) => {
    const nr = proj.rot(...n), cen = proj.rot(n[0] * w / 2, n[1] * h / 2, n[2] * d / 2);
    if (nr[0] * -cen[0] + nr[1] * -cen[1] + nr[2] * (proj.persp - cen[2]) <= 0) return;
    const lum = 0.56 + 0.44 * Math.max(0, nr[0] * LIGHT[0] + nr[1] * LIGHT[1] + nr[2] * LIGHT[2]);
    vis.push({ i, z: cen[2], lum, pts: quad.map(([a, b, c]) => proj.P((a * w) / 2, (b * h) / 2, (c * d) / 2)) });
  });
  vis.sort((a, b) => a.z - b.z);
  for (const f of vis) {
    const col = shade((el.faces && el.faces[names[f.i]]) || el.color || '#FF6A45', f.lum);
    ctx.fillStyle = col; ctx.strokeStyle = col; ctx.lineWidth = 1.5; ctx.lineJoin = 'round';
    poly(ctx, f.pts); ctx.fill(); ctx.stroke();
  }
  if (el.items && vis.some((f) => f.i === 0)) {
    const lum = vis.find((f) => f.i === 0).lum;
    for (const c of el.items) drawItem(ctx, { ...c, z: d / 2 + 0.5 }, getter(c.tracks || {}, t), t, proj, false, drawText, 1 + (lum - 1) * 0.5);
  }
}

export const drawLocal = (ctx, el, g, t, drawText) => drawItem(ctx, el, g, t, FLAT, true, drawText);
