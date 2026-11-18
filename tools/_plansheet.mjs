import { createCanvas, GlobalFonts } from '@napi-rs/canvas';
import { writeFileSync } from 'node:fs';
import { drawFrame } from '/home/user/sandbox/docs/engine/render.js';
import { plan } from '/home/user/sandbox/docs/engine/planner.js';
for (const w of [400, 700, 800]) GlobalFonts.registerFromPath(`/home/user/sandbox/docs/fonts/bricolage-grotesque-latin-${w}-normal.woff2`, 'Bricolage Grotesque');
const [p, v, out] = process.argv.slice(2);
const { tl } = plan(p, v === '1');
const c = createCanvas(tl.width / 3, tl.height / 3), x = c.getContext('2d');
const files = [];
const W = c.width, H = c.height, sheet = createCanvas(W * 4, H * 2), sx = sheet.getContext('2d');
for (let i = 0; i < 8; i++) { x.clearRect(0, 0, W, H); drawFrame(x, tl, 29 * (i + 0.55) / 8, 1 / 3); sx.drawImage(c, (i % 4) * W, Math.floor(i / 4) * H); }
writeFileSync(out, sheet.toBuffer('image/png'));
