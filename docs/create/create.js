import { drawFrame } from '../engine/render.js';
import { plan } from '../engine/planner.js';
import { Preview } from '../engine/webaudio.js';

const $ = (id) => document.getElementById(id);
const stage = $('stage'), ctx = stage.getContext('2d'), scrub = $('scrub'), playBtn = $('play');
const synth = new Preview();
let tl = null, acts = [], vertical = false, prompt = '';
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
    c.width = vertical ? 160 : 320; c.height = vertical ? 284 : 180;
    drawFrame(c.getContext('2d'), tl, a + (b - a) * 0.7, c.width / tl.width);
    btn.append(c, Object.assign(document.createElement('b'), { textContent: name }));
    btn.onclick = () => { synth.stop(); synth.from = a + 0.2; };
    host.append(btn);
  });
}

function generate() {
  synth.stop(); synth.from = 2.4;
  prompt = $('prompt').value;
  const r = plan(prompt, vertical);
  tl = r.tl; acts = r.acts;
  stage.width = vertical ? 540 : 1280; stage.height = vertical ? 960 : 720;
  document.querySelector('.stagecol').dataset.v = vertical ? '1' : '0';
  scrub.max = tl.duration;
  $('chips').innerHTML = [r.brief.name, r.brief.cat, `${r.brief.feats.length} features`].map((s) => `<span>${s}</span>`).join('');
  thumbs();
}

playBtn.onclick = () => { if (!tl) return; if (synth.playing) synth.stop(); else synth.play(tl, synth.from >= tl.duration - 0.05 ? 0 : synth.from); };
scrub.oninput = () => { const was = synth.playing; synth.stop(); synth.from = Number(scrub.value); if (was) synth.play(tl, synth.from); };
$('go').onclick = generate;
$('fmt').onclick = (e) => { const b = e.target.closest('button'); if (!b) return; vertical = b.dataset.v === '1'; for (const x of $('fmt').children) x.setAttribute('aria-pressed', String(x === b)); generate(); };
$('dl').onclick = () => { const a = Object.assign(document.createElement('a'), { href: URL.createObjectURL(new Blob([JSON.stringify(tl)], { type: 'application/json' })), download: 'timeline.json' }); a.click(); };
const copy = (id, s) => { navigator.clipboard?.writeText(s); $(id).dataset.done = 'true'; setTimeout(() => delete $(id).dataset.done, 1200); };
$('cmd').onclick = () => copy('cmd', 'python -m motionvid video timeline.json out/ --blur 3');
$('agent').onclick = () => copy('agent', `Read docs/SKILL.md, then write a motionvid timeline with motionvid.kit for: "${prompt}". Render it with python -m motionvid video.`);

await document.fonts.load('800 40px "Bricolage Grotesque"');
await document.fonts.load('700 40px "Bricolage Grotesque"');
generate();
paint();
