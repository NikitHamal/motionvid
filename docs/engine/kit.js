// motionvid kit (JS twin of src/motionvid/kit/core.py): builds timelines in the browser. Same track rules, same recipes.
export const PAL = { cream: '#F6EFE3', ink: '#17130F', coral: '#FF6A45', lime: '#C9F13B', butter: '#FFD54A', pink: '#FF9DBB', mint: '#3DDBA7', clay: '#D9573B', moss: '#2F5D3A', sand: '#E9DCC3', white: '#FFFFFF', tomato: '#E8402A', sage: '#BFD8B8' };
const NUM = ['x', 'y', 'z', 'scale', 'opacity', 'rotation', 'rx', 'ry', 'rz'], STATIC = ['pts', 'items', 'faces', 'fmt', 'type', 'parts', 'light', 'screen'];
export const k = (t, v, ease) => ({ t: +t.toFixed(4), v: +v.toFixed(3), ...(ease ? { ease } : {}) });

export function item(kind, color, props = {}) {
  const o = { kind }, tr = {};
  if (color) o.color = PAL[color] || color;
  for (const [n, v] of Object.entries(props)) {
    if (STATIC.includes(n) || !(Array.isArray(v) || (NUM.includes(n) && typeof v === 'number'))) o[n] = v;
    else tr[n] = Array.isArray(v) ? v.map((f) => k(...f)) : [k(0, v)];
  }
  if (Object.keys(tr).length) o.tracks = tr;
  return o;
}
export function put(el, name, frames, base) {
  const trk = (el.tracks ||= {});
  const cur = trk[name] || (base !== undefined ? [k(0, base)] : []);
  trk[name] = [...cur, ...frames.map((f) => k(...f))].sort((a, b) => a.t - b.t);
}
export const text = (s, color = 'ink', size = 48, x = 0, y = 0, extra = {}) => item('text', color, { text: s, size, weight: 700, x, y, ...extra });
export const pill = (w, h, color, x = 0, y = 0, extra = {}) => item('rrect', color, { w, h, r: 'pill', x, y, ...extra });
const lift = (items, z) => items.map((i) => (i.z !== undefined || i.tracks?.z ? i : { ...i, z }));

export class Scene {
  constructor(duration, bg = 'cream', { fps = 60, width = 1920, height = 1080 } = {}) {
    this.W = width; this.H = height; this.cur = [];
    this.tl = { rev: 7, fps, duration, width, height, bg: PAL[bg] || bg, elements: [], cuts: [], sfx: [] };
  }
  add(id, kind, color, props = {}) { const el = { id, ...item(kind, color, props) }; this.tl.elements.push(el); this.cur.push(el); return el; }
  group(id, items, props = {}) { return this.add(id, 'group', null, { items, ...props }); }
  sfx(t, role, dur = 0.5, gain_db = -12, pan = 0, extra = {}) { this.tl.sfx.push({ t: +t.toFixed(4), role, dur, gain_db, pan, ...extra }); }
  pan(x) { return +((((Array.isArray(x) ? x[x.length - 1][1] : x) / this.W) - 0.5) * 1.4).toFixed(3); }
  appear(el, t, { dur = 0.55, ease = 'spring', frm = 0.8, sound = 'pop', gain = -13, x } = {}) {
    put(el, 'opacity', [[0, 0], [t, 0], [t + 0.001, 0.01], [t + dur * 0.3, 1, 'm3StdDec']]);
    put(el, 'scale', [[0, frm], [t, frm], [t + dur, 1, ease]]);
    if (sound) this.sfx(t + 0.02, sound, 0.3, gain, this.pan(x ?? el.tracks?.x?.[0]?.v ?? this.W / 2));
    return el;
  }
  card(id, t, x, y, w, h, color, r, items = [], extra = {}) {
    const el = this.group(id, [item('rrect', color, { w, h, r }), ...lift(items, 1)], { x, y, w, h, ...extra });
    return t === null ? el : this.appear(el, t, { x });
  }
  hideScene(t) { for (const el of this.cur) put(el, 'opacity', [[t, 1], [t + 0.001, 0]], 1); this.cur = []; }
  headline(id, s, t, y, size, color = 'ink', { mode = 'mask', dur = 0.9, x = this.W / 2 } = {}) {
    if (mode === 'type') return this.add(id, 'text', color, { text: s, size, x, y, type: { t, cps: 14, n: s.length } });
    const el = this.add(id, 'text', color, { text: s, size, x, y, split: mode === 'mask' ? 'mask' : true, p: [[0, 0], [t, 0], [t + dur, 1]] });
    if (mode === 'mask') this.sfx(t + 0.05, 'swipe', 0.25, -15, this.pan(x));
    return el;
  }
  count(el, t0, t1, a, b, ticks = 7) {
    put(el, 'num', [[t0, a], [t1, b, 'm3Dec']], a);
    for (let i = 0; i < ticks; i++) this.sfx(t0 + (t1 - t0) * (i / ticks) ** 0.8, 'tick', 0.05, -21 + i * 0.4, 0, { st: i * 0.5 });
  }
  iris(tEnd, color, x = this.W / 2, y = this.H / 2, dur = 0.5) {
    this.hideScene(tEnd);
    this.add(`iris${this.tl.cuts.length}`, 'circle', color, { x, y, w: [[tEnd - dur, 0], [tEnd, 3600, 'm3Acc']] });
    this.tl.cuts.push({ t: +tEnd.toFixed(4), kind: 'cut' });
  }
  wipe(tEnd, color, axis = 'x', sign = 1, dur = 0.5) {
    this.hideScene(tEnd);
    const big = 2.4 * Math.max(this.W, this.H), c = axis === 'x' ? this.W / 2 : this.H / 2;
    const pos = [[tEnd - dur, c - sign * big * 0.99], [tEnd, c, 'm3Acc']];
    this.add(`wipe${this.tl.cuts.length}`, 'rrect', color, axis === 'x' ? { x: pos, y: this.H / 2, w: big, h: this.H + 40 } : { y: pos, x: this.W / 2, w: this.W + 40, h: big });
    this.tl.cuts.push({ t: +tEnd.toFixed(4), kind: 'cut' });
  }
  slats(tEnd, color, n = 6, dur = 0.55) {
    this.hideScene(tEnd);
    const hh = this.H / n, c = this.tl.cuts.length;
    for (let i = 0; i < n; i++) { const e = tEnd - (n - 1 - i) * 0.05; this.add(`slat${c}_${i}`, 'rrect', color, { x: this.W / 2, y: hh * (i + 0.5), h: hh + 6, w: [[e - dur, 0], [e, this.W + 40, 'm3Acc']] }); }
    this.tl.cuts.push({ t: +tEnd.toFixed(4), kind: 'cut' });
  }
  build() { return this.tl; }
}
