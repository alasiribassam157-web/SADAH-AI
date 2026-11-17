"""PR #15: age / birth-year memory, «تعرف…» stays a question, carry-over keeps the rest of the sentence."""
from agent import date_math, dialogue, personal_gate, understand as u
from agent.orchestrator import SadahAgent
from agent.topic import score_page


def check(cond, label):
    assert cond, label
    print("PASS ", label)


def say(agent, ctx, text):
    r = agent.handle(text, session="pr15", context=ctx)
    return r, r["context"]


check("من هو" not in u.rewrite("طيب تعرف كم عمري ؟", {})[0], "«تعرف كم عمري» is not «من هو كم عمري»")
check(u.rewrite("تعرف كيف اطبع ؟", {})[0] == "كيف اطبع ؟", "«تعرف كيف» stays a question")
check(u.rewrite("تعرف الممثل جوني ديب", {})[0] == "من هو جوني ديب", "a bare name still becomes «من هو»")
check(u.rewrite("اقولك عمري 21 سنه", {})[0] == "عمري 21 سنه", "«اقولك» lead-in dropped")
check(u.rewrite("وكم سعرها بالريال", {}, "الذهب")[0] == "وكم سعر الذهب بالريال", "carry_topic keeps the rest of the sentence")
code = {"code": "كيف اطبع بلغة بايثون"}
check(u.rewrite("طيب كود جافا", code)[0] == "كيف اطبع بلغة جافا", "carry_code: «كود جافا»")
check(u.rewrite("اكتبها بـ C++", code)[0] == "كيف اطبع بلغة C++", "carry_code: «بـ C++»")
check(personal_gate.asks_age("طيب تعرف كم عمري") and not personal_gate.asks_age("كم عمري لو ولدت 2005"), "age question gate")
check(not date_math.handles("عمري 21 سنه") and not date_math.handles("كم عمري"), "date_math ignores statements")
check(date_math.handles("كم عمري اذا ولدت 2005 ؟"), "date_math keeps a real age computation")
check("21" in date_math.answer("عمري 21 سنه").output, "date_math answers a stated age")
check(not dialogue.is_chatty("انا ابغى كود يرتب مصفوفة") and not dialogue.is_chatty("انا مواليد 2005"), "requests are not small talk")
check(score_page("بناء بيت", {"title": "بيت", "extract": "البيت مبنى"}) >= 0.2, "relaxed page gate")

agent, ctx = SadahAgent(), {}
r, ctx = say(agent, ctx, "طيب تعرف كم عمري ؟")
check("لم تخبرني" in r["answer"] and r["intent"] == "chat", "unknown age: asks, never «ما قدرت أحسب التاريخ»")
r, ctx = say(agent, ctx, "اقولك عمري 21 سنه")
check("21 سنة" in r["answer"] and ctx["user_age"] == "21", "age remembered in the browser context")
agent = SadahAgent()   # a cold serverless container: only the context survives
r, ctx = say(agent, ctx, "عرفت كم عمري")
check("21" in r["answer"], "age answered from the saved context")
r, ctx = say(agent, ctx, "انا مواليد 2005")
check("2005" in r["answer"] and ctx["birth_year"] == "2005", "birth year remembered")
r, ctx = say(agent, ctx, "وش تعرف عني")
check("عمرك" in r["answer"], "profile mentions the age")
print("\nAll PR #15 checks passed")
