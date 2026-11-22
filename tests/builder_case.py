"""The case() helper and the skill list shared by the builder request suites."""


def case(skill: str, q: str, **expect) -> dict:
    return {"skill": skill, "q": q, "expect": expect}


SKILLS = ["landing", "dashboard", "shop", "webapp", "portfolio", "blog", "event", "ask", "refuse"]
