"""Template: Arabic display shop (catalogue + contact). It shows products; it takes no payments."""
from html import escape

from builder import base, content
from builder.spec import Spec

SAMPLE = [("منتج 1", ""), ("منتج 2", ""), ("منتج 3", "")]


def render(spec: Spec) -> dict[str, str]:
    ph = content.PLACEHOLDER
    items = spec.items or SAMPLE
    cards = "".join(
        f'<div class="card"><h3>{escape(name)}</h3><p>السعر: {escape(price) if price else ph}</p>'
        '<a class="btn" href="#contact">اطلب الآن</a></div>' for name, price in items)
    main = (f'<section id="products"><h2>المنتجات</h2><div class="cards">{cards}</div></section>\n'
            f'<section id="contact"><h2>{escape(content.SECTION_TITLES["contact"])}</h2>'
            f"<p>لإتمام الطلب تواصل معنا.</p>{base.contact(spec)}<p>هذا عرض فقط: لا يوجد دفع إلكتروني في هذا الموقع.</p></section>")
    nav = '<a href="#products">المنتجات</a><a href="#contact">تواصل معنا</a>'
    hero = f'<div class="hero"><h1>{escape(spec.name)}</h1><p>تصفّح منتجاتنا</p></div>'
    return {"index.html": base.page(spec, nav, hero, main), "style.css": base.css(spec)}
