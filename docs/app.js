import { drawFrame } from './engine/render.js';
import { drawXray } from './engine/xray.js';

const $ = (id) => document.getElementById(id);
const stage = $('stage'), ctx = stage.getContext('2d'), audio = $('audio'), scrub = $('scrub');
const k = stage.width / 1920;
let tl, cues = [], xray = false, idle = 2.2;

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

function setPlaying(on) { $('ico-play').hidden = on; $('ico-pause').hidden = !on; }
$('play').onclick = () => {
  if (!audio.paused) { audio.pause(); return; }
  if (audio.ended || audio.currentTime >= tl.duration - 0.05) audio.currentTime = 0;
  audio.play();
};
audio.onplay = () => setPlaying(true);
audio.onpause = () => setPlaying(false);
audio.onended = () => setPlaying(false);
scrub.oninput = () => { audio.currentTime = Number(scrub.value); idle = audio.currentTime; };
$('mode').onclick = (e) => {
  const b = e.target.closest('button'); if (!b) return;
  xray = b.dataset.m === 'xray';
  for (const x of $('mode').children) x.setAttribute('aria-pressed', String(x === b));
};
$('cmd').onclick = () => navigator.clipboard?.writeText($('cmd').textContent);

const io = new IntersectionObserver((es) => es.forEach((e) => e.isIntersecting && e.target.classList.add('in')), { threshold: 0.15 });
document.querySelectorAll('.tile, .videos figure, .steps article, .cmd').forEach((el) => { el.classList.add('reveal'); io.observe(el); });

const [tlRes, cueRes] = await Promise.all([fetch('media/showreel.json'), fetch('media/showreel.cues.json')]);
tl = await tlRes.json(); cues = await cueRes.json();
scrub.max = tl.duration;
await Promise.all(['400', '700', '800'].map((w) => document.fonts.load(`${w} 40px "Bricolage Grotesque"`)));
loop();
