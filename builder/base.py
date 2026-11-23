"""Shared page frame and styles for every template (RTL, Arabic, no external resources)."""
from html import escape

from builder import theme
from builder.spec import Spec


def fact(spec: Spec, key: str, label: str, placeholder: bool = True) -> str:
    """One «label: value» line from the request's facts; the editable placeholder when the request gave none."""
    from builder.content import PLACEHOLDER
    value = spec.facts.get(key)
    if not value and not placeholder:
        return ""
    return f'<p>{label}: <bdi dir="ltr">{escape(value)}</bdi></p>' if key in ("phone", "email") and value else \
        f"<p>{label}: {escape(value) if value else PLACEHOLDER}</p>"


def contact(spec: Spec) -> str:
    """Contact lines: stated facts first; phone / e-mail / address keep a placeholder, opening hours only when stated."""
    return (fact(spec, "phone", "الهاتف") + fact(spec, "email", "البريد") + fact(spec, "city", "المدينة")
            + fact(spec, "hours", "ساعات العمل", placeholder=False))


def css(spec: Spec) -> str:
    return theme.css(spec.accent, spec.theme)


def page(spec: Spec, nav: str, hero: str, main: str, script: bool = False) -> str:
    """One complete HTML document; `script` adds the template's own app.js (never inline, never external)."""
    tail = '\n<script src="app.js"></script>' if script else ""
    return (f'<!DOCTYPE html>\n<html lang="{spec.lang}" dir="rtl">\n<head>\n<meta charset="utf-8">\n'
            '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
            f'<title>{escape(spec.name)}</title>\n<link rel="stylesheet" href="style.css">\n</head>\n<body>\n'
            f'<header><strong>{escape(spec.name)}</strong><nav>{nav}</nav></header>\n{hero}\n<main>\n{main}\n</main>\n'
            f'<footer>© {escape(spec.name)}</footer>{tail}\n</body>\n</html>\n')
