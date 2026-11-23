"""Template: Arabic shop with a working cart (catalogue + cart + contact). The cart adds, totals and writes the order text; it takes no payments."""
import re
from html import escape

from builder import base, content, shop_js
from builder.spec import Spec

SAMPLE = [("منتج 1", ""), ("منتج 2", ""), ("منتج 3", "")]
_PRICE = re.compile(r"(\d+(?:\.\d+)?)\s*(\S*)")
CSS = """.cart{background:var(--card);border:1px solid var(--line);border-radius:var(--radius);padding:20px;box-shadow:var(--shadow)}
.cart ul{list-style:none;margin:0;padding:0}
.cart-line{display:flex;align-items:center;justify-content:space-between;gap:12px;padding:12px 0;border-bottom:1px solid var(--line)}
.cart-name{flex:1;font-weight:600}
.qty{display:inline-flex;align-items:center;gap:10px}
.qty button{min-width:44px;min-height:44px;margin:0;padding:0;font-size:1.2rem}
.cart-total{font-size:1.2rem;margin:16px 0 8px}
#cart-order{min-height:9rem;margin-top:8px;resize:vertical}
.cart-actions{display:flex;flex-wrap:wrap;gap:10px}
#cart-status{min-height:1.5em;color:var(--muted)}
nav a span{font-weight:700}
"""


def _card(name: str, price: str, ph: str) -> str:
    m = _PRICE.match(price)
    data = f' data-price="{m.group(1)}" data-unit="{escape(m.group(2))}"' if m else ""
    return (f'<div class="card" data-name="{escape(name)}"{data}><h3>{escape(name)}</h3><p>السعر: {escape(price) if price else ph}</p>'
            f'<button type="button" data-add="{escape(name)}">أضف للسلة</button></div>')


def render(spec: Spec) -> dict[str, str]:
    ph = content.PLACEHOLDER
    cards = "".join(_card(name, price, ph) for name, price in (spec.items or SAMPLE))
    cart = ('<section id="cart"><h2>السلة</h2><div class="cart"><p id="cart-empty">السلة فارغة. أضف منتجًا من القائمة.</p>'
            '<ul id="cart-lines"></ul><p class="cart-total">المجموع: <strong id="cart-total">0</strong></p>'
            '<textarea id="cart-order" readonly aria-label="نص الطلب"></textarea>'
            '<div class="cart-actions"><button type="button" id="cart-copy">نسخ الطلب</button>'
            '<button type="button" id="cart-clear">تفريغ السلة</button></div>'
            '<p id="cart-status" role="status" aria-live="polite"></p></div></section>\n')
    main = (f'<section id="products"><h2>المنتجات</h2><div class="cards">{cards}</div></section>\n{cart}'
            f'<section id="contact"><h2>{escape(content.SECTION_TITLES["contact"])}</h2>'
            f"<p>انسخ طلبك من السلة وأرسله لنا بإحدى وسائل التواصل، ونؤكده معك.</p>{base.contact(spec)}"
            "<p>لا يوجد دفع إلكتروني في هذا الموقع: السلة تجمع طلبك فقط.</p></section>")
    nav = '<a href="#products">المنتجات</a><a href="#cart">السلة (<span id="cart-count">0</span>)</a><a href="#contact">تواصل معنا</a>'
    hero = f'<div class="hero"><h1>{escape(spec.name)}</h1><p>تصفّح منتجاتنا وأضفها إلى السلة</p></div>'
    return {"index.html": base.page(spec, nav, hero, main, script=True), "style.css": base.css(spec) + CSS, "app.js": shop_js.JS}
