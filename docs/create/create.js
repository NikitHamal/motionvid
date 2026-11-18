import { drawFrame } from '../engine/render.js';
import { plan } from '../engine/planner.js';
import { Preview } from '../engine/webaudio.js';
import { assets } from '../engine/assets.js';

assets.base = '../';  // photos live in docs/media/assets

const $ = (id) => document.getElementById(id);
const stage = $('stage'), ctx = stage.getContext('2d'), scrub = $('scrub'), playBtn = $('play');
const synth = new Preview();
let pname = '', tl = null, acts = [], vertical = false, aspect = '16:9', long = false, prompt = '', seed = 0;
const fmt = (s) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, '0')}`;

function paint() {
  if (tl) {
    let t = synth.time;
    if (synth.playing && t >= tl.duration) { synth.stop(); synth.from = 0; t = 0; }
    ctx.clearRect(0, 0, stage.width, stage.height);
    drawFrame(ctx, tl, Math.min(t, tl.duration), stage.width / tl.width);
    scrub.value = t; scrub.style.setProperty('--p', `${(t / tl.duration) * 100}%`);
    $('time').textContent = fmt(t);
    playBtn.dataset.playing = String(synth.playing);
  }
  requestAnimationFrame(paint);
}

function thumbs() {
  const host = $('acts');
  host.innerHTML = '';
  acts.forEach(([name, a, b]) => {
    const c = document.createElement('canvas'), btn = document.createElement('button');
    c.width = vertical ? 160 : 320; c.height = Math.round(c.width * tl.height / tl.width);
    drawFrame(c.getContext('2d'), tl, a + (b - a) * 0.7, c.width / tl.width);
    btn.append(c, Object.assign(document.createElement('b'), { textContent: name }));
    btn.onclick = () => { synth.stop(); synth.from = a + 0.2; };
    host.append(btn);
  });
}

function generate() {
  synth.stop(); synth.from = 2.4;
  prompt = $('prompt').value;
  const r = plan(prompt, vertical, seed, { long, aspect });
  tl = r.tl; pname = r.brief.name; acts = r.acts;
  stage.width = vertical ? 540 : 1280; stage.height = Math.round(stage.width * tl.height / tl.width);
  document.querySelector('.stagecol').dataset.v = vertical ? '1' : '0';
  document.querySelector('.stagecol').dataset.a = aspect;
  scrub.max = tl.duration;
  $('chips').innerHTML = [r.brief.name, r.brief.cat, `${r.brief.dev} + ${r.brief.scr}`, `variant ${seed + 1}`].map((s) => `<span>${s}</span>`).join('');
  thumbs();
}

playBtn.onclick = () => { if (!tl) return; if (synth.playing) synth.stop(); else synth.play(tl, synth.from >= tl.duration - 0.05 ? 0 : synth.from); };
scrub.oninput = () => { const was = synth.playing; synth.stop(); synth.from = Number(scrub.value); if (was) synth.play(tl, synth.from); };
$('go').onclick = () => { seed = 0; generate(); };
$('reroll').onclick = () => { seed += 1; generate(); };
$('fmt').onclick = (e) => { const b = e.target.closest('button'); if (!b) return; aspect = b.dataset.v; vertical = aspect !== '16:9'; for (const x of $('fmt').children) x.setAttribute('aria-pressed', String(x === b)); generate(); };
$('len').onclick = (e) => { const b = e.target.closest('button'); if (!b) return; long = b.dataset.v === '1'; for (const x of $('len').children) x.setAttribute('aria-pressed', String(x === b)); generate(); };
// Projects: saved in this browser (localStorage). A hosted account store replaces this later (docs/ROADMAP.md S1).
const store = () => JSON.parse(localStorage.getItem('mv.projects') || '[]');
function projects() {
  const host = $('projects'); host.innerHTML = '';
  store().forEach((p, i) => { const b = document.createElement('button'); b.className = 'btn tonal'; b.textContent = p.name; b.onclick = () => { $('prompt').value = p.prompt; seed = p.seed; aspect = p.aspect; long = p.long; vertical = aspect !== '16:9'; generate(); }; host.append(b); });
}
$('save').onclick = () => { const l = store(); l.unshift({ name: pname || prompt.slice(0, 18), prompt, seed, aspect, long }); localStorage.setItem('mv.projects', JSON.stringify(l.slice(0, 8))); projects(); copy('save', ''); };
$('dl').onclick = () => { const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([JSON.stringify(tl)], { type: 'application/json' })), download: 'timeline.json' }); a.click(); };
const copy = (id, s) => { navigator.clipboard?.writeText(s); $(id).dataset.done = 'true'; setTimeout(() => delete $(id).dataset.done, 1200); };
$('cmd').onclick = () => copy('cmd', 'python -m motionvid video timeline.json out/ --width 1280 --blur 3');
$('agent').onclick = () => copy('agent', 'Read AGENT.md and docs/SKILL.md, then write examples/demos/<name>.py with motionvid.kit (real photos, real UI screens, 3D mesh) for: "' + prompt + '". Check it with scripts/build_demos.py sheet, then render it.');

await document.fonts.load('800 40px "Bricolage Grotesque"');
await document.fonts.load('700 40px "Bricolage Grotesque"');
generate();
projects();
paint();
