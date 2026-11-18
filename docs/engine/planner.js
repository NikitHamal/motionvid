// Prompt -> timeline planner (rules, no model yet). Reads a brief, picks a palette and acts, writes a motionvid timeline with sound hints.
// A trained planner replaces `brief()` later (docs/ROADMAP.md G1); the timeline it writes stays the same.
import { Scene, item, text, pill, k } from './kit.js';
import { part, mesh, spin, photo, phone3d, laptop3d, bars3d, globe, coins, torusRings, cubePhotos, rack, orbit, screen } from './mesh_kit.js';

const CATS = [  // [id, regex, palette(5), hook line 1, hook line 2, device, screen, photos, hero pool]
  ['travel', /travel|trip|hotel|flight|book|tour|destination|vacation/i, ['sand', 'moss', 'tomato', 'butter', 'ink'], 'Go', 'somewhere real.', 'phone', 'feed', ['beach', 'palms', 'rockies'], ['cube', 'globe', 'coins']],
  ['fashion', /fashion|cloth|wear|sneaker|shoe|style|brand|drop|apparel|beauty/i, ['ink', 'pink', 'butter', 'cream', 'pink'], 'Wear the', 'moment.', 'phone', 'feed', ['fash1', 'fash2', 'fash3'], ['cube', 'carousel', 'torus']],
  ['fintech', /bank|pay|money|card|wallet|fintech|invest|finance|budget/i, ['cream', 'moss', 'butter', 'ink', 'butter'], 'Money,', 'in motion.', 'laptop', 'dash', ['desk', 'laptop', 'analytics'], ['coins', 'bars', 'torus']],
  ['dashboard', /dashboard|analytic|saas|crm|metric|report|data|b2b/i, ['sage', 'ink', 'lime', 'butter', 'ink'], 'Every metric.', 'One screen.', 'laptop', 'dash', ['analytics', 'desk', 'laptop'], ['bars', 'globe', 'cube']],
  ['dev', /dev|code|api|cli|deploy|git|engineer|software|agent|infra|cloud/i, ['ink', 'lime', 'coral', 'cream', 'lime'], 'Ship', 'agents.', 'laptop', 'code', ['racks', 'laptop', 'desk'], ['rack', 'torus', 'globe']],
  ['wellness', /health|habit|fitness|well|yoga|sleep|mind|meditat|run|sport|workout/i, ['ink', 'lime', 'coral', 'cream', 'lime'], 'Move', 'more.', 'phone', 'activity', ['jogger', 'park', 'sunrise'], ['torus', 'bars', 'coins']],
  ['climate', /climate|green|earth|energy|carbon|solar|city|mobility|nature/i, ['cream', 'moss', 'butter', 'sage', 'moss'], 'Cities that', 'breathe.', 'laptop', 'dash', ['lake', 'rockies', 'lake2'], ['globe', 'bars', 'cube']],
  ['generic', /./, ['cream', 'ink', 'lime', 'coral', 'ink'], 'Meet', 'the future.', 'phone', 'feed', ['lake', 'sunrise', 'desk'], ['cube', 'torus', 'globe']],
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
  return { name: cap(name), cat: cat[0], pal: cat[2], hook: [cat[3], cat[4]], dev: cat[5], scr: cat[6], photos: cat[7], heroes: cat[8], feats, stat: stat ? { v: +stat[1], suf: stat[2] } : { v: 24, suf: '%' }, cta: 'Get started' };
}

const hash = (s) => [...s].reduce((h, c) => (h * 31 + c.charCodeAt(0)) >>> 0, 7);
const CUT = ['iris', 'wipe', 'slats'];

