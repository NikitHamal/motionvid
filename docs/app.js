import { drawFrame } from './engine/render.js';
import { drawXray } from './engine/xray.js';

const $ = (id) => document.getElementById(id);
const stage = $('stage'), ctx = stage.getContext('2d'), audio = $('audio'), scrub = $('scrub'), playBtn = $('play');
const k = stage.width / 1920;
let tl, cues = [], xray = false, idle = 2.2, versions = [];

// decorative cookie in the hero, same radial function as the engine's blob shape
{
  let d = '';
  for (let i = 0; i <= 160; i++) {
    const a = (i / 160) * Math.PI * 2, r = 90 * (1 + 0.1 * Math.cos(10 * a));
    d += `${i ? 'L' : 'M'}${(Math.cos(a) * r).toFixed(2)} ${(Math.sin(a) * r).toFixed(2)}`;
  }
  $('cookie').setAttribute('d', d + 'Z');
}

const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;
const now = () => (audio.currentTime > 0 || !audio.paused ? audio.currentTime : idle);

function paint() {
  if (!tl) return;
  const t = Math.min(now(), tl.duration);
  drawFrame(ctx, tl, t, k);
  if (xray) drawXray(ctx, tl, cues, t, k);
  scrub.value = t;
  scrub.style.setProperty('--p', `${(t / tl.duration) * 100}%`);
  $('time').textContent = fmt(t);
}
const loop = () => { paint(); requestAnimationFrame(loop); };

// one state attribute drives the icon swap in CSS; the audio element is the single source of truth
function sync() {
  const on = !audio.paused && !audio.ended;
  playBtn.dataset.playing = String(on);
  playBtn.setAttribute('aria-label', on ? 'Pause' : 'Play');
}
playBtn.onclick = async () => {
  if (!tl) return;
  if (!audio.paused) { audio.pause(); return; }
  if (audio.ended || audio.currentTime >= tl.duration - 0.05) audio.currentTime = 0;
  try { await audio.play(); } catch { /* blocked or interrupted: state stays paused */ }
  sync();
};
['play', 'playing', 'pause', 'ended', 'emptied'].forEach((e) => audio.addEventListener(e, sync));
scrub.oninput = () => { audio.currentTime = Number(scrub.value); idle = audio.currentTime; };
$('mode').onclick = (e) => {
  const b = e.target.closest('button'); if (!b) return;
  xray = b.dataset.m === 'xray';
  for (const x of $('mode').children) x.setAttribute('aria-pressed', String(x === b));
};
$('cmd').onclick = () => navigator.clipboard?.writeText($('cmd').textContent);

async function load(v) {
  audio.pause();
  const [a, b] = await Promise.all([fetch(v.player.timeline).then((r) => r.json()), fetch(v.player.cues).then((r) => r.json())]);
  tl = a; cues = b; idle = Math.min(2.2, tl.duration / 2);
  audio.src = v.player.audio; audio.currentTime = 0;
  scrub.max = tl.duration; scrub.value = idle;
  for (const x of $('ver').children) x.setAttribute('aria-pressed', String(x.dataset.id === v.id));
  sync();
}

function cards() {
  const host = $('videos');
  for (const v of versions) {
    for (const [src, label] of [[v.video, ''], [v.xray, 'X-ray']]) {
      if (!src) continue;
      const f = document.createElement('figure');
      f.innerHTML = `<video controls preload="none" ${v.poster && !label ? `poster="${v.poster}"` : ''} src="${src}"></video><figcaption><em>${v.id}</em>${v.title}${label ? ` ${label}` : ''}</figcaption>`;
      host.append(f);
    }
  }
}

async function demos() {
  const host = $('demos');
  for (const d of await (await fetch('demos.json')).json()) {
    const f = document.createElement('figure');
    f.style.setProperty('--ar', `${d.aspect[0]} / ${d.aspect[1]}`);
    if (d.aspect[1] > d.aspect[0]) f.className = 'tall';
    f.innerHTML = `<video controls preload="none" poster="${d.poster}" src="${d.video}"></video><figcaption>${d.title}<em>${Math.round(d.duration)}s</em></figcaption>`;
    host.append(f);
  }
}

