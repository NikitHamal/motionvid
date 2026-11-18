// motionvid frame engine. One pure function, drawFrame(ctx, timeline, t), used by the site, the Studio app,
// the Python preview page and the Node video renderer. Python twin of the easings: src/motionvid/timeline.py.

import { EASES, val } from './ease.js';
import { drawBox, drawGroup, drawLocal } from './scene3d.js';
import { drawMesh } from './mesh.js';
import { drawMedia } from './assets.js';

export { EASES, val };

const FONT = '"Bricolage Grotesque", system-ui, sans-serif';
const clamp01 = (x) => Math.max(0, Math.min(1, x));

function blobPath(ctx, R, n, amp) {
  const steps = 160;
  ctx.beginPath();
  for (let i = 0; i <= steps; i++) {
    const a = (i / steps) * Math.PI * 2;
    const r = R * (1 + amp * Math.cos(n * a));
    const x = Math.cos(a) * r, y = Math.sin(a) * r;
    if (i === 0) ctx.moveTo(x, y); else ctx.lineTo(x, y);
  }
  ctx.closePath();
}

function roundRect(ctx, w, h, r) {
  const rr = Math.max(0, Math.min(r, w / 2, h / 2));
  ctx.beginPath();
  ctx.roundRect(-w / 2, -h / 2, w, h, rr);
}

function drawText(ctx, el, g, t) {
  const size = g('size', el.size || 96);
  ctx.font = `${el.weight || 800} ${size}px ${FONT}`;
  ctx.textAlign = el.align || 'center';
  ctx.textBaseline = 'middle';
  let text = el.text || el.id;
  if (el.fmt) {  // counter: text from the `num` track, e.g. fmt {pre:'$', suf:'k', dec:1}
    const v = g('num', 0), f = el.fmt;
    text = (f.pre || '') + v.toFixed(f.dec || 0).replace(/\B(?=(\d{3})+(?!\d))/g, ',') + (f.suf || '');
  }
  if (el.type) {
    const n = Math.max(0, Math.min(el.type.n, Math.floor((t - el.type.t) * el.type.cps) + 1));
    text = text.slice(0, t < el.type.t ? 0 : n);
  }
  if (!el.split) {
    const lines = text.split('\n'), lh = size * (el.lh || 1.12);
    lines.forEach((ln, i) => ctx.fillText(ln, 0, (i - (lines.length - 1) / 2) * lh));
    return;
  }
  if (el.split === 'mask') {  // words rise out of a clipped band: the editorial reveal
    const ws = text.split(' '), sp = ctx.measureText(' ').width, wd = ws.map((x) => ctx.measureText(x).width);
    const tot = wd.reduce((a, b) => a + b, 0) + sp * (ws.length - 1), st = el.stagger ?? 0.16, p = g('p', 1);
    ctx.save(); ctx.beginPath(); ctx.rect(-tot / 2 - 30, -size * 0.62, tot + 60, size * 1.24); ctx.clip();
    let x = -tot / 2;
    ws.forEach((wd_, i) => {
      const cp = clamp01(p * (1 + st * ws.length) - i * st);
      ctx.textAlign = 'left'; ctx.fillText(wd_, x, (1 - EASES.outExpo(cp)) * size * 1.15);
      x += wd[i] + sp;
    });
    ctx.restore();
    return;
  }
  const chars = [...text];
  const widths = chars.map((c) => ctx.measureText(c).width);
  const total = widths.reduce((a, b) => a + b, 0);
  const stagger = el.stagger ?? 0.12, p = g('p', 1);
  let x = -total / 2;
  chars.forEach((c, i) => {
    const cp = clamp01(p * (1 + stagger * chars.length) - i * stagger);
    const e = EASES.outBack(cp);
    ctx.save();
    ctx.globalAlpha *= clamp01(cp * 3);
    ctx.translate(x + widths[i] / 2, (1 - e) * size * 0.7);
    ctx.rotate((1 - e) * 0.35 * (i % 2 ? 1 : -1));
    ctx.scale(0.4 + 0.6 * e, 0.4 + 0.6 * e);
    ctx.fillText(c, 0, 0);
    ctx.restore();
    x += widths[i];
  });
}

export function drawFrame(ctx, tl, t, k = 1) {
  ctx.save();
  ctx.scale(k, k);
  ctx.fillStyle = tl.bg || '#F6EFE3';
  ctx.fillRect(0, 0, tl.width, tl.height);
  if (tl.camera) {  // virtual camera: zoom / pan / roll around the frame centre
    const C = tl.camera.tracks || {}, cv = (n, d) => { const v = val(C[n], t); return v === null ? d : v; };
    ctx.translate(tl.width / 2, tl.height / 2);
    ctx.scale(cv('zoom', 1), cv('zoom', 1));
    ctx.rotate((cv('roll', 0) * Math.PI) / 180);
    ctx.translate(-tl.width / 2 - cv('x', 0), -tl.height / 2 - cv('y', 0));
  }
  for (const el of tl.elements) {
    const T = el.tracks || {};
    const g = (n, d) => { const v = val(T[n], t); return v === null ? d : v; };
    const op = clamp01(g('opacity', 1));
    const sc = g('scale', 1);
    if (op <= 0 || sc <= 0) continue;
    ctx.save();
    ctx.globalAlpha = op;
    ctx.translate(g('x', tl.width / 2), g('y', tl.height / 2));
    ctx.rotate((g('rotation', 0) * Math.PI) / 180);
    ctx.scale(sc, sc);
    ctx.fillStyle = el.color || '#17130F';
    ctx.strokeStyle = el.color || '#17130F';
    const w = g('w', el.w || 160), h = g('h', el.h || w);
    switch (el.kind) {
      case 'text': drawText(ctx, el, g, t); break;
      case 'group': drawGroup(ctx, el, g, t, drawText); break;
      case 'box3d': drawBox(ctx, el, g, t, drawText); break;
      case 'mesh': drawMesh(ctx, el, g, t, drawText); break;
      case 'image': case 'video': drawMedia(ctx, el, g, t); break;
      case 'sphere': case 'path': case 'poly': drawLocal(ctx, el, g, t, drawText); break;
      case 'circle': ctx.beginPath(); ctx.ellipse(0, 0, w / 2, h / 2, 0, 0, Math.PI * 2); ctx.fill(); break;
      case 'ring':
        ctx.lineWidth = g('stroke', el.stroke || 12);
        ctx.beginPath(); ctx.ellipse(0, 0, w / 2, h / 2, 0, 0, Math.PI * 2); ctx.stroke(); break;
      case 'blob': blobPath(ctx, w / 2, el.n || 8, g('amp', el.amp ?? 0.08)); ctx.fill(); break;
      default: roundRect(ctx, w, h, el.r === 'pill' ? Math.min(w, h) / 2 : g('r', el.r || 0)); ctx.fill();
    }
    ctx.restore();
  }
  ctx.restore();
}
