"""Templates for the three fixed-layout page kinds: portfolio, blog and event invitation.
Same rules as every template: pure string rendering, every inserted value escaped, no JavaScript.
Their sections are fixed by the kind (the spec's `sections` list is not used); text the builder cannot know
is marked with the placeholder so nobody mistakes it for a fact."""
from html import escape

from builder import base, content
from builder.spec import Spec

PH = content.PLACEHOLDER


def _cards(titles, body=PH) -> str:
    return '<div class="cards">' + "".join(f'<div class="card"><h3>{escape(t)}</h3><p>{escape(body)}</p></div>' for t in titles) + "</div>"


def _section(key: str, title: str, body: str) -> str:
    return f'<section id="{key}"><h2>{escape(title)}</h2>{body}</section>'


def _contact() -> str:
    return _section("contact", "تواصل معنا", f"<p>الهاتف: {PH}</p><p>البريد: {PH}</p>")


def _assemble(spec: Spec, tagline: str, sections: list[tuple[str, str, str]], cta: str) -> dict[str, str]:
    nav = "".join(f'<a href="#{k}">{escape(t)}</a>' for k, t, _ in sections)
    hero = (f'<div class="hero"><h1>{escape(spec.name)}</h1><p>{escape(tagline)}</p>'
            f'<a class="btn" href="#{sections[-1][0]}">{escape(cta)}</a></div>')
    main = "\n".join(_section(k, t, b) for k, t, b in sections)
    return {"index.html": base.page(spec, nav, hero, main), "style.css": base.css(spec)}


def portfolio(spec: Spec) -> dict[str, str]:
    sections = [("about", "نبذة", f"<p>{escape(spec.name)}. {PH}</p>"),
                ("skills", "المهارات", _cards(["المهارة الأولى", "المهارة الثانية", "المهارة الثالثة"])),
                ("projects", "الأعمال", _cards(["العمل الأول", "العمل الثاني", "العمل الثالث"])),
                ("contact", "تواصل معي", f"<p>البريد: {PH}</p><p>الحسابات: {PH}</p>")]
    return _assemble(spec, "ملف أعمال", sections, "تواصل معي")


def blog(spec: Spec) -> dict[str, str]:
    posts = _cards(["عنوان المقال الأول", "عنوان المقال الثاني", "عنوان المقال الثالث"], f"{PH}: ملخص المقال وتاريخه.")
    sections = [("posts", "أحدث المقالات", posts),
                ("about", "عن المدونة", f"<p>{escape(spec.name)}. {PH}</p>"),
                ("contact", "تواصل معنا", f"<p>البريد: {PH}</p>")]
    return _assemble(spec, "مدونة", sections, "تواصل معنا")


def event(spec: Spec) -> dict[str, str]:
    details = f"<p>التاريخ: {PH}</p><p>الوقت: {PH}</p><p>المكان: {PH}</p>"
    program = "<ul>" + "".join(f"<li><span>{t}</span><span>{PH}</span></li>" for t in ("الاستقبال", "الفقرة الرئيسية", "الختام")) + "</ul>"
    sections = [("details", "تفاصيل الحضور", details), ("program", "البرنامج", program),
                ("contact", "للاستفسار", f"<p>الهاتف: {PH}</p>")]
    return _assemble(spec, "يسعدنا حضوركم", sections, "للاستفسار")
