// motionvid MCP server (stdio, no dependencies). Tools: skill, plan_video, render_poster, render_video, list_demos.
// Register: { "command": "node", "args": ["tools/mcp_server.mjs"] }. Agents read the skill first, plan, look at a poster, then render.
import { readFileSync, writeFileSync, mkdirSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { dirname, join } from 'node:path';
import { plan } from '../docs/engine/planner.js';

const ROOT = join(dirname(fileURLToPath(import.meta.url)), '..');
const OUT = join(ROOT, 'out', 'mcp');
mkdirSync(OUT, { recursive: true });
const prompt = { type: 'string', description: 'What the video is for: product name, what it does, who it is for' };
const common = { prompt, aspect: { type: 'string', enum: ['16:9', '9:16', '4:5'] }, long: { type: 'boolean' }, seed: { type: 'integer' } };
const TOOLS = {
  skill: { description: 'Read docs/SKILL.md: the rules for top-tier motion videos. Read before writing any scene.', props: {}, run: () => readFileSync(join(ROOT, 'docs/SKILL.md'), 'utf8') },
  list_demos: { description: 'List the published demos (id, brief, duration, aspect).', props: {}, run: () => readFileSync(join(ROOT, 'docs/demos.json'), 'utf8') },
  plan_video: { description: 'Prompt to timeline JSON (path and summary). Same prompt with another seed gives another hero object.', props: common, required: ['prompt'],
    run: (a) => { const r = plan(a.prompt, a.aspect === '9:16', a.seed || 0, { long: !!a.long, aspect: a.aspect }); const f = join(OUT, `plan_${Date.now()}.json`); writeFileSync(f, JSON.stringify(r.tl)); return JSON.stringify({ timeline: f, category: r.brief.cat, name: r.brief.name, acts: r.acts, duration: r.tl.duration }); } },
  render_poster: { description: 'Render one frame of a timeline to PNG so you can look at it.', props: { timeline: { type: 'string' }, t: { type: 'number' }, width: { type: 'integer' } }, required: ['timeline', 't'],
    run: (a) => { const f = join(OUT, `poster_${Date.now()}.png`); const p = spawnSync('node', [join(ROOT, 'tools/render_video.mjs'), a.timeline, f, '--poster', String(a.t), '--width', String(a.width || 960)], { encoding: 'utf8' }); return p.status === 0 ? f : p.stderr; } },
  render_video: { description: 'Render the full video with sound (mp4). Slow on CPU: about 8 s of wall time per second of video at 60 fps.', props: { timeline: { type: 'string' }, width: { type: 'integer' } }, required: ['timeline'],
    run: (a) => { const d = join(OUT, `video_${Date.now()}`); const p = spawnSync('python3', ['-m', 'motionvid', 'video', a.timeline, d, '--width', String(a.width || 1280), '--blur', '3'], { cwd: ROOT, env: { ...process.env, PYTHONPATH: join(ROOT, 'src') }, encoding: 'utf8' }); return p.status === 0 ? join(d, 'final.mp4') : p.stderr.slice(-800); } },
};
const send = (m) => process.stdout.write(JSON.stringify({ jsonrpc: '2.0', ...m }) + '\n');
function handle(m) {
  if (m.method === 'initialize') return send({ id: m.id, result: { protocolVersion: '2024-11-05', capabilities: { tools: {} }, serverInfo: { name: 'motionvid', version: '0.10.0' } } });
  if (m.method === 'tools/list') return send({ id: m.id, result: { tools: Object.entries(TOOLS).map(([name, t]) => ({ name, description: t.description, inputSchema: { type: 'object', properties: t.props, required: t.required || [] } })) } });
  if (m.method === 'tools/call') {
    const t = TOOLS[m.params.name];
    if (!t) return send({ id: m.id, error: { code: -32602, message: 'unknown tool' } });
    try { return send({ id: m.id, result: { content: [{ type: 'text', text: String(t.run(m.params.arguments || {})) }] } }); } catch (e) { return send({ id: m.id, result: { isError: true, content: [{ type: 'text', text: String(e.message) }] } }); }
  }
  if (m.id !== undefined) send({ id: m.id, result: {} });
}
let buf = '';
process.stdin.on('data', (d) => { buf += d; let i; while ((i = buf.indexOf('\n')) >= 0) { const l = buf.slice(0, i).trim(); buf = buf.slice(i + 1); if (l) handle(JSON.parse(l)); } });
