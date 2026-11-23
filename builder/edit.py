"""Edit a built project with an Arabic instruction, statelessly: (spec, instruction) -> (new spec, note).
Rules only, no model. Every rule that matches is applied; nothing matching means «ما فهمت», never a silent no-op.
Unsupported requests are named (same list as the builder), and a rule that cannot apply says why."""
import re
from dataclasses import dataclass, replace

from builder import content, facts, gameword, themeword
from builder.norm import n
from builder.products import products
from builder.spec import COLORS, SECTIONS, Spec
from builder.understand import SUPPORTED, refused as out_of_scope

_ADD = "(?:" + "|".join(n(w) for w in ("اضف", "اضيف", "زود", "زد", "حط", "ضيف", "ابغى", "ابي", "ابغا", "نبي", "نبغى", "نبغا", "اريد", "اضافة")) + ")"
_DEL = "(?:" + "|".join(n(w) for w in ("احذف", "شيل", "ازل", "امسح", "الغ", "الغي", "بدون", "نزل")) + ")"
_W = r"(?<![ء-ي])"
_END = r"(?![ء-ي])"
_SECTION_WORDS = {"about": ("من نحن", "نبذه", "عن الشركه"), "services": ("الخدمات", "خدمات", "خدماتنا"),
                  "gallery": ("الصور", "صور", "المعرض", "معرض"), "pricing": ("الاسعار", "اسعار", "الباقات", "باقات"),
                  "testimonials": ("الاراء", "اراء", "الشهادات", "شهادات"), "contact": ("التواصل", "تواصل", "الاتصال")}
_COLOR_RX = [(hex_, re.compile(rf"{_W}(?:ال)?{n(ar)}(?:ي)?{_END}")) for ar, hex_ in COLORS.items()]
_KIND = r"(?:منتج|صنف|خدمه|مهاره)"
_KIND_RAW = re.compile(r"\s*و?(?:منتج|صنف|خدمة|خدمه|مهارة|مهاره)\s+")
_ITEM = rf"{_KIND}\s+((?:ال)?[ء-ي]+(?:\s+(?!و?{_KIND})[ء-ي]+){{0,2}})"   # «خدمة توصيل وخدمة تغليف»: two items
_NAME = re.compile(rf"{_W}(?:ال)?اسم(?:\s+(?:المشروع|الموقع|المتجر))?(?:\s+الجديد)?\s*(?:الي|الى|ل|:)?\s+(?!(?:الي|الى|ل){_END})((?:[ء-ي]+\s*){{1,4}})")
_PAIR = re.compile(rf"([ء-ي]+(?:\s[ء-ي]+)?)\s*[:=]?\s*(\d+(?:\.\d+)?)")


@dataclass
class Edit:
    spec: Spec
    note: str
    changed: bool


def _sections(nt: str, verbs: str) -> list[str]:
    """Sections named after a verb, and after «و» («أضف قسم الصور وقسم الأسعار»)."""
    return [key for key, words in _SECTION_WORDS.items()
            if any(re.search(rf"(?:{verbs}|و)\s*(?:قسم\s+)?(?:ال)?{n(w).removeprefix('ال')}{_END}", nt)
                   and re.search(verbs, nt) for w in words)]


def _fact_note(spec: Spec, text: str) -> tuple[Spec, list[str]]:
    got = facts.extract(text).facts
    if m := re.search(rf"{_W}(?:ال)?مدين(?:ه|تنا|تي)\s*(?:الي|الى|:)?\s*({'|'.join(map(n, facts.CITIES))}){_END}", n(text)):
        got["city"] = text[m.start(1):m.end(1)]
    new = {k: v for k, v in got.items() if spec.facts.get(k) != v}
    labels = {"phone": "الجوال", "email": "البريد", "city": "المدينة", "hours": "ساعات العمل", "date": "اليوم",
              "time": "الوقت", "place": "المكان"}
    return replace(spec, facts={**spec.facts, **new}), [f"حدّثت {labels[k]}" for k in new]


def apply(spec: Spec, instruction: str) -> Edit:
    text = " ".join(instruction.split())[:300]
    nt = n(text).lower()
    # «أضف خدمة حجز طاولات»: the name of an item is a label, not a request for the feature
    asked = re.sub(_ITEM, " ", nt)
    if spec.kind == "shop" and re.search(rf"{_W}(?:ال)?سله{_END}", asked) and not out_of_scope(asked, "shop"):
        return Edit(spec, "السلة موجودة في المتجر أصلًا: يضيف الزبون منتجات ويرى المجموع وينسخ الطلب.", False)
    if hit := out_of_scope(asked, spec.kind):
        return Edit(spec, f"«{hit}» غير مدعوم بعد. {SUPPORTED}", False)
    notes, new = [], spec
    # a colour word names the colour when the sentence talks about «اللون» or says change / make it (not inside a name or an item)
    colour_text = _NAME.sub(" ", asked)
    wants_colour = re.search(rf"{_W}(?:ال)?لون|{_W}(?:خل|غير|بدل|حول|{_ADD})", colour_text)
    for hex_, rx in _COLOR_RX:
        if wants_colour and rx.search(colour_text) and hex_ != new.accent:
            new = replace(new, accent=hex_); notes.append("غيّرت اللون")
            break
    if m := _NAME.search(nt):
        name = " ".join(text[m.start(1):m.end(1)].split()[:4])
        if name and name != new.name:
            new = replace(new, name=name); notes.append(f"الاسم الآن «{name}»")
    new, got = _fact_note(new, text)
    notes += got
    new, got = gameword.switch(new, nt)
    notes += got
    new, got = themeword.switch(new, nt)
    notes += got
    new, got = _lists(new, nt, text)
    notes += got
    done = [x for x in notes if not x.startswith("!")]
    refused = [x[1:] for x in notes if x.startswith("!")]
    if done:
        return Edit(new, "، ".join(done + refused) + ".", True)
    return Edit(spec, ("، ".join(refused) + ".") if refused else _why_not(spec, nt), False)


