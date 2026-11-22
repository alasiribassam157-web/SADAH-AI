"""Template: Arabic (RTL) landing page. Pure string rendering, every inserted value is HTML-escaped."""
from html import escape

from builder import base, content
from builder.spec import Spec


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
    hero = (f'<div class="hero"><h1>{escape(spec.name)}</h1><p>{escape(tagline)}</p>'
            '<a class="btn" href="#contact">تواصل معنا</a></div>')
    main = "\n".join(_section(k, spec, services) for k in spec.sections)
    return {"index.html": base.page(spec, nav, hero, main), "style.css": base.css(spec)}
