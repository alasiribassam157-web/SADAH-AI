"""Decorative inline SVG for the hero band: dots, waves, rings, a grid, or an eight-pointed star (the Arabic geometric motif), chosen by
the kind of page and the theme. Pure markup, no files, no outside resources; it is aria-hidden and prints as nothing. The colour is
`currentColor`, set by the stylesheet, so it follows the accent and the theme."""
import math

from builder.spec import Spec


def _dots() -> str:
    return "".join(f'<circle cx="{x}" cy="{y}" r="3"/>' for x in range(25, 800, 50) for y in range(25, 300, 50))


def _waves() -> str:
    return "".join(f'<path d="M0 {y} C 130 {y - 38}, 270 {y + 38}, 400 {y} S 670 {y - 38}, 800 {y}" fill="none" stroke="currentColor" stroke-width="2"/>'
                   for y in (80, 140, 200, 260))


def _rings() -> str:
    return "".join(f'<circle cx="680" cy="70" r="{r}" fill="none" stroke="currentColor" stroke-width="2"/>' for r in (50, 100, 150, 200, 250))


def _grid() -> str:
    lines = [f'<path d="M{x} 0V300"/>' for x in range(0, 801, 50)] + [f'<path d="M0 {y}H800"/>' for y in range(0, 301, 50)]
    return f'<g fill="none" stroke="currentColor" stroke-width="1">{"".join(lines)}</g>'


def _star(cx: float, cy: float, r: float) -> str:
    pts = [(cx + (r if i % 2 == 0 else r * 0.62) * math.cos(math.pi * i / 8), cy + (r if i % 2 == 0 else r * 0.62) * math.sin(math.pi * i / 8)) for i in range(16)]
    return '<polygon points="' + " ".join(f"{x:.1f},{y:.1f}" for x, y in pts) + '" fill="none" stroke="currentColor" stroke-width="1.6"/>'


def _stars() -> str:
    return "".join(_star(x, y, 34) for y in (50, 150, 250) for x in range(60 if y == 150 else 100, 800, 120))


MOTIFS = {"dots": _dots, "waves": _waves, "rings": _rings, "grid": _grid, "stars": _stars}
BY_KIND = {"landing": "rings", "shop": "dots", "dashboard": "grid", "webapp": "grid", "portfolio": "waves", "blog": "waves",
           "event": "stars", "game": "dots"}


def motif(spec: Spec) -> str:
    """The motif a spec gets: '' when decoration is off or the theme is the flat «simple» one."""
    if not spec.art or spec.theme == "simple":
        return ""
    return "stars" if spec.theme == "luxe" else BY_KIND.get(spec.kind, "")


def hero(spec: Spec) -> str:
    name = motif(spec)
    if not name:
        return ""
    body = f'<g fill="currentColor">{MOTIFS[name]()}</g>' if name == "dots" else MOTIFS[name]()
    return f'<svg class="art" viewBox="0 0 800 300" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">{body}</svg>'