// Hero object for a prompt: a different 3D object per category and per seed, spinning over the act.
function hero(S, B, kind, id, t, x, y, size, t1) {
  const [, , , , ] = B.pal, ph = B.photos, sp = spin(t, t1, -34, 34);
  const P = {
    cube: () => [...cubePhotos(size * 0.5, { front: ph[0], right: ph[1], left: ph[2], back: ph[0], top: ph[1] }), ...orbit((i) => part('gem', ['butter', 'cream', 'lime'][i], { r: 40, h: 72, gloss: 22 }), 3, size * 0.5, t + 0.6, t1, 1)],
    globe: () => globe(size * 0.36, 'moss', 'butter'), coins: () => coins(t + 0.6, size * 0.3, ['clay', 'cream', 'moss', 'clay', 'cream']), bars: () => bars3d([0.3, 0.45, 0.4, 0.62, 0.78, 1], t + 0.6, size * 0.8, size * 0.55, ['coral', 'ink', 'butter']),
    torus: () => torusRings(t + 0.5, size * 0.4, ['lime', 'ink', 'cream']), rack: () => rack(size * 0.26, 5),
    carousel: () => orbit((i) => part('rbox', 'ink', { w: 250, h: 350, d: 12, r: 24, screen: ['front', 'back'].map((f) => ({ face: f, items: [photo(ph[i % 3], 230, 330, 16)], w: 230, h: 330, r: 16, bg: '#E9DCC3' })) }), 6, size * 0.42, t + 0.5, t1, 0.5, true),
  }[kind]();
  return mesh(S, id, t, x, y, P, size, { rx: -16, ry: sp, persp: 2100 });
}

