"""PR #10: name capture, conversational gate, strict Wikipedia title gate, browser-side context."""
from agent import dialogue
from agent.orchestrator import SadahAgent
from agent.research import title_ok

agent = SadahAgent()


def say(msg, session="s1", context=None):
    return agent.handle(msg, session=session, context=context)


def check(cond, label):
    assert cond, label


r = say("من انا؟")
check("اسمك" in r["answer"] and r["context"]["awaiting_name"], "asks the name and waits for it")
r = say("بسام")
check("بسام" in r["answer"] and "ماجد" not in r["answer"] and r["context"]["user_name"] == "بسام", "single word = name")
check(not r["context"]["awaiting_name"], "no longer waiting")
check("أنت صديقي" in say("من انا؟")["answer"] and "بسام" in say("من انا؟")["answer"], "remembers the name")
for text in ("لقد اقول لك انا بسام", "لا يعمي انا بسام"):
    r = say(text)
    check("بسام" in r["answer"] and "حاتم" not in r["answer"] and r["intent"] == "chat", text)
r = say("هل فهمت ما اقصده ؟")
check(r["intent"] == "chat" and "ياسين" not in r["answer"] and "🔗" not in r["answer"], "chatty reply, no search")
for text in ("ركز معي", "غلط", "نعم", "بسام"):
    check(say(text, "s2")["intent"] == "chat", text)

# a cold serverless container: the browser sends back what the last response carried
cold = SadahAgent()
r = cold.handle("من انا؟", session="c9", context={"user_name": "سلمى", "user_city": "جدة", "awaiting_name": False})
check("سلمى" in r["answer"], "context restores the name")
r = cold.handle("اسمي", session="c10", context={"awaiting_name": True})
check(r["context"]["awaiting_name"] is not None, "context is returned")

# the gates themselves
check(dialogue.is_chatty("هل فهمت ما اقصده") and dialogue.is_chatty("لا يعمي انا بسام"), "chatty")
check(not dialogue.is_chatty("ما هو الذكاء الاصطناعي") and not dialogue.is_chatty("ترجم انا احبك"), "not chatty")
check(not title_ok({"title": "عبد السلام ياسين", "extract": "مفكر مغربي"}, "هل فهمت ما اقصده"), "title gate rejects")
check(not title_ok({"title": "حاتم علي", "extract": "ممثل سوري"}, "لقد اقول لك انا بسام"), "title gate rejects 2")
check(title_ok({"title": "الذكاء الاصطناعي", "extract": ""}, "الذكاء الاصطناعي"), "title gate accepts")
print("All dialogue checks passed")
