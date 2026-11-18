// motionvid media layer: real photos (kind 'image') and real footage (kind 'video' = a folder of 15 fps jpg frames) drawn by the same engine
// in the browser and in Node. Flat solid look is kept: a tint is a flat color wash, never a gradient.
import { val } from './ease.js';

const cache = new Map();
export const assets = { base: '', loader: null, makeCanvas: null };
if (typeof Image !== 'undefined') {
  assets.loader = (src) => new Promise((res, rej) => { const i = new Image(); i.onload = () => res(i); i.onerror = rej; i.src = assets.base + src; });
}
export function load(src) {
  let e = cache.get(src);
  if (!e) {
    e = { img: null, p: null };
    cache.set(src, e);
    e.p = assets.loader ? assets.loader(src).then((i) => { e.img = i; return i; }, () => null) : Promise.resolve(null);
  }
  return e;
}
export const getImg = (src) => load(src).img;
export const whenLoaded = (src) => load(src).p;
export const evictFootage = (keep) => { for (const s of [...cache.keys()]) if (s.includes('/footage/') && !keep.has(s)) cache.delete(s); };
export function mkCanvas(w, h) {
  if (assets.makeCanvas) return assets.makeCanvas(w, h);
  const c = document.createElement('canvas'); c.width = w; c.height = h; return c;
}
const pool = new Map();
export function scratch(w, h) {  // reusable texture canvas per size
  const k = `${w}x${h}`;
  if (!pool.has(k)) pool.set(k, mkCanvas(w, h));
  const c = pool.get(k); c.getContext('2d').clearRect(0, 0, w, h); return c;
}

// footage frame names for time t: [frame A, frame B, blend]; loop: 'pp' ping-pong | 'wrap' | clamp (default)
export function vidFrame(c, t) {
  const fps = c.fps || 15, n = c.n, u = Math.max(0, (t - (c.t0 || 0)) * fps + (c.ss || 0) * fps), i = Math.floor(u);
  const idx = (j) => (c.loop === 'wrap' ? j % n : c.loop === 'pp' ? ((m) => (m < n ? m : 2 * n - 2 - m))(j % (2 * n - 2)) : Math.min(n - 1, j));
  const nm = (j) => `${c.dir}/f${String(idx(j) + 1).padStart(3, '0')}.jpg`;
  return [nm(i), nm(i + 1), u - i];
}

// every image file the frame at time t needs (Node prefetch; blur sub-frames pass several t)
export function collect(node, t, out = new Set()) {
  const list = Array.isArray(node) ? node : [node];
  for (const c of list) {
    if (!c) continue;
    const o = c.tracks && c.tracks.opacity ? val(c.tracks.opacity, t) : 1;
    if (o !== null && o <= 0) continue;
    if (c.kind === 'image' && c.src) out.add(c.src);
    if (c.kind === 'video') { const f = vidFrame(c, t); out.add(f[0]); if (f[2] > 0.001) out.add(f[1]); }
    if (c.items) collect(c.items, t, out);
    if (c.parts) for (const p of c.parts) for (const sc of p.screen ? [].concat(p.screen) : []) collect(sc.items, t, out);
  }
  return out;
}

function fit(ctx, im, w, h, zoom, px, py, a) {
  const s = Math.max(w / im.width, h / im.height) * zoom, dw = im.width * s, dh = im.height * s;
  ctx.save(); ctx.globalAlpha *= a;
  ctx.drawImage(im, -dw / 2 - ((dw - w) / 2) * px, -dh / 2 - ((dh - h) / 2) * py, dw, dh);
  ctx.restore();
}

// Draw an image/video item centred at (0,0): size w x h, radius r, Ken Burns via zoom/px/py tracks, optional flat tint.
export function drawMedia(ctx, c, cg, t) {
  const w = cg('w', c.w || 400), h = cg('h', c.h ?? w), rr = c.r === 'pill' ? Math.min(w, h) / 2 : cg('r', c.r || 0);
  const zoom = cg('zoom', 1), px = cg('px', 0), py = cg('py', 0);
  const f = c.kind === 'video' ? vidFrame(c, t) : [c.src, null, 0];
  ctx.save();
  ctx.beginPath(); ctx.roundRect(-w / 2, -h / 2, w, h, Math.max(0, Math.min(rr, w / 2, h / 2))); ctx.clip();
  const a = f[0] && getImg(f[0]), b = f[1] && f[2] > 0.001 ? getImg(f[1]) : null;
  if (a) { fit(ctx, a, w, h, zoom, px, py, 1); if (b) fit(ctx, b, w, h, zoom, px, py, f[2]); }
  else { ctx.fillStyle = c.color || '#E9DCC3'; ctx.fillRect(-w / 2, -h / 2, w, h); }
  const ta = cg('tintA', c.tintA || 0);
  if (c.tint && ta > 0) { ctx.globalAlpha *= ta; ctx.fillStyle = c.tint; ctx.fillRect(-w / 2, -h / 2, w, h); }
  ctx.restore();
}

function tri(ctx, tex, s, d) {
  const [[u0, v0], [u1, v1], [u2, v2]] = s, [[x0, y0], [x1, y1], [x2, y2]] = d;
  const D = u0 * (v1 - v2) + u1 * (v2 - v0) + u2 * (v0 - v1);
  if (Math.abs(D) < 1e-9) return;
  const a = (x0 * (v1 - v2) + x1 * (v2 - v0) + x2 * (v0 - v1)) / D, b = (y0 * (v1 - v2) + y1 * (v2 - v0) + y2 * (v0 - v1)) / D;
  const c = (x0 * (u2 - u1) + x1 * (u0 - u2) + x2 * (u1 - u0)) / D, dd = (y0 * (u2 - u1) + y1 * (u0 - u2) + y2 * (u1 - u0)) / D;
  const e = (x0 * (u1 * v2 - u2 * v1) + x1 * (u2 * v0 - u0 * v2) + x2 * (u0 * v1 - u1 * v0)) / D;
  const f = (y0 * (u1 * v2 - u2 * v1) + y1 * (u2 * v0 - u0 * v2) + y2 * (u0 * v1 - u1 * v0)) / D;
  const cx = (x0 + x1 + x2) / 3, cy = (y0 + y1 + y2) / 3;
  ctx.save(); ctx.beginPath();
  [[x0, y0], [x1, y1], [x2, y2]].forEach(([x, y], i) => { const dx = x - cx, dy = y - cy, l = Math.hypot(dx, dy) || 1; ctx[i ? 'lineTo' : 'moveTo'](x + (dx / l) * 1.6, y + (dy / l) * 1.6); });
  ctx.closePath(); ctx.clip(); ctx.transform(a, b, c, dd, e, f); ctx.drawImage(tex, 0, 0); ctx.restore();
}

// Perspective-correct-ish texture mapping: pt(u, v) projects the surface point at u,v in [0,1]; the quad is split into n x n affine triangles.
export function texQuad(ctx, tex, pt, n = 8) {
  const W = tex.width, H = tex.height, g = [];
  for (let j = 0; j <= n; j++) for (let i = 0; i <= n; i++) g.push(pt(i / n, j / n));
  const at = (i, j) => g[j * (n + 1) + i];
  for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
    const s = (a, b) => [(a / n) * W, (b / n) * H];
    tri(ctx, tex, [s(i, j), s(i + 1, j), s(i, j + 1)], [at(i, j), at(i + 1, j), at(i, j + 1)]);
    tri(ctx, tex, [s(i + 1, j), s(i + 1, j + 1), s(i, j + 1)], [at(i + 1, j), at(i + 1, j + 1), at(i, j + 1)]);
  }
}
