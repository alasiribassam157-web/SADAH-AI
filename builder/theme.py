"""The look of every generated site: one stylesheet, light and dark (prefers-color-scheme), responsive, printable.
Pure CSS: no fonts, images or scripts are fetched. The accent colour comes from the request; text on it is white,
and every accent in COLORS is dark enough for that."""

CSS = """:root{--accent:__ACCENT__;--ink:#1f2937;--muted:#6b7280;--bg:#ffffff;--soft:#f3f6fb;--card:#ffffff;--line:#e5e7eb;--shadow:0 10px 28px rgba(15,23,42,.08);--radius:14px}
@media (prefers-color-scheme:dark){:root{--ink:#e5e7eb;--muted:#9ca3af;--bg:#0b1220;--soft:#101a2e;--card:#162036;--line:#243049;--shadow:0 10px 28px rgba(0,0,0,.45)}}
*{box-sizing:border-box}
html{scroll-behavior:smooth}
body{margin:0;font-family:"Segoe UI",Tahoma,"Noto Naskh Arabic",Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.9;direction:rtl;text-align:right}
header{position:sticky;top:0;z-index:5;background:var(--accent);color:#fff;padding:12px 24px;display:flex;flex-wrap:wrap;gap:8px 20px;align-items:center;justify-content:space-between;box-shadow:0 2px 14px rgba(0,0,0,.18)}
header strong{font-size:1.15rem}
nav{display:flex;flex-wrap:wrap;gap:4px 18px}
header a{color:#fff;text-decoration:none;opacity:.9;padding:2px 0;border-bottom:2px solid transparent;transition:border-color .2s,opacity .2s}
header a:hover{opacity:1;border-bottom-color:#fff}
.hero{padding:88px 24px 80px;text-align:center;color:#fff;background:var(--accent);background:linear-gradient(135deg,var(--accent),color-mix(in srgb,var(--accent) 55%,#000))}
.hero h1{margin:0 0 14px;font-size:clamp(2rem,6vw,3.4rem);line-height:1.3}
.hero p{margin:0 auto;max-width:36em;font-size:1.15rem;opacity:.92}
.hero .btn{background:#fff;color:var(--accent);font-weight:700;margin-top:26px}
.btn,button{display:inline-block;margin-top:12px;padding:11px 26px;background:var(--accent);color:#fff;border:0;border-radius:999px;text-decoration:none;font:inherit;cursor:pointer;transition:transform .15s,box-shadow .15s}
.btn:hover,button:hover{transform:translateY(-2px);box-shadow:0 8px 18px rgba(0,0,0,.2)}
:focus-visible{outline:3px solid color-mix(in srgb,var(--accent) 60%,#fff);outline-offset:3px}
section{max-width:980px;margin:0 auto;padding:48px 24px;scroll-margin-top:64px}
main section:nth-child(even){box-shadow:0 0 0 100vmax var(--soft);clip-path:inset(0 -100vmax);background:var(--soft)}
h2{margin:0 0 22px;font-size:1.6rem;border-inline-start:6px solid var(--accent);padding-inline-start:14px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(210px,1fr));gap:18px}
.card{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px 22px;box-shadow:var(--shadow);transition:transform .2s}
.card:hover{transform:translateY(-4px)}
.card h3{margin:0 0 6px;font-size:1.1rem}
.card h3::before{content:"";display:inline-block;width:10px;height:10px;border-radius:50%;background:var(--accent);margin-inline-end:9px}
.card p{margin:0;color:var(--muted)}
.kpi{font-size:2rem;font-weight:800;color:var(--accent);line-height:1.3}
.bar{background:var(--line);border-radius:999px;height:14px;overflow:hidden;margin-bottom:10px}
.bar span{display:block;height:100%;background:linear-gradient(90deg,var(--accent),color-mix(in srgb,var(--accent) 60%,#fff));border-radius:999px}
table{width:100%;border-collapse:collapse;background:var(--card);border-radius:var(--radius);overflow:hidden;box-shadow:var(--shadow)}
th,td{padding:11px 16px;border-bottom:1px solid var(--line);text-align:right}
th{background:var(--accent);color:#fff}
tbody tr:nth-child(even){background:var(--soft)}
label{display:block;margin-top:14px;font-weight:600}
input{width:100%;padding:11px 14px;border:1px solid var(--line);border-radius:10px;font:inherit;background:var(--card);color:var(--ink)}
ul{padding:0;list-style:none}
li{display:flex;justify-content:space-between;align-items:center;gap:12px;padding:11px 4px;border-bottom:1px solid var(--line)}
footer{text-align:center;padding:30px 24px;background:var(--soft);color:var(--muted);font-size:.92rem}
@media (max-width:600px){header{padding:10px 16px}.hero{padding:60px 18px 52px}section{padding:34px 18px}}
@media (prefers-reduced-motion:reduce){*{transition:none!important;scroll-behavior:auto!important}}
@media print{header{position:static;box-shadow:none}.btn,button{display:none}.hero{background:none;color:#000}body{background:#fff;color:#000}}
"""


def css(accent: str) -> str:
    return CSS.replace("__ACCENT__", accent)
