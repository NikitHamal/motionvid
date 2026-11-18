import { useEffect, useMemo, useRef, useState } from "react";
import tlJson from "../docs/media/showreel.json";
import cueJson from "../docs/media/showreel.cues.json";
import audioUrl from "../docs/media/showreel.m4a?url";
import { drawFrame } from "../docs/engine/render.js";
import type { Cue, Timeline } from "../docs/engine/render.js";
import { drawXray } from "../docs/engine/xray.js";

const tl = tlJson as unknown as Timeline;
const cues = cueJson as unknown as Cue[];
const ROLES = ["click", "ui_pop", "impact", "whoosh", "riser"];
const K = 1280 / 1920;
const fmt = (s: number) => `${Math.floor(s / 60)}:${String(Math.floor(s % 60)).padStart(2, "0")}`;

export default function App() {
  const canvas = useRef<HTMLCanvasElement>(null);
  const audio = useRef<HTMLAudioElement>(null);
  const [t, setT] = useState(2.2);
  const [playing, setPlaying] = useState(false);
  const [xray, setXray] = useState(true);
  const [off, setOff] = useState<Set<string>>(new Set());
  const rows = useRef<HTMLUListElement>(null);

  useEffect(() => {
    let raf = 0;
    const tick = () => {
      const a = audio.current!;
      setT((p) => (a.paused && a.currentTime === 0 ? p : a.currentTime));
      raf = requestAnimationFrame(tick);
    };
    document.fonts.load('800 40px "Bricolage Grotesque"').then(() => { raf = requestAnimationFrame(tick); });
    return () => cancelAnimationFrame(raf);
  }, []);

  useEffect(() => {
    const ctx = canvas.current!.getContext("2d")!;
    drawFrame(ctx, tl, Math.min(t, tl.duration), K);
    if (xray) drawXray(ctx, tl, cues, Math.min(t, tl.duration), K);
  }, [t, xray]);

  const visible = useMemo(() => cues.filter((c) => !off.has(c.role)), [off]);
  const active = visible.reduce((n, c, i) => (c.t <= t ? i : n), -1);
  useEffect(() => {
    rows.current?.children[active]?.scrollIntoView({ block: "nearest" });
  }, [active]);

  const seek = (s: number) => { audio.current!.currentTime = s; setT(s); };
  const toggle = () => {
    const a = audio.current!;
    if (a.paused) { if (a.ended) a.currentTime = 0; void a.play(); } else a.pause();
  };

  return (
    <div className="studio">
      <header>
        <b className="mark">motionvid <span>studio</span></b>
        <div className="seg">
          <button aria-pressed={!xray} onClick={() => setXray(false)}>Clean</button>
          <button aria-pressed={xray} onClick={() => setXray(true)}>X-ray</button>
        </div>
      </header>

      <section className="stage">
        <canvas ref={canvas} width={1280} height={720} />
        <div className="bar">
          <button className="fab" onClick={toggle} aria-label={playing ? "Pause" : "Play with sound"}>
            <svg className="i" viewBox="0 0 24 24">{playing ? <path d="M7 5h4v14H7zM13 5h4v14h-4z" /> : <path d="M8 5v14l11-7z" />}</svg>
          </button>
          <input type="range" min={0} max={tl.duration} step={0.01} value={Math.min(t, tl.duration)}
            onChange={(e) => seek(Number(e.target.value))} aria-label="Seek" />
          <output>{fmt(t)}</output>
        </div>
        <audio ref={audio} src={audioUrl} preload="auto"
          onPlay={() => setPlaying(true)} onPause={() => setPlaying(false)} onEnded={() => setPlaying(false)} />
      </section>

      <aside className="cues">
        <div className="chips">
          {ROLES.map((r) => (
            <button key={r} className={`chip ${r}`} aria-pressed={!off.has(r)}
              onClick={() => setOff((p) => { const n = new Set(p); n.has(r) ? n.delete(r) : n.add(r); return n; })}>
              {r}<i>{cues.filter((c) => c.role === r).length}</i>
            </button>
          ))}
        </div>
        <ul ref={rows}>
          {visible.map((c, i) => (
            <li key={`${c.t}-${c.role}-${i}`} className={i === active ? "on" : ""}>
              <button onClick={() => seek(Math.max(0, c.t - 0.3))}>
                <em className={c.role}>{c.role}</em>
                <span>{c.why}</span>
                <b>{c.t.toFixed(2)}</b>
              </button>
            </li>
          ))}
        </ul>
      </aside>
    </div>
  );
}
