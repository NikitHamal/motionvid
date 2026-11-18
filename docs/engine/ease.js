// motionvid easing table + keyframe sampler. Python twin: src/motionvid/timeline.py (parity is tested in tests/test_engine.py).

const bounce = (u) => {
  const n = 7.5625, d = 2.75;
  if (u < 1 / d) return n * u * u;
  if (u < 2 / d) { u -= 1.5 / d; return n * u * u + 0.75; }
  if (u < 2.5 / d) { u -= 2.25 / d; return n * u * u + 0.9375; }
  u -= 2.625 / d; return n * u * u + 0.984375;
};

// Material 3 motion tokens are cubic beziers. 40-step bisection, identical in Python.
export const bezier = (x1, y1, x2, y2) => {
  const cx = 3 * x1, bx = 3 * (x2 - x1) - cx, ax = 1 - cx - bx;
  const cy = 3 * y1, by = 3 * (y2 - y1) - cy, ay = 1 - cy - by;
  const X = (s) => ((ax * s + bx) * s + cx) * s, Y = (s) => ((ay * s + by) * s + cy) * s;
  return (u) => {
    if (u <= 0) return 0;
    if (u >= 1) return 1;
    let lo = 0, hi = 1, s = u;
    for (let i = 0; i < 40; i++) {
      const x = X(s);
      if (Math.abs(x - u) < 1e-7) break;
      if (x < u) lo = s; else hi = s;
      s = (lo + hi) / 2;
    }
    return Y(s);
  };
};

// Damped spring settled into [0, 1]: a = decay, f = oscillations per segment. Residual is blended out so it lands exactly on 1.
const spring = (a, f) => {
  const w = 2 * Math.PI * f;
  return (u) => {
    if (u <= 0) return 0;
    if (u >= 1) return 1;
    const d = Math.exp(-a * u) * (Math.cos(w * u) + (a / w) * Math.sin(w * u));
    return 1 - d * (1 - u ** 8);
  };
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
  outQuart: (u) => 1 - (1 - u) ** 4,
  outQuint: (u) => 1 - (1 - u) ** 5,
  inOutQuint: (u) => (u < 0.5 ? 16 * u ** 5 : 1 - (-2 * u + 2) ** 5 / 2),
  inOutSine: (u) => -(Math.cos(Math.PI * u) - 1) / 2,
  outCirc: (u) => Math.sqrt(1 - (u - 1) ** 2),
  m3Std: bezier(0.2, 0, 0, 1),
  m3StdDec: bezier(0, 0, 0, 1),
  m3StdAcc: bezier(0.3, 0, 1, 1),
  m3Dec: bezier(0.05, 0.7, 0.1, 1),
  m3Acc: bezier(0.3, 0, 0.8, 0.15),
  spring: spring(6, 1.5),
  springSoft: spring(7.5, 1.0),
  springWild: spring(4.5, 2.0),
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