def _lists(spec: Spec, nt: str, text: str) -> tuple[Spec, list[str]]:
    notes, new = [], spec
    if adds := _sections(nt, _ADD):
        if new.kind != "landing":
            return new, ["!هذا النوع ما فيه أقسام قابلة للإضافة"]
        if fresh := [a for a in adds if a not in new.sections]:
            new = replace(new, sections=[s for s in SECTIONS if s in {*new.sections, *fresh}]); notes.append("أضفت القسم")
    if gone := _sections(nt, _DEL):
        if "contact" in gone:
            return new, ["!قسم التواصل لازم يبقى"]
        if new.kind == "landing" and (cut := [g for g in gone if g in new.sections]):
            new = replace(new, sections=[s for s in new.sections if s not in cut]); notes.append("حذفت القسم")
    if re.search(rf"{_ADD}\s+{_ITEM}", nt) or (new.kind == "dashboard" and re.search(rf"{_ADD}\s+[ء-ي]+\s*[:=]?\s*\d", nt)):
        new, got = _add(new, nt, text)
        notes += got
    if m := re.search(rf"{_DEL}\s+(?:{_ITEM}|([ء-ي]+))", nt):
        new, got = _remove(new, (m.group(1) or m.group(2) or "").strip())
        notes += got
    return new, notes


def _add(spec: Spec, nt: str, text: str) -> tuple[Spec, list[str]]:
    if spec.kind == "dashboard":
        m = _PAIR.search(nt[re.search(_ADD, nt).end():])
        if not m:
            return spec, []
        label, value = " ".join(m.group(1).split()), float(m.group(2))
        data = [(k, v) for k, v in spec.data if n(k) != n(label)] + [(label, value)]
        if len(data) < 2:
            return spec, ["!اللوحة تحتاج نقطتين على الأقل: اكتب مثلًا «أضف يناير 10 وفبراير 20»"]
        return replace(spec, data=data), [f"أضفت «{label}»"]
    # names are sliced from the original text so they keep the typed spelling
    names = [" ".join(text[m.start(1):m.end(1)].split()) for m in re.finditer(_ITEM, nt)]
    if spec.kind == "shop":
        priced = {n(a): f"{int(b) if b.is_integer() else b} ريال" for a, b in products("فيه " + _KIND_RAW.sub(" ", text[re.search(_ITEM, nt).start(1):]))}
        new_items = [(x, priced.get(n(x), "")) for x in names]
        new_items += [(a, p) for a, p in ((a, priced[n(a)]) for a in priced) if n(a) not in {n(x) for x in names}]
        kept = [i for i in spec.items if n(i[0]) not in {n(a) for a, _ in new_items}]
        return replace(spec, items=kept + new_items), [f"أضفت «{a}»" for a, _ in new_items]
    if spec.kind in ("landing", "portfolio"):
        base = spec.services or content.defaults_for(spec.business)
        fresh = [x for x in dict.fromkeys(names) if n(x) not in {n(b) for b in base}]
        return (replace(spec, services=base + fresh), [f"أضفت «{x}»" for x in fresh]) if fresh else (spec, [])
    return spec, ["!هذا النوع ما فيه عناصر قابلة للإضافة"]


def _remove(spec: Spec, target: str) -> tuple[Spec, list[str]]:
    key = n(target).removeprefix("ال")
    same = lambda s: n(s).removeprefix("ال") == key  # noqa: E731
    if spec.kind == "shop" and any(same(i[0]) for i in spec.items):
        return replace(spec, items=[i for i in spec.items if not same(i[0])]), [f"حذفت «{target}»"]
    if spec.kind == "dashboard" and any(same(d[0]) for d in spec.data):
        rest = [d for d in spec.data if not same(d[0])]
        return (replace(spec, data=rest), [f"حذفت «{target}»"]) if len(rest) >= 2 else (spec, ["!اللوحة تحتاج نقطتين على الأقل"])
    if spec.services and any(same(s) for s in spec.services):
        return replace(spec, services=[s for s in spec.services if not same(s)]), [f"حذفت «{target}»"]
    return spec, []


def _why_not(spec: Spec, nt: str) -> str:
    if re.search(rf"{_ADD}|{_DEL}|غير|بدل|خلي|عدل", nt):
        return "فهمت أنك تريد تعديلًا لكن ما وجدت له مكانًا في هذا المشروع. جرّب: «غيّر اللون إلى أخضر»، «أضف قسم الأسعار»، «أضف خدمة …»."
    return "ما فهمت التعديل. جرّب: «غيّر اللون إلى أخضر»، «أضف قسم الأسعار»، «غيّر الاسم إلى …» أو اكتب رقم جوالك."
