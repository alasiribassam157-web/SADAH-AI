"""The look of every generated site: one stylesheet, light and dark (prefers-color-scheme), responsive, printable.
Pure CSS: no fonts, images or scripts are fetched. The accent colour comes from the request; text on it is white (or near-black on a light
accent), and every accent in COLORS is dark enough for white. Modern touches: a glass header, a mesh-gradient hero with rounded bottom, numbered
cards with a lift on hover, accent-tinted sections, bars that grow in, and scroll-driven reveal where the browser supports it (no JS).
Every animation stops under prefers-reduced-motion."""

from builder import themes

CSS = """:root{--accent:__ACCENT__;--on:__ON__;--accent-text:__TEXT__;--deep:__DEEP__;--shade:__SHADE__;--ink:#1b2333;--muted:#586174;--bg:#ffffff;--soft:color-mix(in srgb,var(--accent) 5%,#f4f6fb);--card:#ffffff;--line:#e3e7ef;--shadow:0 1px 2px rgba(15,23,42,.05),0 14px 34px rgba(15,23,42,.08);--radius:18px;--glass:color-mix(in srgb,var(--bg) 80%,transparent)}
@media (prefers-color-scheme:dark){:root{--ink:#e8ecf4;--muted:#9aa5b8;--bg:#0a101d;--soft:color-mix(in srgb,var(--accent) 7%,#0f1830);--card:#141e35;--line:#232f4a;--shadow:0 1px 2px rgba(0,0,0,.4),0 16px 38px rgba(0,0,0,.45)}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:"Segoe UI Variable","Segoe UI","SF Arabic","Geeza Pro","Noto Sans Arabic",Tahoma,"Noto Naskh Arabic",Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.85;direction:rtl;text-align:right;-webkit-font-smoothing:antialiased;text-rendering:optimizeLegibility}
::selection{background:color-mix(in srgb,var(--accent) 30%,transparent)}
header{position:sticky;top:0;z-index:5;background:var(--glass);color:var(--ink);padding:10px 24px;display:flex;flex-wrap:wrap;gap:6px 20px;align-items:center;justify-content:space-between;border-bottom:1px solid var(--line);-webkit-backdrop-filter:blur(14px) saturate(1.5);backdrop-filter:blur(14px) saturate(1.5)}
header strong{display:flex;align-items:center;gap:10px;font-size:1.15rem}
header strong::before{content:"";width:28px;height:28px;border-radius:9px;background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 55%,var(--deep)));box-shadow:0 4px 14px color-mix(in srgb,var(--accent) 45%,transparent)}
nav{display:flex;flex-wrap:wrap;gap:2px 4px}
header a{color:var(--ink);text-decoration:none;padding:6px 14px;border-radius:999px;font-size:.95rem;transition:background .2s,color .2s}
header a:hover{background:color-mix(in srgb,var(--accent) 12%,transparent);color:var(--accent-text)}
.hero{position:relative;overflow:hidden;padding:clamp(72px,12vw,120px) 24px clamp(64px,10vw,104px);text-align:center;color:var(--on);background:radial-gradient(60% 80% at 12% 0,rgba(255,255,255,.2),transparent 60%),radial-gradient(55% 70% at 100% 100%,var(--shade),transparent 70%),linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 50%,var(--deep)));background-size:140% 140%,140% 140%,100% 100%;background-position:0 0,100% 100%,0 0;border-radius:0 0 clamp(28px,6vw,64px) clamp(28px,6vw,64px);animation:drift 20s ease-in-out infinite alternate}
.hero>:not(svg){position:relative}
.hero .art{position:absolute;inset:0;width:100%;height:100%;color:var(--on);opacity:.16;pointer-events:none}
.hero h1{margin:0 0 16px;font-size:clamp(2.1rem,6.5vw,3.8rem);font-weight:800;line-height:1.25;text-wrap:balance;text-shadow:0 2px 20px rgba(0,0,0,.16)}
.hero p{margin:0 auto;max-width:36em;font-size:clamp(1.02rem,2.4vw,1.2rem);opacity:.95;text-wrap:balance}
.hero .btn{background:var(--on);color:var(--accent);margin-top:28px;padding:14px 34px;font-weight:700;box-shadow:0 12px 30px rgba(0,0,0,.25)}
.hero .btn::after{content:"\\2190"}
.btn,button{display:inline-flex;align-items:center;justify-content:center;gap:10px;margin-top:12px;padding:12px 28px;background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 78%,var(--deep)));color:var(--on);border:0;border-radius:999px;text-decoration:none;font:inherit;font-weight:600;cursor:pointer;box-shadow:0 6px 18px color-mix(in srgb,var(--accent) 32%,transparent);transition:transform .18s,box-shadow .18s}
.btn:hover,button:hover{transform:translateY(-2px);box-shadow:0 12px 26px color-mix(in srgb,var(--accent) 42%,transparent)}
.btn:active,button:active{transform:scale(.97)}
:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 65%,#fff);outline-offset:3px}
section{counter-reset:c;max-width:1040px;margin:0 auto;padding:clamp(40px,7vw,72px) 24px;scroll-margin-top:72px}
main section:nth-child(even){box-shadow:0 0 0 100vmax var(--soft);clip-path:inset(0 -100vmax);background:var(--soft)}
h2{position:relative;margin:0 0 28px;padding-top:18px;font-size:clamp(1.5rem,3.4vw,2.05rem);line-height:1.4;text-wrap:balance}
h2::before{content:"";position:absolute;top:0;inset-inline-start:0;width:46px;height:5px;border-radius:99px;background:linear-gradient(90deg,var(--accent),color-mix(in srgb,var(--accent) 45%,var(--on)))}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(230px,1fr));gap:20px}
.card{position:relative;counter-increment:c;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:24px;box-shadow:var(--shadow);transition:transform .28s cubic-bezier(.2,.8,.2,1),box-shadow .28s,border-color .28s}
.card:hover{transform:translateY(-6px);border-color:color-mix(in srgb,var(--accent) 45%,var(--line));box-shadow:0 22px 44px color-mix(in srgb,var(--accent) 20%,transparent)}
.card h3{display:flex;align-items:center;gap:12px;margin:0 0 8px;font-size:1.12rem}
.card h3::before{content:counter(c,arabic-indic);display:grid;place-items:center;flex:none;width:34px;height:34px;border-radius:11px;background:var(--accent);color:var(--on);font-size:.95rem;font-weight:700;box-shadow:0 5px 14px color-mix(in srgb,var(--accent) 38%,transparent)}
.card p{margin:0;color:var(--muted)}
.kpi{font-size:2.1rem;font-weight:800;color:var(--accent-text);line-height:1.3;font-variant-numeric:tabular-nums}
.bar{background:var(--line);border-radius:999px;height:14px;overflow:hidden;margin-bottom:10px}
.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--accent),color-mix(in srgb,var(--accent) 60%,var(--on)));border-radius:999px;animation:grow 1.2s cubic-bezier(.2,.8,.2,1) both}
table{width:100%;border-collapse:separate;border-spacing:0;background:var(--card);border:1px solid var(--line);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
th,td{padding:13px 18px;border-bottom:1px solid var(--line);text-align:right}
th{background:var(--accent);color:var(--on);font-weight:700}
tbody tr{transition:background .15s}
tbody tr:hover{background:color-mix(in srgb,var(--accent) 8%,var(--card))}
tbody tr:last-child td{border-bottom:0}
label{display:block;margin-top:14px;font-weight:600}
input,textarea,select{width:100%;padding:12px 16px;border:1.5px solid var(--line);border-radius:12px;font:inherit;background:var(--card);color:var(--ink);transition:border-color .2s,box-shadow .2s}
input:focus,textarea:focus,select:focus{outline:none;border-color:var(--accent);box-shadow:0 0 0 4px color-mix(in srgb,var(--accent) 22%,transparent)}
ul{padding:0;list-style:none}
li{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:12px 4px;border-bottom:1px solid var(--line)}
footer{text-align:center;padding:34px 24px;background:var(--soft);border-top:1px solid var(--line);color:var(--muted);font-size:.92rem}
@keyframes drift{to{background-position:100% 100%,0 0,0 0}}
@keyframes grow{from{clip-path:inset(0 0 0 100%)}to{clip-path:inset(0)}}
@keyframes rise{from{opacity:0;transform:translateY(28px)}to{opacity:1;transform:none}}
@supports (animation-timeline:view()){.card,table,.bar,section>h2{animation:rise linear backwards;animation-timeline:view();animation-range:entry 0% entry 60%}}
@media (max-width:600px){header{padding:8px 14px}.hero{padding:64px 18px 56px}section{padding:36px 18px}}
@media (prefers-reduced-motion:reduce){*,*::before,*::after{animation:none!important;transition:none!important;scroll-behavior:auto!important}}
@media print{.art{display:none}header{position:static;box-shadow:none}.btn,button{display:none}.hero{background:none;color:#000;border-radius:0}body{background:#fff;color:#000}}
"""


def css(accent: str, name: str = "default") -> str:
    """The stylesheet for one accent colour and one theme (builder/themes.py): text on the accent and accent used as text
    are chosen per colour so that both keep a 4.5:1 contrast."""
    on = themes.on(accent)
    light_text = on == "#ffffff"
    base = (CSS.replace("__ACCENT__", accent).replace("__ON__", on).replace("__TEXT__", themes.text(accent, "#ffffff"))
            .replace("__DEEP__", "#000000" if light_text else "#ffffff").replace("__SHADE__", "rgba(0,0,0,.3)" if light_text else "rgba(255,255,255,.3)"))
    return base + themes.extra(accent, name)
