"""Template: Arabic (RTL) landing page. Pure string rendering, every inserted value is HTML-escaped."""
from html import escape

from builder import content
from builder.spec import Spec

CSS = """:root{--accent:%(accent)s;--ink:#1f2937;--bg:#ffffff;--soft:#f3f4f6}
*{box-sizing:border-box}
body{margin:0;font-family:Tahoma,"Segoe UI",Arial,sans-serif;color:var(--ink);background:var(--bg);line-height:1.8;direction:rtl;text-align:right}
header{background:var(--accent);color:#fff;padding:12px 20px;display:flex;flex-wrap:wrap;gap:16px;align-items:center;justify-content:space-between}
header a{color:#fff;text-decoration:none;margin-inline-start:14px}
.hero{padding:72px 20px;text-align:center;background:var(--soft)}
.hero h1{margin:0 0 12px;font-size:2.2rem}
.btn{display:inline-block;margin-top:18px;padding:12px 28px;background:var(--accent);color:#fff;border-radius:8px;text-decoration:none}
section{max-width:960px;margin:0 auto;padding:40px 20px}
h2{border-inline-start:6px solid var(--accent);padding-inline-start:12px}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:16px}
.card{background:var(--soft);border-radius:10px;padding:18px}
footer{text-align:center;padding:24px;background:var(--soft);font-size:.9rem}
"""


def _card(title: str, body: str = "") -> str:
    return f'<div class="card"><h3>{escape(title)}</h3><p>{escape(body)}</p></div>'


def _section(key: str, spec: Spec, services: list[str]) -> str:
    title, ph = content.SECTION_TITLES[key], content.PLACEHOLDER
    if key == "about":
        body = f"<p>{escape(spec.name)} {escape(spec.business)}. {ph}</p>"
    elif key == "services":
        body = '<div class="cards">' + "".join(_card(s, ph) for s in services) + "</div>"
    elif key == "gallery":
        body = f"<p>{ph}: أضف صور مشروعك هنا.</p>"
    elif key == "pricing":
        body = '<div class="cards">' + "".join(_card(p, ph) for p in ("الباقة الأساسية", "الباقة المتقدمة")) + "</div>"
    elif key == "testimonials":
        body = f"<p>{ph}: أضف آراء عملائك الحقيقية هنا.</p>"
    else:
        body = f"<p>الهاتف: {ph}</p><p>البريد: {ph}</p><p>العنوان: {ph}</p>"
    return f'<section id="{key}"><h2>{escape(title)}</h2>{body}</section>'


def render(spec: Spec) -> dict[str, str]:
    """{path: text} of a complete static site."""
    _, tagline, services = content.for_business(spec.business or "")
    nav = "".join(f'<a href="#{k}">{escape(content.SECTION_TITLES[k])}</a>' for k in spec.sections)
    html = (f'<!DOCTYPE html>\n<html lang="{spec.lang}" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{escape(spec.name)}</title>\n<link rel="stylesheet" href="style.css">\n</head>\n<body>\n'
            f'<header><strong>{escape(spec.name)}</strong><nav>{nav}</nav></header>\n'
            f'<div class="hero"><h1>{escape(spec.name)}</h1><p>{escape(tagline)}</p>'
            '<a class="btn" href="#contact">تواصل معنا</a></div>\n<main>\n'
            + "\n".join(_section(k, spec, services) for k in spec.sections)
            + f'\n</main>\n<footer>© {escape(spec.name)}</footer>\n</body>\n</html>\n')
    return {"index.html": html, "style.css": CSS % {"accent": spec.accent}}
