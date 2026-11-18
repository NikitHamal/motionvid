// JS twin of the Python kit's mesh + screens (src/motionvid/kit/mesh.py, screens.py): 3D parts, ready objects and real UI screens for the browser planner.
import { PAL, item, text, pill, k, put } from './kit.js';

const TRK = ['x', 'y', 'z', 'rx', 'ry', 'rz', 's', 'opacity', 'w', 'h', 'd', 'r', 'b', 'len', 'R'], AX = ['x', 'y', 'z'], RT = ['rx', 'ry', 'rz'];
export function part(prim, color, o = {}) {
  const out = { prim, pos: [0, 0, 0], rot: [0, 0, 0] }, tr = {};
  if (color) out.color = PAL[color] || color;
  for (const [n, v] of Object.entries(o)) {
    if (Array.isArray(v) && TRK.includes(n)) tr[n] = v.map((f) => k(...f));
    else if (n === 'pos' || n === 'rot') out[n] = [...v];
    else if (AX.includes(n) && typeof v === 'number') out.pos[AX.indexOf(n)] = v;
    else if (RT.includes(n) && typeof v === 'number') out.rot[RT.indexOf(n)] = v;
    else if (n === 'ramp') out.ramp = v.map((c) => PAL[c] || c);
    else if (n === 'faces') out.faces = Object.fromEntries(Object.entries(v).map(([a, b]) => [a, PAL[b] || b]));
    else out[n] = v;
  }
  if (Object.keys(tr).length) out.tracks = tr;
  return out;
}
export function mesh(S, id, t, x, y, parts, size, o = {}) {
  const el = S.add(id, 'mesh', null, { x, y, w: size, h: size, rx: -12, ry: 0, persp: 1800, ...o, parts });
  return t === null ? el : S.appear(el, t, { frm: 0.7, x });
}
export const spin = (t0, t1, a, b) => [[t0, a], [t1, b, 'inOutSine']];
export const photo = (n, w, h, r, t0 = 0, o = {}) => item('image', null, { src: `media/assets/${n}.jpg`, w, h, r, zoom: [[t0, 1], [t0 + 9, 1.2, 'inOutSine']], ...o });

export const phone3d = (items, w = 420, h = 860) => [part('rbox', 'ink', { w, h, d: 46, r: w * 0.14, seg: 4, gloss: 16, screen: { items, w: w * 0.93, h: h * 0.955, r: w * 0.115, bg: PAL.cream } })];
export function laptop3d(items, w = 900) {
  const lh = w * 0.62, bd = w * 0.66, bh = 26, a = 14 * Math.PI / 180, dy = lh * 0.36;
  return [part('rbox', 'sand', { w: w * 1.04, h: bh, d: bd, r: 12, seg: 3, gloss: 10, y: dy }), part('rbox', 'ink', { w: w * 0.84, h: 3, d: bd * 0.46, r: 1.4, pos: [0, -bh / 2 - 1 + dy, bd * 0.08] }),
    part('rbox', 'sand', { w: w, h: lh, d: 20, r: 14, seg: 3, gloss: 12, rx: 14, pos: [0, -bh / 2 - (lh / 2) * Math.cos(a) + dy, -bd / 2 - (lh / 2) * Math.sin(a)], screen: { items, w: w * 0.94, h: lh * 0.92, r: 12, bg: PAL.cream } })];
}
export const bars3d = (vals, t0, wt, hm, cols, d = 120) => vals.map((v, i) => { const bw = wt / (vals.length + (vals.length - 1) * 0.5), hh = hm * v, ti = t0 + i * 0.12;
  return part('rbox', cols[i % cols.length], { w: bw, d, r: 18, seg: 3, gloss: 10, pos: [-wt / 2 + bw / 2 + i * bw * 1.5, 0, 0], h: [[ti, 4], [ti + 0.9, hh, 'spring']], y: [[ti, hm / 2 - 2], [ti + 0.9, hm / 2 - hh / 2, 'spring']] }); });
