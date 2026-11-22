"""Static checks of a generated site. Nothing is executed: files are parsed and inspected only."""
import re
from html.parser import HTMLParser

VOID = {"meta", "link", "img", "br", "hr", "input", "source"}
_EXTERNAL = re.compile(r"""(?:src|href)\s*=\s*["']?(?:https?:)?//""", re.I)
_SCRIPT = re.compile(r"<script\b([^>]*)>(.*?)</script>", re.I | re.S)
_BANNED_JS = ("eval(", "new Function", "Function(", "document.write", "innerHTML", "outerHTML", "insertAdjacentHTML",
              "fetch(", "XMLHttpRequest", "WebSocket", "sendBeacon", "import(", "importScripts", "http://", "https://",
              "document.cookie", "window.open", "location.href", "location.assign")
ALLOWED_FILES = {"index.html", "style.css", "app.js"}


class _Scan(HTMLParser):
    def __init__(self):
        super().__init__()
        self.stack, self.ids, self.hrefs, self.errors = [], set(), [], []
        self.tags, self.attrs = [], {}
        self.label_for, self.inputs = set(), []
        self.title = ""
        self._in_title = False

    def handle_starttag(self, tag, attrs):
        d = dict(attrs)
        self.tags.append(tag)
        self.attrs.setdefault(tag, []).append(d)
        if d.get("id"):
            self.ids.add(d["id"])
        if tag == "label" and d.get("for"):
            self.label_for.add(d["for"])
        if tag in ("input", "textarea", "select") and d.get("type") not in ("submit", "hidden"):
            self.inputs.append(d)
        if tag == "a" and (d.get("href") or "").startswith("#"):
            self.hrefs.append(d["href"][1:])
        if tag == "img" and not d.get("alt"):
            self.errors.append("صورة بلا نص بديل (alt)")
        if any(k.lower().startswith("on") for k in d):
            self.errors.append(f"معالج حدث مضمّن في <{tag}> غير مسموح")
        if tag == "title":
            self._in_title = True
        if tag not in VOID:
            self.stack.append(tag)

    def handle_endtag(self, tag):
        if tag == "title":
            self._in_title = False
        if tag in VOID:
            return
        if not self.stack or self.stack[-1] != tag:
            self.errors.append(f"وسم غير متطابق: </{tag}>")
        else:
            self.stack.pop()

    def handle_data(self, data):
        if self._in_title:
            self.title += data


def check_html(html: str) -> list[str]:
    s = _Scan()
    s.feed(html)
    out = list(s.errors) + [f"وسم غير مغلق: <{t}>" for t in s.stack]
    root = (s.attrs.get("html") or [{}])[0]
    if root.get("lang") != "ar" or root.get("dir") != "rtl":
        out.append('يجب أن يكون <html lang="ar" dir="rtl">')
    if not s.title.strip():
        out.append("عنوان الصفحة (title) فارغ")
    if not any(m.get("name") == "viewport" for m in s.attrs.get("meta", [])):
        out.append("وسم viewport مفقود")
    if s.tags.count("h1") != 1:
        out.append("يجب وجود عنوان h1 واحد بالضبط")
    out += [f"رابط داخلي إلى قسم غير موجود: #{h}" for h in s.hrefs if h not in s.ids]
    out += [f"حقل إدخال بلا تسمية: {d.get('id') or d.get('type')}" for d in s.inputs
            if d.get("id") not in s.label_for and not d.get("aria-label")]
    for attrs, body in _SCRIPT.findall(html):
        if attrs.strip() != 'src="app.js"' or body.strip():
            out.append("يُسمح فقط بسكربت app.js الخارجي عن الصفحة بلا كود مضمّن")
    if len(_SCRIPT.findall(html)) != html.lower().count("<script"):
        out.append("وسم script غير سليم")
    if _EXTERNAL.search(html):
        out.append("مورد خارجي غير مسموح في هذا القالب")
    return out


def check_js(js: str) -> list[str]:
    """The template's app.js: no dynamic code, no HTML injection, no network, balanced brackets."""
    out = [f"كود محظور في JavaScript: {b}" for b in _BANNED_JS if b in js]
    for a, b in ("()", "{}", "[]"):
        if js.count(a) != js.count(b):
            out.append(f"أقواس JavaScript غير متوازنة: {a}{b}")
    if len(js) > 20000:
        out.append("ملف JavaScript كبير جدًا")
    return out


def check_css(css: str) -> list[str]:
    out = []
    if css.count("{") != css.count("}"):
        out.append("أقواس CSS غير متوازنة")
    if "direction:rtl" not in css.replace(" ", ""):
        out.append("اتجاه RTL غير مضبوط في CSS")
    return out


def check_site(files: dict[str, str]) -> list[str]:
    """All problems of a {path: text} site (empty list = passes)."""
    if "index.html" not in files or "style.css" not in files:
        return ["index.html أو style.css مفقود"]
    out = [f"ملف غير مسموح: {p}" for p in files if p not in ALLOWED_FILES]
    out += check_html(files["index.html"]) + check_css(files["style.css"])
    uses_js = 'src="app.js"' in files["index.html"]
    if uses_js != ("app.js" in files):
        out.append("app.js والصفحة غير متطابقين")
    if "app.js" in files:
        out += check_js(files["app.js"])
    if 'href="style.css"' not in files["index.html"]:
        out.append("index.html لا يربط style.css")
    return out
