// Prompt -> timeline planner (rules, no model yet). Reads a brief, picks a palette and acts, writes a motionvid timeline with sound hints.
// A trained planner replaces `brief()` later (docs/ROADMAP.md G1); the timeline it writes stays the same.
import { Scene, item, text, pill, k } from './kit.js';

const CATS = [
  ['fintech', /bank|pay|money|card|wallet|fintech|invest|finance|budget/i, ['cream', 'ink', 'lime', 'butter', 'coral'], 'Money', 'moves.'],
  ['dashboard', /dashboard|analytic|saas|crm|metric|report|data|b2b/i, ['sage', 'ink', 'lime', 'butter', 'ink'], 'Every metric.', 'One screen.'],
  ['dev', /dev|code|api|cli|deploy|git|build|engineer|software/i, ['ink', 'butter', 'lime', 'ink', 'butter'], 'Build,', 'shipped.'],
  ['wellness', /health|habit|fitness|well|yoga|sleep|mind|meditat|run/i, ['cream', 'mint', 'butter', 'pink', 'ink'], 'Small', 'habits.'],
  ['hardware', /hardware|device|speaker|watch|gadget|product|headphone|camera/i, ['sand', 'clay', 'ink', 'butter', 'ink'], 'Made', 'solid.'],
  ['delivery', /deliver|ship|logistic|parcel|courier|food|order|shop|store/i, ['butter', 'ink', 'tomato', 'cream', 'ink'], 'Door', 'to door.'],
  ['generic', /./, ['cream', 'ink', 'lime', 'coral', 'ink'], 'Meet', 'the future.'],
];
const DARK = new Set(['ink', 'clay', 'tomato', 'moss']);
const fg = (bg) => (DARK.has(bg) ? 'cream' : 'ink');
const cap = (s) => s.charAt(0).toUpperCase() + s.slice(1);
const fit = (s, max, size) => Math.min(size, Math.round(max / (Math.max(3, s.length) * 0.56)));

export function brief(prompt) {
  const p = prompt.trim() || 'Lumen, a payments app with instant transfers, virtual cards and zero fees';
  const q = p.match(/["“']([^"”']{2,24})["”']/) || p.match(/(?:called|named)\s+([A-Z][\w-]{1,20})/) || p.match(/^([A-Z][\w-]{1,20})\b/) || p.match(/\b([A-Z][a-z]{2,14})\b/);
  const name = q ? q[1] : 'Nova';
  const cat = CATS.find((c) => c[1].test(p));
  const tail = (p.split(/\bwith\b|\bthat\b|,\s*(?=\w+\s+\w+)/i).slice(1).join(',') || p).replace(/\band\b/gi, ',').split(',').map((s) => s.trim().replace(/^(a|an|the)\s+/i, '')).filter((s) => s.length > 2 && !s.includes(name));
  const feats = [...tail, 'Instant start', 'Built for teams', 'Zero setup'].slice(0, 3).map((f) => cap(f.split(' ').slice(0, 3).join(' ')));
  const stat = /(\d+(?:\.\d+)?)\s*(%|x\b|k\b|ms\b|s\b)/i.exec(p);
  return { name: cap(name), cat: cat[0], pal: cat[2], hook: [cat[3], cat[4]], feats, stat: stat ? { v: +stat[1], suf: stat[2] } : { v: 24, suf: '%' }, cta: 'Get started' };
}