function flaws(fb) {
  const host = $('flaws');
  const names = { sub_coupling: 'Sub-bass on growth', air_vs_mid_db: 'Air above 9 kHz', dead_air_s: 'Dead air', pan_corr: 'Pan follows x',
    motion_bright_corr: 'Motion foley', preroll_rise_db: 'Cut pre-roll', glyph_ramp_rho: 'Glyph phrasing', tail_300ms_db: 'Tails past the cut', master_lufs_err: 'Master loudness' };
  const units = { sub_coupling: (x) => `${Math.round(x * 100)}%`, air_vs_mid_db: (x) => `${x.toFixed(0)} dB`, dead_air_s: (x) => `${x.toFixed(1)} s`,
    pan_corr: (x) => x.toFixed(2), motion_bright_corr: (x) => x.toFixed(2), preroll_rise_db: (x) => `${x.toFixed(0)} dB`, glyph_ramp_rho: (x) => x.toFixed(2),
    tail_300ms_db: (x) => `${x.toFixed(0)} dB`, master_lufs_err: (x) => `${x.toFixed(1)} LU` };
  const cols = [fb.showreel.classic, fb.v02_scene || fb.showreel.scene, fb.v03_scene || fb.reel2.scene, fb.reel2.scene, fb.launch ? fb.launch.scene : fb.reel2.scene, fb.showreel2.scene, fb.launch2.scene, (fb.launch3 || fb.launch2).scene];
  const cell = (r, key) => `<span class="v ${r.detail[key] ? 'ok' : 'no'}">${units[key](r[key])}</span>`;
  host.innerHTML = '<div class="row head"><span>Check</span><span>v0.1</span><span>v0.2</span><span>v0.3</span><span>v0.4</span><span>v0.5</span><span>v0.6</span><span>v0.7</span><span>v0.8</span></div>' +
    Object.keys(names).map((key) => `<div class="row"><span>${names[key]}</span>${cols.map((c) => cell(c, key)).join('')}</div>`).join('');
}

function studio(a) {
  const r5 = a.rev5, r6 = a.rev6;
  const rows = [['Continuous 2-8 kHz', (r) => `${r.continuous_hf_2k_8k_dbfs.toFixed(0)} dB`], ['Whoosh above 2.2 kHz', (r) => `${r.whoosh.hf_above_2k2_db.toFixed(0)} dB`],
    ['Whoosh decay', (r) => `${r.whoosh.decay_40db_ms.toFixed(0)} ms`], ['Text tick', (r) => `${r.tick_ms.toFixed(0)} ms`], ['Tick spacing', (r) => `${r.min_tick_gap_ms.toFixed(0)} ms`],
    ['Bounce steps', (r) => (r.bounce_gains_db.length ? r.bounce_gains_db.map((g) => g.toFixed(1)).join(' ') : 'flat')], ['Riser level', (r) => `${r.riser_gain_db[0].toFixed(1)} dB`]];
  $('studio').innerHTML = `<div class="row head"><span>Studio sound</span><span>rev 5</span><span>rev 6</span></div>` +
    rows.map(([n, f]) => `<div class="row"><span>${n}</span><span class="v no">${f(r5)}</span><span class="v ok">${f(r6)}</span></div>`).join('') +
    `<div class="row"><span>Gates</span><span class="v no">-</span><span class="v ok">${a.passed}</span></div>`;
}

versions = await (await fetch('versions.json')).json();
studio(await (await fetch('media/studio_audit.json')).json());
cards();
await demos();
flaws(await (await fetch('media/flawbench.json')).json());
const playable = versions.filter((v) => v.player);
$('ver').innerHTML = playable.map((v) => `<button aria-pressed="false" data-id="${v.id}">${v.id}</button>`).join('');
$('ver').onclick = (e) => { const b = e.target.closest('button'); if (b) load(playable.find((v) => v.id === b.dataset.id)); };
await load(playable[playable.length - 1]);
const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), { threshold: 0.15 });
document.querySelectorAll('.tile, .videos figure, .steps article, .cmd, .flaws, .studio').forEach((el) => { el.classList.add('reveal'); io.observe(el); });
await Promise.all(['400', '700', '800'].map((w) => document.fonts.load(`${w} 40px "Bricolage Grotesque"`)));
loop();
