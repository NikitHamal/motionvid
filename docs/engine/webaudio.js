// Browser preview synth for the Create page: a quick stand-in for the Python engine (the exported video uses the real DSP engine).
const DB = (db) => 10 ** (db / 20);

export class Preview {
  constructor() { this.ctx = null; this.t0 = 0; this.from = 0; this.playing = false; this.nodes = []; }
  events(tl) {
    const ev = tl.sfx.map((s) => ({ ...s }));
    for (const c of tl.cuts) ev.push({ t: c.t - 0.16, role: 'whoosh', gain_db: -12, pan: 0 }, { t: c.t, role: 'impact', gain_db: -9, pan: 0 });
    return ev.sort((a, b) => a.t - b.t);
  }
  get time() { return this.playing ? this.from + (this.ctx.currentTime - this.t0) : this.from; }
  play(tl, from = 0) {
    this.ctx ||= new AudioContext();
    this.ctx.resume();
    this.stop(); this.from = from; this.t0 = this.ctx.currentTime + 0.06; this.playing = true;
    this.noise ||= (() => { const b = this.ctx.createBuffer(1, this.ctx.sampleRate, this.ctx.sampleRate), d = b.getChannelData(0); for (let i = 0; i < d.length; i++) d[i] = Math.random() * 2 - 1; return b; })();
    for (const e of this.events(tl)) if (e.t >= from) this.voice(e, this.t0 + e.t - from);
  }
  stop() { this.nodes.forEach((n) => { try { n.stop(); } catch { /* already ended */ } }); this.nodes = []; if (this.playing) this.from = this.time; this.playing = false; }
  out(e, at) { const g = this.ctx.createGain(), p = this.ctx.createStereoPanner(); p.pan.value = Math.max(-1, Math.min(1, e.pan || 0)); g.connect(p).connect(this.ctx.destination); g.gain.value = 0; return { g, at, v: DB(e.gain_db ?? -12) }; }
  osc(o, f0, f1, dur, shape = 'sine', f = 1) {
    const x = this.ctx.createOscillator(); x.type = shape; x.frequency.setValueAtTime(f0, o.at); if (f1) x.frequency.exponentialRampToValueAtTime(f1, o.at + dur * 0.4);
    o.g.gain.setValueAtTime(0, o.at); o.g.gain.linearRampToValueAtTime(o.v * f, o.at + 0.003); o.g.gain.exponentialRampToValueAtTime(0.0001, o.at + dur);
    x.connect(o.g); x.start(o.at); x.stop(o.at + dur + 0.05); this.nodes.push(x);
  }
  sweep(o, f0, f1, dur, peak = 0.4, q = 1.2) {
    const s = this.ctx.createBufferSource(), bp = this.ctx.createBiquadFilter(); s.buffer = this.noise; s.loop = true; bp.type = 'bandpass'; bp.Q.value = q;
    bp.frequency.setValueAtTime(f0, o.at); bp.frequency.exponentialRampToValueAtTime(f1, o.at + dur * peak); bp.frequency.exponentialRampToValueAtTime(f0, o.at + dur);
    o.g.gain.setValueAtTime(0, o.at); o.g.gain.linearRampToValueAtTime(o.v * 1.6, o.at + dur * peak); o.g.gain.linearRampToValueAtTime(0, o.at + dur);
    s.connect(bp).connect(o.g); s.start(o.at); s.stop(o.at + dur + 0.05); this.nodes.push(s);
  }
  voice(e, at) {
    const o = this.out(e, at), r = e.role, fr = e.freq || 523;
    if (r === 'click') this.osc(o, 520, 0, 0.03, 'sine', 1.2);
    else if (r === 'pop') this.osc(o, 330, 380, 0.12);
    else if (r === 'tick') this.osc(o, 1100 * 2 ** ((e.st || 0) / 12), 0, 0.018, 'triangle', 0.8);
    else if (r === 'pluck' || r === 'chime' || r === 'notify') { this.osc(o, fr, 0, 0.4, 'triangle'); const o2 = this.out(e, at + 0.075); this.osc(o2, fr * 1.5, 0, 0.4, 'triangle', 0.7); }
    else if (r === 'toggle') { this.osc(o, 420, 0, 0.03); const o2 = this.out(e, at + 0.06); this.osc(o2, 640, 0, 0.03); }
    else if (r === 'swipe') this.sweep(o, 380, 1700, 0.24, 0.4, 1.4);
    else if (r === 'whoosh') this.sweep(o, 140, 1300, 0.38, 0.55, 1.6);
    else if (r === 'impact' || r === 'sub') this.osc(o, 92, 36, 0.28, 'sine', 1.6);
    else if (r === 'riser') this.sweep(o, 200, 2400, e.dur || 0.6, 0.95, 1.6);
  }
}