export const globe = (r, core = 'moss', ring = 'butter') => [part('sphere', core, { r, gloss: 14 }), ...[0, 1, 2, 3, 4].map((i) => part('torus', ring, { R: r * 1.02, r: 3.2, seg: 64, rz: 90, ry: i * 36 })), part('torus', ring, { R: r * 1.02, r: 3.2, seg: 64 })];
export const coins = (t0, r, cols) => cols.map((c, i) => part('cyl', c, { r, h: r * 0.25, b: r * 0.1, gloss: 24, y: [[t0 + i * 0.3, -r * 5], [t0 + 0.7 + i * 0.3, r * 0.45 - i * r * 0.28, 'spring']] }));
export const torusRings = (t0, R, cols) => [...cols.map((c, i) => part('torus', c, { R: R * (1 - i * 0.26), r: R * 0.12, seg: 64, gloss: 18, rx: [[t0, 90], [t0 + 8, 90 + 40 * (i + 1), 'inOutSine']], rz: [[t0, 0], [t0 + 8, 120 - 40 * i, 'inOutSine']] })), part('sphere', 'butter', { r: R * 0.24, gloss: 26 })];
export function cubePhotos(size, names, body = 'ink') {
  const scr = Object.entries(names).map(([face, n]) => ({ face, items: [photo(n, size * 0.9, size * 0.9, 16)], w: size * 0.9, h: size * 0.9, r: 16, bg: PAL.sand }));
  return [part('rbox', body, { w: size, h: size, d: size, r: size * 0.07, seg: 4, gloss: 10, screen: scr })];
}
export const rack = (w = 300, units = 5) => [part('rbox', 'sand', { w: w + 40, h: units * 70 + 30, d: w * 0.8, r: 18, seg: 3 }), ...Array.from({ length: units }, (_, i) => part('rbox', 'ink', { w, h: 62, d: w * 0.86, r: 10, gloss: 10, pos: [0, -units * 35 + 39 + i * 70, w * 0.06] }))];
export function orbit(fn, n, radius, t0, t1, turns = 1, faceOut = false) {
  return Array.from({ length: n }, (_, i) => {
    const p = fn(i), xs = [], zs = [], ys = [];
    for (let j = 0; j <= 24; j++) { const a = 2 * Math.PI * (i / n + (turns * j) / 24), tt = t0 + ((t1 - t0) * j) / 24; xs.push(k(tt, radius * Math.cos(a))); zs.push(k(tt, radius * Math.sin(a))); ys.push(k(tt, 90 - (a * 180) / Math.PI)); }
    p.tracks = { ...(p.tracks || {}), x: xs, z: zs, ...(faceOut ? { ry: ys } : {}) };
    return p;
  });
}

