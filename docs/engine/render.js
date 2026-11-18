// motionvid frame engine. One pure function, drawFrame(ctx, timeline, t), used by the site, the Studio app,
// the Python preview page and the Node video renderer. Python twin of the easings: src/motionvid/timeline.py.

const bounce = (u) => {
  const n = 7.5625, d = 2.75;
  if (u < 1 / d) return n * u * u;
  if (u < 2 / d) { u -= 1.5 / d; return n * u * u + 0.75; }
  if (u < 2.5 / d) { u -= 2.25 / d; return n * u * u + 0.9375; }
  u -= 2.625 / d; return n * u * u + 0.984375;
};

export const EASES = {
  linear: (u) => u,
  inQuad: (u) => u * u,
  outQuad: (u) => 1 - (1 - u) ** 2,
  inOutQuad: (u) => (u < 0.5 ? 2 * u * u : 1 - (-2 * u + 2) ** 2 / 2),
  inCubic: (u) => u ** 3,
  outCubic: (u) => 1 - (1 - u) ** 3,
  inOutCubic: (u) => (u < 0.5 ? 4 * u ** 3 : 1 - (-2 * u + 2) ** 3 / 2),
  inExpo: (u) => (u <= 0 ? 0 : 2 ** (10 * u - 10)),
  outExpo: (u) => (u >= 1 ? 1 : 1 - 2 ** (-10 * u)),
  outBack: (u) => 1 + 2.70158 * (u - 1) ** 3 + 1.70158 * (u - 1) ** 2,
  inBack: (u) => 2.70158 * u ** 3 - 1.70158 * u ** 2,
  outElastic: (u) => (u <= 0 ? 0 : u >= 1 ? 1 : 2 ** (-10 * u) * Math.sin(((u * 10 - 0.75) * 2 * Math.PI) / 3) + 1),
  outBounce: bounce,
};

export function val(kfs, t) {
  if (!kfs) return null;
  if (t <= kfs[0].t) return kfs[0].v;
  const last = kfs[kfs.length - 1];
  if (t >= last.t) return last.v;
  for (let i = 0; i < kfs.length - 1; i++) {
    const a = kfs[i], b = kfs[i + 1];
    if (t >= a.t && t <= b.t) {
      const span = b.t - a.t;
      const u = span <= 0 ? 1 : (t - a.t) / span;
      return a.v + (b.v - a.v) * EASES[b.ease || 'linear'](u);
    }
  }
  return last.v;
}

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
  ctx.textAlign = 'center';
  ctx.textBaseline = 'middle';
  let text = el.text || el.id;
  if (el.type) {
    const n = Math.max(0, Math.min(el.type.n, Math.floor((t - el.type.t) * el.type.cps) + 1));
    text = text.slice(0, t < el.type.t ? 0 : n);
  }
  if (!el.split) { ctx.fillText(text, 0, 0); return; }
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
