// Cue x-ray: draws every compiled sound cue on a strip over the frame. Shared by site, Studio and the video renderer.
const ROLE_COLOR = { click: '#F6EFE3', ui_pop: '#FFD54A', impact: '#FF6A45', whoosh: '#3DDBA7', riser: '#FF9DBB' };

export function drawXray(ctx, tl, cues, t, k = 1) {
  const pad = 70, y0 = tl.height - 190, h = 130, w = tl.width - pad * 2;
  ctx.save();
  ctx.scale(k, k);
  ctx.fillStyle = 'rgba(23,19,15,0.82)';
  ctx.beginPath(); ctx.roundRect(pad - 30, y0 - 50, w + 60, h + 100, 36); ctx.fill();
  ctx.lineCap = 'round';
  for (const c of cues) {
    const x = pad + (c.t / tl.duration) * w;
    const mag = Math.max(0.12, 1 - Math.abs(c.gain_db) / 24);
    const live = t >= c.t && t - c.t < 0.18;
    ctx.strokeStyle = ROLE_COLOR[c.role] || '#F6EFE3';
    ctx.globalAlpha = t >= c.t ? 1 : 0.38;
    ctx.lineWidth = live ? 9 : 5;
    ctx.beginPath(); ctx.moveTo(x, y0 + h); ctx.lineTo(x, y0 + h - h * mag * (live ? 1.1 : 1)); ctx.stroke();
  }
  ctx.globalAlpha = 1;
  const px = pad + (t / tl.duration) * w;
  ctx.fillStyle = '#F6EFE3';
  ctx.fillRect(px - 2, y0 - 12, 4, h + 24);
  ctx.font = '700 34px "Bricolage Grotesque", system-ui, sans-serif';
  ctx.textBaseline = 'middle';
  const live = cues.filter((c) => t >= c.t && t - c.t < 0.5 && c.role !== 'click').slice(-3);
  ctx.textAlign = 'left';
  live.forEach((c, i) => {
    ctx.fillStyle = ROLE_COLOR[c.role] || '#F6EFE3';
    ctx.fillText(`${c.role}  ${c.t.toFixed(2)}s`, pad + i * 340, y0 - 22);
  });
  ctx.restore();
}