export function plan(prompt, vertical = false, seed = 0) {
  const B = brief(prompt), h = hash(prompt) + seed * 7, [a1, a2, a3, a4, a5] = B.pal;
  const V = vertical, W = V ? 1080 : 1920, H = V ? 1920 : 1080, cx = W / 2, dur = 30;
  const S = new Scene(dur, a1, { width: W, height: H }), acts = [];
  const hA = B.heroes[h % B.heroes.length], hB = B.heroes[(h + 1) % B.heroes.length];
  const cut = (t, col, x, y, i) => { const m = CUT[(h + i) % 3]; if (m === 'iris') S.iris(t, col, x, y); else if (m === 'wipe') S.wipe(t, col, i % 2 ? 'y' : 'x', 1); else S.slats(t, col); };
  // 1 hook (0-6)
  const f1 = fit(B.hook[0], V ? W * 0.85 : W * 0.45, V ? 330 : 280), f2 = fit(B.hook[1], V ? W * 0.85 : W * 0.45, V ? 250 : 200);
  S.headline('a_1', B.hook[0], 0.35, V ? H * 0.12 : H * 0.36, f1, fg(a1), { x: V ? cx : W * 0.27 });
  S.headline('a_2', B.hook[1], 0.8, V ? H * 0.12 + f1 * 0.95 : H * 0.36 + f1 * 0.9, f2, a1 === 'ink' ? 'lime' : 'coral', { x: V ? cx : W * 0.27 });
  hero(S, B, hA, 'a_h', 0.9, V ? cx : W * 0.74, V ? H * 0.68 : H * 0.52, V ? 1100 : 900, 6);
  cut(5.6, a2, W * 0.74, H * 0.5, 0); acts.push(['Hook', 0, 5.6]);
  // 2 product (5.6-13)
  let b = 5.6;
  const sc = screen(B.scr, S, B.dev === 'phone' ? 390 : 846, B.dev === 'phone' ? 820 : 513, b + 1.3, { photos: B.photos, accent: a2 === 'ink' ? 'moss' : a2 }), dx = V ? cx : W * 0.34;
  if (B.dev === 'phone') mesh(S, 'p_d', b + 0.3, dx, V ? H * 0.55 : H * 0.52, phone3d(sc, 420, 860), V ? 1500 : 900, { rx: -6, ry: spin(b + 0.3, b + 7.4, -42, 8), persp: 2100 });
  else mesh(S, 'p_d', b + 0.3, dx, V ? H * 0.55 : H * 0.54, laptop3d(sc, V ? 940 : 900), V ? 1300 : 1100, { rx: -12, ry: spin(b + 0.3, b + 7.4, -30, 10), persp: 2100 });
  const hx = V ? cx : W * 0.72;
  S.headline('p_h', B.feats[0], b + 1.0, V ? H * 0.1 : H * 0.3, fit(B.feats[0], V ? W * 0.9 : W * 0.5, 170), fg(a2), { x: hx });
  const btn = S.group('p_b', [pill(520 * (V ? 0.8 : 1), 140, 'coral'), text(B.cta, 'ink', 58, 0, 0, { weight: 800 })], { x: hx, y: V ? H * 0.9 : H * 0.62, w: 520, h: 140 }); S.appear(btn, b + 2.6, { x: hx });
  put2(btn, 'scale', [[b + 4.84, 1], [b + 4.9, 0.92, 'm3Std'], [b + 5.2, 1, 'springWild']]); S.sfx(b + 4.9, 'click', 0.1, -9, S.pan(hx)); S.sfx(b + 5.4, 'notify', 0.6, -12, S.pan(hx), { freq: 660 });
  cut(13, a3, cx, H * 0.5, 1); acts.push(['Product', 5.6, 13]);
  // 3 real photos on a carousel (13-20)
  b = 13;
  S.headline('f_h', B.feats[1], b + 0.3, V ? H * 0.1 : H * 0.14, fit(B.feats[1], W * 0.85, V ? 150 : 170), fg(a3));
  const cards = orbit((i) => part('rbox', 'ink', { w: 320, h: 440, d: 14, r: 28, screen: ['front', 'back'].map((f) => ({ face: f, items: [photo(B.photos[i % 3], 296, 416, 20, b)], w: 296, h: 416, r: 20, bg: '#E9DCC3' })) }), 6, V ? 330 : 560, b + 0.6, b + 6.8, 0.5, true);
  mesh(S, 'f_c', b + 0.4, cx, V ? H * 0.52 : H * 0.6, cards, V ? 1500 : 1600, { rx: -14, ry: [[b + 0.4, 0]], persp: 2100 });
  cut(20, a4, cx, H * 0.5, 2); acts.push(['Photos', 13, 20]);
  // 4 proof (20-25)
  b = 20;
  const big = S.add('r_n', 'text', fg(a4), { text: '', size: fit('+' + B.stat.v + B.stat.suf, V ? W * 0.85 : W * 0.5, 300), x: V ? cx : W * 0.3, y: V ? H * 0.2 : H * 0.48, weight: 800, fmt: { pre: '+', suf: B.stat.suf, dec: B.stat.v % 1 ? 1 : 0 }, num: [[b + 0.8, 0], [b + 2.6, B.stat.v, 'm3Dec']] });
  S.appear(big, b + 0.8, { sound: null, frm: 0.9 }); S.count(big, b + 0.8, b + 2.6, 0, B.stat.v, 8); S.sfx(b + 3.0, 'chime', 0.6, -12, 0, { freq: 660 });
  hero(S, B, hB, 'r_h', b + 0.4, V ? cx : W * 0.72, V ? H * 0.64 : H * 0.54, V ? 1100 : 900, 25);
  cut(25, a5, cx, H * 0.5, 3); acts.push(['Proof', 20, 25]);
  // 5 brand (25-30)
  b = 25;
  S.headline('b_n', B.name.toLowerCase(), b + 0.5, H * 0.46, fit(B.name, W * 0.85, 300), fg(a5), { mode: 'split', dur: 1.1 });
  const cb = S.group('b_b', [pill(560, 140, 'coral'), text(B.cta, 'ink', 58, 0, 0, { weight: 800 })], { x: cx, y: H * 0.46 + (V ? 330 : 260), w: 560, h: 140 }); S.appear(cb, b + 1.6, { x: cx });
  S.add('outro', 'rrect', 'ink', { w: W, h: H, x: cx, y: H / 2, opacity: [[dur - 1, 0], [dur, 1, 'inQuad']] });
  acts.push(['Brand', 25, 30]);
  return { tl: S.build(), acts, brief: B };
}
function put2(el, name, frames) { const t = (el.tracks ||= {}); t[name] = [...(t[name] || []), ...frames.map((f) => k(...f))].sort((a, b) => a.t - b.t); }
