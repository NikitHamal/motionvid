"""Self-contained HTML preview: animates the timeline on a canvas, in sync with audio.wav."""

from __future__ import annotations

import json
from typing import Any

EASE_JS = """
const B=u=>{const n=7.5625,d=2.75;if(u<1/d)return n*u*u;if(u<2/d){u-=1.5/d;return n*u*u+.75}
if(u<2.5/d){u-=2.25/d;return n*u*u+.9375}u-=2.625/d;return n*u*u+.984375};
const E={linear:u=>u,inQuad:u=>u*u,outQuad:u=>1-(1-u)**2,inOutQuad:u=>u<.5?2*u*u:1-(-2*u+2)**2/2,
inCubic:u=>u**3,outCubic:u=>1-(1-u)**3,inOutCubic:u=>u<.5?4*u**3:1-(-2*u+2)**3/2,
inExpo:u=>u<=0?0:2**(10*u-10),outExpo:u=>u>=1?1:1-2**(-10*u),
outBack:u=>1+2.70158*(u-1)**3+1.70158*(u-1)**2,outBounce:B};
function val(k,t){if(!k)return null;if(t<=k[0].t)return k[0].v;if(t>=k[k.length-1].t)return k[k.length-1].v;
for(let i=0;i<k.length-1;i++){const a=k[i],b=k[i+1];if(t>=a.t&&t<=b.t){const s=b.t-a.t,u=s<=0?1:(t-a.t)/s;
return a.v+(b.v-a.v)*E[b.ease||'linear'](u)}}return k[k.length-1].v}
"""

PAGE = """<!doctype html><meta charset=utf-8><title>motionvid preview</title>
<body style="margin:0;background:#0b0b10;color:#ddd;font:14px system-ui;text-align:center">
<canvas id=c width=%(w)d height=%(h)d style="width:min(96vw,960px);background:#111;margin-top:12px"></canvas><br>
<button id=b style="margin:10px;padding:8px 18px">Play with sound</button><span id=s></span>
<audio id=a src="audio.wav"></audio>
<script>
const TL=%(tl)s,CUES=%(cues)s;%(ease)s
const c=document.getElementById('c'),x=c.getContext('2d'),a=document.getElementById('a');
function draw(t){x.fillStyle='#111';x.fillRect(0,0,c.width,c.height);
for(const e of TL.elements){const T=e.tracks||{},g=(n,d)=>{const v=val(T[n],t);return v===null?d:v};
const px=g('x',c.width/2),py=g('y',c.height/2),sc=g('scale',1),op=g('opacity',1),rot=g('rotation',0);
x.save();x.globalAlpha=Math.max(0,Math.min(1,op));x.translate(px,py);x.rotate(rot*Math.PI/180);x.scale(sc,sc);
x.fillStyle=e.color||'#7cf';if(e.kind==='text'){x.font=(e.size||96)+'px system-ui';x.textAlign='center';
x.fillText(e.text||e.id,0,0)}else{const w=e.w||160,h=e.h||160;x.fillRect(-w/2,-h/2,w,h)}x.restore()}
for(const q of CUES){const d=t-q.t;if(d>=0&&d<.12){x.fillStyle='rgba(255,200,60,'+(1-d/.12)+')';
x.fillRect(0,0,c.width,10);x.font='28px monospace';x.fillText(q.role,20,50)}}
document.getElementById('s').textContent=' t='+t.toFixed(2)+'s'}
let raf;function loop(){draw(a.currentTime);raf=requestAnimationFrame(loop)}
document.getElementById('b').onclick=()=>{a.currentTime=0;a.play();cancelAnimationFrame(raf);loop()};
a.onended=()=>cancelAnimationFrame(raf);draw(0);
</script>
"""


def html(tl: dict[str, Any], cues: list[dict[str, Any]]) -> str:
    slim = [{"role": c["role"], "t": c["t"]} for c in cues]
    return PAGE % {"w": tl["width"], "h": tl["height"], "tl": json.dumps(tl), "cues": json.dumps(slim), "ease": EASE_JS}
