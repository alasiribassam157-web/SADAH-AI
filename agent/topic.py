"""The nominal core of a question — what it is *about*, whatever words it was asked with.

«كيف ابني بيت ؟» is not a question about «ابني»: its core is the action «بناء» and the thing «بيت».
`core()` drops the asking words, turns a first-person verb into its verbal noun through its root, and
`queries()` returns the searches that cover the question, widest first.  No question is special-cased.
"""
import re

from agent import arabic

# asking words: every way Arabic (and English) opens a question or a request
_ASK = re.compile(
    r"(?<!\w)(?:كيف|كيفية|كيفيه|ازاي|شلون|وش|ايش|إيش|شو|ما|ماذا|ماهي|ماهو|لماذا|ليش|ليه|هل|متى|اين|أين|وين|من|"
    r"طريقة|طريقه|طرق|خطوات|خطوة|افضل|أفضل|اسهل|أسهل|ممكن|اقدر|أقدر|ابغى|ابي|أريد|اريد|ودي|لو سمحت|رجاء|"
    r"please|how|what|why|when|where|who|can|could|should|do|does|did|the|a|an|to|for|of|in|on|is|are|"
    r"best|way|ways|steps|step)(?!\w)", re.I)
_ME = re.compile(r"(?<!\w)(?:لي|لك|عندي|عندك|معي|معك|حقي|حقك|نفسي|بنفسي|هو|هي|هم|هذا|هذه|ذلك|تلك|"
                 r"انا|أنا|انت|أنت|انتي|أنتِ|احنا|نحن|اسمك|اسمي|"
                 r"my|me|mine|your|i|it|this|that|they)(?!\w)", re.I)
# bare verb stem -> the verbal noun an encyclopedia would title an article with.  Any person and tense
# reaches the same entry, because the one leading letter (ا/أ/ي/ت/ن) is removed first.
MASDAR = {
    "بني": "بناء", "بنى": "بناء", "طبخ": "طبخ", "زرع": "زراعة", "صلح": "إصلاح", "تعلم": "تعلم",
    "علم": "تعليم", "كتب": "كتابة", "قرا": "قراءة", "سبح": "سباحة", "رسم": "رسم", "شتري": "شراء",
    "نظف": "تنظيف", "ركب": "تركيب", "صنع": "صناعة", "سوي": "عمل", "عمل": "عمل", "حسب": "حساب",
    "فتح": "فتح", "حفظ": "حفظ", "درس": "دراسة", "سافر": "سفر", "طير": "طيران", "شغل": "تشغيل",
    "ستخدم": "استخدام", "لعب": "لعب", "غسل": "غسيل", "ربي": "تربية", "صور": "تصوير", "غني": "غناء",
    "درب": "تدريب", "سجل": "تسجيل", "حمي": "حماية", "شحن": "شحن", "قطع": "قطع", "خيط": "خياطة",
    "رتب": "ترتيب", "نقل": "نقل", "صمم": "تصميم", "برمج": "برمجة", "سوق": "قيادة", "قود": "قيادة",
    "بدا": "بداية", "جمع": "جمع", "ضرب": "ضرب", "طبع": "طباعة", "رسل": "إرسال", "خزن": "تخزين",
    "ختار": "اختيار", "عرف": "معرفة", "فهم": "فهم", "حضر": "تحضير", "جهز": "تجهيز", "ضيف": "إضافة",
}
_VERB_FORM = re.compile(r"^[اأنيت]\S{2,6}$")   # «ابني», «اتعلم», «نزرع»: a first-person / present verb


def verbal_noun(word: str) -> str | None:
    """«ابني» -> «بناء», «اتعلم» -> «تعلم», «يطبخ» -> «طبخ»: drop the one letter that marks the person."""
    clean = arabic.norm(word)
    if not _VERB_FORM.match(clean):
        return None
    bare = clean[1:]
    return MASDAR.get(bare) or MASDAR.get(arabic.strip_suffix(bare)) or MASDAR.get(clean)


