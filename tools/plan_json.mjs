// node tools/plan_json.mjs "<prompt>" out.json [--vertical] [--aspect 4:5] [--long] [--seed n]: the Create page planner, headless (agents and tests use it).
import { writeFileSync } from 'node:fs';
import { plan } from '../docs/engine/planner.js';
const [prompt, out, ...rest] = process.argv.slice(2);
const seed = rest.includes('--seed') ? Number(rest[rest.indexOf('--seed') + 1]) : 0;
const aspect = rest.includes('--aspect') ? rest[rest.indexOf('--aspect') + 1] : undefined;
const r = plan(prompt, rest.includes('--vertical'), seed, { long: rest.includes('--long'), aspect });
writeFileSync(out, JSON.stringify(r.tl));
console.log(`${out}: ${r.brief.cat}, ${r.tl.elements.length} elements, acts ${r.acts.map((a) => a[0]).join('/')}`);