export function plan(prompt, vertical = false) {
  const B = brief(prompt), [a1, a2, a3, a4, a5] = B.pal;
  const W = vertical ? 1080 : 1920, H = vertical ? 1920 : 1080, cx = W / 2, V = vertical;
  const S = new Scene(29, a1, { width: W, height: H });
  const acts = [];
  const u = V ? 0.58 : 1;
  // 1 hook
  const h1 = fit(B.hook[0], W * 0.8, 260 * (V ? 1.1 : 1)), h2 = fit(B.hook[1], W * 0.8, 230 * (V ? 1.1 : 1));
  S.headline('a_1', B.hook[0], 0.35, H * 0.4, h1, fg(a1)); S.headline('a_2', B.hook[1], 0.8, H * 0.4 + h1 * 0.85, h2, 'coral');
  [['lime', 0.82, 0.2, 190], ['pink', 0.9, 0.8, 140], ['butter', 0.12, 0.86, 170]].forEach(([c, fx, fy, d], i) => {
    const o = S.add(`a_o${i}`, 'sphere', c, { x: W * fx, y: H * fy, w: d * (V ? 1.2 : 1) }); S.appear(o, 0.9 + i * 0.2, { frm: 0.4 });
  });
  S.iris(5.6, a2, W * 0.82, H * 0.2); acts.push(['Hook', 0, 5.6]);
  // 2 product
  let b = 5.6;
  const bal = item('text', 'coral', { size: 100 * u + 20, weight: 800, y: V ? -330 : -250, fmt: { pre: '', suf: B.stat.suf, dec: B.stat.v % 1 ? 1 : 0 }, num: [[b + 1.2, 0], [b + 3, B.stat.v, 'm3Dec']] });
  S.count(bal, b + 1.2, b + 3, 0, B.stat.v, 6);
  const ph = V ? 1180 : 940, bars = [.35, .55, .42, .8, .62, .95].map((v, i) => { const t = b + 2.2 + i * 0.07, hh = (V ? 330 : 240) * v; return item('rrect', ['coral', 'lime', 'butter', 'mint', 'pink', 'coral'][i], { r: 24, w: V ? 64 : 52, x: -(V ? 160 : 130) + i * (V ? 64 : 52) * 1.25, h: [[t, 0], [t + 0.8, hh, 'spring']], y: [[t, V ? 360 : 250], [t + 0.8, (V ? 360 : 250) - hh / 2, 'spring']] }); });
  const phone = S.group('p_ph', [item('rrect', 'ink', { w: ph * 0.48, h: ph, r: ph * 0.085, ext: ph * 0.035 }), item('rrect', 'white', { w: ph * 0.446, h: ph * 0.955, r: ph * 0.07, z: 1 }), item('rrect', 'ink', { w: ph * 0.144, h: ph * 0.026, r: 'pill', y: -ph * 0.44, z: 2 }),
    ...[text(B.name, 'ink', 48, 0, V ? -430 : -340, { weight: 800 }), bal, ...bars].map((i) => ({ ...i, z: 3 }))], { x: V ? cx : W * 0.33, y: V ? H * 0.5 : H * 0.52, w: ph * 0.48, h: ph, persp: 1900, rx: [[b + 0.25, -10], [b + 5, -4]], ry: [[b + 0.25, -62], [b + 1.3, -18, 'm3Dec'], [b + 6.5, 12, 'inOutSine']] });
  S.appear(phone, b + 0.25);
  const hx = V ? cx : W * 0.7;
  S.headline('p_h', B.feats[0], b + 1.0, V ? H * 0.12 : H * 0.28, fit(B.feats[0], V ? W * 0.9 : W * 0.5, 170), fg(a2), { x: hx });
  const btn = S.group('p_b', [pill(520 * (V ? 0.8 : 1), 140, 'coral'), text(B.cta, 'ink', 58, 0, 0, { weight: 800 })], { x: hx, y: V ? H * 0.9 : H * 0.62, w: 520, h: 140 }); S.appear(btn, b + 2.6, { x: hx });
  put2(btn, 'scale', [[b + 4.84, 1], [b + 4.9, 0.92, 'm3Std'], [b + 5.2, 1, 'springWild']]); S.sfx(b + 4.9, 'click', 0.1, -9, S.pan(hx));
  S.sfx(b + 5.4, 'notify', 0.6, -12, S.pan(hx), { freq: 660 });
  S.wipe(13, a3, 'x', 1); acts.push(['Product', 5.6, 13]);
  // 3 features
  b = 13;
  S.headline('f_h', 'Why ' + B.name, b + 0.3, V ? H * 0.1 : H * 0.17, fit('Why ' + B.name, W * 0.8, V ? 140 : 170), fg(a3));
  B.feats.forEach((f, i) => {
    const t = b + 0.9 + i * 0.25, x = V ? cx : W * (0.2 + i * 0.3), y = V ? H * (0.28 + i * 0.24) : H * 0.58, cw = V ? 900 : 520, ch = V ? 380 : 500;
    S.card(`f_c${i}`, t, x, y, cw, ch, ['white', 'ink', 'cream'][i], 56, [item('circle', ['coral', 'lime', 'butter'][i], { w: 120, x: V ? -cw * 0.3 : 0, y: V ? 0 : -110 }), text(f, i === 1 ? 'cream' : 'ink', fit(f, cw * 0.8, 62), V ? 60 : 0, V ? 0 : 60, { weight: 800 })],
      { rx: -6, ry: [[t, -80], [t + 0.9, [-14, 0, 14][i], 'spring'], [b + 6.4, [-6, 0, 6][i], 'inOutSine']] });
    S.sfx(t + 0.02, 'swipe', 0.25, -15, S.pan(x));
  });
  S.wipe(20, a4, 'y', -1); acts.push(['Features', 13, 20]);
  // 4 proof
  b = 20;
  const big = S.add('r_n', 'text', fg(a4), { text: '', size: fit('+' + B.stat.v + B.stat.suf, W * 0.8, 300), x: cx, y: V ? H * 0.34 : H * 0.42, weight: 800, fmt: { pre: '+', suf: B.stat.suf, dec: B.stat.v % 1 ? 1 : 0 }, num: [[b + 0.8, 0], [b + 2.6, B.stat.v, 'm3Dec']] });
  S.appear(big, b + 0.8, { sound: null, frm: 0.9 }); S.count(big, b + 0.8, b + 2.6, 0, B.stat.v, 8);
  [['mint', 0.8], ['coral', 0.62], ['butter', 0.9]].forEach(([c, to], i) => {
    const x = V ? W * (0.2 + i * 0.3) : W * (0.34 + i * 0.16), y = V ? H * 0.62 : H * 0.74, t = b + 2.2 + i * 0.18;
    S.card(`r_c${i}`, t, x, y, 230, 230, 'white', 115, [item('ring', 'sand', { w: 160, stroke: 24 }), item('ring', c, { w: 160, stroke: 24, sweep: [[t + 0.3, 0.001], [t + 1.5, to, 'm3Dec']], opacity: [[t + 0.29, 0], [t + 0.3, 1]] })]);
  });
  S.sfx(b + 3.4, 'chime', 0.6, -12, 0, { freq: 660 });
  S.iris(25, a5, cx, H * 0.5); acts.push(['Proof', 20, 25]);
  // 5 brand
  b = 25;
  S.add('b_o', 'sphere', 'coral', { w: V ? 720 : 560, x: cx, y: H * 0.45 }); put2(S.tl.elements.at(-1), 'scale', [[b + 0.1, 0], [b + 0.9, 1, 'spring']]);
  S.headline('b_n', B.name.toLowerCase(), b + 0.6, H * 0.45, fit(B.name, W * 0.85, 250), 'cream', { mode: 'split', dur: 1.1 });
  S.headline('b_c', B.cta, b + 1.6, H * 0.45 + (V ? 520 : 330), 76, fg(a5) === 'ink' ? 'butter' : 'butter', { mode: 'type' });
  S.add('outro', 'rrect', 'ink', { w: W, h: H, x: cx, y: H / 2, opacity: [[28, 0], [29, 1, 'inQuad']] });
  acts.push(['Brand', 25, 29]);
  return { tl: S.build(), acts, brief: B };
}
function put2(el, name, frames) { const t = (el.tracks ||= {}); t[name] = [...(t[name] || []), ...frames.map((f) => k(...f))].sort((a, b) => a.t - b.t); }
