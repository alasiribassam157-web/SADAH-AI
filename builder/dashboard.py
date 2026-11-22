"""Template: Arabic dashboard from (label, value) pairs: KPI cards, CSS bar chart and a table. No JavaScript."""
from html import escape

from builder import base, content
from builder.spec import Spec

SAMPLE = [("البند الأول", 40.0), ("البند الثاني", 65.0), ("البند الثالث", 30.0), ("البند الرابع", 80.0)]


def fmt(value: float) -> str:
    return f"{value:,.0f}" if float(value).is_integer() else f"{value:,.2f}"


def render(spec: Spec) -> dict[str, str]:
    sample = not spec.data
    data = spec.data or SAMPLE
    values = [v for _, v in data]
    top = max(values) or 1
    kpis = [("المجموع", sum(values)), ("المتوسط", sum(values) / len(values)),
            ("الأعلى", max(values)), ("عدد البنود", float(len(values)))]
    cards = "".join(f'<div class="card"><div>{k}</div><div class="kpi">{fmt(v)}</div></div>' for k, v in kpis)
    bars = "".join(f'<p>{escape(label)}: {fmt(v)}</p><div class="bar"><span style="width:{v / top * 100:.0f}%"></span></div>'
                   for label, v in data)
    rows = "".join(f"<tr><td>{escape(label)}</td><td>{fmt(v)}</td></tr>" for label, v in data)
    note = f"<p>{content.PLACEHOLDER}: هذه بيانات تجريبية، استبدلها ببياناتك.</p>" if sample else ""
    main = (f'<section id="summary"><h2>الملخص</h2>{note}<div class="cards">{cards}</div></section>\n'
            f'<section id="chart"><h2>الرسم</h2>{bars}</section>\n'
            f'<section id="table"><h2>الجدول</h2><table><thead><tr><th>البند</th><th>القيمة</th></tr></thead>'
            f'<tbody>{rows}</tbody></table></section>')
    nav = '<a href="#summary">الملخص</a><a href="#chart">الرسم</a><a href="#table">الجدول</a>'
    hero = f'<div class="hero"><h1>{escape(spec.name)}</h1><p>لوحة بيانات</p></div>'
    return {"index.html": base.page(spec, nav, hero, main), "style.css": base.css(spec)}