const rise = (it, t, dy = 34) => { const y = it.tracks?.y?.[0]?.v ?? 0; it.tracks = { ...(it.tracks || {}), y: [k(0, y + dy), k(t, y + dy), k(t + 0.65, y, 'm3Dec')] }; put(it, 'opacity', [[0, 0], [t, 0], [t + 0.25, 1]]); return it; };
const z = (it, v) => ({ ...it, z: v });
// Real UI screens (flat items centred on 0,0)
export function screen(kind, S, w, h, t0, o = {}) {
  const T = -h / 2, c = o.photos || ['beach', 'palms', 'shore'], ink = 'ink', out = [];
  if (kind === 'dash') {
    out.push(z(item('rrect', o.accent || 'moss', { w: w * 0.17, h, r: 0, x: -w * 0.415 }), 1), z(text('Revenue', ink, h * 0.055, -w * 0.18, T + h * 0.09, { weight: 800, align: 'left' }), 2));
    [['MRR', 84.2, 'k'], ['Users', 12.4, 'k'], ['Churn', 1.8, '%']].forEach(([lab, v, suf], i) => {
      const cx = -w * 0.19 + i * w * 0.245, n = item('text', ink, { size: h * 0.07, weight: 800, x: cx, y: T + h * 0.31, fmt: { pre: '', suf, dec: 1 }, num: [[t0 + 0.6 + i * 0.2, 0], [t0 + 2.4 + i * 0.2, v, 'm3Dec']] });
      out.push(z(item('rrect', 'white', { w: w * 0.225, h: h * 0.2, r: h * 0.04, x: cx, y: T + h * 0.27 }), 1), z(text(lab, ink, h * 0.032, cx - w * 0.09, T + h * 0.22, { weight: 600, align: 'left' }), 2), z(n, 2));
      S.count(n, t0 + 0.6 + i * 0.2, t0 + 2.4 + i * 0.2, 0, v, 5);
    });
    [0.3, 0.45, 0.4, 0.62, 0.55, 0.78, 0.7, 0.92].forEach((v, i) => { const bh = h * 0.3 * v, ti = t0 + 1.4 + i * 0.09; out.push(z(item('rrect', i === 7 ? 'butter' : o.accent || 'moss', { w: w * 0.05, r: w * 0.015, x: -w * 0.26 + i * w * 0.083, h: [[ti, 0], [ti + 0.7, bh, 'spring']], y: [[ti, T + h * 0.84], [ti + 0.7, T + h * 0.84 - bh / 2, 'spring']] }), 2)); });
  } else if (kind === 'activity') {
    [['lime', 1, 0.82], ['coral', 0.74, 0.64], ['butter', 0.48, 0.9]].forEach(([col, f, to], i) => { const d = w * 0.7 * f; out.push(z(item('ring', 'sand', { w: d, stroke: h * 0.03, y: T + h * 0.36 }), 1), z(item('ring', col, { w: d, stroke: h * 0.03, y: T + h * 0.36, sweep: [[t0 + 0.6 + i * 0.25, 0.001], [t0 + 2.4 + i * 0.25, to, 'm3Dec']], opacity: [[t0 + 0.55, 0], [t0 + 0.6, 1]] }), 2)); });
    const n = item('text', ink, { size: h * 0.075, weight: 800, y: T + h * 0.36, fmt: { pre: '', suf: '', dec: 0 }, num: [[t0 + 0.8, 0], [t0 + 3, 12480, 'm3Dec']] }); out.push(z(n, 3)); S.count(n, t0 + 0.8, t0 + 3, 0, 12480, 8);
    [0.4, 0.62, 0.5, 0.85, 0.7, 0.95, 0.58].forEach((v, i) => { const bh = h * 0.16 * v, ti = t0 + 1.6 + i * 0.1; out.push(z(item('rrect', i === 5 ? 'lime' : 'sand', { w: w * 0.085, r: w * 0.03, x: (i - 3) * w * 0.125, h: [[ti, 0], [ti + 0.7, bh, 'spring']], y: [[ti, T + h * 0.82], [ti + 0.7, T + h * 0.82 - bh / 2, 'spring']] }), 2)); });
  } else if (kind === 'code') {
    out.push(z(item('rrect', '#262019', { w, h, r: 24 }), 0), z(item('rrect', '#3A3229', { w, h: h * 0.1, r: 0, y: T + h * 0.05 }), 1));
    const COL = { kw: '#FF6A45', fn: '#C9F13B', str: '#FFD54A', txt: '#F6EFE3' }, sz = h * 0.05, lines = o.lines || [[['import ', 'kw'], ['{ app }', 'txt']], [['await ', 'kw'], ['deploy', 'fn'], ["('edge')", 'str']], [['app.', 'txt'], ['scale', 'fn'], ['(0)', 'str']]];
    let tt = t0 + 0.5;
    lines.forEach((toks, i) => { let x = -w * 0.4, cnt = 0; toks.forEach(([s, kd]) => { out.push(z(item('text', COL[kd], { text: s, size: sz, weight: 600, align: 'left', x, y: T + h * 0.16 + i * sz * 1.55, type: { t: tt + cnt / 24, cps: 24, n: s.length } }), 2)); for (let j = 0; j < s.length; j += 3) S.sfx(tt + (cnt + j) / 24, 'tick', 0.05, -23, 0, { st: (j / 3) % 8 * 0.5 }); x += s.length * sz * 0.56; cnt += s.length; }); tt += cnt / 24 + 0.25; });
    return out;
  } else {  // feed: photo hero + title + price counter + nav
    out.push(z(text(o.title || 'Explore', ink, h * 0.058, -w * 0.36, T + h * 0.075, { weight: 800, align: 'left' }), 2), z(item('circle', 'coral', { w: h * 0.05, x: w * 0.36, y: T + h * 0.075 }), 2), z(pill(w * 0.86, h * 0.062, 'sand', 0, T + h * 0.165), 1));
    out.push(z(photo(c[0], w * 0.86, h * 0.34, w * 0.1, t0, { y: T + h * 0.4 }), 1), z(photo(c[1], w * 0.415, h * 0.22, w * 0.08, t0, { x: -w * 0.22, y: T + h * 0.72 }), 1), z(photo(c[2], w * 0.415, h * 0.22, w * 0.08, t0, { x: w * 0.22, y: T + h * 0.72 }), 1));
    const n = item('text', ink, { size: h * 0.04, weight: 800, x: -w * 0.1, y: T + h * 0.605, fmt: { pre: '$', suf: '', dec: 0 }, num: [[t0 + 1, 240], [t0 + 3, 1290, 'm3Dec']] }); out.push(z(n, 2)); S.count(n, t0 + 1, t0 + 3, 240, 1290, 6);
    for (let i = 0; i < 4; i++) out.push(z(item('circle', i ? 'sand' : 'ink', { w: i ? 26 : 34, x: (i - 1.5) * w * 0.2, y: h / 2 - 62 }), 3));
  }
  return out.map((it, i) => (it.tracks?.h || it.tracks?.num || it.tracks?.sweep || it.type ? it : rise(it, t0 + 0.15 + (i % 9) * 0.05)));
}
