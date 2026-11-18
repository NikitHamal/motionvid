// node tools/render_video.mjs <timeline.json> <out.mp4> [--audio a.wav] [--cues cues.json] [--width 1280] [--poster t]
// Frame-exact render of a motionvid timeline (same engine as the site) piped into ffmpeg, muxed with the audio.
import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import ffmpegPath from 'ffmpeg-static';
import { spawn } from 'node:child_process';
import { readFileSync, writeFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';
import { drawFrame } from '../docs/engine/render.js';
import { drawXray } from '../docs/engine/xray.js';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
for (const w of [400, 700, 800]) GlobalFonts.registerFromPath(join(root, `docs/fonts/bricolage-grotesque-latin-${w}-normal.woff2`), 'Bricolage Grotesque');

const [tlPath, outPath, ...rest] = process.argv.slice(2);
const opt = (n, d) => { const i = rest.indexOf(`--${n}`); return i < 0 ? d : rest[i + 1]; };
const tl = JSON.parse(readFileSync(tlPath, 'utf8'));
const cues = opt('cues') ? JSON.parse(readFileSync(opt('cues'), 'utf8')) : null;
const width = Number(opt('width', 1280)), k = width / tl.width, height = Math.round(tl.height * k);
const canvas = createCanvas(width, height), ctx = canvas.getContext('2d');
const blur = Math.max(1, Number(opt('blur', 1)));
const acc = blur > 1 ? createCanvas(width, height) : canvas, actx = acc.getContext('2d');
// motion blur: average `blur` sub-frames across a half-frame shutter; the canvas is both source and accumulator when blur = 1
const frame = (t) => {
  if (blur === 1) drawFrame(ctx, tl, t, k);
  else for (let j = 0; j < blur; j++) {
    drawFrame(ctx, tl, t + ((j + 0.5) / blur - 0.5) * 0.5 / tl.fps, k);
    actx.globalAlpha = 1 / (j + 1);
    actx.drawImage(canvas, 0, 0);
  }
  actx.globalAlpha = 1;
  if (cues) drawXray(actx, tl, cues, t, k);
};

if (opt('poster')) { frame(Number(opt('poster'))); writeFileSync(outPath, acc.toBuffer('image/png')); process.exit(0); }

const n = Math.round(tl.duration * tl.fps);
const args = ['-y', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${width}x${height}`, '-r', String(tl.fps), '-i', '-'];
if (opt('audio')) args.push('-i', opt('audio'));
args.push('-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '20', '-preset', 'medium', '-movflags', '+faststart');
if (opt('audio')) args.push('-c:a', 'aac', '-b:a', '160k', '-shortest');
args.push(outPath);
const ff = spawn(ffmpegPath, args, { stdio: ['pipe', 'ignore', 'inherit'] });
const done = new Promise((res, rej) => { ff.on('close', (c) => (c === 0 ? res() : rej(new Error(`ffmpeg exit ${c}`)))); });
for (let i = 0; i < n; i++) {
  frame(i / tl.fps);
  if (!ff.stdin.write(acc.data())) await new Promise((r) => ff.stdin.once('drain', r));
}
ff.stdin.end();
await done;
console.log(`${outPath}: ${n} frames, ${width}x${height}, ${opt('audio') ? 'with audio' : 'silent'}`);
