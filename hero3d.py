# 3D hero: aaj ki khabrein ek ghoomte 3D ring mein (CSS 3D + canvas, koi library nahi)

import base64
import html
import json
import os


def _audio_data(prid, lang):
    """Awaaz file ho to page ke andar hi daal do (chhoti files hi)."""
    for ext, mime in ((".ogg", "audio/ogg"), (".wav", "audio/wav")):
        path = f"khabar_{prid}_{lang}_f{ext}"
        if os.path.exists(path) and os.path.getsize(path) < 900_000:
            with open(path, "rb") as f:
                return f"data:{mime};base64," + base64.b64encode(f.read()).decode()
    return ""


def hero_html(rows, lang, L, get_cached, audience_names):
    items = []
    for prid, title, link, posted, fetched, audience in rows:
        s = get_cached(prid, lang) or {}
        items.append({
            "title": title,
            "link": link,
            "time": (posted or fetched)[11:16],
            "kicker": audience_names.get((audience or "").strip().lower(), "PIB"),
            "kya": s.get("kya_hua", ""),
            "asar": s.get("aap_pe_asar", ""),
            "karna": s.get("kya_karna_hai", ""),
            "audio": _audio_data(prid, lang),
        })
    labels = {k: L[k] for k in ("kya", "asar", "karna", "checked", "original", "listen", "explain")}
    safe = lambda obj: json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")
    page = TEMPLATE.replace("आज की <span>बड़ी खबरें</span>", html.escape(L.get("hero", "आज की बड़ी खबरें")))
    page = page.replace("← घुमाएं · Drag · Click →", html.escape(L.get("hint", "← Drag · Click →")))
    return page.replace("__DATA__", safe(items)).replace("__LABELS__", safe(labels))


