"""PR #13: spelling, lead-ins and titles, and code carry-over (the context also survives a cold container)."""
from agent import understand as u
from agent.orchestrator import SadahAgent


def check(cond, label):
    assert cond, label


chat = {"code": "كيف اطبع بلغة بايثون"}
check(u.rewrite("كيف اطبع بلغة باتون ؟", {})[0] == "كيف اطبع بلغة بايثون ؟", "typo: باتون")
check(u.rewrite("كم عدد سكان الكويت", {})[0] == "كم عدد سكان الكويت", "no fuzzy match outside language names")
check(u.rewrite("طيب بجافا ؟", chat)[0] == "كيف اطبع بلغة جافا", "carry-over: new language")
check(u.rewrite("قصدي كيف الطباعه فيها ؟", chat)[0] == "كيف اطبع بلغة بايثون", "carry-over: pronoun")
check(u.rewrite("تعرف الممثل جوني ديب ؟", {})[0] == "من هو جوني ديب", "title and «تعرف»")
check(u.rewrite("تعرف اسمي؟", {})[0] == "تعرف اسمي؟", "personal question untouched")
check(u.rewrite("يعني ايه book بالعربي", {})[0] == "يعني ايه book بالعربي", "«يعني ايه» untouched")

agent = SadahAgent()
r1 = agent.handle("كيف اطبع بلغة باتون ؟", session="u1")
check("print(" in r1["answer"] and r1["intent"] == "code", "typo answered with Python code")
r2 = agent.handle("طيب بجافا ؟", session="u1", context=r1["context"])
check("System.out.println" in r2["answer"], "Java after Python")
cold = SadahAgent()   # a fresh container: only the browser's context is known
r3 = cold.handle("قصدي كيف الطباعه فيها ؟", session="u2", context=r2["context"])
check("System.out.println" in r3["answer"] and "كيف أقدر أساعدك" not in r3["answer"], "pronoun after a cold start")
print("All understanding checks passed")
