"""Generalization check: 25 questions the code has never seen, in wordings nobody wrote a rule for.

Nothing here may be special-cased in the agents: the point is that the stemmer, the vocabulary, the
topic core and the passage gate handle shapes that were never anticipated.  Every knowledge question
must come back with a real answer — «لم أجد إجابة موثوقة» counts as a failure — every coding question
with code, every follow-up must inherit its subject, and conversation must stay conversation.

Run offline (the agent in-process):   python -m tests.unseen_generalization_test
Run against the live site:            python tests/unseen_generalization_test.py https://sadah-app.vercel.app
"""
import json
import sys
import urllib.request

APOLOGY = "لم أجد إجابة موثوقة"
ARTICLE = "🔗 http"
# (question, kind, what the answer must contain — one is enough)
CASES = [
    # open «how» questions in dialect and in formal Arabic
    ("كيف ابني بيت ؟", "knowledge", ["بناء", "بيت", "البيوت", "منزل"]),
    ("كيف اتعلم السباحة ؟", "knowledge", ["السباحة", "سباح"]),
    ("كيف اطبخ الرز ؟", "knowledge", ["الأرز", "الرز", "طهي", "الطبخ"]),
    ("كيف ازرع شجرة ؟", "knowledge", ["الشجر", "شجرة", "زراعة", "النبات"]),
    ("شلون اسوي قهوة ؟", "knowledge", ["قهوة", "البن", "تحميص"]),
    ("كيف اكتب رسالة رسمية ؟", "knowledge", ["رسالة", "كتابة", "خطاب"]),
    # «why» questions
    ("لماذا السماء زرقاء ؟", "knowledge", ["السماء", "الضوء", "الغلاف"]),
    ("ليش الماء مهم للجسم ؟", "knowledge", ["الماء", "الجسم", "خلايا"]),
    ("لماذا تحدث الزلازل ؟", "knowledge", ["الزلازل", "الزلزال", "القشرة", "الصفائح"]),
    # aspects of a subject
    ("وش هي فوائد العسل ؟", "knowledge", ["العسل", "النحل"]),
    ("ما فوائد الرياضة ؟", "knowledge", ["الرياضة", "بدني", "الصحة"]),
    ("ما أضرار التدخين ؟", "knowledge", ["التدخين", "التبغ", "الرئة", "السرطان"]),
    ("ما هي مكونات الهواء ؟", "knowledge", ["الهواء", "النيتروجين", "الأكسجين", "غاز"]),
    # entities, in shapes nobody wrote down
    ("تعرف المخرج ستيفن سبيلبرغ ؟", "knowledge", ["سبيلبرغ", "مخرج", "أفلام"]),
    ("سمعت عن مدينة إسطنبول ؟", "knowledge", ["إسطنبول", "تركيا"]),
    # programming in dialect, with typos
    ("سوي لي دالة تجمع رقمين بايثون", "code", ["```"]),
    ("كود يرتب مصفوفة بجافا", "code", ["```"]),
    ("كيف اقرأ ملف نصي بلغة بايثن ؟", "code", ["```"]),
    ("ابغى كود يعكس نص", "code", ["```"]),
    # follow-ups that carry the subject across agents
    [("ما فوائد العسل ؟", "knowledge", ["العسل"]), ("وش فوائده الثانية ؟", "knowledge", ["عسل", "النحل"])],
    [("كيف اطبع بلغة بايثون ؟", "code", ["print"]), ("طيب بجافا ؟", "code", ["System.out"])],
    [("من هو ليونيل ميسي ؟", "knowledge", ["ميسي"]), ("وين ولد ؟", "knowledge", ["الأرجنتين", "روزاريو", "ولد"])],
    # conversation must stay conversation
    ("طيب قصدي شكرا لك", "chat", ["العفو", "أهلاً", "تسلم", "حياك"]),
    ("انت ما فهمت علي", "chat", ["قصدك", "وضّح", "أسمعك", "أعتذر"]),
    ("يا عمي انا تعبان اليوم", "chat", ["🤍", "😊", "معك", "بخير", "طمني"]),
]


def live(url: str):
    endpoint = url.rstrip("/") + "/api/chat"

    def ask(message, session, context):
        body = json.dumps({"message": message, "session": session, "context": context}).encode()
        request = urllib.request.Request(endpoint, body, {"Content-Type": "application/json"})
        with urllib.request.urlopen(request, timeout=90) as response:
            return json.load(response)
    return ask


def offline():
    from agent.orchestrator import SadahAgent
    agent = SadahAgent()
    return lambda message, session, context: agent.handle(message, session=session, context=context)


def verdict(kind: str, answer: str, want: list[str]) -> bool:
    if kind == "chat":
        return ARTICLE not in answer and any(w in answer for w in want)
    if APOLOGY in answer or len(answer) < 40:
        return False
    return any(w in answer for w in want)


def main() -> int:
    ask = live(sys.argv[1]) if len(sys.argv) > 1 else offline()
    failed = 0
    for number, case in enumerate(CASES, 1):
        turns = case if isinstance(case, list) else [case]
        session, context = f"unseen-{number}", {}
        for question, kind, want in turns:
            answer = ask(question, session, context)
            context = answer.get("context", context)
            ok = verdict(kind, answer["answer"], want)
            failed += not ok
            print(("PASS" if ok else "FAIL"), f"[{number}] {question} -> [{answer['intent']}]",
                  repr(answer["answer"][:100]))
    total = sum(len(c) if isinstance(c, list) else 1 for c in CASES)
    print(f"\n{total - failed}/{total} unseen questions answered" + ("" if failed else " — all generalised"))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