TEMPLATE = r"""<!doctype html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Noto+Serif+Devanagari:wght@700;800&family=Mukta:wght@400;600;700&display=swap" rel="stylesheet">
<style>
* { box-sizing: border-box; }
body { margin: 0; font-family: Mukta, system-ui, sans-serif; }
.hero { position: relative; height: 640px; overflow: hidden; border-radius: 18px; color: #F4F1EA;
        background: radial-gradient(ellipse at 50% 115%, #1d4a3e 0%, #0d1c18 55%, #060a09 100%); }
#bg { position: absolute; inset: 0; width: 100%; height: 100%; }
.head { position: absolute; top: 18px; left: 24px; right: 24px; display: flex; justify-content: space-between;
        align-items: baseline; gap: 12px; flex-wrap: wrap; }
.head h1 { margin: 0; font-family: 'Noto Serif Devanagari', Georgia, serif; font-size: 26px; font-weight: 800; }
.head h1 span { color: #F2A65A; }
.hint { font-size: 13px; opacity: .7; }
.stage { position: absolute; top: 70px; left: 0; right: 0; height: 300px; perspective: 1100px; }
.ring { position: absolute; left: 50%; top: 50%; width: 0; height: 0; transform-style: preserve-3d; }
.card { position: absolute; width: 240px; height: 172px; left: -120px; top: -86px; border-radius: 14px;
        padding: 14px; text-align: left; color: #F4F1EA; font-family: inherit; cursor: pointer;
        background: linear-gradient(160deg, rgba(255,255,255,.16), rgba(255,255,255,.04));
        border: 1px solid rgba(255,255,255,.2); box-shadow: 0 22px 44px rgba(0,0,0,.5);
        backdrop-filter: blur(6px); backface-visibility: hidden; transition: border-color .3s, box-shadow .3s; }
.card.active { border-color: #F2A65A; box-shadow: 0 0 0 2px #F2A65A, 0 26px 54px rgba(0,0,0,.55); }
.kicker { font-size: 11px; font-weight: 700; letter-spacing: .08em; text-transform: uppercase; color: #F2A65A; }
.ctitle { font-family: 'Noto Serif Devanagari', Georgia, serif; font-size: 16px; font-weight: 700; line-height: 1.4;
          margin-top: 6px; display: -webkit-box; -webkit-line-clamp: 4; -webkit-box-orient: vertical; overflow: hidden; }
.ctime { position: absolute; bottom: 10px; left: 14px; font-size: 12px; opacity: .75; }
.nav { position: absolute; top: 196px; width: 44px; height: 44px; border-radius: 50%; border: 1px solid rgba(255,255,255,.35);
       background: rgba(0,0,0,.35); color: #F4F1EA; font-size: 22px; cursor: pointer; }
.nav.prev { left: 16px; } .nav.next { right: 16px; }
.panel { position: absolute; left: 24px; right: 24px; bottom: 20px; height: 230px; overflow: auto;
         background: rgba(255,255,255,.07); border: 1px solid rgba(255,255,255,.15); border-radius: 14px; padding: 16px 18px; }
.panel h2 { margin: 0 0 6px; font-family: 'Noto Serif Devanagari', Georgia, serif; font-size: 20px; line-height: 1.4; }
.panel h4 { margin: 10px 0 2px; font-size: 13px; letter-spacing: .04em; color: #8FD4B8; }
.panel p { margin: 0; font-size: 15.5px; line-height: 1.6; }
.check { display: inline-block; margin-top: 10px; font-size: 12.5px; color: #8FD4B8;
         background: rgba(143,212,184,.15); border-radius: 6px; padding: 2px 8px; }
.btns { display: flex; gap: 10px; margin-top: 12px; flex-wrap: wrap; }
.btn { background: #F2A65A; color: #1b1206; border: none; border-radius: 999px; padding: 9px 18px; font-weight: 700;
       cursor: pointer; font-family: inherit; font-size: 14px; text-decoration: none; }
.btn.ghost { background: transparent; color: #F4F1EA; border: 1px solid rgba(255,255,255,.4); }
.muted { opacity: .8; font-size: 15px; }
@media (max-width: 640px) {
  .card { width: 180px; height: 150px; left: -90px; top: -75px; } .ctitle { font-size: 14px; -webkit-line-clamp: 3; }
  .head h1 { font-size: 21px; } .panel { height: 250px; }
}
</style></head>
<body>
<div class="hero">
  <canvas id="bg" aria-hidden="true"></canvas>
  <div class="head"><h1>आज की <span>बड़ी खबरें</span></h1><div class="hint">← घुमाएं · Drag · Click →</div></div>
  <div class="stage" id="stage"><div class="ring" id="ring"></div></div>
  <button class="nav prev" id="prev" aria-label="Previous">‹</button>
  <button class="nav next" id="next" aria-label="Next">›</button>
  <div class="panel" id="panel" aria-live="polite"></div>
</div>
<script>
const DATA = __DATA__;
const L = __LABELS__;
const ring = document.getElementById("ring");
const panel = document.getElementById("panel");
const stage = document.getElementById("stage");
const calm = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
const n = Math.max(DATA.length, 1);
const step = 360 / n;
const cardW = window.innerWidth < 640 ? 180 : 240;
const radius = Math.max(220, Math.round((cardW / 2) / Math.tan(Math.PI / n) + 50));
let angle = 0, target = null, dragging = false, lastX = 0, hover = false, active = -1;
let player = null;

// ---- Cards ----
const cards = DATA.map((d, i) => {
  const b = document.createElement("button");
  b.className = "card";
  b.style.transform = `rotateY(${i * step}deg) translateZ(${radius}px)`;
  const k = document.createElement("div"); k.className = "kicker"; k.textContent = d.kicker;
  const t = document.createElement("div"); t.className = "ctitle"; t.textContent = d.title;
  const tm = document.createElement("div"); tm.className = "ctime"; tm.textContent = "🕒 " + d.time + " · PIB";
  b.append(k, t, tm);
  b.addEventListener("click", () => { target = -i * step; });
  ring.appendChild(b);
  return b;
});

function el(tag, cls, text) { const e = document.createElement(tag); if (cls) e.className = cls; if (text) e.textContent = text; return e; }

// ---- Neeche wala panel ----
function showPanel(i) {
  const d = DATA[i]; if (!d) return;
  if (player) { player.pause(); player = null; }
  panel.replaceChildren();
  panel.append(el("h2", "", d.title));
  if (d.kya) {
    panel.append(el("h4", "", L.kya), el("p", "", d.kya));
    if (d.asar) panel.append(el("h4", "", L.asar), el("p", "", d.asar));
    if (d.karna) panel.append(el("h4", "", L.karna), el("p", "", d.karna));
    panel.append(el("div", "check", L.checked));
  } else {
    panel.append(el("p", "muted", L.explain + " ↓"));
  }
  const btns = el("div", "btns");
  if (d.audio) {
    const b = el("button", "btn", L.listen);
    b.addEventListener("click", () => {
      if (player && !player.paused) { player.pause(); return; }
      player = new Audio(d.audio); player.play();
    });
    btns.append(b);
  }
  const a = el("a", "btn ghost", L.original + " ↗"); a.href = d.link; a.target = "_blank"; a.rel = "noopener";
  btns.append(a);
  panel.append(btns);
}

// ---- Ghumana: auto, drag, buttons ----
document.getElementById("prev").onclick = () => { target = Math.round(angle / step) * step + step; };
document.getElementById("next").onclick = () => { target = Math.round(angle / step) * step - step; };
stage.addEventListener("pointerenter", () => hover = true);
stage.addEventListener("pointerleave", () => { hover = false; dragging = false; });
stage.addEventListener("pointerdown", e => { dragging = true; lastX = e.clientX; target = null; });
window.addEventListener("pointerup", () => { if (dragging) { dragging = false; target = Math.round(angle / step) * step; } });
window.addEventListener("pointermove", e => { if (dragging) { angle += (e.clientX - lastX) * 0.35; lastX = e.clientX; } });

function frame() {
  if (target !== null) {
    angle += (target - angle) * 0.12;
    if (Math.abs(target - angle) < 0.05) { angle = target; target = null; }
  } else if (!dragging && !hover && !calm) {
    angle -= 0.06;
  }
  ring.style.transform = `translateZ(-${radius}px) rotateY(${angle}deg)`;
  const idx = ((Math.round(-angle / step) % n) + n) % n;
  if (idx !== active) {
    if (cards[active]) cards[active].classList.remove("active");
    active = idx; if (cards[active]) cards[active].classList.add("active");
    showPanel(active);
  }
  requestAnimationFrame(frame);
}

// ---- Peeche taare (canvas) ----
const cv = document.getElementById("bg"), ctx = cv.getContext("2d");
let W, H, pts = [];
function resize() {
  W = cv.width = cv.offsetWidth; H = cv.height = cv.offsetHeight;
  pts = Array.from({ length: 70 }, (_, i) => ({ x: Math.random() * W, y: Math.random() * H,
        vx: (Math.random() - .5) * .25, vy: (Math.random() - .5) * .25, c: i % 3 }));
}
const colors = ["rgba(242,166,90,", "rgba(255,255,255,", "rgba(143,212,184,"];
function stars() {
  ctx.clearRect(0, 0, W, H);
  for (const p of pts) {
    if (!calm) { p.x += p.vx; p.y += p.vy; }
    if (p.x < 0 || p.x > W) p.vx *= -1; if (p.y < 0 || p.y > H) p.vy *= -1;
    ctx.fillStyle = colors[p.c] + ".8)"; ctx.beginPath(); ctx.arc(p.x, p.y, 1.6, 0, 7); ctx.fill();
  }
  for (let i = 0; i < pts.length; i++) for (let j = i + 1; j < pts.length; j++) {
    const a = pts[i], b = pts[j], dist = Math.hypot(a.x - b.x, a.y - b.y);
    if (dist < 110) { ctx.strokeStyle = colors[a.c] + (0.18 * (1 - dist / 110)) + ")";
      ctx.beginPath(); ctx.moveTo(a.x, a.y); ctx.lineTo(b.x, b.y); ctx.stroke(); }
  }
  requestAnimationFrame(stars);
}
window.addEventListener("resize", resize);
resize(); stars(); frame();
</script>
</body></html>
"""
