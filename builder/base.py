"""Shared page frame and styles for every template (RTL, Arabic, no external resources)."""
from html import escape

from builder.spec import Spec

CSS = """:root{--accent:%(accent)s;--ink:#1f2937;--bg:#ffffff;--soft:#f3f4f6}
*{box-sizing:border-box}
body{margin:0;font-family:Tahoma,"Segoe UI",Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.8;direction:rtl;text-align:right}
header{background:var(--accent);color:#fff;padding:12px 20px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between}
header a{color:#fff;text-decoration:none;margin-inline-start:14px}
.hero{padding:56px 20px;text-align:center;background:var(--soft)}
.hero h1{margin:0 0 12px;font-size:2.2rem}
.btn,button{display:inline-block;margin-top:12px;padding:10px 24px;background:var(--accent);color:#fff;border:0;border-radius:8px;text-decoration:none;font:inherit;cursor:pointer}
section{max-width:960px;margin:0 auto;padding:32px 20px}
h2{border-inline-start:6px solid var(--accent);padding-inline-start:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(200px,1fr));gap:16px}
.card{background:var(--soft);border-radius:10px;padding:18px}
.kpi{font-size:1.8rem;font-weight:bold;color:var(--accent)}
.bar{background:#e5e7eb;border-radius:6px;height:16px;overflow:hidden}
.bar span{display:block;height:100%%;background:var(--accent)}
table{width:100%%;border-collapse:collapse}
th,td{padding:8px 12px;border-bottom:1px solid #e5e7eb;text-align:right}
label{display:block;margin-top:12px}
input{width:100%%;padding:10px;border:1px solid #9ca3af;border-radius:8px;font:inherit}
ul{padding:0;list-style:none}
li{display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #e5e7eb}
footer{text-align:center;padding:24px;background:var(--soft);font-size:.9rem}
"""


def css(spec: Spec) -> str:
    return CSS % {"accent": spec.accent}


def page(spec: Spec, nav: str, hero: str, main: str, script: bool = False) -> str:
    """One complete HTML document; `script` adds the template's own app.js (never inline, never external)."""
    tail = '\n<script src="app.js"></script>' if script else ""
    return (f'<!DOCTYPE html>\n<html lang="{spec.lang}" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{escape(spec.name)}</title>\n<link rel="stylesheet" href="style.css">\n</head>\n<body>\n'
            f'<header><strong>{escape(spec.name)}</strong><nav>{nav}</nav></header>\n{hero}\n<main>\n{main}\n</main>\n'
            f'<footer>© {escape(spec.name)}</footer>{tail}\n</body>\n</html>\n')
