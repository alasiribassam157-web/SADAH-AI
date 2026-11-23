"""Themes: six looks for every generated site, as CSS laid over the base stylesheet (builder/theme.py).

default  follows the visitor's light/dark setting;  light / dark  force one of them;  luxe  warm black with gold lines and serif headings;
simple  white, flat, no gradient hero;  glass  deep night with blurred accent light and frosted cards. Colours are chosen for contrast: text on the accent is white or near-black, whichever reads better,
and an accent used as text is lightened until it reaches 4.5:1 on the page background."""

PALETTE = {
    "light": dict(ink="#1f2937", muted="#5b6472", bg="#ffffff", soft="#f3f6fb", card="#ffffff", line="#e5e7eb", shadow="0 10px 28px rgba(15,23,42,.08)"),
    "dark": dict(ink="#e5e7eb", muted="#9ca3af", bg="#0b1220", soft="#101a2e", card="#162036", line="#243049", shadow="0 10px 28px rgba(0,0,0,.45)"),
    "luxe": dict(ink="#f1e9d8", muted="#b8ad96", bg="#0e0c09", soft="#16130e", card="#1c1812", line="#3a3223", shadow="none"),
    "simple": dict(ink="#111827", muted="#5b6472", bg="#ffffff", soft="#f7f8fa", card="#ffffff", line="#e2e5ea", shadow="none"),
    "glass": dict(ink="#eef1fb", muted="#a9b4cc", bg="#070b16", soft="#0d1425", card="#101a30", line="#26324d", shadow="0 20px 50px rgba(0,0,0,.5)"),
}
LUXE_GOLD = "#c9a24b"
_ROOT = ":root{--ink:%(ink)s;--muted:%(muted)s;--bg:%(bg)s;--soft:%(soft)s;--card:%(card)s;--line:%(line)s;--shadow:%(shadow)s%(more)s}"
_LUXE = """body{font-family:"Noto Naskh Arabic","Amiri",Georgia,serif}
header{background:var(--bg);color:var(--ink);box-shadow:none;border-bottom:2px solid var(--accent)}
header a{color:var(--ink)}
header a:hover{border-bottom-color:var(--accent)}
.hero{background:radial-gradient(circle at 50% 0,color-mix(in srgb,var(--accent) 38%,var(--bg)),var(--bg) 72%);color:var(--ink);border-radius:0;animation:none}
.hero h1{letter-spacing:.02em}
.hero .art{color:var(--accent);opacity:.2}
.hero .btn{background:var(--accent);color:var(--on)}
.card{border-color:var(--accent);border-width:1px}
th{background:var(--soft);color:var(--ink);border-bottom:2px solid var(--accent)}
"""
_SIMPLE = """:root{--radius:6px}
header{background:var(--bg);color:var(--ink);box-shadow:none;border-bottom:1px solid var(--line)}
header a{color:var(--ink)}
header a:hover{border-bottom-color:var(--accent)}
.hero{background:var(--bg);color:var(--ink);padding:72px 24px 56px;text-align:start;border-radius:0;animation:none}
.hero h1{text-shadow:none}
.hero .btn{box-shadow:none}
.hero .btn::after{content:none}
h2::before{display:none}
.card h3::before{box-shadow:none;border-radius:6px}
.btn,button{background:var(--accent);box-shadow:none}
header strong::before{display:none}
.hero p{margin:0;color:var(--muted)}
.hero .btn{background:var(--accent);color:var(--on)}
.btn,button{border-radius:6px}
.card{box-shadow:none}
.card:hover{transform:none}
h2{border:0;border-bottom:2px solid var(--accent);padding:0 0 8px;display:inline-block}
main section:nth-child(even){box-shadow:none;clip-path:none;background:none}
th{background:var(--soft);color:var(--ink)}
"""
_GLASS = """html{background:var(--bg)}
body{background:transparent}
body::before{content:"";position:fixed;inset:0;z-index:-1;background:radial-gradient(55% 45% at 88% -4%,color-mix(in srgb,var(--accent) 38%,transparent),transparent 70%),radial-gradient(45% 40% at 0 40%,color-mix(in srgb,var(--accent) 20%,#6d28d9),transparent 72%),radial-gradient(50% 40% at 70% 105%,color-mix(in srgb,var(--accent) 24%,transparent),transparent 70%)}
header{background:rgba(7,11,22,.55)}
.hero{background:none;color:var(--ink);border-radius:0;animation:none}
.hero .art{color:var(--accent);opacity:.22}
.hero h1{text-shadow:none}
@supports (background-clip:text){.hero h1{background:linear-gradient(135deg,#fff,color-mix(in srgb,var(--accent) 45%,#fff));-webkit-background-clip:text;background-clip:text;color:transparent}}
.hero p{color:var(--muted);opacity:1}
.hero .btn{background:var(--accent);color:var(--on);box-shadow:0 12px 34px color-mix(in srgb,var(--accent) 50%,transparent)}
main section:nth-child(even){box-shadow:none;clip-path:none;background:none}
.card,table{background:rgba(255,255,255,.05);border:1px solid rgba(255,255,255,.12);-webkit-backdrop-filter:blur(16px) saturate(1.3);backdrop-filter:blur(16px) saturate(1.3)}
.card:hover{background:rgba(255,255,255,.09)}
th{background:rgba(255,255,255,.08);color:var(--ink)}
tbody tr:hover{background:rgba(255,255,255,.06)}
input,textarea,select{background:rgba(255,255,255,.06);border-color:rgba(255,255,255,.14)}
footer{background:transparent}
"""
LABELS = {"default": "تلقائي", "light": "فاتح", "dark": "داكن", "luxe": "فخم", "simple": "بسيط", "glass": "زجاجي"}


def _lum(hex_: str) -> float:
    ch = [int(hex_[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    lin = [c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4 for c in ch]
    return 0.2126 * lin[0] + 0.7152 * lin[1] + 0.0722 * lin[2]


def contrast(a: str, b: str) -> float:
    hi, lo = sorted((_lum(a), _lum(b)), reverse=True)
    return (hi + 0.05) / (lo + 0.05)


def on(accent: str) -> str:
    """The text colour for use on the accent: white, or near-black when the accent is light."""
    return "#ffffff" if contrast("#ffffff", accent) >= contrast("#1a1409", accent) else "#1a1409"


def text(accent: str, bg: str) -> str:
    """The accent lightened (or darkened) just enough to read as text on `bg`."""
    target = "#ffffff" if _lum(bg) < 0.5 else "#000000"
    for step in range(0, 101, 5):
        mixed = "#" + "".join(f"{round(int(accent[i:i + 2], 16) * (100 - step) / 100 + int(target[i:i + 2], 16) * step / 100):02x}" for i in (1, 3, 5))
        if contrast(mixed, bg) >= 4.5:
            return mixed
    return target


def extra(accent: str, name: str) -> str:
    """The CSS to lay over the base stylesheet for one theme ('' for the default look in light mode)."""
    if name == "default":   # light by default; the dark-mode media query of theme.CSS gets its own accent-as-text colour
        return "@media (prefers-color-scheme:dark){:root{--accent-text:%s}}\n" % text(accent, PALETTE["dark"]["bg"])
    pal = PALETTE[name]
    more = f";--accent-text:{text(accent, pal['bg'])}"
    out = _ROOT % {**pal, "more": more} + "\n"
    return out + {"luxe": _LUXE, "simple": _SIMPLE, "glass": _GLASS}.get(name, "")
