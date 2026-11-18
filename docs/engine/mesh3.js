// motionvid mesh3: procedural hero geometry for the mesh engine (rev 3D v3).
// Prims: wave (height field), blob (morphing sphere), knot (torus knot tube), helix (spiral tube), ribbon (twisted band).
// Faces carry `u` (0..1) so a part can map a color ramp over them (solid facets, no gradients). Up is -y.
const TAU = Math.PI * 2;
const sub = (a, b) => [a[0] - b[0], a[1] - b[1], a[2] - b[2]];
const cross = (a, b) => [a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0]];
const mid = (q) => [0, 1, 2].map((i) => q.reduce((s, p) => s + p[i], 0) / q.length);
const nrm = (v) => { const l = Math.hypot(...v) || 1; return v.map((x) => x / l); };
function quad(a, b, c, d, u, out, ref) {
  const n = nrm(cross(sub(c, a), sub(d, b))), cc = mid([a, b, c, d]);
  if (ref && n[0] * (cc[0] - ref[0]) + n[1] * (cc[1] - ref[1]) + n[2] * (cc[2] - ref[2]) < 0) { n[0] *= -1; n[1] *= -1; n[2] *= -1; }
  out.push({ p: [a, b, c, d], n, c: cc, tag: 'side', u });
}
export function wave(v, ph) {
  const nu = v.seg || 44, nv = Math.round(nu * (v.d / v.w)) || 30, out = [], k = v.freq || 2.2, A = v.amp;
  const hgt = (x, z) => A * (0.55 * Math.sin(k * x * TAU + ph) + 0.3 * Math.sin(k * 1.7 * z * TAU - ph * 1.3 + 1.1) + 0.22 * Math.sin((x + z) * k * 2.3 * TAU + ph * 0.7));
  const P = (i, j) => { const x = i / nu - 0.5, z = j / nv - 0.5; return [x * v.w, -hgt(x, z), z * v.d]; };
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) {
    const a = P(i, j), b = P(i + 1, j), c = P(i + 1, j + 1), d = P(i, j + 1);
    const y = -(a[1] + b[1] + c[1] + d[1]) / 4;
    quad(a, d, c, b, Math.max(0, Math.min(1, (y / A + 1) / 2)), out, [a[0], a[1] + 99999, a[2]]);
  }
  return out;
}
export function blob(v, ph) {
  const nu = v.seg || 48, nv = Math.round(nu / 2), out = [], A = v.amp ?? 0.22;
  const rad = (th, ps) => {
    const x = Math.cos(ps) * Math.cos(th), y = Math.sin(ps), z = Math.cos(ps) * Math.sin(th);
    return v.r * (1 + A * (0.5 * Math.sin(2.1 * x + ph) * Math.cos(1.7 * y - ph * 0.8) + 0.35 * Math.sin(3.2 * z + ph * 1.3 + x) + 0.2 * Math.sin(4.1 * y - 2.2 * x + ph * 0.6)));
  };
  const P = (i, j) => { const th = (i / nu) * TAU, ps = -Math.PI / 2 + (j / nv) * Math.PI, r = rad(th, ps); return [r * Math.cos(ps) * Math.cos(th), r * Math.sin(ps), r * Math.cos(ps) * Math.sin(th)]; };
  for (let i = 0; i < nu; i++) for (let j = 0; j < nv; j++) quad(P(i, j), P(i + 1, j), P(i + 1, j + 1), P(i, j + 1), i / nu, out, [0, 0, 0]);
  return out;
}
function tube(path, r, nv, closed, out, uf, twist = 0) {
  const n = path.length - (closed ? 0 : 1), ring = [];
  for (let i = 0; i <= n; i++) {
    const p = path[i % path.length], q = path[(i + 1) % path.length], o = path[(i + path.length - 1) % path.length];
    const T = nrm(sub(closed || i < path.length - 1 ? q : p, closed || i > 0 ? o : p));
    const up = Math.abs(T[1]) > 0.9 ? [1, 0, 0] : [0, 1, 0], N = nrm(cross(T, up)), B = cross(T, N), rr = typeof r === 'function' ? r(i / n) : r;
    ring.push(Array.from({ length: nv }, (_, j) => { const a = (j / nv) * TAU + twist * (i / n) * TAU; return [p[0] + rr * (N[0] * Math.cos(a) + B[0] * Math.sin(a)), p[1] + rr * (N[1] * Math.cos(a) + B[1] * Math.sin(a)), p[2] + rr * (N[2] * Math.cos(a) + B[2] * Math.sin(a))]; }));
  }
  for (let i = 0; i < n; i++) for (let j = 0; j < nv; j++) {
    const a = ring[i][j], b = ring[i + 1][j], c = ring[i + 1][(j + 1) % nv], d = ring[i][(j + 1) % nv], pc = path[i % path.length];
    quad(a, b, c, d, uf(i / n), out, pc);
  }
}
export function knot(v) {
  const p = v.p || 2, q = v.q || 3, N = v.seg || 220, path = [], out = [];
  for (let i = 0; i < N; i++) { const t = (i / N) * TAU, rr = v.R * (1 + 0.38 * Math.cos(q * t)); path.push([rr * Math.cos(p * t), v.R * 0.5 * Math.sin(q * t), rr * Math.sin(p * t)]); }
  tube(path, v.r, 16, true, out, (u) => u);
  return out;
}
export function helix(v) {
  const N = v.seg || 160, turns = v.turns || 3, path = [], out = [];
  for (let i = 0; i <= N; i++) { const t = (i / N) * turns * TAU; path.push([v.R * Math.cos(t), (i / N - 0.5) * v.h, v.R * Math.sin(t)]); }
  tube(path, (u) => v.r * (0.55 + 0.45 * Math.sin(u * Math.PI)), 12, false, out, (u) => u);
  return out;
}
export function ribbon(v, ph) {
  const N = v.seg || 90, tw = v.turns || 1.5, out = [], w = v.w || 120, L = v.len || 700;
  const P = (i, s) => { const u = i / N, a = u * tw * TAU + ph, x = (u - 0.5) * L, y = Math.sin(u * TAU * 1.2 + ph) * v.R * 0.4; return [x + Math.cos(a) * s * w * 0 , y + Math.sin(a) * s * w * 0.5, Math.cos(a) * s * w * 0.5 + Math.sin(u * TAU + ph) * v.R * 0.3]; };
  for (let i = 0; i < N; i++) { const a = P(i, -1), b = P(i + 1, -1), c = P(i + 1, 1), d = P(i, 1); quad(a, b, c, d, i / N, out, null); }
  return out;
}
export const DYN = { wave: (v, ph) => wave(v, ph), blob: (v, ph) => blob(v, ph), knot: (v) => knot(v), helix: (v) => helix(v), ribbon: (v, ph) => ribbon(v, ph) };
export const STATIC_DYN = new Set(['knot', 'helix']);
export function ramp(cols, u) {
  if (!cols || !cols.length) return null;
  const x = Math.max(0, Math.min(0.9999, u)) * (cols.length - 1), i = Math.floor(x), f = x - i;
  const h = (c) => parseInt(c.slice(1), 16), a = h(cols[i]), b = h(cols[i + 1] || cols[i]);
  const m = (s) => Math.round(((a >> s) & 255) * (1 - f) + ((b >> s) & 255) * f);
  return '#' + [16, 8, 0].map((s) => m(s).toString(16).padStart(2, '0')).join('');
}