def core(question: str) -> tuple[str, str]:
    """(action, subject): «كيف ابني بيت» -> («بناء», «بيت»); «ما فوائد العسل» -> («», «فوائد العسل»)."""
    text = re.sub(r"[؟?!.،,]+", " ", question)
    text = _ME.sub(" ", _ASK.sub(" ", text))
    action, rest = "", []
    for word in text.split():
        if not action and (noun := verbal_noun(word)):
            action = noun
        elif len(arabic.norm(word)) > 1:
            rest.append(word)
    return action, " ".join(rest).strip()


# nouns that name an aspect of a subject rather than a subject: «فوائد العسل» is a question about honey
_ASPECT = re.compile(r"^(?:فوائد|منافع|أضرار|اضرار|مميزات|عيوب|أسباب|اسباب|خطوات|مكونات|أنواع|انواع|"
                     r"تعريف|أهمية|اهمية|تأثير|مخاطر|شروط|benefits|causes|steps|types|effects)$")


def head_words(subject: str) -> list[str]:
    """The subject's own words, the thing itself before the aspect asked about it."""
    words = [w for w in subject.split() if len(arabic.norm(w)) >= 3]
    return sorted(words, key=lambda w: (bool(_ASPECT.match(arabic.norm(w))), -len(w)))


def queries(question: str) -> list[str]:
    """The searches that cover a question, best first — «كيف ابني بيت» asks about building, and houses;
    «لماذا السماء زرقاء» asks about the sky.  A narrower search follows the whole phrase."""
    action, subject = core(question)
    found = [f"{action} {subject}".strip(), subject, *head_words(subject)[:2], action]
    return [q for i, q in enumerate(found) if q and q not in found[:i]] or [question.strip(" ؟?")]


def asked_roots(question: str) -> set[str]:
    """What the question is really about: the roots of its action and its subject."""
    action, subject = core(question)
    return arabic.roots(f"{action} {subject}")


def relevance(question: str, text: str) -> float:
    """0…1: the share of the question's roots that `text` actually talks about."""
    asked = asked_roots(question)
    return len(asked & arabic.roots(text)) / len(asked) if asked else 0.0


def on_topic(question: str, text: str, need: float = 0.20) -> bool:
    """The general gate that replaced «the title must match»: a shared root, in the title or the body."""
    return relevance(question, text) >= need


def covers(question: str, text: str) -> bool:
    """Strict: the text talks about everything the question asks about (two thirds of it when it is long)."""
    asked = asked_roots(question)
    return bool(asked) and relevance(question, text) >= (1.0 if len(asked) <= 2 else 2 / 3)


# a page that answers something else: «السماء الزرقاء (فلم)» is not an answer about the sky
_WORKS = r"فلم|فيلم|رواية|مسلسل|أغنية|اغنية|ألبوم|البوم|لعبة|مسرحية|كتاب|film|movie|novel|song|album|game"
_QUALIFIER = re.compile(rf"\((?:{_WORKS}|توضيح|disambiguation)\)")
_IS_WORK = re.compile(rf"^.{{0,160}}?(?:هو|هي|is a|was a)\s+(?:{_WORKS})")
_ASKS_WORK = re.compile(rf"(?<!\w)(?:{_WORKS})(?!\w)", re.I)


def score_page(question: str, page: dict) -> float:
    """How well one search hit answers the question — its title counts more than its body."""
    asked = asked_roots(question)
    if not asked:
        return 0.0
    title, body = arabic.roots(page.get("title", "")), arabic.roots(page.get("extract", ""))
    extra = len(title - asked)   # «بيت الصفاة» answers about one particular house, not about houses
    lead = asked & (title | arabic.roots(page.get("extract", "")[:200]))   # a question root in the title / opening
    hit = 0.7 * (len(asked & title) / len(asked)) / (1 + (0.2 if lead else 0.6) * extra) + 0.3 * len(asked & body) / len(asked)
    if _ASKS_WORK.search(question):   # the question really is about a film or a book
        return hit
    work = _QUALIFIER.search(page.get("title", "")) or _IS_WORK.match(page.get("extract", ""))
    return hit * (0.4 if work else 1.0)


def best_page(question: str, pages, need: float = 0.20) -> dict | None:
    """Pick the hit that is really about the question, instead of trusting the first result blindly."""
    ranked = sorted(pages, key=lambda p: score_page(question, p), reverse=True)
    return ranked[0] if ranked and score_page(question, ranked[0]) >= need else None
